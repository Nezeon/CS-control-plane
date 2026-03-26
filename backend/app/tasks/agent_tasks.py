import json
import logging
import re
import uuid
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger("tasks.agent")

# Words to ignore when extracting customer name from Fathom meeting titles
_IGNORE_SEGMENTS = {
    "hivepro", "hive pro", "threat exposure management", "tem",
    "demo", "demonstration", "product demo", "pov",
    "qbr", "review", "sync", "call", "meeting", "weekly",
    "onboarding", "training", "kickoff", "follow up", "followup",
    "internal", "internal team meeting", "team meeting", "standup",
    "weekly standup", "daily standup", "status update", "check in", "checkin",
}

# Keywords that indicate an internal (non-customer) meeting — skip these
_INTERNAL_KEYWORDS = {
    "internal", "standup", "stand-up", "daily standup", "weekly standup",
    "intern ", "internship", "intern standup",
    "interview", "candidate", "hiring",
    "all hands", "townhall", "town hall",
    "sprint", "retrospective", "retro",
    "impromptu", "team building", "offsite",
    "concerns",  # e.g. "Hive Pro Concerns"
    "ai agents",  # e.g. "AI Agents Projects Discussion"
    "development review", "code review", "architecture",
    "agent development", "project discussion", "projects discussion",
    "team sync", "team call", "planning call", "planning session",
    "1:1", "one on one", "1-on-1",
    "biso",  # internal security officer meetings
    "dinner", "event planning",
    "roadmap", "ciso dinner",
    "prep call", "prep ",
}

# Keywords that indicate a customer-facing meeting — allow these
# NOTE: Only include terms specific to customer interactions. Avoid
# generic words like "review", "discussion", "session" which also
# appear in internal meetings.
_CUSTOMER_KEYWORDS = {
    "cadence", "poc", "qbr", "demo", "demonstration",
    "onboarding", "kickoff", "introduction", "platform",
    "deployment", "integration", "caasm", "tem",
    "vpt", "results", "touchpoint", "next steps",
    "insurance", "bank", "finance",
}


def _is_customer_meeting(db, title: str, participants: list[str] | None = None) -> bool:
    """
    Classify whether a Fathom meeting is customer-facing or internal.

    Returns True if the meeting should be imported (customer-facing).
    Returns False if it's internal (standup, interview, 1:1, etc.).
    """
    if not title:
        return False

    title_lower = title.lower().strip()

    # 1. Quick skip: internal keywords
    for kw in _INTERNAL_KEYWORDS:
        if kw in title_lower:
            return False

    # 2. Quick pass: || delimiter = Fathom standard customer format
    #    e.g. "Ujjivan Bank || HivePro TEM || Demo"
    if "||" in title:
        return True

    # 3. Quick pass: "-hivepro" or "hivepro-" pattern = cadence/customer call
    #    e.g. "DMS-HivePro | Regular Cadence Call", "KSAA-Hivepro | Weekly Cadence Call"
    if re.search(r'hivepro\s*[-|]|[-|]\s*hivepro', title_lower):
        return True

    # 4. Skip "Name & Name" or "Name, Name" patterns (1:1 / informal)
    #    e.g. "David & Bryan", "Daniel & Bryan", "Charlie & Bryan"
    if re.match(r'^[\w]+\s*[&,]\s*[\w]+$', title.strip()):
        return False

    # 5. Check for customer-meeting keywords
    for kw in _CUSTOMER_KEYWORDS:
        if kw in title_lower:
            return True

    # 6. Check if title matches an existing customer name in DB
    #    BUT require descriptive content beyond just the name — bare name-only
    #    titles are usually internal prep calls, not structured customer meetings.
    from app.models.customer import Customer
    customers = db.query(Customer.name).all()
    for (cname,) in customers:
        if cname.lower() in title_lower or title_lower in cname.lower():
            remaining = title_lower.replace(cname.lower(), "").strip(" -|/&,.")
            if len(remaining) < 5:
                continue  # Just a name, no description — ambiguous, skip
            return True

    # 7. Default: skip unknown meetings (conservative — only import what we're sure about)
    return False


