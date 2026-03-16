"""
Reflection Engine — Tier-aware self-assessment for agents.

Called during the 'reflect' pipeline stage. Depth varies by tier:
  Tier 3 (Specialist): Self-assessment — "What went well? Confidence? Escalate?"
  Tier 2 (Lane Lead):  Cross-specialist synthesis — "Themes? Conflicts? Recommendations?"
  Tier 1 (Supervisor): Strategic synthesis — "Customer impact? Risk? Priorities?"
  Tier 4 (Foundation): No reflection — returns empty result.

Reflection output is stored in episodic memory as a high-importance entry.
"""

import json
import logging

from app.agents.memory import MemoryManager
from app.agents.profile_loader import ProfileLoader

logger = logging.getLogger("reflection_engine")


class ReflectionEngine:

    def __init__(self, agent_id: str, memory: MemoryManager):
        self.agent_id = agent_id
        self.memory = memory

        loader = ProfileLoader.get()
        profile = loader.get_agent_profile(agent_id) or {}
        self.agent_name = profile.get("name", agent_id)
        self.tier = profile.get("tier", 3)
        self.role = profile.get("role", "")

    def reflect(
        self,
        execution_summary: str,
        result: dict,
        context: dict,
    ) -> dict:
        """
        Run tier-appropriate reflection.

        Returns:
            {
                "reflection": str,       # The full reflection text
                "confidence": float,     # 0.0 - 1.0
                "lessons": list[str],    # Key takeaways
                "should_escalate": bool, # Whether to escalate
            }
        """
        if self.tier == 4:
            return {"reflection": "", "confidence": 0.0, "lessons": [], "should_escalate": False}

        system_prompt, user_prompt = self._build_reflection_prompt(execution_summary, result, context)

        try:
            from app.services import claude_service

            response = claude_service.generate_sync(
                system_prompt=system_prompt,
                user_message=user_prompt,
                max_tokens=1024,
                temperature=0.3,
            )

            if "error" in response:
                logger.warning(f"Reflection Claude call failed: {response.get('error')}")
                return {"reflection": "", "confidence": 0.0, "lessons": [], "should_escalate": False}

            content = response["content"]
            parsed = self._parse_reflection(content)

            # Store in episodic memory
            importance = {1: 9, 2: 8, 3: 7}.get(self.tier, 7)
            self._record_reflection(content, importance, context)

            return parsed

        except Exception as e:
            logger.error(f"Reflection failed for {self.agent_id}: {e}")
            return {"reflection": "", "confidence": 0.0, "lessons": [], "should_escalate": False}

    def _build_reflection_prompt(
        self,
        execution_summary: str,
        result: dict,
        context: dict,
    ) -> tuple[str, str]:
        """Build system + user prompt based on tier."""
        result_preview = json.dumps(result, default=str)[:2000]
        customer_name = context.get("customer_name", "unknown")

        if self.tier == 3:
            system = (
                f"You are {self.agent_name}, a Tier 3 specialist agent ({self.role}). "
                "Perform a brief self-assessment of your work."
            )
            user = (
                f"You just completed this task:\n{execution_summary}\n\n"
                f"Your output:\n{result_preview}\n\n"
                f"Customer: {customer_name}\n\n"
                "Respond in JSON with these fields:\n"
                '- "confidence": float 0.0-1.0 (how confident are you in your output?)\n'
                '- "went_well": string (what went well?)\n'
                '- "could_improve": string (what could be better?)\n'
                '- "lessons": list of 1-3 short strings (key takeaways)\n'
                '- "should_escalate": boolean (does this need lead attention?)\n'
                '- "escalation_reason": string or null'
            )

        elif self.tier == 2:
            system = (
                f"You are {self.agent_name}, a Tier 2 Lane Lead ({self.role}). "
                "Synthesize the work from your specialists and provide a lane-level assessment."
            )
            user = (
                f"Task summary:\n{execution_summary}\n\n"
                f"Combined output:\n{result_preview}\n\n"
                f"Customer: {customer_name}\n\n"
                "Respond in JSON with these fields:\n"
                '- "confidence": float 0.0-1.0\n'
                '- "cross_cutting_themes": list of strings (patterns across specialist work)\n'
                '- "conflicts": string or null (where specialists disagree)\n'
                '- "recommendations": list of 1-3 strings\n'
                '- "lessons": list of 1-3 short strings\n'
                '- "should_escalate": boolean (does this need orchestrator attention?)\n'
                '- "escalation_reason": string or null'
            )

        else:  # tier == 1
            system = (
                f"You are {self.agent_name}, the Tier 1 Orchestrator ({self.role}). "
                "Provide a strategic synthesis across all lanes."
            )
            user = (
                f"Task summary:\n{execution_summary}\n\n"
                f"Aggregated output:\n{result_preview}\n\n"
                f"Customer: {customer_name}\n\n"
                "Respond in JSON with these fields:\n"
                '- "confidence": float 0.0-1.0\n'
                '- "customer_impact": string (overall impact assessment)\n'
                '- "risk_assessment": string\n'
                '- "next_priorities": list of 1-3 strings\n'
                '- "lessons": list of 1-3 short strings\n'
                '- "should_escalate": boolean (does this need human attention?)\n'
                '- "escalation_reason": string or null'
            )

        return system, user

    def _parse_reflection(self, content: str) -> dict:
        """Parse Claude's reflection response into a structured dict."""
        from app.services import claude_service

        parsed = claude_service.parse_json_response(content)

        confidence = 0.0
        try:
            confidence = float(parsed.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            pass

        lessons = parsed.get("lessons", [])
        if not isinstance(lessons, list):
            lessons = [str(lessons)] if lessons else []

        should_escalate = bool(parsed.get("should_escalate", False))

        return {
            "reflection": content,
            "confidence": confidence,
            "lessons": lessons,
            "should_escalate": should_escalate,
        }

    def _record_reflection(self, reflection_text: str, importance: int, context: dict) -> None:
        """Store reflection in episodic memory."""
        self.memory.remember_execution(
            summary=f"[Reflection] {reflection_text[:500]}",
            importance=importance,
            customer_id=context.get("customer_id", ""),
            customer_name=context.get("customer_name", ""),
            event_type="reflection",
            execution_id=context.get("execution_id", ""),
        )
