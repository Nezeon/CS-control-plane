"""
QBR (Quarterly Business Review) Agent — Tier 3 Specialist (Value Lane).

Synthesizes customer data into comprehensive business review narratives.
Reports to: Damon Reeves (value_lead)
Traits: trend_analysis, customer_sentiment
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.models.report import Report

logger = logging.getLogger("agents.qbr")


class QBRAgent(BaseAgent):
    """Generates quarterly business review content."""

    agent_id = "qbr_value"

    def perceive(self, task: dict) -> dict:
        customer = task.get("customer_memory", {}).get("customer", {})
        if not customer.get("name"):
            raise ValueError("No customer context available")

        self.memory.set_context("customer_name", customer.get("name"))
        self.memory.set_context("customer_tier", customer.get("tier"))
        return task

    def retrieve(self, task: dict) -> dict:
        customer_name = task.get("customer_name", "unknown")
        context = self.memory.assemble_context(
            f"quarterly business review for {customer_name}"
        )
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        customer_memory = context.get("customer_memory", {})
        user_message = self._build_prompt(customer_memory)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past QBR Insights\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=4000, temperature=0.3)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "QBR content generated."),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_report(self, db_session, customer_id, result: dict) -> None:
        """Create a Report record with QBR content."""
        output = result.get("output", result)
        now = datetime.now(timezone.utc)
        ninety_days_ago = now - timedelta(days=90)

        report = Report(
            id=uuid.uuid4(),
            report_type="qbr",
            customer_id=customer_id,
            title=f"Quarterly Business Review \u2014 {now.strftime('%B %Y')}",
            content=output,
            period_start=ninety_days_ago.date(),
            period_end=now.date(),
        )
        db_session.add(report)
        db_session.commit()

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(self, memory: dict) -> str:
        customer = memory.get("customer", {})
        health = memory.get("health", {})
        tickets = memory.get("tickets", {})
        calls = memory.get("calls", {})
        action_items = memory.get("action_items", [])
        alerts = memory.get("alerts", [])

        parts = [
            f"## Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Renewal Date: {customer.get('renewal_date', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            "",
            "## Current Health",
            f"Score: {health.get('current_score', 'N/A')} | Risk: {health.get('risk_level', 'N/A')}",
            f"Risk Flags: {', '.join(health.get('risk_flags', [])) or 'None'}",
            "",
            "## Health Score Trend (last 30 days)",
        ]

        trend = health.get("trend", health.get("trend_30d", []))
        if trend:
            for t in trend[:10]:
                parts.append(f"  {t.get('date', '?')}: {t.get('score', '?')}")
        else:
            parts.append("  No trend data available.")

        parts.extend([
            "",
            f"## Tickets ({tickets.get('total_recent', 0)} total, {tickets.get('open_count', 0)} open)",
        ])
        for t in tickets.get("items", [])[:10]:
            parts.append(
                f"  - [{t.get('severity', '?')}] {t.get('summary', 'N/A')} "
                f"(status: {t.get('status', '?')})"
            )

        parts.extend([
            "",
            f"## Recent Calls ({calls.get('total_recent', 0)} total)",
        ])
        for c in calls.get("items", [])[:5]:
            parts.append(
                f"  - [{c.get('sentiment', '?')}] {c.get('summary', 'N/A')[:100]}"
            )

        parts.extend([
            "",
            f"## Pending Action Items: {len(action_items)}",
            f"## Active Alerts: {len(alerts)}",
        ])

        return "\n".join(parts)


AgentFactory.register("qbr_value", QBRAgent)
