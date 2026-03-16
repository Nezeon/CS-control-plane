import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("services.event")


class EventService:
    """Processes events through the Orchestrator and broadcasts results."""

    def _get_orchestrator(self):
        from app.agents.orchestrator import orchestrator
        return orchestrator

    def _persist_alert(self, sync_db, customer_id, event_type, agent_name, output):
        """Persist an Alert record and send Slack notification."""
        from app.models.alert import Alert

        if not customer_id:
            return None

        risk_level = output.get("risk_level", "high_risk")
        severity_map = {"critical": "critical", "high_risk": "high"}
        severity = severity_map.get(risk_level, "high")

        alert = Alert(
            id=uuid.uuid4(),
            customer_id=customer_id,
            alert_type=event_type,
            severity=severity,
            title=output.get("summary", f"Risk alert from {agent_name}")[:500],
            description=output.get("detail", output.get("reasoning", ""))[:2000] or None,
            suggested_action=output.get("suggested_action", output.get("recommendation"))[:1000] if output.get("suggested_action") or output.get("recommendation") else None,
            status="open",
        )
        sync_db.add(alert)
        sync_db.commit()
        sync_db.refresh(alert)

        # Send Slack notification (fire-and-forget)
        try:
            from app.services.slack_service import slack_service
            if slack_service.configured:
                sent = slack_service.send_alert(alert)
                if sent:
                    alert.slack_notified = True
                    sync_db.commit()
        except Exception as e:
            logger.warning(f"Slack notification failed (non-critical): {e}")

        logger.info(f"[EventService] Persisted alert {alert.id} (severity={severity})")
        return alert

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
                if result.get("success"):
                    agent = orchestrator.get_agent(agent_name)
                    # Call intelligence saves even without customer_id (Fathom sync)
                    if agent_name == "fathom_agent" and hasattr(agent, "save_insight"):
                        agent.save_insight(sync_db, customer_id, payload, result)
                        # Embed insight into ChromaDB for RAG similarity search
                        try:
                            from app.services.rag_service import rag_service
                            output = result.get("output", {})
                            if isinstance(output, dict):
                                topics = output.get("key_topics", [])
                                embed_text = f"{output.get('summary', '')} {' '.join(topics) if isinstance(topics, list) else ''}"
                                if embed_text.strip():
                                    from app.models.call_insight import CallInsight as _CI
                                    latest = sync_db.query(_CI).filter_by(
                                        fathom_recording_id=payload.get("recording_id")
                                    ).order_by(_CI.processed_at.desc()).first()
                                    insight_id = str(latest.id) if latest else str(uuid.uuid4())
                                    rag_service.embed_insight(insight_id, embed_text, {
                                        "customer_id": str(customer_id) if customer_id else "",
                                        "sentiment": output.get("sentiment", ""),
                                        "call_date": payload.get("call_date", ""),
                                        "recording_id": payload.get("recording_id", ""),
                                    })
                                    logger.info(f"RAG: embedded call insight {insight_id}")
                        except Exception as rag_err:
                            logger.warning(f"RAG embedding failed (non-critical): {rag_err}")
                        # Broadcast insight_ready for frontend
                        output = result.get("output", {})
                        await manager.broadcast("insight_ready", {
                            "customer_id": str(customer_id) if customer_id else None,
                            "recording_id": payload.get("recording_id"),
                            "sentiment": output.get("sentiment") if isinstance(output, dict) else None,
                            "summary": (output.get("summary", "")[:200]) if isinstance(output, dict) else "",
                        })
                    elif customer_id and agent_name == "health_monitor" and hasattr(agent, "save_score"):
                        agent.save_score(sync_db, customer_id, result)
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

                # Chat completion handling
                if event_type.startswith("user_chat_"):
                    try:
                        from app.services.chat_service import chat_service
                        chat_service.complete_message_sync(
                            sync_db, str(event.id), result, route_result
                        )
                    except Exception as e:
                        logger.warning(f"Chat completion failed: {e}")

                # ── Draft-first flow (ARCHITECTURE.md Section 8) ──────
                # Create a draft for non-chat, non-health-alert events.
                # Health alerts auto-post (informational, per spec 8.3).
                # Chat events are interactive — no draft needed.
                if not event_type.startswith("user_chat_") and agent_name:
                    self._create_draft_for_output(
                        sync_db, agent_name, event.id, customer_id,
                        event_type, result, payload,
                    )

                event.status = "completed" if result.get("success") else "failed"
                event.routed_to = agent_name
                event.processed_at = datetime.now(timezone.utc)
                await db_session.commit()

                await manager.broadcast("event_processed", {
                    "event_id": str(event.id),
                    "event_type": event_type,
                    "routed_to": agent_name,
                    "customer": str(customer_id) if customer_id else None,
                    "status": "completed" if result.get("success") else "failed",
                })

                # Persist alert + Slack notify if high risk
                output = result.get("output", {})
                if isinstance(output, dict) and output.get("risk_level") in ("high_risk", "critical"):
                    alert_record = self._persist_alert(
                        sync_db, customer_id, event_type, agent_name, output
                    )
                    await manager.broadcast("new_alert", {
                        "alert_id": str(alert_record.id) if alert_record else None,
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


    def _create_draft_for_output(
        self, sync_db, agent_name, event_id, customer_id,
        event_type, result, payload,
    ):
        """Create a draft record for the agent's output and post Slack card."""
        try:
            from app.services import draft_service

            output = result.get("output", {})
            confidence = None
            if isinstance(output, dict):
                confidence = output.get("confidence") or output.get("confidence_score")

            # Resolve customer name for Slack card
            customer_name = "Unknown"
            health_score = None
            try:
                from app.models.customer import Customer
                if customer_id:
                    cust = sync_db.query(Customer).filter_by(id=customer_id).first()
                    if cust:
                        customer_name = cust.name
                        health_score = cust.current_health
            except Exception:
                pass

            # Extract priority from output
            priority = None
            if isinstance(output, dict):
                priority = output.get("severity") or output.get("priority")

            draft_service.create_draft(
                db=sync_db,
                agent_id=agent_name,
                event_id=event_id,
                customer_id=customer_id,
                draft_content=output if isinstance(output, dict) else {"raw": str(output)[:2000]},
                confidence=confidence,
                event_type=event_type,
                customer_name=customer_name,
                health_score=health_score,
                priority=priority,
            )
        except Exception as e:
            logger.warning(f"[EventService] Draft creation failed (non-critical): {e}")


event_service = EventService()