def _is_celery_available() -> bool:
    """Check if Redis/Celery broker is reachable."""
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.close()
        return True
    except Exception:
        return False


# Aliases for Fathom meeting titles → canonical customer names (lowercased)
_FATHOM_CUSTOMER_ALIASES = {
    "mubcap": "mubadala capital",
    "dms": "direct marketing solutions (dms)",
    "pdo": "petroleum development oman (pdo)",
    "difc": "dubai international financial centre (difc)",
    "bnpb": "badan nasional penanggulangan bencana (bnpb)",
    "modon": "saudi authority for industrial cities and technology zones (modon)",
    "ksgaa": "king salman global academy of arabic language (ksgaa)",
    "gph": "the general presidency for the affairs of the grand mosque and the prophet's mosque (gph) - phase 1",
    "mof": "ministry of finance (mof)",
    "oia": "oman investment authority (oia)",
    "eskanbank": "eskan bank b.s.c",
    "eskan bank": "eskan bank b.s.c",
    "visionbank": "vision bank",
    "itmonkey": "it monkey, south africa",
    "it monkey": "it monkey, south africa",
    "jes": "jeraisy electronic services",
    "connexpay": "connexpay",
    "alraedah": "al raedah finance",
    "alraedahfinance": "al raedah finance",
}


def _resolve_customer(db, title: str, participants: list[str] | None = None):
    """
    Match a Fathom meeting title to an existing customer, or auto-create as prospect.

    Tries exact match, containment, then alias lookup against existing customers.
    If no match, auto-creates a new customer with tier='prospect'.

    Returns (customer_id: UUID, customer_name: str). Always returns a valid pair.
    """
    from app.models.customer import Customer

    if not title:
        return None, None

    # Parse title into segments (split on ||, |, —, –, or spaced -)
    segments = re.split(r'\s*\|\|\s*|\s*\|\s*|\s*[—–]\s*|\s+-\s+', title)
    segments = [s.strip() for s in segments if s.strip()]

    # Further split "Name-HivePro" style compounds (hyphen directly joining words)
    expanded = []
    for seg in segments:
        if re.search(r'\bhivepro\b', seg, re.IGNORECASE) and '-' in seg:
            parts = [p.strip() for p in seg.split('-') if p.strip()]
            expanded.extend(parts)
        else:
            expanded.append(seg)
    segments = expanded

    # Extract customer name from "Hive Pro ... W/CustomerName" pattern
    # e.g. "Hive Pro Demo W/ Geisinger" -> adds "Geisinger"
    for seg in list(segments):
        match = re.search(r'\bw/\s*(.+)$', seg, re.IGNORECASE)
        if match and re.match(r'^hive\s*pro\b', seg, re.IGNORECASE):
            customer_part = match.group(1).strip()
            if len(customer_part) >= 3:
                segments.append(customer_part)

    # Filter out HivePro product / generic words
    candidate_segments = []
    for seg in segments:
        seg_lower = seg.lower().strip()
        if seg_lower in _IGNORE_SEGMENTS:
            continue
        # Skip segments that are purely HivePro product names
        if re.match(r'^hive\s*pro\b', seg, re.IGNORECASE):
            continue
        # Skip event-type suffixes (cadence call, poc kickoff, etc.)
        if seg_lower in {
            "cadence call", "regular cadence call", "weekly cadence call",
            "poc kickoff", "kickoff call", "intro call", "intro/demo",
            "product demo", "platform demo", "hands-on demo",
        }:
            continue
        # Skip very short or numeric-only segments (e.g. "demo 2")
        cleaned = re.sub(r'\d+', '', seg).strip()
        if len(cleaned) < 3:
            continue
        candidate_segments.append(seg)

    if not candidate_segments:
        return None, None

    # Load existing customers
    customers = db.query(Customer.id, Customer.name).all()
    customer_map = {c.name.lower(): (c.id, c.name) for c in customers}

    # Try exact match first, then containment
    for seg in candidate_segments:
        seg_lower = seg.lower()
        # Exact match
        if seg_lower in customer_map:
            return customer_map[seg_lower]
        # Containment: customer name in segment or segment in customer name
        for cname_lower, (cid, cname) in customer_map.items():
            if cname_lower in seg_lower or seg_lower in cname_lower:
                return cid, cname

    # Check alias map before auto-creating
    for seg in candidate_segments:
        alias_target = _FATHOM_CUSTOMER_ALIASES.get(seg.lower())
        if alias_target and alias_target in customer_map:
            return customer_map[alias_target]

    # No match — auto-create as prospect so we keep all call data
    best_name = candidate_segments[0].strip()
    best_name = re.sub(
        r'\s+(poc|kickoff|demo|intro|call|cadence|w/)\s*.*$',
        '', best_name, flags=re.IGNORECASE,
    ).strip()
    if len(best_name) < 2:
        best_name = candidate_segments[0].strip()
    best_name = best_name.title()

    existing = db.query(Customer).filter(
        Customer.name.ilike(best_name)
    ).first()
    if existing:
        return existing.id, existing.name

    new_customer = Customer(
        id=uuid.uuid4(),
        name=best_name,
        tier="prospect",
    )
    db.add(new_customer)
    db.flush()
    logger.info(f"Auto-created prospect '{best_name}' from Fathom meeting: {title}")
    return new_customer.id, best_name


