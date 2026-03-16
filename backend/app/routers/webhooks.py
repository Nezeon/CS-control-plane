"""
Webhook receivers for external integrations.

Fathom sends a POST when new meeting content is ready. We verify the
signature, extract the meeting data, and push a `fathom_recording_ready`
event into the existing orchestrator pipeline.
"""

import base64
import hashlib
import hmac
import logging
import time

from fastapi import APIRouter, Header, HTTPException, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.fathom_service import fathom_service

logger = logging.getLogger("routers.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _verify_fathom_signature(
    body: bytes,
    webhook_id: str,
    webhook_timestamp: str,
    webhook_signature: str,
    secret: str,
) -> bool:
    """
    Verify a Fathom webhook signature (HMAC-SHA256).

    Signed content = "{webhook_id}.{webhook_timestamp}.{body}"
    Secret is base64-encoded after the "whsec_" prefix.
    """
    if not secret:
        return True  # Skip verification if no secret configured

    try:
        # Strip "whsec_" prefix and decode
        secret_bytes = base64.b64decode(secret.removeprefix("whsec_"))
    except Exception:
        logger.error("Failed to decode webhook secret")
        return False

    # Check timestamp freshness (5-minute tolerance)
    try:
        ts = int(webhook_timestamp)
        if abs(time.time() - ts) > 300:
            logger.warning("Webhook timestamp too old — possible replay attack")
            return False
    except (ValueError, TypeError):
        return False

    # Compute expected signature
    signed_content = f"{webhook_id}.{webhook_timestamp}.{body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(secret_bytes, signed_content.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    # The header may contain multiple signatures: "v1,<sig1> v1,<sig2>"
    for sig_entry in webhook_signature.split(" "):
        parts = sig_entry.split(",", 1)
        if len(parts) == 2 and hmac.compare_digest(expected, parts[1]):
            return True

    return False


@router.post("/fathom", status_code=status.HTTP_200_OK)
async def fathom_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    webhook_id: str | None = Header(default=None, alias="webhook-id"),
    webhook_timestamp: str | None = Header(default=None, alias="webhook-timestamp"),
    webhook_signature: str | None = Header(default=None, alias="webhook-signature"),
):
    """
    Receive Fathom webhook events (meeting_content_ready).

    Fathom POSTs the full meeting object (with transcript, summary,
    action_items based on your webhook configuration).
    """
    body = await request.body()

    # Verify signature if secret is configured
    if settings.FATHOM_WEBHOOK_SECRET:
        if not webhook_id or not webhook_timestamp or not webhook_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook verification headers",
            )
        if not _verify_fathom_signature(
            body, webhook_id, webhook_timestamp, webhook_signature,
            settings.FATHOM_WEBHOOK_SECRET,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    payload = await request.json()
    recording_id = payload.get("recording_id")
    title = payload.get("title", "Untitled Meeting")

    logger.info(f"Fathom webhook received: recording_id={recording_id}, title={title}")

    # Build transcript text from the structured array
    transcript_items = payload.get("transcript", [])
    transcript_text = fathom_service.build_flat_transcript(transcript_items)

    # Extract participants
    participants = fathom_service.extract_participants(payload)

    # Estimate duration
    duration_minutes = fathom_service.estimate_duration_minutes(payload)

    # Extract summary
    summary_data = payload.get("default_summary", {})
    fathom_summary = summary_data.get("markdown_formatted") if summary_data else None

    # Extract action items
    fathom_action_items = payload.get("action_items", [])

    # Build event payload matching what FathomAgent expects
    event_payload = {
        "recording_id": str(recording_id),
        "title": title,
        "transcript": transcript_text,
        "participants": participants,
        "duration_minutes": duration_minutes,
        "fathom_summary": fathom_summary,
        "fathom_action_items": fathom_action_items,
        "call_date": payload.get("recording_start_time") or payload.get("created_at"),
        "fathom_url": payload.get("url"),
        "share_url": payload.get("share_url"),
    }

    # Resolve customer from meeting title (sync DB for simplicity)
    customer_id = None
    try:
        from app.database import get_sync_session
        from app.tasks.agent_tasks import _resolve_customer
        sync_db = get_sync_session()
        try:
            customer_id, customer_name = _resolve_customer(sync_db, title, participants)
            if customer_id:
                sync_db.commit()
                logger.info(f"Fathom webhook: matched customer '{customer_name}' for '{title}'")
        finally:
            sync_db.close()
    except Exception as e:
        logger.warning(f"Customer resolution failed (non-critical): {e}")

    # Push into the event pipeline
    from app.services.event_service import event_service

    result = await event_service.create_and_process_event(
        db_session=db,
        event_type="fathom_recording_ready",
        source="fathom_webhook",
        payload=event_payload,
        customer_id=customer_id,
    )

    logger.info(
        f"Fathom webhook processed: recording_id={recording_id}, "
        f"event_status={result.get('status')}"
    )

    return {"status": "received", "event_id": str(result.get("id"))}


# ── Jira Webhook ─────────────────────────────────────────────────────────


@router.post("/jira", status_code=status.HTTP_200_OK)
async def jira_webhook(request: Request):
    """
    Receive Jira webhook events (issue_created, issue_updated).

    Jira Cloud sends webhooks with:
      - webhookEvent: "jira:issue_created" | "jira:issue_updated" | ...
      - issue: full issue object
      - changelog: list of field changes (for updates)

    We sync the issue into our DB and optionally trigger the triage pipeline.
    """
    payload = await request.json()

    # Optional: verify shared secret
    if settings.JIRA_WEBHOOK_SECRET:
        secret_header = request.headers.get("x-jira-webhook-secret", "")
        if secret_header != settings.JIRA_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Jira webhook secret",
            )

    webhook_event = payload.get("webhookEvent", "")
    issue = payload.get("issue")

    if not issue:
        logger.warning(f"[JiraWebhook] No issue in payload, event={webhook_event}")
        return {"status": "ignored", "reason": "no issue in payload"}

    jira_key = issue.get("key", "unknown")
    logger.info(f"[JiraWebhook] Received {webhook_event} for {jira_key}")

    # Determine if this is a create or update
    is_create = "created" in webhook_event
    trigger_triage = is_create  # Only auto-triage new tickets

    # Sync the single issue
    try:
        from app.tasks.jira_sync import sync_single_issue
        result = sync_single_issue(jira_key, trigger_triage=trigger_triage)
        logger.info(f"[JiraWebhook] Synced {jira_key}: {result['action']}")
    except RuntimeError:
        # Jira not configured -- accept webhook but skip sync
        logger.warning("[JiraWebhook] Jira service not configured, skipping sync")
        return {"status": "skipped", "reason": "jira not configured"}
    except Exception as e:
        logger.error(f"[JiraWebhook] Failed to sync {jira_key}: {e}", exc_info=True)
        # Return 200 anyway to prevent Jira from retrying
        return {"status": "error", "issue": jira_key, "error": str(e)[:200]}

    # Note: sync_single_issue already creates triage events for new tickets
    # via _fire_triage_events() — no need to duplicate here.

    return {"status": "synced", "issue": jira_key, "action": result.get("action")}


