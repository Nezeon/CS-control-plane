import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("services.event")


class EventService:
    """Processes events through the Orchestrator and broadcasts results."""

    def _get_orchestrator(self):
        from app.agents.orchestrator import orchestrator
        return orchestrator

    async def create_and_process_event(
        self, db_session, event_type: str, source: str,
        payload: dict, customer_id=None,
    ) -> dict:
        """
        Create an event record, process it through the orchestrator,
        and broadcast results via WebSocket.
        """
        from app.models.event import Event
        from app.websocket_manager import manager

        event = Event(
            id=uuid.uuid4(),
            event_type=event_type,
            source=source or "api",
            payload=payload,
            customer_id=customer_id,
            status="pending",
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        event_dict = {
            "event_id": str(event.id),
            "event_type": event_type,
            "source": source,
            "payload": payload,
            "customer_id": str(customer_id) if customer_id else None,
        }

        # Broadcast event received
        await manager.broadcast("event_received", {
            "event_id": str(event.id),
            "event_type": event_type,
            "source": source,
            "customer_id": str(customer_id) if customer_id else None,
        })

        # Try Celery dispatch
        try:
            from app.tasks.agent_tasks import _is_celery_available, process_event

            if _is_celery_available():
                task = process_event.apply_async(args=[event_dict])
                event.status = "queued"
                await db_session.commit()

                orchestrator = self._get_orchestrator()
                from app.agents.orchestrator import EVENT_ROUTING
                agent_name = EVENT_ROUTING.get(event_type, "unknown")

                await manager.broadcast("event_processing", {
                    "event_id": str(event.id),
                    "task_id": task.id,
                    "agent": agent_name,
                })

                return {
                    "id": event.id,
                    "event_type": event_type,
                    "status": "queued",
                    "created_at": event.created_at,
                    "task_id": task.id,
                }
        except Exception as e:
            logger.debug(f"Celery unavailable, falling back to sync: {e}")

        # Sync fallback
        try:
            from app.database import get_sync_session

            orchestrator = self._get_orchestrator()
            sync_db = get_sync_session()
            try:
                route_result = orchestrator.route(sync_db, event_dict)
                agent_name = route_result.get("agent_name")
                result = route_result.get("result", {})

                # Save agent-specific outputs
                if result.get("success") and customer_id:
                    agent = orchestrator.get_agent(agent_name)
                    if agent_name == "health_monitor" and hasattr(agent, "save_score"):
                        agent.save_score(sync_db, customer_id, result)
                    elif agent_name == "call_intelligence" and hasattr(agent, "save_insight"):
                        agent.save_insight(sync_db, customer_id, payload, result)
                    elif agent_name == "troubleshooter" and hasattr(agent, "save_result"):
                        ticket_id = payload.get("ticket_id")
                        if ticket_id:
                            agent.save_result(sync_db, ticket_id, result)
                    elif agent_name == "escalation_summary" and hasattr(agent, "save_result"):
                        ticket_id = payload.get("ticket_id")
                        if ticket_id:
                            agent.save_result(sync_db, ticket_id, result)
                    elif agent_name == "qbr_value" and hasattr(agent, "save_report"):
                        agent.save_report(sync_db, customer_id, result)

                event.status = "completed" if result.get("success") else "failed"
                event.routed_to = agent_name
                event.processed_at = datetime.now(timezone.utc)
                await db_session.commit()

                await manager.broadcast("event_processed", {
                    "event_id": str(event.id),
                    "event_type": event_type,
                    "agent": agent_name,
                    "success": result.get("success", False),
                    "customer_id": str(customer_id) if customer_id else None,
                })

                # Broadcast alert if high risk
                output = result.get("output", {})
                if isinstance(output, dict) and output.get("risk_level") in ("high_risk", "critical"):
                    await manager.broadcast("new_alert", {
                        "customer_id": str(customer_id) if customer_id else None,
                        "risk_level": output["risk_level"],
                        "score": output.get("score"),
                    })

                return {
                    "id": event.id,
                    "event_type": event_type,
                    "status": event.status,
                    "created_at": event.created_at,
                }
            finally:
                sync_db.close()
        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            event.status = "failed"
            await db_session.commit()
            return {
                "id": event.id,
                "event_type": event_type,
                "status": "failed",
                "created_at": event.created_at,
            }


event_service = EventService()
