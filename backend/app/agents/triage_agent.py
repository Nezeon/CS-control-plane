"""
Ticket Triage Agent — Tier 3 Specialist (Support Lane).

Auto-classifies and prioritizes incoming support tickets.
Reports to: Rachel Torres (support_lead)
Traits: pattern_recognition, sla_awareness
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.services import rag_service

logger = logging.getLogger("agents.triage_agent")


class TicketTriageAgent(BaseAgent):
    """Auto-classifies and prioritizes incoming support tickets."""

    agent_id = "triage_agent"

    def perceive(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")

        if not summary:
            raise ValueError("No ticket summary in event payload")

        self.memory.set_context("summary", summary)
        self.memory.set_context("description", payload.get("description", ""))
        self.memory.set_context("severity", payload.get("severity", "P3"))
        self.memory.set_context("jira_id", payload.get("jira_id", "N/A"))
        return task

    def retrieve(self, task: dict) -> dict:
        payload = task.get("payload", {})
        summary = payload.get("summary", "")
        description = payload.get("description", "")

        # RAG: similar past tickets
        query_text = f"{summary} {description}"[:500]
        similar_tickets = rag_service.find_similar_tickets(query_text, n_results=5)
        self.memory.set_context("similar_tickets", similar_tickets)

        # Episodic + semantic memory
        context = self.memory.assemble_context(query_text)
        context["similar_tickets"] = similar_tickets
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        payload = task.get("payload", {})
        customer = context.get("customer_memory", {}).get("customer", {})
        tickets_context = context.get("customer_memory", {}).get("tickets", {})
        similar_tickets = context.get("similar_tickets", [])

        user_message = self._build_prompt(
            summary=payload.get("summary", ""),
            description=payload.get("description", ""),
            severity=payload.get("severity", "P3"),
            customer=customer,
            tickets_context=tickets_context,
            similar_tickets=similar_tickets,
            payload=payload,
        )

        # Enrich with episodic context
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Similar Triage Work\n"
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
        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("reasoning", "Ticket triaged."),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_result(self, db_session, ticket_id, result: dict) -> None:
        """Save triage result to the ticket's JSONB field."""
        from app.models.ticket import Ticket

        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.triage_result = result.get("output", result)
            db_session.commit()

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_prompt(
        self,
        summary: str,
        description: str,
        severity: str,
        customer: dict,
        tickets_context: dict,
        similar_tickets: list,
        payload: dict,
    ) -> str:
        parts = [
            "## Incoming Ticket",
            f"Summary: {summary}",
            f"Description: {description[:2000]}",
            f"Reported Severity: {severity}",
            f"Jira ID: {payload.get('jira_id', 'N/A')}",
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            f"Known Constraints: {', '.join(customer.get('known_constraints', [])) or 'None'}",
            "",
            f"## Open Tickets: {tickets_context.get('open_count', 0)} of {tickets_context.get('total_recent', 0)} recent",
        ]

        if similar_tickets:
            parts.append("")
            parts.append("## Similar Past Tickets (from vector search)")
            for st in similar_tickets[:3]:
                sim = st.get("similarity", 0)
                meta = st.get("metadata", {})
                parts.append(
                    f"- [similarity={sim:.2f}] {st.get('text', 'N/A')[:200]} "
                    f"(status: {meta.get('status', '?')}, severity: {meta.get('severity', '?')})"
                )
        else:
            parts.append("\n## No similar past tickets found in vector database.")

        parts.extend([
            "",
            "## Required Output Format",
            "Return a JSON object with these fields:",
            "- category: one of [Deployment, Scan, Connector, Performance, UI, Integration]",
            "- severity: one of [P0, P1, P2, P3] (P0=critical, P1=high, P2=medium, P3=low)",
            "- suggested_action: specific next step for the support engineer",
            "- potential_root_cause: your best assessment of the root cause",
            "- confidence: float 0.0-1.0 indicating classification confidence",
            "- diagnostics: {required_script: string or null, kb_article: string or null}",
            "- similar_ticket_ids: list of similar ticket IDs from the vector search above",
            '- email_draft: a brief customer acknowledgment email (2-3 sentences confirming receipt, category, and expected next steps). Start with "Dear [Customer],"',
            "- reasoning: brief explanation of your classification logic",
        ])

        return "\n".join(parts)


AgentFactory.register("triage_agent", TicketTriageAgent)
