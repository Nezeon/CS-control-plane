"""
Health Monitor Agent — Tier 3 Specialist (Value Lane).

Runs daily health checks on every customer using 5 deterministic checks
backed by real data sources (Jira tickets, Fathom calls, health history,
alerts, customer DB). Claude is used only for narrative generation.

Lane: Value
Traits: trend_analysis, risk_assessment, customer_sentiment
"""

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.models.health_score import HealthScore

logger = logging.getLogger("agents.health_monitor")

# Weights for each health check (must sum to 1.0)
CHECK_WEIGHTS = [0.25, 0.20, 0.20, 0.20, 0.15]


class HealthMonitorAgent(BaseAgent):
    """Computes customer health scores using 5 deterministic checks + Claude narrative."""

    agent_id = "health_monitor"

    # ── 5 Deterministic Health Checks ─────────────────────────────────

    def _check_ticket_severity(self, db, customer_id) -> dict:
        """Check open P0/P1 ticket load and aging."""
        if not customer_id:
            return {"score": 100, "flag": None, "detail": "No customer ID"}

        rows = db.execute(text("""
            SELECT severity, created_at
            FROM tickets
            WHERE customer_id = CAST(:cid AS uuid)
              AND status NOT IN ('resolved', 'closed')
              AND severity IN ('P0', 'P1', 'critical')
        """), {"cid": str(customer_id)}).fetchall()

        if not rows:
            return {"score": 100, "flag": None, "detail": "No open P0/P1 tickets"}

        now = datetime.now(timezone.utc)
        score = 100
        aging_found = False

        for row in rows:
            sev = row[0]
            created = row[1]
            age_days = (now - created).days if created else 0

            if sev in ("P0", "critical"):
                score -= 20
                if age_days > 3:
                    aging_found = True
            elif sev == "P1":
                score -= 10
                if age_days > 5:
                    aging_found = True

        score = max(score, 0)
        flag = "p0_tickets_aging" if aging_found else None
        detail = f"{len(rows)} open critical tickets"
        if aging_found:
            detail += " (some aging beyond threshold)"
        return {"score": score, "flag": flag, "detail": detail}

    def _check_call_sentiment(self, db, customer_id) -> dict:
        """Check recent call sentiment trend from Fathom data."""
        if not customer_id:
            return {"score": 100, "flag": None, "detail": "No customer ID"}

        rows = db.execute(text("""
            SELECT sentiment
            FROM call_insights
            WHERE customer_id = CAST(:cid AS uuid)
              AND processed_at > NOW() - INTERVAL '14 days'
            ORDER BY processed_at DESC
            LIMIT 5
        """), {"cid": str(customer_id)}).fetchall()

        if not rows:
            return {"score": 100, "flag": None, "detail": "No recent calls"}

        negative_count = sum(
            1 for row in rows if row[0] in ("negative", "mixed")
        )

        if negative_count == 0:
            score = 100
        elif negative_count == 1:
            score = 80
        elif negative_count == 2:
            score = 50
        else:
            score = 20

        flag = "negative_sentiment_trend" if negative_count >= 2 else None
        detail = f"{negative_count}/{len(rows)} recent calls with negative/mixed sentiment"
        return {"score": score, "flag": flag, "detail": detail}

    def _check_renewal_proximity(self, customer_memory: dict) -> dict:
        """Check renewal date proximity combined with risk flags."""
        customer = customer_memory.get("customer", {})
        renewal_str = customer.get("renewal_date")

        if not renewal_str:
            return {"score": 100, "flag": None, "detail": "No renewal date set"}

        try:
            if isinstance(renewal_str, str):
                renewal_date = datetime.fromisoformat(renewal_str).date()
            else:
                renewal_date = renewal_str
            days_until = (renewal_date - datetime.now(timezone.utc).date()).days
        except (ValueError, TypeError):
            return {"score": 100, "flag": None, "detail": "Invalid renewal date"}

        existing_flags = customer_memory.get("health", {}).get("risk_flags", [])
        has_risk = len(existing_flags) > 0

        if days_until > 180:
            score = 100
        elif days_until > 90:
            score = 80
        elif days_until > 30:
            score = 50
        else:
            score = 20

        flag = None
        if days_until <= 30 and has_risk:
            flag = "renewal_critical"
        elif days_until <= 90 and has_risk:
            flag = "renewal_at_risk"

        detail = f"Renewal in {days_until} days"
        if has_risk:
            detail += f" (with {len(existing_flags)} existing risk flags)"
        return {"score": score, "flag": flag, "detail": detail}

    def _check_health_trend(self, db, customer_id) -> dict:
        """Check if health score is declining vs 7 days ago."""
        if not customer_id:
            return {"score": 100, "flag": None, "detail": "No customer ID"}

        rows = db.execute(text("""
            SELECT score, calculated_at
            FROM health_scores
            WHERE customer_id = CAST(:cid AS uuid)
            ORDER BY calculated_at DESC
            LIMIT 2
        """), {"cid": str(customer_id)}).fetchall()

        if len(rows) < 2:
            return {"score": 100, "flag": None, "detail": "Not enough historical data"}

        latest_score = rows[0][0]
        previous_score = rows[1][0]
        drop = previous_score - latest_score

        if drop <= 0:
            score = 100
            detail = f"Stable/improving (latest={latest_score}, previous={previous_score})"
        elif drop <= 5:
            score = 90
            detail = f"Minor drop of {drop} points"
        elif drop <= 15:
            score = 60
            detail = f"Moderate drop of {drop} points"
        else:
            score = 30
            detail = f"Significant drop of {drop} points"

        flag = "health_declining" if drop > 15 else None
        return {"score": score, "flag": flag, "detail": detail}

    def _check_alert_load(self, db, customer_id) -> dict:
        """Check open high/critical alert count."""
        if not customer_id:
            return {"score": 100, "flag": None, "detail": "No customer ID"}

        result = db.execute(text("""
            SELECT COUNT(*)
            FROM alerts
            WHERE customer_id = CAST(:cid AS uuid)
              AND status = 'open'
              AND severity IN ('critical', 'high')
        """), {"cid": str(customer_id)}).scalar()

        count = result or 0

        if count == 0:
            score = 100
        elif count == 1:
            score = 70
        elif count == 2:
            score = 40
        else:
            score = 20

        flag = "high_alert_load" if count > 0 else None
        detail = f"{count} open high/critical alerts"
        return {"score": score, "flag": flag, "detail": detail}

    # ── Score Computation ─────────────────────────────────────────────

    def _compute_health_score(
        self, checks: list[dict]
    ) -> tuple[int, list[str], str]:
        """Weighted average of 5 checks → (score, risk_flags, risk_level)."""
        score = round(sum(c["score"] * w for c, w in zip(checks, CHECK_WEIGHTS)))
        score = max(0, min(100, score))
        flags = [c["flag"] for c in checks if c.get("flag")]

        if score >= 70:
            risk_level = "healthy"
        elif score >= 50:
            risk_level = "watch"
        elif score >= 30:
            risk_level = "high_risk"
        else:
            risk_level = "critical"

        return score, flags, risk_level

    # ── Pipeline Stages ───────────────────────────────────────────────

    def perceive(self, task: dict) -> dict:
        customer_memory = task.get("customer_memory", {})
        customer_id = task.get("customer_id")
        db = self._current_db

        if not db:
            raise ValueError("No database session available")

        # Run 5 deterministic health checks
        checks = [
            self._check_ticket_severity(db, customer_id),
            self._check_call_sentiment(db, customer_id),
            self._check_renewal_proximity(customer_memory),
            self._check_health_trend(db, customer_id),
            self._check_alert_load(db, customer_id),
        ]

        score, flags, risk_level = self._compute_health_score(checks)

        # Store in working memory for later stages
        self.memory.set_context("checks", checks)
        self.memory.set_context("health_score", score)
        self.memory.set_context("risk_flags", flags)
        self.memory.set_context("risk_level", risk_level)
        self.memory.set_context("customer_name", task.get("customer_name", ""))

        factors = {
            "ticket_severity": checks[0]["score"],
            "call_sentiment": checks[1]["score"],
            "renewal_proximity": checks[2]["score"],
            "health_trend": checks[3]["score"],
            "alert_load": checks[4]["score"],
        }
        self.memory.set_context("factors", factors)

        logger.info(
            f"[HealthMonitor] {task.get('customer_name', 'unknown')}: "
            f"score={score}, risk={risk_level}, flags={flags}"
        )
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context(
            f"health analysis for {task.get('customer_name', 'unknown')}"
        )
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        customer_memory = context.get("customer_memory", {})
        customer = customer_memory.get("customer", {})
        checks = self.memory.get_context("checks") or []
        score = self.memory.get_context("health_score") or 50
        risk_level = self.memory.get_context("risk_level") or "unknown"
        risk_flags = self.memory.get_context("risk_flags") or []
        factors = self.memory.get_context("factors") or {}

        user_message = self._build_prompt(
            customer=customer,
            checks=checks,
            score=score,
            risk_level=risk_level,
            risk_flags=risk_flags,
            factors=factors,
            customer_memory=customer_memory,
        )

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Health Analyses\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=2048, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}

        score = self.memory.get_context("health_score") or 50
        risk_level = self.memory.get_context("risk_level") or "unknown"
        risk_flags = self.memory.get_context("risk_flags") or []
        factors = self.memory.get_context("factors") or {}

        return {
            "success": True,
            "score": score,
            "health_score": score,
            "risk_level": risk_level,
            "risk_flags": risk_flags,
            "factors": factors,
            "summary": thinking.get("summary", "Health score calculated."),
            "recommendations": thinking.get("recommendations", []),
            "draft_jira_ticket": thinking.get("draft_jira_ticket"),
            "reasoning_summary": thinking.get("summary", "Health score calculated."),
        }

    # ── DB Save ───────────────────────────────────────────────────────

    def save_score(self, db_session, customer_id, result: dict) -> None:
        """Create a HealthScore record from agent output."""
        output = result.get("output", result)
        score = HealthScore(
            id=uuid.uuid4(),
            customer_id=customer_id,
            score=output.get("score", output.get("health_score", 50)),
            factors=output.get("factors", {}),
            risk_flags=output.get("risk_flags", []),
            risk_level=output.get("risk_level", "healthy"),
        )
        db_session.add(score)
        db_session.commit()

    # ── Prompt Building ───────────────────────────────────────────────

    def _build_prompt(
        self,
        customer: dict,
        checks: list[dict],
        score: int,
        risk_level: str,
        risk_flags: list[str],
        factors: dict,
        customer_memory: dict,
    ) -> str:
        check_names = [
            "Ticket Severity Load",
            "Call Sentiment Trend",
            "Renewal Proximity",
            "Historical Health Trend",
            "Open Alert Load",
        ]

        parts = [
            f"## Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Renewal Date: {customer.get('renewal_date', 'N/A')}",
            "",
            f"## Computed Health Score: {score}/100 (Risk Level: {risk_level})",
            f"Risk Flags: {', '.join(risk_flags) or 'None'}",
            "",
            "## Health Check Results:",
        ]

        for name, check, weight in zip(check_names, checks, CHECK_WEIGHTS):
            flag_marker = " [FLAG]" if check.get("flag") else ""
            parts.append(
                f"- {name} (weight {int(weight*100)}%): "
                f"score={check['score']}/100{flag_marker} — {check['detail']}"
            )

        # Add ticket context
        tickets = customer_memory.get("tickets", {})
        parts.extend([
            "",
            f"## Recent Tickets: {tickets.get('total_recent', 0)} total, "
            f"{tickets.get('open_count', 0)} open",
        ])

        # Add call context
        calls = customer_memory.get("calls", {})
        parts.extend([
            f"## Recent Calls: {calls.get('total_recent', 0)} total",
        ])

        # Add alert context
        alerts = customer_memory.get("alerts", [])
        if alerts:
            parts.append(f"## Active Alerts: {len(alerts)}")

        parts.extend([
            "",
            "## Required Output Format",
            "Return a JSON object with these fields:",
            '- summary: 2-3 sentence narrative of this customer\'s health status',
            '- recommendations: array of 1-3 specific actionable recommendations',
            '- draft_jira_ticket: object with "summary" and "priority" fields '
            'if risk_level is not "healthy", otherwise null',
            '- reasoning: brief explanation of your analysis',
        ])

        return "\n".join(parts)


AgentFactory.register("health_monitor", HealthMonitorAgent)
