import json
import logging

from app.agents.base_agent import BaseAgent
from app.services import claude_service, rag_service

logger = logging.getLogger("agents.ticket_triage")

TRIAGE_SYSTEM_PROMPT = """You are a Ticket Triage Agent for a cybersecurity SaaS company (HivePro).
Analyze the incoming support ticket with customer context and similar past tickets.
Classify, prioritize, and suggest actions.

Return ONLY valid JSON (no markdown fences):
{
  "category": "<scan_failure|connector_issue|deployment|configuration|performance|access_control|integration|other>",
  "confirmed_severity": "<P1|P2|P3|P4>",
  "suggested_action": "<1-2 sentence recommended next step>",
  "potential_root_cause": "<1-2 sentence hypothesis>",
  "is_duplicate": <true|false>,
  "duplicate_of": "<ticket_id or null>",
  "estimated_effort": "<low|medium|high>",
  "requires_escalation": <true|false>,
  "escalation_reason": "<reason or null>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<2-3 sentence explanation of triage decisions>"
}"""


class TicketTriageAgent(BaseAgent):
    """Auto-classifies and prioritizes incoming support tickets."""

    agent_name = "ticket_triage"
    agent_type = "support"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        payload = event.get("payload", {})
        summary = payload.get("summary", "")
        description = payload.get("description", "")
        severity = payload.get("severity", "P3")

        if not summary:
            return {
                "success": False,
                "output": {"error": "No ticket summary in event payload"},
                "reasoning_summary": "Event payload missing summary field.",
            }

        # Query RAG for similar past tickets
        query_text = f"{summary} {description}"[:500]
        similar_tickets = rag_service.find_similar_tickets(query_text, n_results=5)

        customer = customer_memory.get("customer", {})
        tickets_context = customer_memory.get("tickets", {})

        user_message = self._build_prompt(
            summary=summary,
            description=description,
            severity=severity,
            customer=customer,
            tickets_context=tickets_context,
            similar_tickets=similar_tickets,
            payload=payload,
        )

        response = claude_service.generate_sync(
            system_prompt=TRIAGE_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=2048,
            temperature=0.2,
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
            "reasoning_summary": parsed.get("reasoning", "Ticket triaged."),
        }

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
            f"## Incoming Ticket",
            f"Summary: {summary}",
            f"Description: {description[:2000]}",
            f"Reported Severity: {severity}",
            f"Jira ID: {payload.get('jira_id', 'N/A')}",
            "",
            f"## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            f"Known Constraints: {', '.join(customer.get('known_constraints', [])) or 'None'}",
            "",
            f"## Open Tickets: {tickets_context.get('open_count', 0)} of {tickets_context.get('total_recent', 0)} recent",
        ]

        # Add similar past tickets from RAG
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

        return "\n".join(parts)
