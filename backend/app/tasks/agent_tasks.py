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


def _resolve_customer(db, title: str, participants: list[str] | None = None):
    """
    Match a Fathom meeting title to an existing customer, or auto-create one.

    Title formats from Fathom:
      "Ujjivan Bank || HivePro Threat Exposure Management || Demo"
      "hivepro -demo 2 - jeddah airpots"
      "Genpact || HivePro TEM || Product Demo"

    Returns (customer_id: UUID, customer_name: str) or (None, None).
    """
    from app.models.customer import Customer

    if not title:
        return None, None

    # Parse title into segments (split on || or — or -)
    segments = re.split(r'\s*\|\|\s*|\s*[—–]\s*|\s+-\s+', title)
    segments = [s.strip() for s in segments if s.strip()]

    # Filter out HivePro product / generic words
    candidate_segments = []
    for seg in segments:
        seg_lower = seg.lower().strip()
        if seg_lower in _IGNORE_SEGMENTS:
            continue
        # Skip segments that are purely HivePro product names
        if re.match(r'^hivepro\b', seg, re.IGNORECASE):
            continue
        # Skip if segment is only ignore-words combined (e.g. "internal team meeting")
        if any(seg_lower == ign for ign in _IGNORE_SEGMENTS):
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

    # No match found — auto-create a new customer from the best candidate
    best_name = candidate_segments[0]  # First non-HivePro segment is usually the customer
    # Title-case it for consistency
    best_name = best_name.strip().title()

    # Double-check it wasn't just created in this session
    existing = db.query(Customer).filter(
        Customer.name.ilike(best_name)
    ).first()
    if existing:
        return existing.id, existing.name

    new_customer = Customer(
        id=uuid.uuid4(),
        name=best_name,
        tier="standard",
    )
    db.add(new_customer)
    db.flush()  # get the ID without full commit
    logger.info(f"Auto-created customer '{best_name}' from Fathom meeting title: {title}")
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
            # Fathom agent saves even without customer_id (Fathom sync)
            if agent_name == "fathom_agent" and hasattr(agent, "save_insight"):
                payload = event.get("payload", {})
                # Resolve customer if missing
                customer_name = ""
                if not customer_id:
                    customer_id, customer_name = _resolve_customer(
                        db, payload.get("title", ""), payload.get("participants")
                    )
                agent.save_insight(db, customer_id, payload, result)
                # Embed insight into ChromaDB for RAG similarity search
                try:
                    from app.services.rag_service import rag_service
                    output = result.get("output", {})
                    if isinstance(output, dict):
                        topics = output.get("key_topics", [])
                        embed_text = f"{output.get('summary', '')} {' '.join(topics) if isinstance(topics, list) else ''}"
                        if embed_text.strip():
                            from app.models.call_insight import CallInsight as _CI
                            latest = db.query(_CI).filter_by(
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
                # Ingest into meeting_knowledge ChromaDB for agentic RAG
                _ingest_to_knowledge_base(payload, result, customer_name)
                # Notify Slack with the call summary (webhook path)
                try:
                    from app.services.slack_service import slack_service
                    if slack_service.configured:
                        output = result.get("output", result)
                        if isinstance(output, dict):
                            slack_service.send_call_insight_notification(
                                title=payload.get("title", "Untitled"),
                                customer_name=customer_name or "",
                                summary=output.get("summary", ""),
                                sentiment=output.get("sentiment", ""),
                                sentiment_score=output.get("sentiment_score"),
                                action_items=output.get("action_items", []),
                                risks=output.get("risks", []),
                                key_topics=output.get("key_topics", []),
                            )
                except Exception as slack_err:
                    logger.warning(f"Slack call notification failed (non-critical): {slack_err}")
            elif customer_id and agent_name == "health_monitor" and hasattr(agent, "save_score"):
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


async def run_fathom_sync(days: int = 7) -> dict:
    """
    Core Fathom sync logic — reusable from Celery task, router, or startup.

    Fetches meetings from Fathom API, skips already-imported ones,
    processes new recordings through the Fathom agent, and runs pattern detection.

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

    db = get_sync_session()
    try:
        existing_ids = {
            row[0] for row in
            db.query(CallInsight.fathom_recording_id)
            .filter(CallInsight.fathom_recording_id.isnot(None))
            .all()
        }

        imported = 0
        skipped = 0
        internal_skipped = 0
        for meeting in meetings:
            recording_id = str(meeting.get("recording_id", ""))
            if recording_id in existing_ids or not meeting.get("transcript"):
                skipped += 1
                continue

            meeting_title = meeting.get("title", "Untitled")
            meeting_participants = fathom_service.extract_participants(meeting)

            # Skip very short transcripts (<3000 chars ≈ <3 min) — likely internal quick calls
            raw_transcript = fathom_service.build_flat_transcript(
                meeting.get("transcript", [])
            )
            if len(raw_transcript) < 3000:
                internal_skipped += 1
                logger.info(f"Fathom sync: skipped short meeting ({len(raw_transcript)} chars): {meeting_title}")
                skipped += 1
                continue

            # Filter: skip internal meetings (before any Claude call)
            if not _is_customer_meeting(db, meeting_title, meeting_participants):
                internal_skipped += 1
                logger.info(f"Fathom sync: skipped internal meeting: {meeting_title}")
                skipped += 1
                continue

            transcript_text = raw_transcript  # already built above for length check
            participants = meeting_participants  # already extracted above
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

            # Resolve customer from meeting title (meeting_title set above)
            customer_id, customer_name = _resolve_customer(
                db, meeting_title, participants
            )

            # Direct FathomAgent call — bypasses T1→T2→T3 pipeline for speed
            # 1 Claude call per meeting (~30s) instead of ~6 calls (~3 min)
            from app.agents.fathom_agent import FathomAgent
            agent = FathomAgent()

            customer_info = {}
            if customer_name:
                customer_info = {"name": customer_name}

            prompt = agent._build_prompt(
                transcript_text, customer_info, event_payload
            )
            response = agent._call_claude(prompt, max_tokens=3000, temperature=0.3)
            result = agent._parse_claude(response)

            if result.get("error"):
                logger.warning(f"Fathom sync: Claude parse error for {recording_id}: {result.get('error')}")
                skipped += 1
                continue

            # Wrap result in the format save_insight expects
            wrapped_result = {"success": True, "output": result}

            # Save to DB
            agent.save_insight(db, customer_id, event_payload, wrapped_result)

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

            # Ingest into meeting_knowledge ChromaDB
            _ingest_to_knowledge_base(event_payload, wrapped_result, customer_name or "")

            db.commit()  # commit customer auto-creates + insights per meeting
            imported += 1
            logger.info(f"Fathom sync: imported recording {recording_id} (customer={customer_name or 'unknown'})")

            # Notify Slack with the call summary
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
                    )
            except Exception as e:
                logger.warning(f"Fathom sync: Slack notification failed (non-critical): {e}")

        # Run pattern detection after sync completes
        patterns_found = _detect_call_patterns(db)

        return {
            "status": "ok",
            "imported": imported,
            "skipped": skipped,
            "total": len(meetings),
            "patterns_detected": len(patterns_found),
        }
    finally:
        db.close()


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
      2. Recurring problem topics across 3+ meetings
      3. Action item overload (5+ items from recent calls for one customer)
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
            GROUP BY ci.customer_id, c.name
            HAVING COUNT(*) >= 2
        """)).fetchall()

        for row in rows:
            rd = dict(row._mapping)
            # Dedup: skip if open alert already exists
            existing = db.query(Alert).filter_by(
                customer_id=rd["customer_id"],
                alert_type="call_sentiment_pattern",
                status="open",
            ).first()
            if existing:
                continue

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=rd["customer_id"],
                alert_type="call_sentiment_pattern",
                severity="high",
                title=f"Repeated negative call sentiment — {rd['name']}",
                description=f"{rd['neg_count']} calls with negative/mixed sentiment in the last 14 days",
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

    # ── Pattern 2: Recurring topics across multiple meetings ────────
    try:
        import json as _json

        rows = db.execute(text("""
            SELECT ci.key_topics, ci.customer_id, c.name
            FROM call_insights ci
            LEFT JOIN customers c ON ci.customer_id = c.id
            WHERE ci.processed_at > NOW() - INTERVAL '14 days'
              AND ci.key_topics IS NOT NULL
              AND ci.fathom_recording_id IS NOT NULL
        """)).fetchall()

        topic_counts: dict[str, list[str]] = {}  # topic -> list of customer names
        for row in rows:
            rd = dict(row._mapping)
            topics = rd.get("key_topics", [])
            if isinstance(topics, str):
                try:
                    topics = _json.loads(topics)
                except Exception:
                    topics = []
            cname = rd.get("name", "Unknown")
            for topic in (topics or []):
                t = str(topic).lower().strip()
                if t:
                    topic_counts.setdefault(t, []).append(cname)

        problem_keywords = {"issue", "bug", "problem", "outage", "escalation", "blocker", "error", "failure", "delay"}
        # Track customer_ids for each topic to create per-customer alerts
        topic_customer_ids: dict[str, set] = {}
        for row in rows:
            rd = dict(row._mapping)
            topics = rd.get("key_topics", [])
            if isinstance(topics, str):
                try:
                    topics = _json.loads(topics)
                except Exception:
                    topics = []
            cid = rd.get("customer_id")
            for topic in (topics or []):
                t = str(topic).lower().strip()
                if t and cid:
                    topic_customer_ids.setdefault(t, set()).add(cid)

        for topic, customers_list in topic_counts.items():
            if len(customers_list) < 3:
                continue
            # Only alert for problem-related topics
            if not any(kw in topic for kw in problem_keywords):
                continue

            unique_customers = list(set(customers_list))
            customer_ids_for_topic = topic_customer_ids.get(topic, set())

            # Create one alert per affected customer (customer_id is NOT NULL)
            alert_created = False
            for cid in customer_ids_for_topic:
                existing = db.query(Alert).filter_by(
                    customer_id=cid,
                    alert_type="recurring_topic_pattern",
                    status="open",
                ).filter(Alert.description.ilike(f"%{topic}%")).first()
                if existing:
                    continue

                alert = Alert(
                    id=uuid.uuid4(),
                    customer_id=cid,
                    alert_type="recurring_topic_pattern",
                    severity="medium",
                    title=f"Recurring problem topic across calls: {topic}",
                    description=f"Topic '{topic}' appeared in {len(customers_list)} calls across customers: {', '.join(unique_customers[:5])}",
                    suggested_action=f"Investigate root cause of '{topic}' — affecting multiple customers",
                    status="open",
                )
                db.add(alert)
                alert_created = True

                try:
                    from app.services.slack_service import slack_service
                    if slack_service.configured:
                        db.flush()
                        db.refresh(alert)
                        slack_service.send_alert(alert)
                        alert.slack_notified = True
                except Exception:
                    pass

            if alert_created:
                patterns.append({"type": "recurring_topic", "topic": topic, "count": len(customers_list)})
    except Exception as e:
        logger.warning(f"Pattern detection (recurring topics) failed: {e}")

    # ── Pattern 3: Action item overload ─────────────────────────────
    try:
        rows = db.execute(text("""
            SELECT ci.customer_id, c.name,
                   SUM(jsonb_array_length(COALESCE(ci.action_items, '[]'::jsonb))) AS total_actions
            FROM call_insights ci
            JOIN customers c ON ci.customer_id = c.id
            WHERE ci.processed_at > NOW() - INTERVAL '14 days'
              AND ci.fathom_recording_id IS NOT NULL
            GROUP BY ci.customer_id, c.name
            HAVING SUM(jsonb_array_length(COALESCE(ci.action_items, '[]'::jsonb))) >= 5
        """)).fetchall()

        for row in rows:
            rd = dict(row._mapping)
            existing = db.query(Alert).filter_by(
                customer_id=rd["customer_id"],
                alert_type="action_item_overload",
                status="open",
            ).first()
            if existing:
                continue

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=rd["customer_id"],
                alert_type="action_item_overload",
                severity="medium",
                title=f"Action item overload — {rd['name']}",
                description=f"{rd['total_actions']} action items from calls in the last 14 days",
                suggested_action=f"Review and prioritize action items for {rd['name']} — risk of items falling through cracks",
                status="open",
            )
            db.add(alert)
            patterns.append({"type": "action_overload", "customer": rd["name"], "count": rd["total_actions"]})

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
        logger.warning(f"Pattern detection (action overload) failed: {e}")

    if patterns:
        db.commit()
        logger.info(f"Pattern detection: found {len(patterns)} patterns — {patterns}")
    else:
        logger.info("Pattern detection: no new patterns found")

    return patterns


@celery_app.task(name="run_health_check_all", bind=True)
def run_health_check_all(self) -> dict:
    """Run health check for all customers."""
    from app.agents.agent_factory import AgentFactory
    from app.agents.memory_agent import CustomerMemoryAgent
    from app.database import get_sync_session
    from app.models.customer import Customer

    db = get_sync_session()
    try:
        customers = db.query(Customer).all()
        memory_agent = CustomerMemoryAgent()
        results = []
        for customer in customers:
            event = {
                "event_type": "daily_health_check",
                "source": "celery_cron",
                "customer_id": customer.id,
                "payload": {},
            }
            # Direct routing to health_monitor
            customer_memory = memory_agent.build_memory(db, customer.id)
            specialist = AgentFactory.create("health_monitor")
            result = specialist.run(db, event, customer_memory)

            # Save score if successful
            if result.get("success"):
                agent = AgentFactory.create("health_monitor")
                if hasattr(agent, "save_score"):
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
