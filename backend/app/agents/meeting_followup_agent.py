"""
Meeting Followup Agent (Riley Park) -- Tier 3 Specialist (Value Lane).

Analyzes meeting transcripts and generates:
- Executive summary
- Key takeaways
- Action items with owners
- Sentiment assessment
- Draft follow-up email (NO auto-send)

Reports to: Damon Reeves (value_lead)
Traits: customer_sentiment, confidence_scoring
"""

import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("agents.meeting_followup")


class MeetingFollowupAgent(BaseAgent):
    """Analyzes meeting transcripts and drafts follow-up emails."""

    agent_id = "meeting_followup"

    def perceive(self, task: dict) -> dict:
        payload = task.get("payload", {})
        title = payload.get("title", "Untitled Meeting")
        transcript = payload.get("transcript", "")

        if not transcript:
            raise ValueError("No meeting transcript in event payload")

        self.memory.set_context("title", title)
        self.memory.set_context("transcript", transcript)
        self.memory.set_context("participants", payload.get("participants", []))
        self.memory.set_context("duration_minutes", payload.get("duration_minutes", 0))
        self.memory.set_context("call_date", payload.get("call_date", ""))
        return task

    def retrieve(self, task: dict) -> dict:
        payload = task.get("payload", {})
        transcript = payload.get("transcript", "")

        # Episodic + semantic memory
        query_text = f"{payload.get('title', '')} {transcript[:300]}"
        context = self.memory.assemble_context(query_text)
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        payload = task.get("payload", {})
        customer = context.get("customer_memory", {}).get("customer", {})
        health = context.get("customer_memory", {}).get("health", {})
        tickets = context.get("customer_memory", {}).get("tickets", {})
        calls = context.get("customer_memory", {}).get("calls", {})

        user_message = self._build_prompt(
            title=payload.get("title", "Meeting"),
            transcript=payload.get("transcript", ""),
            participants=payload.get("participants", []),
            duration=payload.get("duration_minutes", 0),
            call_date=payload.get("call_date", ""),
            customer=customer,
            health=health,
            tickets=tickets,
            calls=calls,
        )

        # Enrich with episodic context
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Meeting Analysis Work\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=4096, temperature=0.3)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}

        return {
            "success": True,
            **thinking,
            "reasoning_summary": thinking.get("summary", "Meeting analyzed and email drafted."),
        }

    # -- Prompt Building -------------------------------------------------------

    def _build_prompt(
        self,
        title: str,
        transcript: str,
        participants: list,
        duration: int,
        call_date: str,
        customer: dict,
        health: dict,
        tickets: dict,
        calls: dict,
    ) -> str:
        # Format participants
        participant_lines = []
        for p in participants:
            name = p.get("name", "Unknown")
            email = p.get("email", "")
            role = p.get("role", "")
            participant_lines.append(f"  - {name} <{email}> ({role})")
        participants_str = "\n".join(participant_lines) if participant_lines else "  (no participant info)"

        # Format recent calls for context
        recent_calls_str = ""
        call_items = calls.get("items", [])
        if call_items:
            recent_calls_str = "\n".join(
                f"  - [{c.get('call_date', '?')}] {c.get('summary', 'N/A')[:150]} (sentiment: {c.get('sentiment', '?')})"
                for c in call_items[:3]
            )

        parts = [
            "## Meeting Details",
            f"Title: {title}",
            f"Date: {call_date}",
            f"Duration: {duration} minutes",
            f"Participants:\n{participants_str}",
            "",
            "## Meeting Transcript",
            transcript[:6000],
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Health Score: {health.get('current_score', 'N/A')} ({health.get('risk_level', 'N/A')})",
            f"Open Tickets: {tickets.get('open_count', 0)} of {tickets.get('total_recent', 0)} recent",
            f"Renewal Date: {customer.get('renewal_date', 'N/A')}",
            f"Deployment: {customer.get('deployment_mode', 'N/A')} | Version: {customer.get('product_version', 'N/A')}",
        ]

        if recent_calls_str:
            parts.extend(["", "## Recent Past Calls", recent_calls_str])

        parts.extend([
            "",
            "## Instructions",
            "Analyze this meeting transcript thoroughly. Return a JSON object with these fields:",
            "",
            '  "summary": "2-3 sentence executive summary of the meeting",',
            '  "key_takeaways": ["takeaway 1", "takeaway 2", ...],',
            '  "action_items": [',
            '    {"title": "action description", "owner": "person name", "deadline_suggestion": "timeframe", "priority": "high/medium/low"}',
            "  ],",
            '  "sentiment": "positive/neutral/negative/mixed",',
            '  "sentiment_score": 0.0 to 1.0 (1.0 = very positive),',
            '  "risks": ["risk 1 if any"],',
            '  "draft_email": "Full professional follow-up email text addressed to all attendees. Include: greeting, meeting summary paragraph, key takeaways as bullets, action items as a table, and a professional closing. Use the actual participant names."',
            "",
            "Return ONLY valid JSON. The draft_email should be a complete, ready-to-send email.",
        ])

        return "\n".join(parts)


AgentFactory.register("meeting_followup", MeetingFollowupAgent)
