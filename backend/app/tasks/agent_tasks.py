import logging
import uuid
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger("tasks.agent")


def _is_celery_available() -> bool:
    """Check if Redis/Celery broker is reachable."""
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.close()
        return True
    except Exception:
        return False


@celery_app.task(name="process_event", bind=True, max_retries=2)
def process_event(self, event: dict) -> dict:
    """
    Process an event through the orchestrator.
    Called as Celery task or synchronously as fallback.
    """
    from app.agents.orchestrator import orchestrator
    from app.database import get_sync_session
    from app.models.event import Event

    db = get_sync_session()
    try:
        # Update event status to processing
        event_id = event.get("event_id")
        if event_id:
            db_event = db.query(Event).filter(Event.id == event_id).first()
            if db_event:
                db_event.status = "processing"
                db.commit()

        # Route through orchestrator
        route_result = orchestrator.route(db, event)

        agent_name = route_result.get("agent_name")
        result = route_result.get("result", {})

        # Post-processing: save agent-specific outputs
        customer_id = event.get("customer_id")
        if result.get("success") and customer_id:
            agent = orchestrator.get_agent(agent_name)
            if agent_name == "health_monitor" and hasattr(agent, "save_score"):
                agent.save_score(db, customer_id, result)
            elif agent_name == "call_intelligence" and hasattr(agent, "save_insight"):
                agent.save_insight(db, customer_id, event.get("payload", {}), result)
            elif agent_name == "troubleshooter" and hasattr(agent, "save_result"):
                ticket_id = event.get("payload", {}).get("ticket_id")
                if ticket_id:
                    agent.save_result(db, ticket_id, result)
            elif agent_name == "escalation_summary" and hasattr(agent, "save_result"):
                ticket_id = event.get("payload", {}).get("ticket_id")
                if ticket_id:
                    agent.save_result(db, ticket_id, result)
            elif agent_name == "qbr_value" and hasattr(agent, "save_report"):
                agent.save_report(db, customer_id, result)

        # Update event status
        if event_id:
            db_event = db.query(Event).filter(Event.id == event_id).first()
            if db_event:
                db_event.status = "completed" if result.get("success") else "failed"
                db_event.routed_to = agent_name
                db_event.processed_at = datetime.now(timezone.utc)
                db.commit()

        return {
            "event_id": str(event_id) if event_id else None,
            "agent_name": agent_name,
            "success": result.get("success", False),
            "reasoning": result.get("reasoning_summary", ""),
        }

    except Exception as e:
        logger.error(f"process_event failed: {e}")
        if event_id:
            try:
                db_event = db.query(Event).filter(Event.id == event_id).first()
                if db_event:
                    db_event.status = "failed"
                    db_event.processed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        raise
    finally:
        db.close()


@celery_app.task(name="run_health_check_all", bind=True)
def run_health_check_all(self) -> dict:
    """Run health check for all customers."""
    from app.agents.orchestrator import orchestrator
    from app.database import get_sync_session
    from app.models.customer import Customer

    db = get_sync_session()
    try:
        customers = db.query(Customer).all()
        results = []
        for customer in customers:
            event = {
                "event_type": "daily_health_check",
                "source": "celery_cron",
                "customer_id": customer.id,
                "payload": {},
            }
            route_result = orchestrator.route(db, event)
            agent_name = route_result.get("agent_name")
            result = route_result.get("result", {})

            # Save score if successful
            if result.get("success"):
                agent = orchestrator.get_agent("health_monitor")
                if agent and hasattr(agent, "save_score"):
                    agent.save_score(db, customer.id, result)

            results.append({
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "success": result.get("success", False),
            })

        succeeded = sum(1 for r in results if r["success"])
        return {
            "total": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "results": results,
        }
    finally:
        db.close()
