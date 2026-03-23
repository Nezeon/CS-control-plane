"""
Pipeline-Aware Base Agent — Foundation for all 13 CS Control Plane agents.

Every agent subclass sets `agent_id` and overrides the pipeline methods it needs:
  perceive → retrieve → think → act → reflect → quality_gate → finalize

The pipeline engine reads the tier-specific stage list from pipeline.yaml and calls
the appropriate methods in order. Traits fire at each stage.

Usage:
    class TriageAgent(BaseAgent):
        agent_id = "triage_agent"

        def perceive(self, task): ...
        def retrieve(self, task): ...
        def think(self, task, context): ...
        def act(self, task, thinking): ...
"""

import json
import logging
import time
import uuid
from abc import ABC

from app.agents.memory import MemoryManager
from app.agents.profile_loader import ProfileLoader
from app.agents.reflection_engine import ReflectionEngine
from app.agents.traits.registry import TraitRegistry
from app.models.agent_log import AgentLog
from app.services import claude_service


class BaseAgent(ABC):
    """Base class for all pipeline-aware CS Control Plane agents."""

    agent_id: str = ""       # YAML key (e.g., "triage_agent")
    agent_name: str = ""     # Human name (e.g., "Kai Nakamura")
    agent_type: str = ""     # legacy field — auto-set from lane

    def __init__(self):
        loader = ProfileLoader.get()
        profile = loader.get_agent_profile(self.agent_id) or {}

        self.agent_name = profile.get("name", self.agent_id)
        self.tier: int = profile.get("tier", 3)
        self.lane: str | None = profile.get("lane")
        self.role: str = profile.get("role", "")
        self.system_instruction: str = profile.get("system_instruction", "")
        self.profile: dict = profile

        # Legacy compat
        self.agent_type = self.lane or "control"

        # Subsystems
        self.memory = MemoryManager(self.agent_id, self.lane)
        self.traits = TraitRegistry.resolve(profile.get("traits", []))
        self.reflection = ReflectionEngine(self.agent_id, self.memory)
        self.logger = logging.getLogger(f"agents.{self.agent_id}")

        # Set by pipeline engine before each run
        self._current_db = None

    # ── Pipeline Methods (subclasses override as needed) ─────────────

    def perceive(self, task: dict) -> dict:
        """Stage: perceive — Understand the incoming task, add to working memory."""
        return task

    def retrieve(self, task: dict) -> dict:
        """Stage: retrieve — Pull relevant context from memory systems."""
        description = task.get("description", str(task.get("payload", "")))[:500]
        self.logger.info(f"[{self.agent_id}] retrieve: querying memory with description_len={len(description)}")
        ctx = self.memory.assemble_context(description)
        self.logger.info(f"[{self.agent_id}] retrieve: memory returned keys={list(ctx.keys()) if isinstance(ctx, dict) else '?'}")
        return ctx

    def think(self, task: dict, context: dict) -> dict:
        """Stage: think — Reason about the task. Usually calls Claude."""
        return {}

    def act(self, task: dict, thinking: dict) -> dict:
        """Stage: act — Execute the task, produce output."""
        return thinking

    def reflect(self, task: dict, result: dict) -> dict:
        """Stage: reflect — Self-assess via ReflectionEngine."""
        self.logger.info(f"[{self.agent_id}] reflect: starting self-assessment, result_keys={list(result.keys()) if isinstance(result, dict) else '?'}")
        return self.reflection.reflect(
            execution_summary=task.get("description", str(task)[:500]),
            result=result,
            context={
                "customer_name": task.get("customer_name", ""),
                "customer_id": task.get("customer_id", ""),
                "execution_id": task.get("execution_id", ""),
            },
        )

    def quality_gate(self, task: dict, result: dict) -> dict:
        """Stage: quality_gate — Evaluate deliverable quality (Tier 1 only)."""
        return result

    def finalize(self, task: dict, result: dict) -> dict:
        """Stage: finalize — Polish and prepare final output."""
        return result

    # ── Legacy Interface ─────────────────────────────────────────────

    def execute(self, event: dict, customer_memory: dict) -> dict:
        """Legacy interface for backward compat. Override pipeline methods instead."""
        return {
            "success": True,
            "output": {"message": f"{self.agent_id}: no-op execute()"},
            "reasoning_summary": "Legacy execute() not overridden.",
        }

    # ── Public Entry Point ───────────────────────────────────────────

    def run(self, db_session, event: dict, customer_memory: dict | None = None) -> dict:
        """
        Pipeline-aware run. Uses PipelineEngine to execute tier-specific stages.
        This is the public entry point called by the orchestrator and Celery tasks.
        """
        from app.agents.pipeline_engine import PipelineEngine

        self._current_db = db_session
        engine = PipelineEngine(self, db_session)
        return engine.execute(event, customer_memory)

    # ── Execution Logging (preserved from v1) ────────────────────────

    def log_execution(
        self,
        db_session,
        event: dict,
        input_summary: str,
        output: dict,
        reasoning: str,
        status: str,
        duration_ms: int,
        customer_id=None,
    ) -> None:
        """Write an AgentLog record to the database. Best-effort — never raises."""
        try:
            log = AgentLog(
                id=uuid.uuid4(),
                agent_name=self.agent_id or self.agent_name,
                agent_type=self.agent_type,
                event_type=event.get("event_type", "unknown"),
                trigger_event=event.get("source", "api"),
                customer_id=customer_id,
                input_summary=input_summary[:2000] if input_summary else None,
                output_summary=json.dumps(output, default=str)[:2000] if output else None,
                reasoning_summary=reasoning[:2000] if reasoning else None,
                status=status,
                duration_ms=duration_ms,
            )
            db_session.add(log)
            db_session.commit()
        except Exception as e:
            self.logger.warning(f"Failed to log execution: {e}")
            try:
                db_session.rollback()
            except Exception:
                pass

    # ── Claude Helpers ───────────────────────────────────────────────

    def _call_claude(
        self,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        system_prompt: str | None = None,
    ) -> dict:
        """
        Convenience: call Claude with this agent's system_instruction.

        Returns {"content": str, ...} on success or {"error": str, ...} on failure.
        """
        import time as _time

        from app.agents.demo_logger import claude_call_start, claude_call_done, claude_call_error

        self.logger.info(claude_call_start(self.agent_name or self.agent_id, len(user_message)))
        self.logger.info(
            f"[{self.agent_id}] Claude call params: max_tokens={max_tokens}, "
            f"temperature={temperature}, prompt_len={len(user_message)}, "
            f"system_len={len(system_prompt or self.system_instruction)}"
        )
        call_start = _time.perf_counter()

        response = claude_service.generate_sync(
            system_prompt=system_prompt or self.system_instruction,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        call_ms = int((_time.perf_counter() - call_start) * 1000)
        if "error" in response:
            self.logger.warning(claude_call_error(
                response.get("error", response.get("detail", "unknown")), call_ms
            ))
        else:
            content_len = len(response.get("content", ""))
            input_tokens = response.get("input_tokens", 0)
            output_tokens = response.get("output_tokens", 0)
            self.logger.info(claude_call_done(
                content_len, call_ms, input_tokens, output_tokens
            ))

        return response

    def _parse_claude(self, response: dict) -> dict:
        """
        Parse a Claude response dict.

        If the response contains an error key, returns {"error": detail}.
        Otherwise parses the JSON content.
        """
        if "error" in response:
            self.logger.warning(f"[{self.agent_id}] _parse_claude: error in response — {response.get('detail', response['error'])}")
            return {"error": response.get("detail", response["error"])}
        parsed = claude_service.parse_json_response(response["content"])
        if "error" in parsed:
            self.logger.warning(f"[{self.agent_id}] _parse_claude: JSON parse failed — {parsed['error']}")
        else:
            self.logger.info(f"[{self.agent_id}] _parse_claude: success, keys={list(parsed.keys())}")
        return parsed

    # ── Task Brief Helpers ────────────────────────────────────────

    def _prepend_brief(self, prompt: str, task: dict) -> str:
        """
        Prepend a structured task brief to a Claude prompt.

        Reads from task["specialist_brief"] (T3) or task["task_brief"] (T2).
        Also injects rework feedback when task["is_rework"] is True.
        Appends per-channel chat history when available (chat events only).
        """
        brief = task.get("specialist_brief") or task.get("task_brief") or {}
        is_rework = task.get("is_rework", False)
        history = task.get("payload", {}).get("conversation_history", [])

        if not brief and not is_rework and not history:
            self.logger.info(f"[{self.agent_id}] _prepend_brief: no brief, rework, or chat history — skipping")
            return prompt

        parts = []

        # Rework feedback takes priority
        if is_rework:
            parts.append("## REWORK REQUEST — Your previous output was insufficient.")
            parts.append(f"Feedback from supervisor: {task.get('rework_feedback', 'Address all success criteria.')}")
            missing = task.get("rework_missing", [])
            if missing:
                parts.append(f"Missing criteria: {', '.join(missing)}")
            parts.append("Please address ALL of the above in your revised output.\n")

        if brief:
            parts.append("## Task Brief from Supervisor")
            if brief.get("objective"):
                parts.append(f"Objective: {brief['objective']}")
            if brief.get("focus_areas"):
                parts.append(f"Focus Areas: {', '.join(brief['focus_areas'])}")
            if brief.get("context_summary"):
                parts.append(f"Context: {brief['context_summary']}")
            if brief.get("data_to_examine"):
                parts.append(f"Data to Examine: {', '.join(brief['data_to_examine'])}")
            if brief.get("expected_output"):
                parts.append(f"Expected Output Format: {json.dumps(brief['expected_output'], default=str)}")
            if brief.get("success_criteria"):
                parts.append(f"Success Criteria: {'; '.join(brief['success_criteria'])}")
            parts.append("")

        # Per-channel chat history (only present for chat events, not webhooks/cron)
        if history:
            parts.append("## Recent Chat Context")
            for msg in history[-10:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                parts.append(f"**{role}:** {msg['content'][:300]}")
            parts.append("")

        self.logger.info(
            f"[{self.agent_id}] _prepend_brief: is_rework={is_rework}, "
            f"brief_keys={list(brief.keys()) if brief else 'none'}, "
            f"chat_history={len(history)} msgs, "
            f"prepended {len(parts)} sections"
        )
        return "\n".join(parts) + "\n" + prompt

    def _validate_output(
        self,
        specialist_key: str,
        specialist_brief: dict,
        specialist_result: dict,
        task: dict,
    ) -> dict:
        """
        Validate a specialist's output against the brief's success criteria.

        Cost-aware: skips validation if no success_criteria or confidence >= 0.8.
        Returns {"passes": bool, "score": float, "feedback": str, "missing": list}.
        """
        if not specialist_brief.get("success_criteria"):
            return {"passes": True, "score": 1.0, "feedback": "", "missing": []}

        # Cost optimization: skip for high-confidence results
        reflection = specialist_result.get("reflection", {})
        confidence = reflection.get("confidence", 0.0) if isinstance(reflection, dict) else 0.0
        if confidence >= 0.8:
            return {
                "passes": True,
                "score": confidence,
                "feedback": "High confidence — validation skipped",
                "missing": [],
            }

        output = specialist_result.get("output", specialist_result)
        summary = specialist_result.get("reasoning_summary", str(output)[:500])

        prompt = (
            f"## Validation Check\n"
            f"Specialist: {specialist_key}\n"
            f"Task Objective: {specialist_brief.get('objective', 'N/A')}\n\n"
            f"## Success Criteria\n"
        )
        for criterion in specialist_brief.get("success_criteria", []):
            prompt += f"- {criterion}\n"

        prompt += (
            f"\n## Specialist Output\n"
            f"Success: {specialist_result.get('success')}\n"
            f"Summary: {summary}\n"
            f"Output: {json.dumps(output, default=str)[:1500]}\n\n"
            f"## Instructions\n"
            f"Does this output meet the success criteria? Be strict but fair.\n"
            f'Return JSON: {{"passes": true, "score": 0.85, "feedback": "what is missing or wrong", "missing": ["criterion that failed"]}}'
        )

        response = self._call_claude(prompt, max_tokens=512, temperature=0.1)
        parsed = self._parse_claude(response)

        if "error" in parsed:
            return {"passes": True, "score": 0.5, "feedback": "Validation parse failed", "missing": []}

        return parsed

    # ── WebSocket Broadcast ───────────────────────────────────────

    def _broadcast_delegation(self, event_type: str, data: dict):
        """Fire-and-forget WebSocket broadcast for delegation/validation events."""
        try:
            import asyncio
            from app.websocket_manager import manager

            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop and loop.is_running():
                loop.create_task(manager.broadcast(event_type, data))
            else:
                new_loop = asyncio.new_event_loop()
                try:
                    new_loop.run_until_complete(manager.broadcast(event_type, data))
                finally:
                    new_loop.close()
        except Exception as e:
            self.logger.debug(f"Delegation broadcast failed (non-critical): {e}")
