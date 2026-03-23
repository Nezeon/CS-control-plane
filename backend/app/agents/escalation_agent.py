"""
Escalation Agent — Tier 3 Specialist (Support Lane).

Generates technical escalation summaries for L2/L3 engineering.
Lane: Support
Traits: sla_awareness, risk_assessment, customer_sentiment
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("agents.escalation")


class EscalationAgent(BaseAgent):
    """Generates technical escalation summaries for ticket escalation."""

    agent_id = "escalation_summary"

    def perceive(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")
        ticket_id = payload.get("ticket_id")

        if not summary and not ticket_id:
            raise ValueError("No ticket info in event payload")

        self.memory.set_context("summary", summary)
        self.memory.set_context("ticket_id", ticket_id)
        self.memory.set_context("ticket_data", self._load_ticket(task))
        return task

    def retrieve(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")
        context = self.memory.assemble_context(f"escalation for: {summary}")
        context["customer_memory"] = task.get("customer_memory", {})

        # Check for prior outputs from lane lead pipeline
        prior_outputs = task.get("prior_outputs", {})
        if prior_outputs:
            if "triage" in prior_outputs:
                context["triage_result"] = prior_outputs["triage"].get("output", {})
            if "troubleshoot" in prior_outputs:
                context["troubleshoot_result"] = prior_outputs["troubleshoot"].get("output", {})

        return context

    def think(self, task: dict, context: dict) -> dict:
        ticket_data = self.memory.get_context("ticket_data", {})
        customer = context.get("customer_memory", {}).get("customer", {})

        # Merge prior outputs into ticket data
        if context.get("triage_result"):
            ticket_data["triage_result"] = context["triage_result"]
        if context.get("troubleshoot_result"):
            ticket_data["troubleshoot_result"] = context["troubleshoot_result"]

        user_message = self._build_prompt(ticket_data, customer)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Similar Escalations\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=3000, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "Escalation summary generated."),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_result(self, db_session, ticket_id, result: dict) -> None:
        """Save escalation summary to the ticket's JSONB field."""
        from app.models.ticket import Ticket

        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.escalation_summary = result.get("output", result)
            db_session.commit()

    # ── Helpers ───────────────────────────────────────────────────────

    def _load_ticket(self, task: dict) -> dict:
        """Load ticket info from payload."""
        payload = task.get("payload", {})
        return {
            "summary": payload.get("summary", ""),
            "description": payload.get("description", ""),
            "severity": payload.get("severity", "P3"),
            "ticket_type": payload.get("ticket_type", ""),
            "triage_result": payload.get("triage_result"),
            "troubleshoot_result": payload.get("troubleshoot_result"),
            "jira_id": payload.get("jira_id", "N/A"),
        }

    def _build_prompt(self, ticket: dict, customer: dict) -> str:
        parts = [
            "## Ticket Being Escalated",
            f"Jira ID: {ticket.get('jira_id', 'N/A')}",
            f"Summary: {ticket.get('summary', 'N/A')}",
            f"Description: {ticket.get('description', 'N/A')[:2000]}",
            f"Severity: {ticket.get('severity', 'N/A')}",
            f"Type: {ticket.get('ticket_type', 'N/A')}",
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            f"Known Constraints: {', '.join(customer.get('known_constraints', [])) or 'None'}",
        ]

        triage = ticket.get("triage_result")
        if triage:
            parts.extend([
                "",
                "## AI Triage Results",
                f"Category: {triage.get('category', 'N/A')}",
                f"Confidence: {triage.get('confidence', 'N/A')}",
                f"Suggested Action: {triage.get('suggested_action', 'N/A')}",
                f"Root Cause Hypothesis: {triage.get('potential_root_cause', 'N/A')}",
            ])

        troubleshoot = ticket.get("troubleshoot_result")
        if troubleshoot:
            parts.extend([
                "",
                "## AI Troubleshoot Results",
                f"Root Cause: {troubleshoot.get('root_cause', 'N/A')}",
                f"Confidence: {troubleshoot.get('confidence', 'N/A')}",
                f"Estimated Time: {troubleshoot.get('estimated_time', 'N/A')}",
            ])
            steps = troubleshoot.get("resolution_steps", [])
            if steps:
                parts.append("Resolution Steps Tried:")
                for s in steps[:5]:
                    if isinstance(s, dict):
                        parts.append(f"  {s.get('step', '?')}. {s.get('action', 'N/A')}")
                    else:
                        parts.append(f"  - {s}")

        return "\n".join(parts)


AgentFactory.register("escalation_summary", EscalationAgent)