def _ingest_to_knowledge_base(event_payload: dict, result: dict, customer_name: str = ""):
    """Ingest a processed Fathom recording into the meeting_knowledge ChromaDB collection."""
    try:
        from app.services.meeting_knowledge_service import meeting_knowledge_service

        output = result.get("output", result)
        if not isinstance(output, dict):
            return

        data = {
            "recording_id": event_payload.get("recording_id", ""),
            "title": event_payload.get("title", ""),
            "participants": event_payload.get("participants", []),
            "duration_minutes": event_payload.get("duration_minutes"),
            "summary": output.get("summary", ""),
            "key_topics": output.get("key_topics", []),
            "action_items": output.get("action_items", []),
            "decisions": output.get("decisions", []),
            "risks": output.get("risks", []),
            "customer_name": customer_name,
        }
        count = meeting_knowledge_service.ingest_call_insight(data)
        if count > 0:
            logger.info(f"Knowledge base: ingested {count} chunks for {event_payload.get('recording_id', '?')}")
    except Exception as e:
        logger.warning(f"Knowledge base ingestion failed (non-critical): {e}")


@celery_app.task(name="process_event", bind=True, max_retries=2)
def process_event(self, event: dict) -> dict:
    """
    Process an event via direct specialist routing.
    Called as Celery task or synchronously as fallback.
    """
    from app.agents.orchestrator import EVENT_ROUTING
    from app.agents.agent_factory import AgentFactory
    from app.agents.memory_agent import CustomerMemoryAgent
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

        # Direct routing: event → specialist (no orchestrator, no lane leads)
        event_type = event.get("event_type", "")
        customer_id = event.get("customer_id")
        agent_id = EVENT_ROUTING.get(event_type)

        if not agent_id or not AgentFactory.is_registered(agent_id):
            raise ValueError(f"No specialist for event_type={event_type}")

        logger.info(f"[DirectRoute] {event_type} → {agent_id} (customer={customer_id})")

        memory_agent = CustomerMemoryAgent()
        customer_memory = (
            memory_agent.build_memory(db, customer_id) if customer_id
            else memory_agent.build_portfolio_memory(db)
        )

        specialist = AgentFactory.create(agent_id)
        result = specialist.run(db, event, customer_memory)
        route_result = {"agent_name": agent_id, "result": result}

        agent_name = agent_id
        result = route_result.get("result", {})

        # Post-processing: save agent-specific outputs
        if result.get("success"):
            agent = AgentFactory.create(agent_name) if AgentFactory.is_registered(agent_name) else None
            if customer_id and agent_name == "health_monitor" and hasattr(agent, "save_score"):
                agent.save_score(db, customer_id, result)
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

        # Chat completion handling
        event_type = event.get("event_type", "")
        if event_type.startswith("user_chat_"):
            try:
                from app.services.chat_service import chat_service
                chat_service.complete_message_sync(db, str(event_id), result, route_result)
            except Exception as e:
                logger.warning(f"Chat completion failed: {e}")

        # Draft-first flow: create draft + Slack card for non-chat events
        if not event_type.startswith("user_chat_") and agent_name and result.get("success"):
            try:
                from app.services.event_service import event_service
                customer_id = event.get("customer_id")
                event_service._create_draft_for_output(
                    db, agent_name, event_id, customer_id,
                    event_type, result, event.get("payload", {}),
                )
            except Exception as e:
                logger.warning(f"Draft creation failed (non-critical): {e}")

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


