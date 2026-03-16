"""
Pipeline Engine — Runs an agent through its tier-specific pipeline stages.

Loads stage definitions from pipeline.yaml, executes each stage in order,
fires trait hooks, stores results in episodic memory, and logs to agent_logs.
Broadcasts progress via WebSocket at each lifecycle event.

Usage:
    engine = PipelineEngine(agent, db_session)
    result = engine.execute(event, customer_memory)
"""

import asyncio
import logging
import time
import uuid

from app.agents.profile_loader import ProfileLoader
from app.agents.demo_logger import (
    pipeline_header,
    stage_start,
    stage_complete,
    pipeline_complete,
)

logger = logging.getLogger("pipeline_engine")


def _sync_broadcast(event_type: str, data: dict) -> None:
    """Best-effort WebSocket broadcast from sync context.

    In dev/eager mode, Celery tasks run in the FastAPI process where the
    event loop is active, so broadcasts reach connected clients.
    In production (separate Celery workers), there's no running loop —
    the broadcast is silently skipped (future: Redis pub/sub bridge).
    """
    try:
        from app.websocket_manager import manager
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(event_type, data))
    except RuntimeError:
        pass


class PipelineEngine:
    """Orchestrates the tier-specific pipeline for a single agent run."""

    def __init__(self, agent, db_session):
        self.agent = agent
        self.db = db_session
        self.stages = self._load_stages()

    def _load_stages(self) -> list[dict]:
        """Load pipeline stages from pipeline.yaml for this agent's tier."""
        loader = ProfileLoader.get()
        pipeline = loader.get_pipeline_for_tier(self.agent.tier)
        if not pipeline:
            return []
        return pipeline.get("stages", [])

    def execute(self, event: dict, customer_memory: dict | None = None) -> dict:
        """
        Run the full pipeline. Returns standard result dict:
        {"success": bool, "output": dict, "reasoning_summary": str, ...}
        """
        start = time.perf_counter()
        execution_id = str(uuid.uuid4())

        # Build task dict from event
        task = self._build_task(event, customer_memory, execution_id)

        context = {}
        thinking = {}
        result = {}
        reflection = {}

        stage_names = [s.get("name", s.get("type", "?")) for s in self.stages]
        customer_name = ""
        if customer_memory:
            customer_name = customer_memory.get("customer", {}).get("name", "")
        if not customer_name:
            customer_name = event.get("payload", {}).get("customer_name", "Unknown")

        try:
            header = pipeline_header(
                agent_id=self.agent.agent_id,
                agent_name=getattr(self.agent, "agent_name", self.agent.agent_id),
                tier=self.agent.tier,
                event_type=event.get("event_type", "?"),
                customer_name=customer_name,
                stages=stage_names,
            )
            logger.info(header)

            # Broadcast pipeline started
            _sync_broadcast("pipeline:started", {
                "execution_id": execution_id,
                "agent_id": self.agent.agent_id,
                "agent_name": getattr(self.agent, "agent_name", self.agent.agent_id),
                "tier": self.agent.tier,
                "stages_total": len(self.stages),
            })

            for idx, stage in enumerate(self.stages):
                stage_type = stage.get("type", "")
                stage_name = stage.get("name", stage_type)
                _stage_t0 = time.perf_counter()

                logger.info(stage_start(
                    agent_name=getattr(self.agent, "agent_name", self.agent.agent_id),
                    tier=self.agent.tier,
                    stage_name=stage_name,
                    stage_type=stage_type,
                    stage_num=idx + 1,
                    total=len(self.stages),
                ))

                # Broadcast stage started
                _sync_broadcast("pipeline:stage_started", {
                    "execution_id": execution_id,
                    "agent_id": self.agent.agent_id,
                    "stage_name": stage_name,
                    "stage_type": stage_type,
                    "stage_number": idx + 1,
                })

                # Also broadcast chat:agent_working for user-facing chat
                # (the frontend listens for this to show agent activity)
                payload = event.get("payload", {})
                if payload.get("conversation_id") and payload.get("message_id"):
                    _sync_broadcast("chat:agent_working", {
                        "conversation_id": payload["conversation_id"],
                        "message_id": payload["message_id"],
                        "agent_id": self.agent.agent_id,
                        "agent_name": getattr(self.agent, "agent_name", self.agent.agent_id),
                        "stage": stage_name,
                    })

                # Fire trait pre-hooks
                trait_context = self._fire_trait_hooks(stage_type, task, context, result)
                if trait_context:
                    task["_trait_context"] = trait_context
                    logger.info(f"[Pipeline]   Trait hooks fired for {stage_type}: {len(trait_context)} chars context added")

                if stage_type == "perceive":
                    perceive_result = self.agent.perceive(task)
                    if isinstance(perceive_result, dict):
                        context.update(perceive_result)
                    logger.info(f"[Pipeline]   perceive() → context keys: {list(context.keys())}")

                elif stage_type == "retrieve":
                    retrieve_result = self.agent.retrieve(task)
                    if isinstance(retrieve_result, dict):
                        context.update(retrieve_result)
                    logger.info(f"[Pipeline]   retrieve() → context keys: {list(context.keys())}")

                elif stage_type == "think":
                    thinking = self.agent.think(task, context) or {}
                    logger.info(f"[Pipeline]   think() → keys: {list(thinking.keys()) if isinstance(thinking, dict) else '?'}")

                elif stage_type == "act":
                    result = self.agent.act(task, thinking) or {}
                    # Fire postprocess traits
                    result = self._fire_postprocess_traits(result, context)
                    logger.info(f"[Pipeline]   act() → success={result.get('success', '?')}, keys: {list(result.keys()) if isinstance(result, dict) else '?'}")

                elif stage_type == "reflect":
                    reflection = self.agent.reflect(task, result) or {}
                    logger.info(f"[Pipeline]   reflect() → keys: {list(reflection.keys()) if isinstance(reflection, dict) else '?'}")

                elif stage_type == "quality_gate":
                    result = self.agent.quality_gate(task, result) or result
                    logger.info(f"[Pipeline]   quality_gate() → confidence={result.get('confidence', '?')}")

                elif stage_type == "finalize":
                    result = self.agent.finalize(task, result) or result
                    logger.info(f"[Pipeline]   finalize() → final result keys: {list(result.keys()) if isinstance(result, dict) else '?'}")

                # Broadcast stage completed
                stage_duration_ms = int((time.perf_counter() - _stage_t0) * 1000)
                logger.info(stage_complete(
                    tier=self.agent.tier,
                    stage_name=stage_name,
                    duration_ms=stage_duration_ms,
                ))
                _sync_broadcast("pipeline:stage_completed", {
                    "execution_id": execution_id,
                    "agent_id": self.agent.agent_id,
                    "stage_name": stage_name,
                    "stage_type": stage_type,
                    "stage_number": idx + 1,
                    "duration_ms": stage_duration_ms,
                })

            # Determine final output
            output = result if isinstance(result, dict) else {}
            success = output.get("success", True) if "success" in output else True
            reasoning = output.get("reasoning_summary", str(output)[:200])

            # Store execution in episodic memory
            self._store_episodic(task, reasoning, execution_id)

            # Log to agent_logs table
            duration_ms = int((time.perf_counter() - start) * 1000)
            status = "completed" if success else "failed"
            self.agent.log_execution(
                db_session=self.db,
                event=event,
                input_summary=task.get("description", "")[:2000],
                output=output,
                reasoning=reasoning,
                status=status,
                duration_ms=duration_ms,
                customer_id=task.get("customer_id"),
            )

            # Broadcast pipeline completed
            _sync_broadcast("pipeline:completed", {
                "execution_id": execution_id,
                "agent_id": self.agent.agent_id,
                "status": status,
                "total_duration_ms": duration_ms,
                "stages_completed": len(self.stages),
            })

            logger.info(pipeline_complete(
                agent_name=getattr(self.agent, "agent_name", self.agent.agent_id),
                tier=self.agent.tier,
                status=status,
                duration_ms=duration_ms,
                stages_count=len(self.stages),
            ))

            return {
                "success": success,
                "output": output,
                "reasoning_summary": reasoning,
                "execution_id": execution_id,
                "reflection": reflection,
            }

        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.agent.logger.error(f"[{self.agent.agent_id}] pipeline failed: {e}")
            self.agent.log_execution(
                db_session=self.db,
                event=event,
                input_summary=task.get("description", "")[:2000],
                output={"error": str(e)},
                reasoning=f"Pipeline exception: {e}",
                status="failed",
                duration_ms=duration_ms,
                customer_id=task.get("customer_id"),
            )
            return {
                "success": False,
                "output": {"error": str(e)},
                "reasoning_summary": f"Pipeline failed: {e}",
                "execution_id": execution_id,
            }

        finally:
            self.agent.memory.clear_working()

    # ── Internal Helpers ─────────────────────────────────────────────

    def _build_task(
        self,
        event: dict,
        customer_memory: dict | None,
        execution_id: str,
    ) -> dict:
        """Build a unified task dict from the event and customer memory."""
        payload = event.get("payload", {})
        customer_id = event.get("customer_id")

        # Customer name from memory or payload
        customer_name = ""
        if customer_memory:
            customer_name = customer_memory.get("customer", {}).get("name", "")

        # Build description from event
        description = (
            event.get("description", "")
            or payload.get("user_query", "")
            or payload.get("summary", "")
            or payload.get("description", "")
            or event.get("event_type", "unknown event")
        )

        return {
            "event_type": event.get("event_type", ""),
            "payload": payload,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_memory": customer_memory or {},
            "description": description,
            "execution_id": execution_id,
            "source": event.get("source", "api"),
            # Lane lead / orchestrator may inject extra fields
            "lane_lead_plan": event.get("lane_lead_plan"),
            "prior_outputs": event.get("prior_outputs"),
            "priority": event.get("priority", 5),
            # Brief and rework fields (injected by orchestrator/lane leads)
            "task_brief": event.get("task_brief"),
            "specialist_brief": event.get("specialist_brief"),
            "orchestrator_rationale": event.get("orchestrator_rationale"),
            "is_rework": event.get("is_rework", False),
            "rework_feedback": event.get("rework_feedback"),
            "rework_missing": event.get("rework_missing"),
            "event_id": event.get("event_id"),
        }

    def _fire_trait_hooks(
        self,
        stage_type: str,
        task: dict,
        context: dict,
        result: dict,
    ) -> str:
        """Fire trait hooks for the current stage. Returns combined context string."""
        parts = []
        for trait in self.agent.traits:
            try:
                if stage_type == "perceive":
                    text = trait.on_perceive(context=task)
                elif stage_type == "think":
                    text = trait.on_think(task=task.get("description", ""), context=context)
                elif stage_type == "reflect":
                    text = trait.on_reflect(result=result, context=context)
                else:
                    text = ""
                if text:
                    parts.append(text)
            except Exception as e:
                logger.warning(f"Trait {trait.name} hook failed at {stage_type}: {e}")
        return "\n".join(parts)

    def _fire_postprocess_traits(self, result: dict, context: dict) -> dict:
        """Fire on_act_postprocess for all traits after the act stage."""
        for trait in self.agent.traits:
            try:
                result = trait.on_act_postprocess(result=result, context=context)
            except Exception as e:
                logger.warning(f"Trait {trait.name} postprocess failed: {e}")
        return result

    def _store_episodic(self, task: dict, reasoning: str, execution_id: str) -> None:
        """Store execution summary in agent's episodic memory."""
        try:
            importance = self._infer_importance(task)
            self.agent.memory.remember_execution(
                summary=reasoning[:500],
                importance=importance,
                customer_id=str(task.get("customer_id", "")),
                customer_name=task.get("customer_name", ""),
                event_type=task.get("event_type", ""),
                execution_id=execution_id,
            )
        except Exception as e:
            logger.warning(f"Failed to store episodic memory: {e}")

    def _infer_importance(self, task: dict) -> int:
        """Infer importance score (1-10) from task priority and tier."""
        priority = task.get("priority", 5)
        # Higher tier agents produce more important memories
        tier_boost = {1: 2, 2: 1, 3: 0, 4: 0}.get(self.agent.tier, 0)
        return min(10, max(1, priority + tier_boost))
