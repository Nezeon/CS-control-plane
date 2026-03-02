import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.agents.base_agent import BaseAgent
from app.models.report import Report
from app.services import claude_service

logger = logging.getLogger("agents.qbr_value")

QBR_SYSTEM_PROMPT = """You are a QBR (Quarterly Business Review) Agent for a cybersecurity SaaS company (HivePro).
Synthesize customer data from the last 90 days into a comprehensive business review narrative.

Return ONLY valid JSON (no markdown fences):
{
  "executive_summary": "<3-5 sentence executive overview>",
  "health_trend_narrative": "<paragraph analyzing health score trends and what's driving them>",
  "ticket_analysis": {
    "summary": "<1-2 sentence ticket overview>",
    "total_tickets": <int>,
    "resolved_tickets": <int>,
    "avg_resolution_days": <float>,
    "top_categories": ["<category 1>", "<category 2>"]
  },
  "call_sentiment_analysis": {
    "summary": "<1-2 sentence sentiment overview>",
    "avg_sentiment_score": <float>,
    "trend": "<improving|stable|declining>",
    "key_concerns": ["<concern 1>", "<concern 2>"]
  },
  "achievements": ["<achievement 1>", "<achievement 2>"],
  "risks_and_concerns": ["<risk 1>", "<risk 2>"],
  "recommendations": ["<recommendation 1>", "<recommendation 2>"],
  "next_quarter_goals": ["<goal 1>", "<goal 2>"],
  "reasoning": "<2-3 sentence explanation>"
}"""


class QBRAgent(BaseAgent):
    """Generates quarterly business review content."""

    agent_name = "qbr_value"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        customer = customer_memory.get("customer", {})
        if not customer.get("name"):
            return {
                "success": False,
                "output": {"error": "No customer context available"},
                "reasoning_summary": "Customer memory is empty.",
            }

        user_message = self._build_prompt(customer_memory)

        response = claude_service.generate_sync(
            system_prompt=QBR_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=4000,
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
                "output": {"error": "Failed to parse response", "raw": response["content"][:500]},
                "reasoning_summary": "Claude returned unparseable response.",
            }

        return {
            "success": True,
            "output": parsed,
            "reasoning_summary": parsed.get("reasoning", "QBR content generated."),
        }

    def save_report(self, db_session, customer_id, result: dict) -> None:
        """Create a Report record with QBR content."""
        output = result.get("output", {})
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

        trend = health.get("trend_30d", [])
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
