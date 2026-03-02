import json
import logging
import uuid
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.models.health_score import HealthScore
from app.services import claude_service

logger = logging.getLogger("agents.health_monitor")

HEALTH_SYSTEM_PROMPT = """You are a Customer Health Monitor for a cybersecurity SaaS company (HivePro).
Analyze the customer context and calculate a health score from 0-100 using these 6 weighted factors:

1. **Product Adoption** (weight: 0.20) — Active usage, feature utilization, deployment completeness
2. **Support Health** (weight: 0.20) — Open ticket count, severity distribution, resolution trends
3. **Engagement** (weight: 0.15) — Call frequency, responsiveness, stakeholder participation
4. **Sentiment** (weight: 0.15) — Call sentiment trends, satisfaction signals, complaint frequency
5. **Outcome Delivery** (weight: 0.15) — Whether the product is delivering on promised value
6. **Contract/Renewal Risk** (weight: 0.15) — Days to renewal, contract expansion signals, churn indicators

Return ONLY valid JSON (no markdown fences):
{
  "score": <int 0-100>,
  "risk_level": "<healthy|at_risk|critical>",
  "factors": {
    "product_adoption": {"score": <0-100>, "rationale": "<1 sentence>"},
    "support_health": {"score": <0-100>, "rationale": "<1 sentence>"},
    "engagement": {"score": <0-100>, "rationale": "<1 sentence>"},
    "sentiment": {"score": <0-100>, "rationale": "<1 sentence>"},
    "outcome_delivery": {"score": <0-100>, "rationale": "<1 sentence>"},
    "contract_risk": {"score": <0-100>, "rationale": "<1 sentence>"}
  },
  "risk_flags": ["<flag1>", "<flag2>"],
  "summary": "<2-3 sentence overall assessment>",
  "recommended_actions": ["<action1>", "<action2>"]
}"""


class HealthMonitorAgent(BaseAgent):
    """Calculates customer health scores using Claude AI."""

    agent_name = "health_monitor"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        if customer_memory.get("error"):
            return {
                "success": False,
                "output": {"error": customer_memory["error"]},
                "reasoning_summary": "Failed to load customer memory.",
            }

        user_message = self._build_prompt(customer_memory)
        response = claude_service.generate_sync(
            system_prompt=HEALTH_SYSTEM_PROMPT,
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
            "reasoning_summary": parsed.get("summary", "Health score calculated."),
        }

    def save_score(self, db_session, customer_id, result: dict) -> None:
        """Create a HealthScore record from agent output."""
        output = result.get("output", {})
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

    def _build_prompt(self, memory: dict) -> str:
        customer = memory.get("customer", {})
        health = memory.get("health", {})
        tickets = memory.get("tickets", {})
        calls = memory.get("calls", {})

        parts = [
            f"## Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
            f"Renewal Date: {customer.get('renewal_date', 'N/A')}",
            f"Integrations: {', '.join(customer.get('integrations', [])) or 'None'}",
            "",
            f"## Current Health",
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
        ]
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
