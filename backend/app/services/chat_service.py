"""
Chat Service — Business logic for user-facing AI chat.

Split into two paths:
  - create_message_sync: FAST (~50ms) — saves conversation + messages, returns immediately
  - process_message_sync: HEAVY (10-60s) — classifies, pre-fetches, runs agent pipeline
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

logger = logging.getLogger("services.chat")

# ── Intent Classification ─────────────────────────────────────────────────

CALL_KEYWORDS = [
    "call", "meeting", "fathom", "transcript", "recording", "sentiment",
    "takeaway", "discussed", "action item", "recap", "conversation",
    "talked", "key points", "follow up", "follow-up",
]

HEALTH_KEYWORDS = [
    "health", "score", "risk", "churn", "renewal", "at-risk", "trending",
    "decline", "improve", "deteriorat",
]

TICKET_KEYWORDS = [
    "ticket", "issue", "bug", "support", "escalation", "sla", "incident",
    "outage", "p1", "p2", "critical",
]


def classify_intent(message: str) -> dict:
    """Classify user chat message into agent routing intent."""
    lower = message.lower()

    if any(kw in lower for kw in CALL_KEYWORDS):
        return {
            "intent": "fathom",
            "event_type": "user_chat_fathom",
            "lanes": ["value"],
        }

    if any(kw in lower for kw in HEALTH_KEYWORDS):
        return {
            "intent": "health",
            "event_type": "user_chat_health",
            "lanes": ["value"],
        }

    if any(kw in lower for kw in TICKET_KEYWORDS):
        return {
            "intent": "ticket",
            "event_type": "user_chat_ticket",
            "lanes": ["support"],
        }

    return {
        "intent": "general",
        "event_type": "user_chat_general",
        "lanes": ["value", "support"],
    }


def _try_resolve_customer(db: Session, message: str):
    """Try to fuzzy-match a customer name from the user's query."""
    from app.models.customer import Customer

    customers = db.query(Customer.id, Customer.name).all()
    lower = message.lower()
    cust_names = [name for _, name in customers]
    logger.info(f"[Chat] Customer resolution: {len(customers)} in DB, query='{lower[:80]}'")
    logger.info(f"[Chat]   DB customers: {cust_names[:20]}{'...' if len(cust_names) > 20 else ''}")

    # Pass 1: exact substring match (customer name in query)
    for cust_id, name in customers:
        if name.lower() in lower:
            return cust_id, name

    # Pass 2: all words of customer name appear in query (handles word reordering)
    for cust_id, name in customers:
        name_words = name.lower().split()
        if len(name_words) >= 1 and all(w in lower for w in name_words):
            return cust_id, name

    # Pass 3: query words match a significant portion of a customer name
    import re
    query_words = set(re.sub(r'[^\w\s]', '', lower).split())
    best_match = None
    best_score = 0
    for cust_id, name in customers:
        name_words = set(name.lower().split())
        if not name_words:
            continue
        overlap = query_words & name_words
        score = len(overlap) / len(name_words)
        if score >= 0.5 and len(overlap) >= 1 and score > best_score:
            best_score = score
            best_match = (cust_id, name)

    if best_match:
        return best_match

    return None, None


# Common filler words to strip when extracting entity names from queries
_ENTITY_FILLER = {
    "what", "was", "were", "is", "are", "the", "a", "an", "in", "on", "at",
    "of", "for", "to", "with", "from", "by", "and", "or", "not", "no",
    "last", "recent", "latest", "first", "my", "our", "their", "this",
    "that", "about", "how", "which", "who", "when", "where", "why",
    "call", "calls", "meeting", "meetings", "discussed", "discussion",
    "takeaway", "takeaways", "key", "points", "summary", "recap",
    "summaries", "customer", "customers", "tell", "me", "give", "show",
    "get", "had", "have", "has", "been", "any", "all", "some", "what's",
    "happened", "happening", "during", "between", "after", "before",
    "issues", "problems", "deployment", "status", "update", "updates",
    "do", "did", "does", "doing", "can", "could", "would", "should",
}


