import json
import logging
import uuid
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.models.call_insight import CallInsight
from app.services import claude_service

logger = logging.getLogger("agents.call_intelligence")

CALL_INTEL_SYSTEM_PROMPT = """You are a Call Intelligence Agent for a cybersecurity SaaS company (HivePro).
Analyze the call transcript and extract structured insights.

Return ONLY valid JSON (no markdown fences):
{
  "summary": "<3-5 sentence executive summary of the call>",
  "sentiment": "<positive|neutral|negative|mixed>",
  "sentiment_score": <float from -1.0 to 1.0>,
  "key_topics": ["<topic1>", "<topic2>", ...],
  "decisions": ["<decision1>", "<decision2>", ...],
  "action_items": [
    {"title": "<action>", "owner": "<person>", "deadline": "<date or null>"}
  ],
  "risks": ["<risk1>", "<risk2>", ...],
  "customer_recap_draft": "<2-3 paragraph professional email recap suitable to send to the customer>"
}"""


class CallIntelAgent(BaseAgent):
    """Extracts structured insights from call transcripts using Claude AI."""

    agent_name = "call_intelligence"
    agent_type = "value"

    def execute(self, event: dict, customer_memory: dict) -> dict:
        payload = event.get("payload", {})
        transcript = payload.get("transcript", "")
        if not transcript:
            return {
                "success": False,
                "output": {"error": "No transcript in event payload"},
                "reasoning_summary": "Event payload missing transcript field.",
            }

        customer = customer_memory.get("customer", {})
        user_message = self._build_prompt(transcript, customer, payload)

        response = claude_service.generate_sync(
            system_prompt=CALL_INTEL_SYSTEM_PROMPT,
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
            "reasoning_summary": f"Extracted insights: sentiment={parsed.get('sentiment', '?')}, "
            f"{len(parsed.get('key_topics', []))} topics, "
            f"{len(parsed.get('action_items', []))} action items.",
        }

    def save_insight(self, db_session, customer_id, event_payload: dict, result: dict) -> None:
        """Create a CallInsight record from agent output."""
        output = result.get("output", {})
        insight = CallInsight(
            id=uuid.uuid4(),
            customer_id=customer_id,
            fathom_recording_id=event_payload.get("recording_id"),
            call_date=datetime.now(timezone.utc),
            participants=event_payload.get("participants", []),
            summary=output.get("summary"),
            decisions=output.get("decisions", []),
            action_items=output.get("action_items", []),
            risks=output.get("risks", []),
            sentiment=output.get("sentiment"),
            sentiment_score=output.get("sentiment_score"),
            key_topics=output.get("key_topics", []),
            customer_recap_draft=output.get("customer_recap_draft"),
            raw_transcript=event_payload.get("transcript"),
        )
        db_session.add(insight)
        db_session.commit()

    def _build_prompt(self, transcript: str, customer: dict, payload: dict) -> str:
        parts = [
            f"## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            "",
            f"## Call Details",
            f"Participants: {', '.join(payload.get('participants', ['Unknown']))}",
            f"Duration: {payload.get('duration_minutes', 'N/A')} minutes",
            "",
            f"## Transcript",
            transcript[:8000],  # Cap transcript length for token limits
        ]
        return "\n".join(parts)