def _build_fathom_prompt(transcript: str, customer: dict, payload: dict) -> str:
    """Build prompt for Fathom call transcript analysis."""
    parts = [
        "You are an expert call intelligence analyst. Analyze the following customer call "
        "transcript and extract structured insights with precision and depth.",
        "",
        "## Customer Context",
        f"Customer: {customer.get('name', 'Unknown')}",
        f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
        "",
        "## Call Details",
        f"Title: {payload.get('title', 'N/A')}",
        f"Participants: {', '.join(payload.get('participants', ['Unknown']))}",
        f"Duration: {payload.get('duration_minutes', 'N/A')} minutes",
        "",
        "## Transcript",
        transcript[:8000],
        "",
        "## Output Format",
        "Respond with ONLY a JSON object (no markdown, no extra text). Use this exact schema:",
        '{"summary": "2-3 paragraph executive summary of the call",',
        ' "key_topics": ["topic1", "topic2"],',
        ' "action_items": [{"task": "description", "owner": "person name", "deadline": "date or null"}],',
        ' "decisions": ["decision1", "decision2"],',
        ' "risks": ["risk1", "risk2"],',
        ' "customer_recap_draft": "Brief recap suitable to send to the customer"}',
    ]
    return "\n".join(parts)


def _save_call_insight(db, customer_id, event_payload: dict, result: dict) -> None:
    """Save a CallInsight record from Claude analysis output."""
    from app.models.call_insight import CallInsight

    raw_date = event_payload.get("call_date")
    if isinstance(raw_date, str) and raw_date:
        try:
            call_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            call_date = datetime.now(timezone.utc)
    elif isinstance(raw_date, datetime):
        call_date = raw_date
    else:
        call_date = datetime.now(timezone.utc)

    insight = CallInsight(
        id=uuid.uuid4(),
        customer_id=customer_id,
        fathom_recording_id=event_payload.get("recording_id"),
        call_date=call_date,
        participants=event_payload.get("participants", []),
        summary=result.get("summary"),
        decisions=result.get("decisions", []),
        action_items=result.get("action_items", []),
        risks=result.get("risks", []),
        sentiment=result.get("sentiment"),
        sentiment_score=result.get("sentiment_score"),
        key_topics=result.get("key_topics", []),
        customer_recap_draft=result.get("customer_recap_draft"),
        raw_transcript=event_payload.get("transcript"),
    )
    db.add(insight)


