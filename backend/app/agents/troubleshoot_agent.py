import logging
from uuid import UUID

from app.agents.base_agent import BaseAgent
from app.services import claude_service, rag_service

logger = logging.getLogger("agents.troubleshooter")

TROUBLESHOOT_SYSTEM_PROMPT = """You are a Troubleshooter Agent for a cybersecurity SaaS company (HivePro).
Analyze the support ticket along with customer context and similar resolved tickets.
Determine root cause, suggest resolution steps, and draft customer communication.

Return ONLY valid JSON (no markdown fences):
{
  "root_cause": "<1-2 sentence root cause hypothesis>",
  "confidence": <float 0.0-1.0>,
  "evidence": ["<evidence point 1>", "<evidence point 2>"],
  "resolution_steps": [
    {"step": 1, "action": "<what to do>", "details": "<how to do it>"},
    {"step": 2, "action": "<what to do>", "details": "<how to do it>"}
  ],
  "estimated_time": "<e.g. 2-4 hours>",
  "requires_customer_action": <true|false>,
  "customer_communication_draft": "<professional email draft to customer explaining the issue and next steps>",
  "reasoning": "<2-3 sentence explanation of troubleshooting decisions>"
}"""


class TroubleshootAgent(BaseAgent):
    """Analyzes tickets for root cause and suggests resolution steps."""

    agent_name = "troubleshooter"
    agent_type = "support"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        payload = event.get("payload", {})
        summary = payload.get("summary", "")
        description = payload.get("description", "")

        if not summary:
            return {
                "success": False,
                "output": {"error": "No ticket summary in event payload"},
                "reasoning_summary": "Event payload missing summary field.",
            }

        # Query RAG for similar resolved tickets
        query_text = f"{summary} {description}"[:500]
        similar_tickets = rag_service.find_similar_tickets(
            query_text, n_results=5, where={"status": "resolved"}
        )

        customer = customer_memory.get("customer", {})
        user_message = self._build_prompt(
            summary=summary,
            description=description,
            severity=payload.get("severity", "P3"),
            triage_result=payload.get("triage_result"),
            customer=customer,
            similar_tickets=similar_tickets,
        )

        response = claude_service.generate_sync(
            system_prompt=TROUBLESHOOT_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=3000,
            temperature=0.3,
        )

        if "error" in response:
            return {
                "success": False,
                "output": response,
                "reasoning_summary": f"Claude API error: {response.get('detail', response.get('error'))}",
            }

        parsed = claude_service.parse_json_response(response["content"])
        if "error" in parsed and parsed["error"] == "parse_failed":
            return {
                "success": False,
                "output": {"error": "Failed to parse Claude response", "raw": response["content"][:500]},
                "reasoning_summary": "Claude returned unparseable response.",
            }

        return {
            "success": True,
            "output": parsed,
            "reasoning_summary": parsed.get("reasoning", "Troubleshooting complete."),
        }

    def save_result(self, db_session, ticket_id, result: dict) -> None:
        """Save troubleshoot result to the ticket's JSONB field."""
        from app.models.ticket import Ticket

        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.troubleshoot_result = result.get("output", {})
            db_session.commit()

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
