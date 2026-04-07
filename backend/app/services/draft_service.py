"""
Draft Service — Agent output recording and Slack notification.

Every agent output is saved as a record and posted to Slack as an
informational card for the CS team.
"""

import logging
import uuid

from app.config import get_channel_for_draft, settings
from app.models.agent_draft import AgentDraft
from app.models.audit_log import AuditLog

logger = logging.getLogger("services.draft")

# Agent ID → human-readable name for Slack cards
AGENT_DISPLAY_NAMES = {
    "triage_agent": "Ticket Triage (Kai Nakamura)",
    "health_monitor": "Health Monitor (Dr. Aisha Okafor)",
    "escalation_agent": "Escalation Writer (Maya Santiago)",
    "troubleshooter": "Troubleshooting (Leo Petrov)",
    "qbr_value": "QBR / Value (Sofia Marquez)",
    "sow_agent": "SOW & Prerequisite (Ethan Brooks)",
    "deployment_intelligence": "Deployment Intel (Zara Kim)",
    "cso_orchestrator": "CS Orchestrator (Naveen Kapoor)",
    "presales_funnel": "Pre-Sales Funnel Analyst (Jordan Reeves)",
}

# Agent ID → draft_type mapping
AGENT_DRAFT_TYPE = {
    "triage_agent": "triage",
    "health_monitor": "health_alert",
    "escalation_agent": "escalation",
    "troubleshooter": "troubleshoot",
    "qbr_value": "qbr",
    "sow_agent": "sow",
    "deployment_intelligence": "deployment",
    "presales_funnel": "presales",
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
    "presales": "deals",
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
    """Create a draft record and post an informational Slack card."""
    draft_type = AGENT_DRAFT_TYPE.get(agent_id, agent_id)
    channel = get_channel_for_draft(draft_type)

    draft = AgentDraft(
        id=uuid.uuid4(),
        agent_id=agent_id,
        event_id=event_id,
        customer_id=customer_id,
        draft_type=draft_type,
        draft_content=draft_content,
        status="posted",
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

    # Extract jira_id for Slack card link
    jira_id = draft_content.get("jira_id") if isinstance(draft_content, dict) else None
    if not jira_id and isinstance(draft_content, dict):
        jira_id = (draft_content.get("output") or {}).get("jira_id")

    # Post Slack card — use custom card for presales, generic for others
    try:
        from app.services.slack_service import slack_service

        if draft_type == "presales":
            resp = slack_service.send_presales_card(
                channel=channel,
                draft_content=draft_content,
                draft_id=str(draft.id),
                dashboard_url=dashboard_url,
                event_type=event_type or draft_type,
            )
        else:
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
                jira_id=jira_id,
                jira_base_url=settings.JIRA_API_URL if jira_id else None,
                confidence=confidence,
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
        for key in ("summary", "reasoning_summary", "output_summary", "detail", "reasoning"):
            val = content.get(key)
            if val and isinstance(val, str):
                return val[:800]
        # Try nested output
        output = content.get("output", {})
        if isinstance(output, dict):
            for key in ("summary", "reasoning_summary", "reasoning"):
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
        "triage": "Ticket classified — check category and severity.",
        "call_intel": "Call analysis complete — review summary and action items.",
        "health_alert": "Health score changes and risk flags detected.",
        "escalation": "Escalation document drafted for engineering.",
        "troubleshoot": "Root cause analysis and next steps identified.",
        "qbr": "QBR document drafted for customer review.",
        "sow": "SOW document and checklist prepared.",
        "deployment": "Deployment validation results available.",
        "presales": "Pipeline analysis — deals, stages, and win probabilities.",
    }
    return action_hints.get(draft_type, "Agent analysis complete.")