async def run_fathom_sync(days: int = 7) -> dict:
    """
    Core Fathom sync logic — reusable from Celery task, router, or startup.

    Fetches meetings from Fathom API, skips already-imported ones,
    processes new recordings through Claude, and runs pattern detection.

    Returns {status, imported, skipped, total, patterns_detected}.
    """
    from datetime import timedelta
    from app.config import settings
    from app.services.fathom_service import fathom_service, FathomAPIError
    from app.database import get_sync_session
    from app.models.call_insight import CallInsight

    if not settings.FATHOM_API_KEY:
        return {"status": "skipped", "reason": "FATHOM_API_KEY not configured"}

    since = datetime.now(timezone.utc) - timedelta(days=days)
    created_after = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        meetings = await fathom_service.list_all_meetings(
            created_after=created_after,
            include_transcript=True,
            include_summary=True,
            include_action_items=True,
        )
    except FathomAPIError as e:
        return {"status": "error", "error": str(e)}

    # Use a short-lived session for the initial check to avoid Neon idle timeout
    init_db = get_sync_session()
    try:
        existing_ids = {
            row[0] for row in
            init_db.query(CallInsight.fathom_recording_id)
            .filter(CallInsight.fathom_recording_id.isnot(None))
            .all()
        }
    finally:
        init_db.close()

    imported = 0
    skipped = 0
    internal_skipped = 0
    from app.services import claude_service
    from app.services.sentiment_analyzer import analyze_sentiment

    errors = 0
    for meeting in meetings:
        recording_id = str(meeting.get("recording_id", ""))
        if recording_id in existing_ids or not meeting.get("transcript"):
            skipped += 1
            continue

        meeting_title = meeting.get("title", "Untitled")
        meeting_participants = fathom_service.extract_participants(meeting)

        # Skip very short transcripts (<3000 chars ≈ <3 min)
        raw_transcript = fathom_service.build_flat_transcript(
            meeting.get("transcript", [])
        )
        if len(raw_transcript) < 3000:
            internal_skipped += 1
            logger.info(f"Fathom sync: skipped short meeting ({len(raw_transcript)} chars): {meeting_title}")
            skipped += 1
            continue

        # Wrap each meeting in try/except so transient errors don't kill the whole sync
        try:
            # Filter: skip internal meetings (fresh session to avoid Neon timeout)
            db = get_sync_session()
            try:
                is_customer = _is_customer_meeting(db, meeting_title, meeting_participants)
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Fathom sync: DB error checking meeting {recording_id}: {e}")
            errors += 1
            continue

        if not is_customer:
            internal_skipped += 1
            logger.info(f"Fathom sync: skipped internal meeting: {meeting_title}")
            skipped += 1
            continue

        transcript_text = raw_transcript
        participants = meeting_participants
        duration = fathom_service.estimate_duration_minutes(meeting)

        summary_data = meeting.get("default_summary", {})
        fathom_summary = (
            summary_data.get("markdown_formatted") if summary_data else None
        )

        event_payload = {
            "recording_id": recording_id,
            "title": meeting.get("title", "Untitled"),
            "transcript": transcript_text,
            "participants": participants,
            "duration_minutes": duration,
            "fathom_summary": fathom_summary,
            "fathom_action_items": meeting.get("action_items", []),
            "call_date": (
                meeting.get("recording_start_time")
                or meeting.get("created_at")
            ),
        }

        # Resolve customer (fresh session)
        try:
            db = get_sync_session()
            try:
                customer_id, customer_name = _resolve_customer(
                    db, meeting_title, participants
                )
                db.commit()  # commit any auto-created prospect
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Fathom sync: DB error resolving customer for {recording_id}: {e}")
            errors += 1
            continue

        # Claude API call (no DB needed — this takes 10-30s)
        prompt = _build_fathom_prompt(
            transcript_text,
            {"name": customer_name} if customer_name else {},
            event_payload,
        )
        response = claude_service.generate_sync(
            system_prompt="You are an expert call intelligence analyst for a Customer Success team.",
            user_message=prompt,
            max_tokens=3000,
            temperature=0.3,
        )
        if "error" in response:
            logger.warning(f"Fathom sync: Claude error for {recording_id}: {response.get('detail')}")
            skipped += 1
            continue

        result = {}
        try:
            raw_content = response.get("content", "")
            result = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        except (json.JSONDecodeError, TypeError):
            result = claude_service.parse_json_response(response.get("content", ""))

        if not isinstance(result, dict) or result.get("error"):
            logger.warning(f"Fathom sync: Claude parse error for {recording_id}: {str(result)[:200]}")
            skipped += 1
            continue

        # VADER sentiment analysis (no DB needed)
        try:
            sentiment_input = event_payload.get("transcript") or result.get("summary", "")
            sentiment_result = analyze_sentiment(sentiment_input)
            result["sentiment"] = sentiment_result["sentiment"]
            result["sentiment_score"] = sentiment_result["sentiment_score"]
        except Exception as e:
            logger.warning(f"VADER sentiment failed for {recording_id}, defaulting to neutral: {e}")
            result["sentiment"] = "neutral"
            result["sentiment_score"] = 0.5

        wrapped_result = {"success": True, "output": result}

        # Save to DB (fresh session to avoid Neon timeout)
        try:
            db = get_sync_session()
            try:
                _save_call_insight(db, customer_id, event_payload, result)

                # RAG embed
                try:
                    from app.services.rag_service import rag_service
                    topics = result.get("key_topics", [])
                    embed_text = f"{result.get('summary', '')} {' '.join(topics) if isinstance(topics, list) else ''}"
                    if embed_text.strip():
                        latest = db.query(CallInsight).filter_by(
                            fathom_recording_id=recording_id
                        ).order_by(CallInsight.processed_at.desc()).first()
                        iid = str(latest.id) if latest else str(uuid.uuid4())
                        rag_service.embed_insight(iid, embed_text, {
                            "customer_id": str(customer_id) if customer_id else "",
                            "sentiment": result.get("sentiment", ""),
                            "call_date": event_payload.get("call_date", ""),
                            "recording_id": recording_id,
                        })
                except Exception:
                    pass

                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Fathom sync: DB error saving insight for {recording_id}: {e}")
            errors += 1
            continue

        # Ingest into meeting_knowledge ChromaDB (no DB needed)
        _ingest_to_knowledge_base(event_payload, wrapped_result, customer_name or "")

        # Track in existing_ids to avoid re-import if duplicated in API response
        existing_ids.add(recording_id)
        imported += 1
        logger.info(f"Fathom sync: imported recording {recording_id} (customer={customer_name or 'unknown'})")

        # Notify Slack (no DB needed)
        try:
            from app.services.slack_service import slack_service
            if slack_service.configured:
                slack_service.send_call_insight_notification(
                    title=meeting_title,
                    customer_name=customer_name or "",
                    summary=result.get("summary", ""),
                    sentiment=result.get("sentiment", ""),
                    sentiment_score=result.get("sentiment_score"),
                    action_items=result.get("action_items", []),
                    risks=result.get("risks", []),
                    key_topics=result.get("key_topics", []),
                    participants=event_payload.get("participants", []),
                    call_date=event_payload.get("call_date"),
                )
        except Exception as e:
            logger.warning(f"Fathom sync: Slack notification failed (non-critical): {e}")

    # Run pattern detection after sync completes
    db = get_sync_session()
    try:
        patterns_found = _detect_call_patterns(db)
    finally:
        db.close()

    return {
        "status": "ok",
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "total": len(meetings),
        "patterns_detected": len(patterns_found),
    }


