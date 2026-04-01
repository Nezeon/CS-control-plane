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
    "decline", "improve", "deteriorat", "attrition", "unhappy", "retain",
    "retention", "satisfied",
]

TICKET_KEYWORDS = [
    "ticket", "issue", "bug", "support", "escalation", "sla", "incident",
    "outage", "p1", "p2", "critical",
]

DEAL_KEYWORDS = [
    "deal", "pipeline", "funnel", "conversion", "stalled", "win rate",
    "close rate", "chances", "probability", "poc", "demo", "prospect",
    "hubspot", "presales", "pre-sales",
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

    if any(kw in lower for kw in DEAL_KEYWORDS):
        return {
            "intent": "deal",
            "event_type": "user_chat_deal",
            "lanes": ["presales"],
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
    "deal", "deals", "chances", "probability", "getting", "closing",
    "winning", "win", "close", "us", "pipeline", "funnel", "stalled",
    "conversion", "rate", "stage",
    "feature", "features", "requested", "request", "requests", "most",
    "maximum", "number", "many", "top", "common", "frequent", "frequently",
    "concern", "concerns", "improvement", "improvements", "bug", "bugs",
    "across", "overall", "total", "count", "list", "biggest",
    "highest", "lowest", "worst", "best", "chance", "likely",
    "attrition", "churn", "retain", "retention", "happy", "unhappy",
    "satisfied", "dissatisfied", "result", "reason", "reasons", "main",
    "primary", "didn", "didnt", "didn't", "dont", "why",
    "everything", "info", "information", "details", "detail", "overview",
    "account", "profile", "history", "complete", "full", "entire",
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

        # Fetch conversation once — reused for customer update + Slack channel detection
        conv = db.query(ChatConversation).filter_by(id=conversation_id).first()

        # Update conversation with customer if resolved
        if resolved_customer_id:
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

            # ── Universal cross-reference: enrich with data from all sources ──
            # Runs when we have a resolved customer OR an explicit entity in the query
            explicit_entity = _extract_entity_from_query(message)
            xref_entity = explicit_entity or customer_name
            if xref_entity:
                xref_search = xref_entity.lower().split()[0] if xref_entity else ""
                if len(xref_search) >= 3:
                    try:
                        from sqlalchemy import text as sa_text
                        # Related deals — prefer customer_id match, fall back to text search
                        if "related_deals" not in prefetched:
                            if resolved_customer_id:
                                deal_rows = db.execute(sa_text("""
                                    SELECT deal_name, stage, amount, company_name
                                    FROM deals
                                    WHERE customer_id = CAST(:cid AS uuid)
                                    ORDER BY amount DESC NULLS LAST LIMIT 5
                                """), {"cid": str(resolved_customer_id)}).fetchall()
                            else:
                                deal_rows = db.execute(sa_text("""
                                    SELECT deal_name, stage, amount, company_name
                                    FROM deals
                                    WHERE LOWER(deal_name) LIKE :s OR LOWER(company_name) LIKE :s
                                    ORDER BY amount DESC NULLS LAST LIMIT 5
                                """), {"s": f"%{xref_search}%"}).fetchall()
                            if deal_rows:
                                prefetched["related_deals"] = [
                                    {"deal_name": r[0], "stage": r[1], "amount": r[2], "company_name": r[3]}
                                    for r in deal_rows
                                ]

                        # Related call insights — prefer customer_id match, fall back to text search
                        if "related_calls" not in prefetched:
                            if resolved_customer_id:
                                call_rows = db.execute(sa_text("""
                                    SELECT summary, sentiment, key_topics, risks, decisions, action_items,
                                           call_date, meeting_type
                                    FROM call_insights
                                    WHERE customer_id = CAST(:cid AS uuid)
                                    ORDER BY call_date DESC NULLS LAST LIMIT 8
                                """), {"cid": str(resolved_customer_id)}).fetchall()
                            else:
                                call_rows = db.execute(sa_text("""
                                    SELECT summary, sentiment, key_topics, risks, decisions, action_items,
                                           call_date, meeting_type
                                    FROM call_insights
                                    WHERE LOWER(summary) LIKE :s
                                    ORDER BY call_date DESC NULLS LAST LIMIT 5
                                """), {"s": f"%{xref_search}%"}).fetchall()
                            if call_rows:
                                prefetched["related_calls"] = [
                                    {
                                        "summary": r[0][:400] if r[0] else "",
                                        "sentiment": r[1],
                                        "key_topics": r[2] or [],
                                        "risks": r[3] or [],
                                        "decisions": r[4] or [],
                                        "action_items": r[5] or [],
                                        "call_date": str(r[6]) if r[6] else None,
                                        "meeting_type": r[7] or "",
                                    }
                                    for r in call_rows
                                ]

                        # Meeting chunks from ChromaDB (for deal/health/ticket intents)
                        if "meeting_chunks" not in prefetched:
                            from app.services.meeting_knowledge_service import meeting_knowledge_service
                            chunks = meeting_knowledge_service.filter_by_customer(xref_entity, top_k=5)
                            if chunks:
                                prefetched["meeting_chunks"] = chunks

                        xref_keys = [k for k in ("related_deals", "related_calls", "meeting_chunks") if k in prefetched]
                        if xref_keys:
                            logger.info(f"[Chat] Cross-reference for '{xref_entity}': {xref_keys}")
                    except Exception as e:
                        logger.debug(f"[Chat] Cross-reference failed: {e}")

            # ── Portfolio-wide aggregation (when no specific entity) ──
            # Provides ticket analysis, call topics, and pipeline stats for broad questions
            if not xref_entity:
                try:
                    from sqlalchemy import text as sa_text
                    from collections import Counter

                    # Feature requests + improvements from Jira (with customer names)
                    ticket_rows = db.execute(sa_text("""
                        SELECT t.ticket_type, t.summary, t.severity, c.name as customer_name
                        FROM tickets t
                        LEFT JOIN customers c ON c.id = t.customer_id
                        WHERE t.ticket_type IN ('Improvement', 'New Feature')
                        ORDER BY t.created_at DESC LIMIT 30
                    """)).fetchall()
                    if ticket_rows:
                        prefetched["feature_requests"] = [
                            {
                                "type": r[0],
                                "summary": r[1],
                                "severity": r[2],
                                "customer": r[3] or "Unknown",
                            }
                            for r in ticket_rows
                        ]

                    # Bug tickets (top issues)
                    bug_rows = db.execute(sa_text("""
                        SELECT t.summary, t.severity, t.status, c.name as customer_name
                        FROM tickets t
                        LEFT JOIN customers c ON c.id = t.customer_id
                        WHERE t.ticket_type = 'Bug' AND t.status IN ('open', 'in_progress')
                        ORDER BY CASE t.severity WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, t.created_at DESC
                        LIMIT 15
                    """)).fetchall()
                    if bug_rows:
                        prefetched["open_bugs"] = [
                            {"summary": r[0], "severity": r[1], "status": r[2], "customer": r[3] or "Unknown"}
                            for r in bug_rows
                        ]

                    # Aggregated call topics across all customers
                    topic_rows = db.execute(sa_text("""
                        SELECT key_topics FROM call_insights
                        WHERE key_topics IS NOT NULL AND key_topics != '[]'::jsonb
                        ORDER BY processed_at DESC LIMIT 50
                    """)).fetchall()
                    if topic_rows:
                        all_topics = []
                        for r in topic_rows:
                            topics = r[0]
                            if isinstance(topics, list):
                                all_topics.extend(t.lower() if isinstance(t, str) else str(t) for t in topics)
                        topic_freq = Counter(all_topics).most_common(15)
                        prefetched["aggregated_topics"] = topic_freq

                    # Pipeline summary
                    pipeline = db.execute(sa_text("""
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN stage = 'closedwon' THEN 1 ELSE 0 END) as won,
                            SUM(CASE WHEN stage = 'closedlost' THEN 1 ELSE 0 END) as lost,
                            SUM(CASE WHEN stage NOT IN ('closedwon', 'closedlost') THEN 1 ELSE 0 END) as open_deals
                        FROM deals
                    """)).fetchone()
                    if pipeline:
                        prefetched["pipeline_summary"] = {
                            "total": pipeline[0], "won": pipeline[1],
                            "lost": pipeline[2], "open": pipeline[3],
                        }

                    pf_keys = [k for k in ("feature_requests", "open_bugs", "aggregated_topics", "pipeline_summary") if k in prefetched]
                    if pf_keys:
                        logger.info(f"[Chat] Portfolio prefetch: {pf_keys}")
                except Exception as e:
                    logger.debug(f"[Chat] Portfolio prefetch failed: {e}")

            # Deal intent: also prefetch loss analysis for portfolio questions
            if intent == "deal":
                try:
                    from app.agents.presales_funnel_agent import PreSalesFunnelAgent
                    agent = PreSalesFunnelAgent()
                    prefetched["loss_analysis"] = agent._compute_loss_analysis(db)
                    logger.info(f"[Chat] Loss analysis: {prefetched['loss_analysis'].get('with_call_data', 0)} deals with call data")
                except Exception as e:
                    logger.debug(f"[Chat] Loss analysis failed: {e}")

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

            # Deal intent: prefetch pipeline metrics + meeting intelligence
            if intent == "deal":
                entity = _extract_entity_from_query(message)
                try:
                    from app.agents.presales_funnel_agent import PreSalesFunnelAgent
                    agent = PreSalesFunnelAgent()
                    prefetched["funnel_metrics"] = agent._compute_conversion_rates(db)
                    prefetched["stalled_deals"] = agent._find_stalled_deals(db)
                    prefetched["deal_probabilities"] = agent._compute_deal_probability(db, deal_name=entity)
                    logger.info(f"[Chat] Deal prefetch: {prefetched['funnel_metrics'].get('total_deals', 0)} deals, {len(prefetched.get('deal_probabilities', []))} probabilities")
                except Exception as e:
                    logger.warning(f"[Chat] Deal prefetch failed: {e}")

                # Also fetch meeting intelligence for the deal's company
                if entity:
                    try:
                        from app.services.meeting_knowledge_service import meeting_knowledge_service
                        chunks = meeting_knowledge_service.filter_by_customer(entity, top_k=5)
                        if chunks:
                            prefetched["meeting_chunks"] = chunks
                            logger.info(f"[Chat] Deal meeting context: {len(chunks)} chunks for '{entity}'")
                    except Exception as e:
                        logger.debug(f"[Chat] Deal meeting fetch failed: {e}")

            # Detect Slack channel for per-channel context (reuses conv fetched above)
            slack_channel = (conv.metadata_ or {}).get("slack_channel") if conv else None

            # Load conversation history — per-channel for Slack, per-conversation for web
            conv_history = self._get_recent_messages(
                db, conversation_id, limit=10 if slack_channel else 5, slack_channel=slack_channel
            )
            logger.info(f"[Chat] Conversation history: {len(conv_history)} prior messages loaded (channel={slack_channel or 'none'})")

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
            "conversation_history": conv_history,
            **prefetched,
        }
        logger.info(f"[Chat]   Payload keys: {list(event_payload.keys())}")

        # 5. Create event record — strip transient keys that are only needed
        #    in-memory for the agent pipeline, not for DB persistence
        _TRANSIENT_PAYLOAD_KEYS = {"conversation_history", "meeting_chunks"}
        event_payload_for_db = {k: v for k, v in event_payload.items() if k not in _TRANSIENT_PAYLOAD_KEYS}

        logger.info("[Chat] ── STEP 4: Create event record ──")
        event = Event(
            id=uuid.uuid4(),
            event_type=intent_info["event_type"],
            source="user_chat",
            payload=event_payload_for_db,
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
        logger.info(f"[Chat]   Calling route_direct() for event={event.id}")
        _stage("run_pipeline", "Running agent pipeline", 5, "Routing to specialist...")

        from app.services.event_service import route_direct
        from app.agents.orchestrator import EVENT_ROUTING

        # Broadcast which specialist is working
        _agent_names = {
            "triage_agent": "Kai Nakamura", "troubleshooter": "Leo Petrov",
            "escalation_summary": "Maya Santiago", "health_monitor": "Dr. Aisha Okafor",
            "qbr_value": "Sofia Marquez",
            "sow_prerequisite": "Ethan Brooks", "deployment_intelligence": "Zara Kim",
        }
        specialist = EVENT_ROUTING.get(intent_info["event_type"])
        if specialist:
            self._broadcast("chat:agent_working", {
                "conversation_id": conversation_id_str,
                "agent_id": specialist,
                "agent_name": _agent_names.get(specialist, specialist),
                "stage": "analyzing",
            })

        route_result = route_direct(db, {
            "event_id": str(event.id),
            "event_type": intent_info["event_type"],
            "source": "user_chat",
            "payload": event_payload,
            "customer_id": str(resolved_customer_id) if resolved_customer_id else None,
            "description": message,
        })

        result = route_result.get("result", {})

        # Log pipeline output for debugging
        _stage("pipeline_result", "Pipeline completed", 6, f"Success: {result.get('success')}")
        logger.info("[Chat] ── STEP 6: Pipeline result ──")
        logger.info(f"[Chat]   route_result keys: {list(route_result.keys())}")
        logger.info(f"[Chat]   result.success   : {result.get('success') if result else 'N/A'}")

        # 9. Update event status
        event.status = "completed" if result.get("success") else "failed"
        event.routed_to = route_result.get("agent_name")
        event.processed_at = datetime.now(timezone.utc)

        # 10. Format the answer
        logger.info(f"[Chat] ── STEP 7: Format answer (intent={intent}) ──")
        _stage("format_answer", "Formatting response", 7, f"Intent: {intent}")
        final_result = result
        try:
            answer = format_answer(intent, final_result)
        except Exception as fmt_err:
            logger.error(f"[Chat]   ✗ format_answer CRASHED: {fmt_err}")
            logger.error(f"[Chat]     result type={type(final_result).__name__}, keys={list(final_result.keys()) if isinstance(final_result, dict) else '?'}")
            raise
        agents = self._extract_agents_involved(result)

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
                "lanes_used": result.get("lanes_used", intent_info["lanes"]),
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

        answer = format_answer(intent, result)
        agents = self._extract_agents_involved(result)

        msg.content = answer
        msg.pipeline_status = "completed" if result.get("success") else "failed"
        msg.agents_involved = agents
        if msg.execution_metadata:
            msg.execution_metadata = {
                **msg.execution_metadata,
                "lanes_used": result.get("lanes_used", []),
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

        from app.agents.orchestrator import EVENT_ROUTING

        # Try to infer specialist from event type
        event_type = result.get("event_type", "")
        specialist = EVENT_ROUTING.get(event_type)
        if specialist:
            agents.add(specialist)

        return sorted(agents)

    def _get_recent_messages(self, db: Session, conversation_id, limit: int = 5, slack_channel: str | None = None) -> list[dict]:
        """Load recent messages for follow-up context. Per-channel for Slack, per-conversation otherwise."""
        from app.models.chat_message import ChatMessage
        from app.models.chat_conversation import ChatConversation
        from sqlalchemy import select as sa_select

        if slack_channel:
            # Per-channel: messages from ALL conversations in this Slack channel
            channel_conv_ids = (
                db.query(ChatConversation.id)
                .filter(ChatConversation.metadata_["slack_channel"].astext == slack_channel)
                .subquery()
            )
            messages = (
                db.query(ChatMessage)
                .filter(ChatMessage.conversation_id.in_(sa_select(channel_conv_ids.c.id)))
                .filter(ChatMessage.pipeline_status != "processing")
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            # Per-conversation: original behavior (web/Slack)
            messages = (
                db.query(ChatMessage)
                .filter_by(conversation_id=conversation_id)
                .filter(ChatMessage.pipeline_status != "processing")
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
                .all()
            )

        # 500-char limit: used by fast path (Haiku) which needs fuller context;
        # _prepend_brief() further trims to 300 for full pipeline prompts
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