def _extract_entity_from_query(message: str) -> str | None:
    """
    Extract a likely customer/company name from a query when DB resolution fails.

    Strips punctuation, removes common filler words, and returns remaining words
    as a potential entity name for ChromaDB filter_by_customer() lookup.
    Returns None if nothing meaningful remains.
    """
    import re
    # Strip punctuation, keep only letters/numbers/spaces
    cleaned = re.sub(r"[^\w\s]", "", message.lower())
    words = cleaned.split()
    entity_words = [w for w in words if w not in _ENTITY_FILLER and len(w) > 1]

    if not entity_words:
        return None

    # Skip if too long (probably not a name) or single short word (too generic)
    if len(entity_words) > 4 or (len(entity_words) == 1 and len(entity_words[0]) < 4):
        return None

    return " ".join(entity_words)


# ── Answer Formatting ─────────────────────────────────────────────────────

def format_answer(intent: str, result: dict) -> str:
    """Convert raw agent pipeline output into a human-readable chat response."""
    if not result or not result.get("success"):
        error = result.get("error", "Unknown error") if result else "No result"
        return f"I wasn't able to process your request. Error: {error}"

    output = result.get("output", result)
    if isinstance(output, str):
        return output

    # Try to get synthesized summary from orchestrator
    summary = (
        output.get("summary")
        or output.get("reasoning_summary")
        or result.get("reasoning_summary")
        or ""
    )

    if intent == "fathom":
        return _format_fathom_answer(output, summary)
    elif intent == "health":
        return _format_health_answer(output, summary)
    elif intent == "ticket":
        return _format_ticket_answer(output, summary)

    # General fallback
    if summary:
        return summary

    return json.dumps(output, indent=2, default=str)[:3000]


def _ensure_list(val) -> list:
    """Safely coerce a value to a list. Handles dict, str, None, and list."""
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        # Claude sometimes returns {"1": "step one", "2": "step two"} instead of a list
        return list(val.values())
    if isinstance(val, str):
        return [val]
    return []


def _format_fathom_answer(output: dict, summary: str) -> str:
    """Format Fathom agent answer."""
    parts = []

    if summary:
        parts.append(summary)

    # Extract from deliverables if present
    deliverables = output.get("deliverables", {})
    value_result = deliverables.get("value", {})
    value_output = value_result.get("output", value_result) if isinstance(value_result, dict) else {}

    # Key actions
    actions = _ensure_list(output.get("key_actions") or value_output.get("action_items") or [])
    if actions:
        parts.append("\n**Action Items:**")
        for a in actions[:5]:
            item = a if isinstance(a, str) else (a.get("description", a.get("action", str(a))) if isinstance(a, dict) else str(a))
            parts.append(f"- {item}")

    # Sentiment
    sentiment = value_output.get("sentiment") or output.get("sentiment")
    if sentiment:
        parts.append(f"\n**Sentiment:** {sentiment}")

    # Next steps
    next_steps = _ensure_list(output.get("next_steps") or [])
    if next_steps:
        parts.append("\n**Next Steps:**")
        for s in next_steps[:3]:
            parts.append(f"- {s if isinstance(s, str) else str(s)}")

    if not parts:
        return json.dumps(output, indent=2, default=str)[:3000]

    return "\n".join(parts)


def _format_health_answer(output: dict, summary: str) -> str:
    """Format health monitoring answer."""
    parts = []
    if summary:
        parts.append(summary)

    risk = output.get("risk_level")
    score = output.get("score") or output.get("overall_score")
    if score is not None:
        parts.append(f"\n**Health Score:** {score}/100")
    if risk:
        parts.append(f"**Risk Level:** {risk}")

    next_steps = _ensure_list(output.get("next_steps") or [])
    if next_steps:
        parts.append("\n**Recommendations:**")
        for s in next_steps[:3]:
            parts.append(f"- {s if isinstance(s, str) else str(s)}")

    return "\n".join(parts) if parts else (summary or json.dumps(output, indent=2, default=str)[:3000])


