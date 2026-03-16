"""
Troubleshooter Agent — Tier 3 Specialist (Support Lane).

Analyzes tickets for root cause and suggests resolution steps.
Reports to: Rachel Torres (support_lead)
Traits: root_cause_analysis, pattern_recognition
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.services import rag_service

logger = logging.getLogger("agents.troubleshooter")


class TroubleshootAgent(BaseAgent):
    """Analyzes tickets for root cause and suggests resolution steps."""

    agent_id = "troubleshooter"

    def perceive(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")

        if not summary:
            raise ValueError("No ticket summary in event payload")

        self.memory.set_context("summary", summary)
        self.memory.set_context("description", payload.get("description", ""))
        self.memory.set_context("severity", payload.get("severity", "P3"))
        self.memory.set_context("triage_result", payload.get("triage_result"))
        return task

    def retrieve(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")
        description = payload.get("description", "")

        # RAG: similar resolved tickets
        query_text = f"{summary} {description}"[:500]
        similar_tickets = rag_service.find_similar_tickets(
            query_text, n_results=5, where={"status": "resolved"}
        )
        self.memory.set_context("similar_tickets", similar_tickets)

        # Episodic + semantic memory
        context = self.memory.assemble_context(query_text)
        context["similar_tickets"] = similar_tickets
        context["customer_memory"] = task.get("customer_memory", {})

        # Check for prior triage output passed by lane lead
        prior_outputs = task.get("prior_outputs", {})
        if prior_outputs and "triage" in prior_outputs:
            triage_output = prior_outputs["triage"].get("output", {})
            context["triage_result"] = triage_output

        return context

    def think(self, task: dict, context: dict) -> dict:
        payload = task.get("payload", {})
        customer = context.get("customer_memory", {}).get("customer", {})
        similar_tickets = context.get("similar_tickets", [])
        triage_result = context.get("triage_result") or payload.get("triage_result")

        user_message = self._build_prompt(
            summary=payload.get("summary", ""),
            description=payload.get("description", ""),
            severity=payload.get("severity", "P3"),
            triage_result=triage_result,
            customer=customer,
            similar_tickets=similar_tickets,
        )

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Similar Troubleshooting\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=3000, temperature=0.3)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "Troubleshooting complete."),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_result(self, db_session, ticket_id, result: dict) -> None:
        """Save troubleshoot result to the ticket's JSONB field."""
        from app.models.ticket import Ticket

        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.troubleshoot_result = result.get("output", result)
            db_session.commit()

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(
        self, summary: str, description: str, severity: str,
        triage_result: dict | None, customer: dict, similar_tickets: list,
    ) -> str:
        parts = [
            "## Ticket to Troubleshoot",
            f"Summary: {summary}",
            f"Description: {description[:2000]}",
            f"Severity: {severity}",
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            f"Known Constraints: {', '.join(customer.get('known_constraints', [])) or 'None'}",
        ]

        if triage_result:
            parts.extend([
                "",
                "## Triage Results (already performed)",
                f"Category: {triage_result.get('category', 'N/A')}",
                f"Suggested Action: {triage_result.get('suggested_action', 'N/A')}",
                f"Potential Root Cause: {triage_result.get('potential_root_cause', 'N/A')}",
            ])

        if similar_tickets:
            parts.extend(["", "## Similar Resolved Tickets (from vector search)"])
            for st in similar_tickets[:3]:
                sim = st.get("similarity", 0)
                meta = st.get("metadata", {})
                parts.append(
                    f"- [similarity={sim:.2f}] {st.get('text', 'N/A')[:200]} "
                    f"(status: {meta.get('status', '?')}, severity: {meta.get('severity', '?')})"
                )
        else:
            parts.append("\n## No similar resolved tickets found.")

        return "\n".join(parts)


AgentFactory.register("troubleshooter", TroubleshootAgent)
