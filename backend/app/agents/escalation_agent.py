import logging

from app.agents.base_agent import BaseAgent
from app.services import claude_service

logger = logging.getLogger("agents.escalation_summary")

ESCALATION_SYSTEM_PROMPT = """You are an Escalation Summary Agent for a cybersecurity SaaS company (HivePro).
Generate a technical escalation document for a ticket being escalated to L2/L3 engineering.
Include all context an engineer needs to pick up this issue quickly.

Return ONLY valid JSON (no markdown fences):
{
  "problem_statement": "<clear 2-3 sentence problem statement>",
  "investigation_summary": "<what has been investigated so far, findings>",
  "reproduction_steps": ["<step 1>", "<step 2>", "<step 3>"],
  "impact_assessment": {
    "severity": "<P1|P2|P3|P4>",
    "affected_users": "<scope of impact>",
    "business_impact": "<business-level impact description>"
  },
  "technical_details": {
    "environment": "<deployment details>",
    "error_details": "<relevant logs, error messages>",
    "related_components": ["<component 1>", "<component 2>"]
  },
  "suggested_next_steps": ["<step 1 for L2/L3>", "<step 2>"],
  "escalation_urgency": "<immediate|high|medium|low>",
  "reasoning": "<2-3 sentence explanation>"
}"""


class EscalationAgent(BaseAgent):
    """Generates technical escalation summaries for ticket escalation."""

    agent_name = "escalation_summary"
    agent_type = "support"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        payload = event.get("payload", {})
        ticket_id = payload.get("ticket_id")
        summary = payload.get("summary", "")

        if not summary and not ticket_id:
            return {
                "success": False,
                "output": {"error": "No ticket info in event payload"},
                "reasoning_summary": "Event payload missing ticket data.",
            }

        # Try to load ticket data from DB if we have ticket_id
        ticket_data = self._load_ticket(event, customer_memory)

        customer = customer_memory.get("customer", {})
        user_message = self._build_prompt(ticket_data, customer)

        response = claude_service.generate_sync(
            system_prompt=ESCALATION_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=3000,
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
                "output": {"error": "Failed to parse response", "raw": response["content"][:500]},
                "reasoning_summary": "Claude returned unparseable response.",
            }

        return {
            "success": True,
            "output": parsed,
            "reasoning_summary": parsed.get("reasoning", "Escalation summary generated."),
        }

    def save_result(self, db_session, ticket_id, result: dict) -> None:
        """Save escalation summary to the ticket's JSONB field."""
        from app.models.ticket import Ticket

        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.escalation_summary = result.get("output", {})
            db_session.commit()

    def _load_ticket(self, event: dict, customer_memory: dict) -> dict:
        """Load ticket info from payload or memory."""
        payload = event.get("payload", {})
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