def _format_ticket_answer(output: dict, summary: str) -> str:
    """Format ticket/support answer."""
    parts = []
    if summary:
        parts.append(summary)

    actions = _ensure_list(output.get("key_actions") or output.get("suggested_actions") or [])
    if actions:
        parts.append("\n**Suggested Actions:**")
        for a in actions[:5]:
            item = a if isinstance(a, str) else str(a)
            parts.append(f"- {item}")

    return "\n".join(parts) if parts else (summary or json.dumps(output, indent=2, default=str)[:3000])


# ── Core Service ──────────────────────────────────────────────────────────

class ChatService:
    """Business logic for user-facing chat."""

    def _broadcast(self, event_type: str, data: dict):
        """Fire-and-forget WebSocket broadcast."""
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
            logger.debug(f"[Chat] Broadcast failed (non-critical): {e}")

    # ── FAST PATH: Create messages, return immediately ─────────────────

    def create_message_sync(
        self,
        db: Session,
        user_id,
        message: str,
        customer_id=None,
        conversation_id=None,
        message_id=None,
        assistant_message_id=None,
    ) -> dict:
        """
        FAST PATH (~50ms) — Create conversation + messages, return immediately.

        Does NOT run the agent pipeline. That happens in process_message_sync().
        """
        from app.models.chat_conversation import ChatConversation
        from app.models.chat_message import ChatMessage

        user_id = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        conv_id = uuid.UUID(str(conversation_id)) if conversation_id else None
        msg_id = uuid.UUID(str(message_id)) if message_id else None
        asst_id = uuid.UUID(str(assistant_message_id)) if assistant_message_id else None

        logger.info(f"[Chat] Creating message: conv={conv_id}, user={user_id}, msg='{message[:80]}...'")

        # 1. Resolve or create conversation
        if conv_id:
            conv = db.query(ChatConversation).filter_by(id=conv_id).first()
            if not conv:
                conv = ChatConversation(id=conv_id, user_id=user_id, title=message[:60])
                db.add(conv)
                logger.info(f"[Chat] New conversation created: {conv_id}")
        else:
            conv = ChatConversation(user_id=user_id, title=message[:60])
            db.add(conv)

        db.flush()
        logger.info(f"[Chat] Conversation ID: {conv.id}")

        # 2. Save user message
        user_msg = ChatMessage(
            conversation_id=conv.id,
            role="user",
            content=message,
        )
        if msg_id:
            user_msg.id = msg_id
        db.add(user_msg)
        db.flush()

        # 3. Save placeholder assistant message
        assistant_msg = ChatMessage(
            conversation_id=conv.id,
            role="assistant",
            content="Thinking...",
            pipeline_status="processing",
        )
        if asst_id:
            assistant_msg.id = asst_id
        db.add(assistant_msg)
        db.flush()

        db.commit()

        logger.info(f"[Chat] Messages saved: user_msg={user_msg.id}, assistant_msg={assistant_msg.id}")

        return {
            "conversation_id": str(conv.id),
            "message_id": str(user_msg.id),
            "assistant_message_id": str(assistant_msg.id),
        }

    # ── UNIFIED PATH: Create records + run fast path in background ─────

    def process_message_full(
        self,
        user_id_str: str,
        message: str,
        customer_id_str: str | None,
        conversation_id_str: str,
        message_id_str: str,
        assistant_msg_id_str: str,
    ) -> None:
        """
        Single background thread entry: creates DB records THEN runs the fast path.
        Called from /send — the endpoint returns immediately with pre-generated UUIDs.
        """
        from app.database import get_sync_session

        db = get_sync_session()
        try:
            # 1. Create conversation + messages (reuses warm sync pool, ~50ms)
            result = self.create_message_sync(
                db=db,
                user_id=user_id_str,
                message=message,
                customer_id=customer_id_str if customer_id_str else None,
                conversation_id=conversation_id_str,
                message_id=message_id_str,
                assistant_message_id=assistant_msg_id_str,
            )
            db.close()

            # 2. Run the fast path (opens its own session)
            self.process_message_sync(
                user_id_str=user_id_str,
                message=message,
                customer_id_str=customer_id_str,
                conversation_id_str=conversation_id_str,
                assistant_msg_id_str=assistant_msg_id_str,
            )
        except Exception as e:
            logger.error(f"[Chat] process_message_full failed: {e}", exc_info=True)
            try:
                from app.models.chat_message import ChatMessage
                import uuid as _uuid
                msg = db.query(ChatMessage).filter_by(id=_uuid.UUID(assistant_msg_id_str)).first()
                if msg and msg.pipeline_status == "processing":
                    msg.content = "I encountered an error processing your request. Please try again."
                    msg.pipeline_status = "failed"
                    db.commit()
            except Exception:
                pass
            finally:
                db.close()

    # ── HEAVY PATH: Run agent pipeline in background ───────────────────

    def process_message_sync(
        self,
        user_id_str: str,
        message: str,
        customer_id_str: str | None,
        conversation_id_str: str,
        assistant_msg_id_str: str,
    ) -> None:
        """
        HEAVY PATH (10-60s) — Runs in a background thread.

        Opens its own DB session, classifies intent, pre-fetches data,
        runs the agent pipeline, and broadcasts the result via WebSocket.
        """
        import sys
        from app.database import get_sync_session

        logger.info(f"{'#'*70}")
        logger.info(f"# [Chat] BACKGROUND THREAD STARTED")
        logger.info(f"# Query  : {message[:120]!r}")
        logger.info(f"# Conv   : {conversation_id_str}")
        logger.info(f"# MsgID  : {assistant_msg_id_str}")
        logger.info(f"{'#'*70}")

        db = get_sync_session()
        try:
            self._process_message_inner(
                db, user_id_str, message, customer_id_str,
                conversation_id_str, assistant_msg_id_str,
            )
        except Exception as e:
            logger.error(f"[Chat] Background processing crashed: {e}", exc_info=True)
            logger.error(f"[Chat] ✗ CRASH: {e}")
            # Try to update the assistant message with the error
            try:
                from app.models.chat_message import ChatMessage
                assistant_msg_id = uuid.UUID(assistant_msg_id_str)
                msg = db.query(ChatMessage).filter_by(id=assistant_msg_id).first()
                if msg and msg.pipeline_status == "processing":
                    msg.content = "I encountered an error processing your request. Please try again."
                    msg.pipeline_status = "failed"
                    msg.execution_metadata = {"error": str(e)}
                    db.commit()

                self._broadcast("chat:message_failed", {
                    "conversation_id": conversation_id_str,
                    "message_id": assistant_msg_id_str,
                    "error": str(e)[:200],
                })
            except Exception as inner_e:
                logger.error(f"[Chat] Failed to update error state: {inner_e}")
        finally:
            db.close()
            logger.info(f"[Chat] Background thread exiting for conv={conversation_id_str}")
            logger.info(f"[Chat] Background processing finished for conv={conversation_id_str}")

    def _process_message_inner(
        self,
        db: Session,
        user_id_str: str,
        message: str,
        customer_id_str: str | None,
        conversation_id_str: str,
        assistant_msg_id_str: str,
    ) -> None:
        """Core background processing logic."""
        import sys
        from app.models.chat_conversation import ChatConversation
        from app.models.chat_message import ChatMessage
        from app.models.customer import Customer
        from app.models.event import Event

        conversation_id = uuid.UUID(conversation_id_str)
        assistant_msg_id = uuid.UUID(assistant_msg_id_str)
        customer_id = uuid.UUID(customer_id_str) if customer_id_str else None

        logger.info("[Chat] ── STEP 1: Classify intent ──")

        # Helper for stage broadcasts
        def _stage(stage: str, label: str, num: int, detail: str = ""):
            self._broadcast("chat:stage_update", {
                "conversation_id": conversation_id_str,
                "message_id": assistant_msg_id_str,
                "stage": stage,
                "stage_label": label,
                "stage_number": num,
                "total_stages": 7,
                "detail": detail,
            })

        # 1. Classify intent
        intent_info = classify_intent(message)
        intent = intent_info["intent"]
        logger.info(f"[Chat]   intent={intent}  event_type={intent_info['event_type']}  lanes={intent_info['lanes']}")
        _stage("classify_intent", "Classifying intent", 1, f"Intent: {intent}")

        # 2. Resolve customer
        logger.info("[Chat] ── STEP 2: Resolve customer ──")
        resolved_customer_id = customer_id
        customer_name = None
        if not resolved_customer_id:
            resolved_customer_id, customer_name = _try_resolve_customer(db, message)
            if resolved_customer_id:
                logger.info(f"[Chat]   Fuzzy match → {customer_name} ({resolved_customer_id})")
            else:
                logger.info("[Chat]   No customer matched in query")
        else:
            logger.info(f"[Chat]   customer_id provided: {resolved_customer_id}")

        if resolved_customer_id and not customer_name:
            cust = db.query(Customer).filter_by(id=resolved_customer_id).first()
            customer_name = cust.name if cust else None
            if customer_name:
                logger.info(f"[Chat]   Customer name resolved: {customer_name}")

        _stage("resolve_customer", "Resolving customer", 2, f"Customer: {customer_name or 'None matched'}")

        # Update conversation with customer if resolved
        if resolved_customer_id:
            conv = db.query(ChatConversation).filter_by(id=conversation_id).first()
            if conv and not conv.customer_id:
                conv.customer_id = resolved_customer_id
                db.commit()

        # ── FAST PATH: Build memory + single Claude call ──
        logger.info("[Chat] ── STEP 3: FAST PATH — Build memory + single-call response ──")
        prefetched = {}
        try:
            from app.agents.memory_agent import CustomerMemoryAgent
            from app.services.chat_fast_path import chat_fast_path

            # Build customer/portfolio memory (1-2 DB queries)
            memory_agent = CustomerMemoryAgent()
            if resolved_customer_id:
                logger.info(f"[Chat] Memory: building customer memory for {customer_name} ({resolved_customer_id})")
                customer_memory = memory_agent.build_memory(db, resolved_customer_id)
            else:
                logger.info("[Chat] Memory: building portfolio memory (no customer)")
                customer_memory = memory_agent.build_portfolio_memory(db)
            logger.info(f"[Chat] Memory assembled: keys={list(customer_memory.keys())}")

            # Fathom intent: search ChromaDB meeting knowledge base (155+ real meetings)
            if intent == "fathom":
                from app.services.meeting_knowledge_service import meeting_knowledge_service

                # Determine the best customer name for targeted search:
                # 1. Use DB-resolved name if available
                # 2. Otherwise, extract entity name from query (matches meeting titles in ChromaDB)
                search_customer = customer_name
                if not search_customer:
                    search_customer = _extract_entity_from_query(message)
                    if search_customer:
                        logger.info(f"[Chat] Extracted entity from query: '{search_customer}'")

                # Primary: customer-specific filter (searches meeting_title metadata)
                chunks = []
                if search_customer:
                    chunks = meeting_knowledge_service.filter_by_customer(search_customer, top_k=15)
                    logger.info(f"[Chat] Customer filter '{search_customer}': {len(chunks)} chunks")

                # Supplement with semantic search if not enough customer-specific results
                if len(chunks) < 8:
                    search_query = message
                    if search_customer:
                        search_query = f"[Customer: {search_customer}] {message}"
                    semantic_chunks = meeting_knowledge_service.semantic_search(search_query, top_k=15)
                    seen = {c["chunk_id"] for c in chunks}
                    for c in semantic_chunks:
                        if c["chunk_id"] not in seen:
                            chunks.append(c)
                            seen.add(c["chunk_id"])
                    logger.info(f"[Chat] Meeting knowledge total: {len(chunks)} chunks (customer + semantic)")

                prefetched["meeting_chunks"] = chunks

            # Load conversation history for follow-up coherence
            conv_history = self._get_recent_messages(db, conversation_id, limit=5)
            logger.info(f"[Chat] Conversation history: {len(conv_history)} prior messages loaded")

            # Single Claude Haiku call (~1-3s)
            fast_result = chat_fast_path.answer(
                message=message,
                intent=intent,
                customer_name=customer_name,
                customer_memory=customer_memory,
                prefetched=prefetched,
                conversation_history=conv_history,
            )

            if fast_result and fast_result.get("answer"):
                duration_ms = fast_result.get("duration_ms", 0)
                logger.info(f"[Chat] ✓ FAST PATH succeeded in {duration_ms}ms")
                logger.info(f"[Chat]   Model: {fast_result.get('model', '?')}")
                logger.info(f"[Chat]   Answer length: {len(fast_result['answer'])} chars")
                logger.info(f"[Chat]   Preview: {fast_result['answer'][:200]}")

                # Update assistant message
                assistant_msg = db.query(ChatMessage).filter_by(id=assistant_msg_id).first()
                if assistant_msg:
                    assistant_msg.content = fast_result["answer"]
                    assistant_msg.pipeline_status = "completed"
                    assistant_msg.agents_involved = fast_result["agents_involved"]
                    assistant_msg.execution_metadata = {
                        "intent": intent,
                        "event_type": intent_info["event_type"],
                        "customer_name": customer_name,
                        "fast_path": True,
                        "model": fast_result.get("model", ""),
                        "agent_id": fast_result["agent_id"],
                        "duration_ms": duration_ms,
                    }
                    db.commit()
                    logger.info(f"[Chat] Message saved: status=completed, agent={fast_result['agent_id']}")

                # Log execution for Agent Nexus visibility
                self._log_fast_path(
                    db, fast_result, intent_info, message, resolved_customer_id, duration_ms
                )

                # Broadcast completion
                self._broadcast("chat:message_complete", {
                    "conversation_id": conversation_id_str,
                    "message_id": assistant_msg_id_str,
                    "content": fast_result["answer"],
                    "agents_involved": fast_result["agents_involved"],
                    "fast_path": True,
                })
                return  # DONE — skip the full pipeline

            logger.info("[Chat]   Fast path returned None — falling through to full pipeline")
        except Exception as fast_err:
            logger.warning(f"[Chat]   Fast path error (falling through): {fast_err}")

        # ── FULL PIPELINE (fallback) ──
        logger.info("[Chat] ── FULL PIPELINE: Running agent hierarchy ──")

        # 4. Build event payload
        event_payload = {
            "user_query": message,
            "conversation_id": conversation_id_str,
            "message_id": assistant_msg_id_str,
            "intent": intent,
            "customer_name": customer_name,
            **prefetched,
        }
        logger.info(f"[Chat]   Payload keys: {list(event_payload.keys())}")

        # 5. Create event record
        logger.info("[Chat] ── STEP 4: Create event record ──")
        event = Event(
            id=uuid.uuid4(),
            event_type=intent_info["event_type"],
            source="user_chat",
            payload=event_payload,
            customer_id=resolved_customer_id,
            status="pending",
        )
        db.add(event)
        db.commit()
        logger.info(f"[Chat]   Event created: id={event.id} type={intent_info['event_type']}")
        _stage("create_event", "Creating event record", 4, f"Event: {intent_info['event_type']}")

        # 6. Link event to assistant message
        assistant_msg = db.query(ChatMessage).filter_by(id=assistant_msg_id).first()
        if assistant_msg:
            assistant_msg.event_id = event.id
            assistant_msg.execution_metadata = {
                "intent": intent,
                "event_type": intent_info["event_type"],
                "customer_name": customer_name,
            }
            db.commit()

        # 7. Broadcast processing event
        self._broadcast("chat:processing", {
            "conversation_id": conversation_id_str,
            "message_id": assistant_msg_id_str,
            "event_id": str(event.id),
        })

        # 8. Run the pipeline (THE SLOW PART)
        logger.info("[Chat] ── STEP 5: Run agent pipeline ──")
        logger.info(f"[Chat]   Calling orchestrator.route() for event={event.id}")
        _stage("run_pipeline", "Running agent pipeline", 5, "Orchestrator routing to agents...")

        from app.agents.orchestrator import orchestrator, EVENT_ROUTING, EVENT_LANE_MAP, LANE_LEAD_MAP

        # Broadcast which agents are expected to work
        _agent_names = {
            "cso_orchestrator": "Naveen Kapoor", "support_lead": "Rachel Torres",
            "value_lead": "Damon Reeves", "delivery_lead": "Priya Mehta",
            "triage_agent": "Kai Nakamura", "troubleshooter": "Leo Petrov",
            "escalation_summary": "Maya Santiago", "health_monitor": "Dr. Aisha Okafor",
            "fathom_agent": "Jordan Ellis", "qbr_value": "Sofia Marquez",
            "sow_prerequisite": "Ethan Brooks", "deployment_intelligence": "Zara Kim",
            "customer_memory": "Atlas",
        }
        self._broadcast("chat:agent_working", {
            "conversation_id": conversation_id_str,
            "agent_id": "cso_orchestrator",
            "agent_name": "Naveen Kapoor",
            "stage": "routing",
        })
        for lane in EVENT_LANE_MAP.get(intent_info["event_type"], []):
            lead_id = LANE_LEAD_MAP.get(lane)
            if lead_id:
                self._broadcast("chat:agent_working", {
                    "conversation_id": conversation_id_str,
                    "agent_id": lead_id,
                    "agent_name": _agent_names.get(lead_id, lead_id),
                    "stage": "coordinating",
                })
        specialist = EVENT_ROUTING.get(intent_info["event_type"])
        if specialist and specialist != "cso_orchestrator":
            self._broadcast("chat:agent_working", {
                "conversation_id": conversation_id_str,
                "agent_id": specialist,
                "agent_name": _agent_names.get(specialist, specialist),
                "stage": "analyzing",
            })

        route_result = orchestrator.route(db, {
            "event_id": str(event.id),
            "event_type": intent_info["event_type"],
            "source": "user_chat",
            "payload": event_payload,
            "customer_id": str(resolved_customer_id) if resolved_customer_id else None,
            "description": message,
        })

        result = route_result.get("result", {})
        orchestrator_result = route_result.get("orchestrator_result", {})

        # Log raw pipeline output for debugging
        orch_success = orchestrator_result.get("success") if orchestrator_result else None
        orch_output = orchestrator_result.get("output", {}) if orchestrator_result else {}
        _stage("pipeline_result", "Pipeline completed", 6, f"Success: {result.get('success')}")
        logger.info("[Chat] ── STEP 6: Pipeline result ──")
        logger.info(f"[Chat]   route_result keys        : {list(route_result.keys())}")
        logger.info(f"[Chat]   orchestrator_result.success: {orch_success}")
        logger.info(f"[Chat]   orchestrator_result.output keys: {list(orch_output.keys()) if isinstance(orch_output, dict) else type(orch_output).__name__}")
        logger.info(f"[Chat]   result.success            : {result.get('success') if result else 'N/A'}")
        if isinstance(orch_output, dict):
            for k, v in orch_output.items():
                if k not in ("deliverables",):
                    logger.info(f"[Chat]     output.{k} = {type(v).__name__}: {str(v)[:80]}")

        # 9. Update event status
        event.status = "completed" if result.get("success") else "failed"
        event.routed_to = route_result.get("agent_name")
        event.processed_at = datetime.now(timezone.utc)

        # 10. Format the answer
        logger.info(f"[Chat] ── STEP 7: Format answer (intent={intent}) ──")
        _stage("format_answer", "Formatting response", 7, f"Intent: {intent}")
        final_result = orchestrator_result or result
        try:
            answer = format_answer(intent, final_result)
        except Exception as fmt_err:
            logger.error(f"[Chat]   ✗ format_answer CRASHED: {fmt_err}")
            logger.error(f"[Chat]     result type={type(final_result).__name__}, keys={list(final_result.keys()) if isinstance(final_result, dict) else '?'}")
            raise
        agents = self._extract_agents_involved(orchestrator_result or result)

        logger.info(f"[Chat]   Answer: {len(answer)} chars, agents={agents}")
        logger.info(f"[Chat]   Answer preview: {answer[:200]}")

        # 11. Update assistant message
        assistant_msg = db.query(ChatMessage).filter_by(id=assistant_msg_id).first()
        if assistant_msg:
            assistant_msg.content = answer
            assistant_msg.pipeline_status = "completed" if result.get("success") else "failed"
            assistant_msg.agents_involved = agents
            assistant_msg.execution_metadata = {
                "intent": intent,
                "event_type": intent_info["event_type"],
                "lanes_used": (orchestrator_result or result).get("lanes_used", intent_info["lanes"]),
                "customer_name": customer_name,
            }
            db.commit()

        # 12. Broadcast completion
        self._broadcast("chat:message_complete", {
            "conversation_id": conversation_id_str,
            "message_id": assistant_msg_id_str,
            "content": answer,
            "agents_involved": agents,
            "event_id": str(event.id),
            "execution_metadata": assistant_msg.execution_metadata if assistant_msg else {},
        })

        logger.info(f"[Chat] ✓ DONE — response sent to frontend ({len(answer)} chars)")
        logger.info(f"[Chat] Message complete broadcast sent for conv={conversation_id_str}")

    def complete_message_sync(
        self, db: Session, event_id: str, result: dict, route_result: dict
    ):
        """
        Called from event_service / agent_tasks when a user_chat pipeline completes.
        Updates the placeholder assistant ChatMessage with the actual answer.
        """
        from app.models.chat_message import ChatMessage

        msg = (
            db.query(ChatMessage)
            .filter_by(event_id=event_id, pipeline_status="processing")
            .first()
        )
        if not msg:
            logger.debug(f"[Chat] No pending chat message for event {event_id}")
            return

        intent = "general"
        if msg.execution_metadata and isinstance(msg.execution_metadata, dict):
            intent = msg.execution_metadata.get("intent", "general")

        orchestrator_result = route_result.get("orchestrator_result", result)
        answer = format_answer(intent, orchestrator_result or result)
        agents = self._extract_agents_involved(orchestrator_result or result)

        msg.content = answer
        msg.pipeline_status = "completed" if result.get("success") else "failed"
        msg.agents_involved = agents
        if msg.execution_metadata:
            msg.execution_metadata = {
                **msg.execution_metadata,
                "lanes_used": (orchestrator_result or result).get("lanes_used", []),
            }
        db.commit()

        self._broadcast("chat:message_complete", {
            "conversation_id": str(msg.conversation_id),
            "message_id": str(msg.id),
            "content": answer,
            "agents_involved": agents,
        })

    def _extract_agents_involved(self, result: dict) -> list[str]:
        """Extract list of agent IDs that participated."""
        agents = set()
        agents.add("cso_orchestrator")

        deliverables = result.get("deliverables", {})
        if not deliverables and isinstance(result.get("output"), dict):
            deliverables = result["output"].get("deliverables", {})

        lanes_used = result.get("lanes_used", [])
        if not lanes_used and isinstance(result.get("output"), dict):
            lanes_used = result["output"].get("lanes_used", [])

        from app.agents.orchestrator import LANE_LEAD_MAP, EVENT_ROUTING

        for lane in lanes_used:
            lead = LANE_LEAD_MAP.get(lane)
            if lead:
                agents.add(lead)

        # Try to infer specialist from event type
        event_type = result.get("event_type", "")
        specialist = EVENT_ROUTING.get(event_type)
        if specialist:
            agents.add(specialist)

        return sorted(agents)

    def _get_recent_messages(self, db: Session, conversation_id, limit: int = 5) -> list[dict]:
        """Load recent conversation messages for follow-up context."""
        from app.models.chat_message import ChatMessage

        messages = (
            db.query(ChatMessage)
            .filter_by(conversation_id=conversation_id)
            .filter(ChatMessage.pipeline_status != "processing")
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {"role": m.role, "content": m.content[:500]}
            for m in reversed(messages)
        ]

    def _log_fast_path(
        self, db: Session, fast_result: dict, intent_info: dict,
        message: str, customer_id, duration_ms: int,
    ) -> None:
        """Log a fast path execution to agent_logs for visibility."""
        try:
            from app.models.agent_log import AgentLog

            log = AgentLog(
                id=uuid.uuid4(),
                agent_name=fast_result["agent_id"],
                agent_type="fast_path",
                event_type=intent_info["event_type"],
                trigger_event="user_chat",
                customer_id=customer_id,
                input_summary=message[:2000],
                output_summary=fast_result["answer"][:2000],
                reasoning_summary=f"Fast path: {intent_info['intent']} via {fast_result.get('model', 'haiku')}",
                status="completed",
                duration_ms=duration_ms,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning(f"[Chat] Failed to log fast path execution: {e}")


chat_service = ChatService()
