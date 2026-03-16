"""
Draft Service — Draft-first approval workflow (ARCHITECTURE.md Section 8).

Every agent output is saved as a DRAFT, posted to Slack with Approve/Edit/Dismiss
buttons, and only executed after human approval.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.config import get_channel_for_draft, settings
from app.models.agent_draft import AgentDraft
from app.models.audit_log import AuditLog

logger = logging.getLogger("services.draft")

# Agent ID → human-readable name for Slack cards
AGENT_DISPLAY_NAMES = {
    "triage_agent": "Ticket Triage (Kai Nakamura)",
    "fathom_agent": "Call Intelligence (Jordan Ellis)",
    "health_monitor": "Health Monitor (Dr. Aisha Okafor)",
    "escalation_agent": "Escalation Writer (Maya Santiago)",
    "troubleshooter": "Troubleshooting (Leo Petrov)",
    "qbr_value": "QBR / Value (Sofia Marquez)",
    "sow_agent": "SOW & Prerequisite (Ethan Brooks)",
    "deployment_intelligence": "Deployment Intel (Zara Kim)",
    "meeting_followup": "Meeting Followup (Riley Park)",
    "cso_orchestrator": "CS Orchestrator (Naveen Kapoor)",
}

# Agent ID → draft_type mapping
AGENT_DRAFT_TYPE = {
    "triage_agent": "triage",
    "fathom_agent": "call_intel",
    "health_monitor": "health_alert",
    "escalation_agent": "escalation",
    "troubleshooter": "troubleshoot",
    "qbr_value": "qbr",
    "sow_agent": "sow",
    "deployment_intelligence": "deployment",
    "meeting_followup": "call_intel",
}

# Draft type → dashboard tab for deep-links
DRAFT_DASHBOARD_TAB = {
    "triage": "tickets",
    "call_intel": "calls",
    "health_alert": "",  # main dashboard
    "escalation": "tickets",
    "troubleshoot": "tickets",
    "qbr": "qbr",
    "sow": "overview",
    "deployment": "overview",
}


def create_draft(
    db,
    agent_id: str,
    event_id,
    customer_id,
    draft_content: dict,
    confidence: float | None = None,
    event_type: str = "",
    customer_name: str = "Unknown",
    health_score: int | None = None,
    priority: str | None = None,
) -> AgentDraft:
    """Create a draft record and post a Slack card with approval buttons."""
    draft_type = AGENT_DRAFT_TYPE.get(agent_id, agent_id)
    channel = get_channel_for_draft(draft_type)

    draft = AgentDraft(
        id=uuid.uuid4(),
        agent_id=agent_id,
        event_id=event_id,
        customer_id=customer_id,
        draft_type=draft_type,
        draft_content=draft_content,
        status="pending",
        slack_channel=channel,
        confidence=confidence,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Build dashboard deep-link
    tab = DRAFT_DASHBOARD_TAB.get(draft_type, "")
    if customer_id and tab:
        dashboard_url = f"{settings.DASHBOARD_BASE_URL}/customers/{customer_id}?tab={tab}"
    elif customer_id:
        dashboard_url = f"{settings.DASHBOARD_BASE_URL}/customers/{customer_id}"
    else:
        dashboard_url = settings.DASHBOARD_BASE_URL

    # Extract summary and action from draft content
    summary = _extract_summary(draft_content)
    action_required = _extract_action(draft_content, draft_type)
    agent_name = AGENT_DISPLAY_NAMES.get(agent_id, agent_id)

    # Post Slack card
    try:
        from app.services.slack_service import slack_service

        resp = slack_service.send_agent_card(
            channel=channel,
            agent_name=agent_name,
            event_type=event_type or draft_type,
            customer_name=customer_name,
            health_score=health_score,
            priority=priority,
            summary=summary,
            action_required=action_required,
            draft_id=str(draft.id),
            dashboard_url=dashboard_url,
        )
        if isinstance(resp, dict) and resp.get("ts"):
            draft.slack_message_ts = resp["ts"]
            db.commit()
            logger.info(f"[Draft] Posted card to {channel} (ts={resp['ts']})")
        elif resp:
            logger.info(f"[Draft] Posted card to {channel}")
    except Exception as e:
        logger.warning(f"[Draft] Slack post failed (non-critical): {e}")

    # Log to audit
    _log_audit(
        db,
        agent=agent_id,
        event_id=event_id,
        customer_id=customer_id,
        action=f"draft_created:{draft_type}",
        input_summary=event_type[:500] if event_type else "",
        output_summary=summary[:500],
        confidence=confidence,
        dashboard_url=dashboard_url,
    )

    logger.info(f"[Draft] Created {draft.id} ({draft_type}) for customer {customer_id}")
    return draft


def approve_draft(db, draft_id, approved_by: str = "slack_user") -> AgentDraft | None:
    """Approve a draft — mark as approved, log to audit."""
    draft = db.query(AgentDraft).filter_by(id=draft_id).first()
    if not draft:
        return None

    draft.status = "approved"
    draft.approved_by = approved_by
    draft.approved_at = datetime.now(timezone.utc)
    db.commit()

    _log_audit(
        db,
        agent=draft.agent_id,
        event_id=draft.event_id,
        customer_id=draft.customer_id,
        action=f"draft_approved:{draft.draft_type}",
        output_summary=f"Draft {draft_id} approved by {approved_by}",
        confidence=draft.confidence,
        human_action="approved",
    )

    logger.info(f"[Draft] {draft_id} approved by {approved_by}")
    return draft


def dismiss_draft(db, draft_id, dismissed_by: str = "slack_user") -> AgentDraft | None:
    """Dismiss a draft — mark as dismissed, log rejection to audit."""
    draft = db.query(AgentDraft).filter_by(id=draft_id).first()
    if not draft:
        return None

    draft.status = "dismissed"
    draft.approved_by = dismissed_by
    draft.approved_at = datetime.now(timezone.utc)
    db.commit()

    _log_audit(
        db,
        agent=draft.agent_id,
        event_id=draft.event_id,
        customer_id=draft.customer_id,
        action=f"draft_dismissed:{draft.draft_type}",
        output_summary=f"Draft {draft_id} dismissed by {dismissed_by}",
        confidence=draft.confidence,
        human_action="dismissed",
    )

    logger.info(f"[Draft] {draft_id} dismissed by {dismissed_by}")
    return draft


def edit_draft(db, draft_id, edit_diff: dict, edited_by: str = "slack_user") -> AgentDraft | None:
    """Edit a draft — store edit diff, mark as edited, log to audit."""
    draft = db.query(AgentDraft).filter_by(id=draft_id).first()
    if not draft:
        return None

    draft.status = "edited"
    draft.edit_diff = edit_diff
    draft.approved_by = edited_by
    draft.approved_at = datetime.now(timezone.utc)
    db.commit()

    _log_audit(
        db,
        agent=draft.agent_id,
        event_id=draft.event_id,
        customer_id=draft.customer_id,
        action=f"draft_edited:{draft.draft_type}",
        output_summary=f"Draft {draft_id} edited by {edited_by}",
        confidence=draft.confidence,
        human_action="edited",
        human_edit_diff=edit_diff,
    )

    logger.info(f"[Draft] {draft_id} edited by {edited_by}")
    return draft


# ── Internal helpers ──────────────────────────────────────────────────


def _log_audit(
    db,
    agent: str,
    event_id=None,
    customer_id=None,
    action: str = "",
    input_summary: str = "",
    output_summary: str = "",
    confidence: float | None = None,
    human_action: str | None = None,
    human_edit_diff: dict | None = None,
    dashboard_url: str | None = None,
):
    """Insert a row into the audit_log table."""
    try:
        log = AuditLog(
            id=uuid.uuid4(),
            agent=agent,
            event_id=event_id,
            customer_id=customer_id,
            action=action,
            input_summary=input_summary[:2000] if input_summary else None,
            output_summary=output_summary[:2000] if output_summary else None,
            confidence=confidence,
            human_action=human_action,
            human_edit_diff=human_edit_diff,
            dashboard_url=dashboard_url,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning(f"[Audit] Failed to log (non-critical): {e}")


def _extract_summary(content: dict) -> str:
    """Extract a human-readable summary from draft content."""
    if isinstance(content, dict):
        for key in ("summary", "reasoning_summary", "output_summary", "detail"):
            val = content.get(key)
            if val and isinstance(val, str):
                return val[:800]
        # Try nested output
        output = content.get("output", {})
        if isinstance(output, dict):
            for key in ("summary", "reasoning_summary"):
                val = output.get(key)
                if val and isinstance(val, str):
                    return val[:800]
    return "Agent output ready for review."


def _extract_action(content: dict, draft_type: str) -> str:
    """Extract the suggested action from draft content."""
    if isinstance(content, dict):
        for key in ("suggested_action", "action_required", "next_step", "recommendation"):
            val = content.get(key)
            if val and isinstance(val, str):
                return val[:400]
        # Infer from draft type
        output = content.get("output", {})
        if isinstance(output, dict):
            for key in ("suggested_action", "next_step"):
                val = output.get(key)
                if val and isinstance(val, str):
                    return val[:400]

    action_hints = {
        "triage": "Review ticket classification and approve Jira label update.",
        "call_intel": "Review call analysis and approve customer email draft.",
        "health_alert": "Review health score changes and risk flags.",
        "escalation": "Review escalation document and approve send to engineering.",
        "troubleshoot": "Review root cause analysis and next steps.",
        "qbr": "Review QBR document before sharing with customer.",
        "sow": "Review SOW document and checklist before sharing.",
        "deployment": "Review deployment validation results.",
    }
    return action_hints.get(draft_type, "Review and approve agent output.")
