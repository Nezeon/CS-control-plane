import logging
import time
import uuid
from abc import ABC, abstractmethod

from app.database import get_sync_session
from app.models.agent_log import AgentLog


class BaseAgent(ABC):
    """Base class for all CS Control Plane agents."""

    agent_name: str = "base"
    agent_type: str = "control"  # control | value | support

    def __init__(self):
        self.logger = logging.getLogger(f"agents.{self.agent_name}")

    @abstractmethod
    def execute(self, event: dict, customer_memory: dict) -> dict:
        """
        Core agent logic. Subclasses implement this.

        Args:
            event: The triggering event dict (event_type, payload, customer_id, etc.)
            customer_memory: Structured customer context from MemoryAgent

        Returns:
            {"success": bool, "output": dict, "reasoning_summary": str}
        """
        ...

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
        """Write an AgentLog record to the database."""
        import json

        log = AgentLog(
            id=uuid.uuid4(),
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            event_type=event.get("event_type", "unknown"),
            trigger_event=event.get("source", "api"),
            customer_id=customer_id,
            input_summary=input_summary[:2000] if input_summary else None,
            output_summary=json.dumps(output)[:2000] if output else None,
            reasoning_summary=reasoning[:2000] if reasoning else None,
            status=status,
            duration_ms=duration_ms,
        )
        db_session.add(log)
        db_session.commit()

    def run(self, db_session, event: dict, customer_memory: dict) -> dict:
        """
        Wraps execute() with timing, logging, and error handling.
        This is the public entry point for the orchestrator.
        """
        start = time.perf_counter()
        customer_id = event.get("customer_id")
        input_summary = f"event_type={event.get('event_type')}, customer_id={customer_id}"

        try:
            result = self.execute(event, customer_memory)
            duration_ms = int((time.perf_counter() - start) * 1000)

            status = "completed" if result.get("success") else "failed"
            self.log_execution(
                db_session=db_session,
                event=event,
                input_summary=input_summary,
                output=result.get("output", {}),
                reasoning=result.get("reasoning_summary", ""),
                status=status,
                duration_ms=duration_ms,
                customer_id=customer_id,
            )
            self.logger.info(
                f"[{self.agent_name}] {status} in {duration_ms}ms "
                f"for customer={customer_id}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.logger.error(f"[{self.agent_name}] failed: {e}")
            self.log_execution(
                db_session=db_session,
                event=event,
                input_summary=input_summary,
                output={"error": str(e)},
                reasoning=f"Exception: {e}",
                status="failed",
                duration_ms=duration_ms,
                customer_id=customer_id,
            )
            return {
                "success": False,
                "output": {"error": str(e)},
                "reasoning_summary": f"Agent failed with exception: {e}",
            }