# ── Slack Events API Webhook ────────────────────────────────────────────


@router.post("/slack", status_code=status.HTTP_200_OK)
async def slack_events(request: Request):
    """
    Receive Slack Events API callbacks.

    Handles:
    - ``url_verification`` challenge (during Slack app setup)
    - ``event_callback`` with message events (user chat)

    Returns 200 immediately; processes messages in a background thread via
    the existing chat pipeline (fast path / full agent hierarchy).
    """
    import asyncio
    import json
    from app.services.slack_chat_handler import slack_chat_handler

    body = await request.body()

    # ── Verify signature ────────────────────────────────────────────
    slack_signature = request.headers.get("x-slack-signature", "")
    slack_timestamp = request.headers.get("x-slack-request-timestamp", "")

    if settings.SLACK_SIGNING_SECRET:
        if not slack_chat_handler.verify_signature(slack_timestamp, body, slack_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature",
            )

    payload = json.loads(body)

    # ── URL verification challenge (Slack app setup handshake) ──────
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    # ── Event callbacks ─────────────────────────────────────────────
    if payload.get("type") != "event_callback":
        return {"ok": True}

    event = payload.get("event", {})
    event_id = payload.get("event_id", "")

    # Only handle plain user messages (no bot messages, edits, or subtypes)
    if event.get("type") != "message" or event.get("subtype") or event.get("bot_id"):
        return {"ok": True}

    # Ignore the bot's own messages to prevent loops
    if settings.SLACK_BOT_USER_ID and event.get("user") == settings.SLACK_BOT_USER_ID:
        return {"ok": True}

    # Optional: restrict to specific channel(s)
    channel = event.get("channel", "")
    if settings.SLACK_CHAT_CHANNEL:
        allowed = [c.strip() for c in settings.SLACK_CHAT_CHANNEL.split(",")]
        if channel not in allowed:
            return {"ok": True}

    # Deduplicate (Slack retries after 3s if no 200)
    if slack_chat_handler.is_duplicate(event_id):
        logger.debug(f"[SlackWebhook] Duplicate event {event_id}, skipping")
        return {"ok": True}

    # Extract message details
    text = event.get("text", "").strip()
    slack_user_id = event.get("user", "")

    # Strip @mention prefix (e.g. "<@U12345> how is ACME?" -> "how is ACME?")
    if settings.SLACK_BOT_USER_ID:
        mention_prefix = f"<@{settings.SLACK_BOT_USER_ID}>"
        if text.startswith(mention_prefix):
            text = text[len(mention_prefix):].strip()

    if not text:
        return {"ok": True}

    # Thread mapping: use thread_ts if replying in a thread, else the message's own ts
    thread_ts = event.get("thread_ts") or event.get("ts", "")

    # Resolve Slack user display name (best-effort)
    from app.services.slack_service import slack_service
    user_info = slack_service.get_user_info(slack_user_id)
    slack_user_name = user_info["display_name"] if user_info else slack_user_id

    logger.info(
        f"[SlackWebhook] Message from {slack_user_name} in {channel}: {text[:80]}"
    )

    # Spawn background thread (same pattern as /api/chat/send)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        slack_chat_handler.handle_message,
        channel,
        slack_user_id,
        slack_user_name,
        text,
        thread_ts,
        event_id,
    )

    return {"ok": True}