@celery_app.task(name="sync_fathom_meetings", bind=True)
def sync_fathom_meetings(self, days: int = 7) -> dict:
    """Celery task wrapper for run_fathom_sync."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run_fathom_sync(days))
    finally:
        loop.close()


def _detect_call_patterns(db) -> list[dict]:
    """
    Analyze recent call insights for cross-call patterns.
    Creates Alert records + sends Slack for any findings.

    Patterns checked:
      1. Repeated negative sentiment (same customer, 2+ in 14 days)
    """
    from sqlalchemy import text
    from app.models.alert import Alert

    patterns = []

    # ── Pattern 1: Repeated negative sentiment ──────────────────────
    try:
        rows = db.execute(text("""
            SELECT ci.customer_id, c.name, COUNT(*) AS neg_count
            FROM call_insights ci
            JOIN customers c ON ci.customer_id = c.id
            WHERE ci.processed_at > NOW() - INTERVAL '14 days'
              AND ci.sentiment IN ('negative', 'mixed')
              AND ci.fathom_recording_id IS NOT NULL
              AND c.is_active = true
            GROUP BY ci.customer_id, c.name
            HAVING COUNT(*) >= 2
        """)).fetchall()
        logger.info(f"Pattern 1 (negative sentiment): {len(rows)} customers with 2+ negative calls")

        for row in rows:
            rd = dict(row._mapping)
            # Dedup: skip if open alert already exists
            existing = db.query(Alert).filter_by(
                customer_id=rd["customer_id"],
                alert_type="call_sentiment_pattern",
                status="open",
            ).first()
            if existing:
                logger.info(f"Pattern 1: skipped {rd['name']} — open alert already exists")
                continue

            # Fetch actual call details for a richer description
            detail_rows = db.execute(text("""
                SELECT ci.call_date, ci.sentiment, ci.sentiment_score,
                       ci.fathom_recording_id
                FROM call_insights ci
                WHERE ci.customer_id = CAST(:cid AS uuid)
                  AND ci.processed_at > NOW() - INTERVAL '14 days'
                  AND ci.sentiment IN ('negative', 'mixed')
                ORDER BY ci.call_date DESC LIMIT 5
            """), {"cid": str(rd["customer_id"])}).fetchall()

            call_lines = []
            for dr in detail_rows:
                d = dict(dr._mapping)
                date_str = d["call_date"].strftime("%b %d") if d.get("call_date") else "Unknown"
                score = f", {d['sentiment_score']:.2f}" if d.get("sentiment_score") is not None else ""
                call_lines.append(f"  • {date_str} — {d['sentiment']}{score}")

            description = f"{rd['neg_count']} calls with negative/mixed sentiment in the last 14 days"
            if call_lines:
                description += ":\n" + "\n".join(call_lines)

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=rd["customer_id"],
                alert_type="call_sentiment_pattern",
                severity="high",
                title=f"Repeated negative call sentiment — {rd['name']}",
                description=description,
                suggested_action=f"Review recent call recordings for {rd['name']} and schedule a check-in",
                status="open",
            )
            db.add(alert)
            patterns.append({"type": "negative_sentiment", "customer": rd["name"], "count": rd["neg_count"]})

            # Slack notification
            try:
                from app.services.slack_service import slack_service
                if slack_service.configured:
                    db.flush()
                    db.refresh(alert)
                    slack_service.send_alert(alert)
                    alert.slack_notified = True
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Pattern detection (negative sentiment) failed: {e}")

    if patterns:
        db.commit()
        logger.info(f"Pattern detection: created {len(patterns)} NEW alerts — {patterns}")
    else:
        logger.info("Pattern detection: no NEW patterns (existing open alerts may have suppressed duplicates — check logs above)")

    return patterns


@celery_app.task(name="run_health_check_all", bind=True)
def run_health_check_all(self) -> dict:
    """Run daily health check for all customers.

    For each customer: runs 5 deterministic health checks + Claude narrative,
    saves score, creates drafts for at-risk customers, sends threshold alerts,
    runs alert rules engine, and posts daily digest to Slack.
    """
    from collections import Counter

    from app.agents.agent_factory import AgentFactory
    from app.agents.memory_agent import CustomerMemoryAgent
    from app.config import settings
    from app.database import get_sync_session
    from app.models.customer import Customer

    # Load customer list with a short-lived session to avoid Neon idle timeout
    init_db = get_sync_session()
    try:
        customers_data = [
            (str(c.id), c.name)
            for c in init_db.query(Customer).filter(Customer.is_active == True).all()
        ]
    finally:
        init_db.close()

    if not customers_data:
        logger.info("[HealthCheck] No active customers found — skipping")
        return {"total": 0, "succeeded": 0, "failed": 0, "results": []}

    memory_agent = CustomerMemoryAgent()
    results = []
    all_flags: list[str] = []

    for i, (cust_id, cust_name) in enumerate(customers_data):
        # Fresh DB session per customer to prevent Neon timeout
        db = get_sync_session()
        try:
            event = {
                "event_type": "daily_health_check",
                "source": "cron",
                "customer_id": cust_id,
                "customer_name": cust_name,
                "payload": {},
            }

            customer_memory = memory_agent.build_memory(db, cust_id)
            specialist = AgentFactory.create("health_monitor")
            result = specialist.run(db, event, customer_memory)

            output = result.get("output", {})
            if not isinstance(output, dict):
                output = {}

            success = result.get("success", False)
            risk_level = output.get("risk_level", "unknown")
            score = output.get("score", output.get("health_score"))
            risk_flags = output.get("risk_flags", [])

            # Save health score to DB
            if success and hasattr(specialist, "save_score"):
                specialist.save_score(db, cust_id, result)

            db.commit()

            # Threshold alert to #cs-executive-urgent for high_risk/critical
            if success and risk_level in ("high_risk", "critical"):
                try:
                    from app.services.slack_service import slack_service
                    if slack_service.configured:
                        flags_str = ", ".join(risk_flags) or "None"
                        # Truncate summary at last sentence within 500 chars
                        raw_summary = output.get("summary", "N/A")
                        if len(raw_summary) > 500:
                            cut = raw_summary[:500].rfind(".")
                            raw_summary = raw_summary[: cut + 1] if cut > 100 else raw_summary[:500] + "…"
                        slack_service.send_message(
                            channel=settings.SLACK_CH_EXEC_URGENT,
                            text=(
                                f":rotating_light: *Health Alert — {cust_name}*\n"
                                f"Score: {score}/100 | Risk: {risk_level}\n"
                                f"Flags: {flags_str}\n"
                                f"Summary: {raw_summary}"
                            ),
                        )
                except Exception as e:
                    logger.warning(f"[HealthCheck] Urgent alert failed for {cust_name}: {e}")

            all_flags.extend(risk_flags)
            results.append({
                "customer_id": cust_id,
                "customer_name": cust_name,
                "success": success,
                "score": score,
                "risk_level": risk_level,
                "risk_flags": risk_flags,
            })
            logger.info(f"[HealthCheck] {i+1}/{len(customers_data)} {cust_name}: score={score}, risk={risk_level}")
        except Exception as e:
            logger.warning(f"[HealthCheck] Failed for {cust_name}: {e}")
            results.append({
                "customer_id": cust_id,
                "customer_name": cust_name,
                "success": False,
                "score": None,
                "risk_level": "unknown",
                "risk_flags": [],
            })
        finally:
            db.close()

        # Cross-customer pattern detection: 5+ customers with same flag → executive urgent
        flag_counts = Counter(all_flags)
        threshold_alerts = []
        for flag, count in flag_counts.items():
            if count >= 5:
                threshold_alerts.append({"type": "issue_cluster", "issue": flag, "affected_count": count})
                try:
                    from app.services.slack_service import slack_service
                    if slack_service.configured:
                        slack_service.send_message(
                            channel=settings.SLACK_CH_EXEC_URGENT,
                            text=(
                                f":warning: *Cross-Customer Pattern Detected*\n"
                                f"Issue: `{flag}` affecting {count} customers\n"
                                f"This exceeds the 5-customer threshold — requires executive attention."
                            ),
                        )
                except Exception:
                    pass

    # Run alert rules engine with a fresh session
    post_db = get_sync_session()
    try:
        from app.services.alert_rules_engine import alert_rules_engine
        alert_stats = alert_rules_engine.evaluate_all(post_db)
        logger.info(f"[HealthCheck] Alert rules: {alert_stats.get('alerts_created', 0)} alerts created")
    except Exception as e:
        logger.warning(f"[HealthCheck] Alert rules failed (non-fatal): {e}")
    finally:
        post_db.close()

    # Post daily digest to #cs-health-alerts
    succeeded = sum(1 for r in results if r["success"])
    at_risk = [r for r in results if r.get("risk_level") in ("watch", "high_risk", "critical")]
    try:
        from app.services.slack_service import slack_service
        if slack_service.configured:
            digest = (
                f":chart_with_upwards_trend: *Health Check Complete*\n"
                f"Customers scored: {succeeded}/{len(results)}\n"
                f"At-risk: {len(at_risk)}"
            )
            if at_risk:
                digest += "\n\n*At-Risk Customers:*\n"
                for r in sorted(at_risk, key=lambda x: x.get("score") or 999):
                    digest += (
                        f"- *{r['customer_name']}* — "
                        f"Score: {r.get('score', '?')}/100, "
                        f"Risk: {r.get('risk_level', '?')}\n"
                    )
            if threshold_alerts:
                digest += "\n*Threshold Alerts:*\n"
                for ta in threshold_alerts:
                    digest += f"- `{ta['issue']}` affecting {ta['affected_count']} customers\n"

            slack_service.send_message(
                channel=settings.SLACK_CH_HEALTH_ALERTS,
                text=digest,
            )
    except Exception as e:
        logger.warning(f"[HealthCheck] Digest post failed (non-fatal): {e}")

    logger.info(
        f"[HealthCheck] Done: {succeeded}/{len(results)} succeeded, "
        f"{len(at_risk)} at-risk, {len(threshold_alerts)} threshold alerts"
    )

    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "at_risk": len(at_risk),
        "threshold_alerts": threshold_alerts,
        "results": results,
    }
