"""
Health Monitor Agent — Tier 3 Specialist (Value Lane).

Calculates customer health scores using 6 weighted factors.
Reports to: Damon Reeves (value_lead)
Traits: trend_analysis, customer_sentiment
"""

import logging
import uuid

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.models.health_score import HealthScore

logger = logging.getLogger("agents.health_monitor")


class HealthMonitorAgent(BaseAgent):
    """Calculates customer health scores using Claude AI."""

    agent_id = "health_monitor"

    def perceive(self, task: dict) -> dict:
        customer_memory = task.get("customer_memory", {})
        if customer_memory.get("error"):
            raise ValueError(f"Customer memory error: {customer_memory['error']}")

        self.memory.set_context("customer_memory", customer_memory)
        self.memory.set_context("customer_name", task.get("customer_name", ""))
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context(
            f"health analysis for {task.get('customer_name', 'unknown')}"
        )
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        customer_memory = context.get("customer_memory", {})
        user_message = self._build_prompt(customer_memory)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Similar Analyses\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        # Add trait context
        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=2048, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("summary", "Health score calculated."),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_score(self, db_session, customer_id, result: dict) -> None:
        """Create a HealthScore record from agent output."""
        output = result.get("output", result)
        score = HealthScore(
            id=uuid.uuid4(),
            customer_id=customer_id,
            score=output.get("score", 50),
            factors=output.get("factors", {}),
            risk_flags=output.get("risk_flags", []),
            risk_level=output.get("risk_level", "healthy"),
        )
        db_session.add(score)
        db_session.commit()

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(self, memory: dict) -> str:
        customer = memory.get("customer", {})
        health = memory.get("health", {})
        tickets = memory.get("tickets", {})
        calls = memory.get("calls", {})
        portfolio = memory.get("portfolio")

        parts = []

        # Portfolio-level analysis (when no specific customer)
        if portfolio:
            parts.extend([
                f"## Portfolio Analysis ({portfolio.get('total_customers', 0)} customers)",
                "",
                "## Customer Health Rankings (worst to best):",
            ])
            for c in portfolio.get("customers", []):
                risk_tag = "HIGH_RISK" if c.get("risk_level") in ("high_risk", "critical") else "WATCH" if c.get("risk_level") == "watch" else "OK"
                parts.append(
                    f"- [{risk_tag}] {c['name']} — Score: {c.get('health_score', 'N/A')}/100, "
                    f"Risk: {c.get('risk_level', 'unknown')}, Tier: {c.get('tier', 'N/A')}, "
                    f"Renewal: {c.get('renewal_date', 'N/A')}"
                )
            at_risk = portfolio.get("at_risk", [])
            if at_risk:
                parts.append(f"\n## At-Risk Customers ({len(at_risk)}):")
                for c in at_risk:
                    flags = ", ".join(c.get("risk_flags", [])) or "N/A"
                    parts.append(f"- {c['name']}: score={c.get('health_score')}, flags={flags}")
            parts.append("")
        else:
            parts.extend([
                f"## Customer: {customer.get('name', 'Unknown')}",
                f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
                f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
                f"Renewal Date: {customer.get('renewal_date', 'N/A')}",
                f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
                "",
            ])

        parts.extend([
            "## Current Health",
            f"Score: {health.get('current_score', 'N/A')} | Risk: {health.get('risk_level', 'N/A')}",
            f"Risk Flags: {', '.join(health.get('risk_flags', [])) or 'None'}",
            "",
            f"## Recent Tickets ({tickets.get('total_recent', 0)} total, {tickets.get('open_count', 0)} open)",
            self._format_tickets(tickets.get("items", [])),
            "",
            f"## Recent Calls ({calls.get('total_recent', 0)} total)",
            self._format_calls(calls.get("items", [])),
            "",
            f"## Pending Action Items: {len(memory.get('action_items', []))}",
            f"## Active Alerts: {len(memory.get('alerts', []))}",
        ])
        return "\n".join(parts)

    def _format_tickets(self, items: list) -> str:
        if not items:
            return "No recent tickets."
        lines = []
        for t in items[:10]:
            lines.append(
                f"- [{t.get('severity', '?')}] {t.get('summary', 'N/A')} "
                f"(status: {t.get('status', '?')}, type: {t.get('type', '?')})"
            )
        return "\n".join(lines)

    def _format_calls(self, items: list) -> str:
        if not items:
            return "No recent calls."
        lines = []
        for c in items[:5]:
            topics = ", ".join(c.get("key_topics", [])[:3]) or "N/A"
            lines.append(
                f"- [{c.get('sentiment', '?')}] {c.get('summary', 'N/A')[:100]} "
                f"(topics: {topics})"
            )
        return "\n".join(lines)


AgentFactory.register("health_monitor", HealthMonitorAgent)
