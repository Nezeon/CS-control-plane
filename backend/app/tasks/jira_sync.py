"""
Jira Sync -- Bulk and incremental ticket synchronization.

Pulls issues from Jira via JQL, maps them to our Ticket model,
upserts into PostgreSQL, and optionally triggers triage events.

Usage:
  - Full sync:        sync_jira_tickets()
  - Incremental:      sync_jira_tickets(since="2026-03-06")
  - Single issue:     sync_single_issue("CS-123")
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.jira_service import jira_service

logger = logging.getLogger("tasks.jira_sync")


def sync_jira_tickets(
    since: str | None = None,
    project_keys: list[str] | None = None,
    trigger_triage: bool = True,
) -> dict:
    """
    Pull tickets from Jira and upsert into our database.

    Args:
        since: ISO date string for incremental sync (e.g. "2026-03-06").
               If None, syncs all open tickets.
        project_keys: Jira project keys to sync. Defaults to all customer projects.
        trigger_triage: If True, fire triage events for new tickets.

    Returns:
        {created: int, updated: int, skipped: int, errors: int, total: int}
    """
    from app.database import get_sync_session
    from app.models.customer import Customer

    if not jira_service.configured:
        logger.warning("[JiraSync] Jira not configured, skipping sync")
        return {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": 0}

    db = get_sync_session()
    try:
        # Build project keys from customers if not specified
        if not project_keys:
            customers_with_jira = (
                db.query(Customer.jira_project_key)
                .filter(Customer.jira_project_key.isnot(None))
                .distinct()
                .all()
            )
            project_keys = [c[0] for c in customers_with_jira]

            # Always include default project
            from app.config import settings
            if settings.JIRA_DEFAULT_PROJECT and settings.JIRA_DEFAULT_PROJECT not in project_keys:
                project_keys.append(settings.JIRA_DEFAULT_PROJECT)

        if not project_keys:
            logger.info("[JiraSync] No project keys configured, skipping")
            return {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": 0}

        # Build JQL
        jql = jira_service.build_sync_jql(project_keys=project_keys, since=since)
        logger.info(f"[JiraSync] Starting sync: JQL={jql}")

        # Fetch all matching issues
        issues = jira_service.search_all_issues(jql)
        logger.info(f"[JiraSync] Fetched {len(issues)} issues from Jira")

        # Upsert each issue
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": len(issues)}
        new_ticket_ids = []
        updated_ticket_ids = []
        status_changed_ticket_ids = []

        for issue in issues:
            try:
                result = _upsert_ticket(db, issue)
                stats[result["action"]] += 1
                if result["action"] == "created":
                    if trigger_triage:
                        new_ticket_ids.append(result["ticket_id"])
                    updated_ticket_ids.append(result["ticket_id"])
                elif result["action"] == "updated":
                    updated_ticket_ids.append(result["ticket_id"])
                    if result.get("status_changed"):
                        status_changed_ticket_ids.append(result["ticket_id"])
            except Exception as e:
                logger.error(f"[JiraSync] Failed to upsert {issue.get('key')}: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(
            f"[JiraSync] Sync complete: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['skipped']} skipped, "
            f"{stats['errors']} errors"
        )

        # Fire triage events for new tickets
        if new_ticket_ids and trigger_triage:
            _fire_triage_events(db, new_ticket_ids)

        # Fire update events for status-changed tickets
        if status_changed_ticket_ids:
            _fire_update_events(db, status_changed_ticket_ids)

        # Embed new/updated tickets into ChromaDB for RAG search
        if updated_ticket_ids:
            _embed_tickets(db, updated_ticket_ids)

        return stats

    finally:
        db.close()


def sync_single_issue(jira_key: str, trigger_triage: bool = True) -> dict:
    """
    Sync a single Jira issue by key (e.g. "CS-123").
    Returns {action: "created"|"updated"|"skipped", ticket_id: UUID}
    """
    from app.database import get_sync_session

    if not jira_service.configured:
        raise RuntimeError("Jira not configured")

    issue = jira_service.get_issue(jira_key)
    db = get_sync_session()
    try:
        result = _upsert_ticket(db, issue)
        db.commit()

        if result["action"] == "created" and trigger_triage:
            _fire_triage_events(db, [result["ticket_id"]])

        logger.info(f"[JiraSync] Single sync: {jira_key} -> {result['action']}")
        return result
    finally:
        db.close()


def _upsert_ticket(db: Session, jira_issue: dict) -> dict:
    """
    Insert or update a Ticket from a Jira issue.
    Returns {action: "created"|"updated"|"skipped", ticket_id: UUID}
    """
    from app.models.ticket import Ticket
    from app.models.user import User

    mapped = jira_service.map_issue_to_ticket(jira_issue)
    jira_id = mapped["jira_id"]

    # Look up existing ticket
    ticket = db.query(Ticket).filter_by(jira_id=jira_id).first()

    # Resolve customer: try project key first, then match from ticket summary
    customer_id, customer_name = jira_service.resolve_customer_id(db, mapped["_project_key"])
    if not customer_id:
        customer_id, customer_name = _resolve_customer_from_summary(db, mapped["summary"])

    # Resolve assignee from email
    assigned_to_id = None
    if mapped["_assignee_email"]:
        user = db.query(User).filter_by(email=mapped["_assignee_email"]).first()
        if user:
            assigned_to_id = user.id

    if ticket:
        # Update existing ticket if Jira has newer data
        changed = False
        old_status = ticket.status
        for field in ("summary", "description", "ticket_type", "severity", "status", "resolved_at"):
            new_val = mapped.get(field)
            if new_val is not None and getattr(ticket, field) != new_val:
                setattr(ticket, field, new_val)
                changed = True

        if customer_id and not ticket.customer_id:
            ticket.customer_id = customer_id
            changed = True

        if assigned_to_id and ticket.assigned_to_id != assigned_to_id:
            ticket.assigned_to_id = assigned_to_id
            changed = True

        if not changed:
            return {"action": "skipped", "ticket_id": ticket.id}

        # Track status changes for firing update events
        new_status = ticket.status
        status_changed = old_status != new_status
        return {
            "action": "updated",
            "ticket_id": ticket.id,
            "status_changed": status_changed,
            "old_status": old_status,
            "new_status": new_status,
        }
    else:
        # Create new ticket
        ticket = Ticket(
            id=uuid.uuid4(),
            jira_id=jira_id,
            customer_id=customer_id,
            summary=mapped["summary"],
            description=mapped["description"],
            ticket_type=mapped["ticket_type"],
            severity=mapped["severity"],
            status=mapped["status"],
            assigned_to_id=assigned_to_id,
            created_at=mapped["created_at"],
            resolved_at=mapped["resolved_at"],
        )
        db.add(ticket)
        db.flush()  # Get the ID
        return {"action": "created", "ticket_id": ticket.id}


def _fire_triage_events(db: Session, ticket_ids: list):
    """Create triage events for newly synced tickets so the agent pipeline processes them."""
    from app.models.event import Event
    from app.models.ticket import Ticket

    for ticket_id in ticket_ids:
        ticket = db.query(Ticket).filter_by(id=ticket_id).first()
        if not ticket:
            continue

        event = Event(
            id=uuid.uuid4(),
            event_type="jira_ticket_created",
            source="jira_sync",
            payload={
                "ticket_id": str(ticket.id),
                "jira_id": ticket.jira_id,
                "summary": ticket.summary,
                "description": (ticket.description or "")[:2000],
                "severity": ticket.severity,
                "ticket_type": ticket.ticket_type,
            },
            customer_id=ticket.customer_id,
            status="pending",
        )
        db.add(event)

    db.commit()
    logger.info(f"[JiraSync] Created {len(ticket_ids)} triage events for new tickets")


def _fire_update_events(db: Session, ticket_ids: list):
    """Create update events for tickets whose status changed during sync."""
    from app.models.event import Event
    from app.models.ticket import Ticket

    for ticket_id in ticket_ids:
        ticket = db.query(Ticket).filter_by(id=ticket_id).first()
        if not ticket:
            continue

        event = Event(
            id=uuid.uuid4(),
            event_type="jira_ticket_updated",
            source="jira_sync",
            payload={
                "ticket_id": str(ticket.id),
                "jira_id": ticket.jira_id,
                "summary": ticket.summary,
                "description": (ticket.description or "")[:2000],
                "severity": ticket.severity,
                "status": ticket.status,
                "ticket_type": ticket.ticket_type,
            },
            customer_id=ticket.customer_id,
            status="pending",
        )
        db.add(event)

    db.commit()
    logger.info(f"[JiraSync] Created {len(ticket_ids)} update events for status-changed tickets")


def _embed_tickets(db: Session, ticket_ids: list):
    """Embed tickets into ChromaDB for RAG similarity search."""
    from app.models.ticket import Ticket
    from app.services import rag_service

    embedded = 0
    for ticket_id in ticket_ids:
        try:
            ticket = db.query(Ticket).filter_by(id=ticket_id).first()
            if not ticket:
                continue

            text = f"{ticket.summary} {ticket.description or ''}"[:2000]
            if not text.strip():
                continue

            rag_service.embed_ticket(
                ticket_id=str(ticket.id),
                text=text,
                metadata={
                    "jira_id": ticket.jira_id or "",
                    "customer_id": str(ticket.customer_id) if ticket.customer_id else "",
                    "severity": ticket.severity or "",
                    "status": ticket.status or "",
                    "ticket_type": ticket.ticket_type or "",
                },
            )
            embedded += 1
        except Exception as e:
            logger.warning(f"[JiraSync] Failed to embed ticket {ticket_id}: {e}")

    if embedded:
        logger.info(f"[JiraSync] Embedded {embedded} tickets into ChromaDB")


# Aliases that map to canonical customer names in the DB
_CUSTOMER_ALIASES = {
    "mubcap": "mubadala capital",
    "mubadala cap": "mubadala capital",
    "muc": "mubadala capital",
    "ujjivanbank": "ujjivan bank",
    "soharbank": "sohar bank",
    "alraedahfinance": "alraedah finance",
    "alraedah finance": "alraedah finance",
    "gph_makka": "gph",
    "gph/ksgaa": "gph",
    "ksgaa(saudi)": "ksgaa",
    "goosehead/dms": "goosehead insurance",
    "goosehead/internal": "goosehead insurance",
    "jes/deg": "jes",
    "kazi/deg/connexPay/goosehead insurance": "kazi",
    "visionbank/internal lab": "visionbank",
    "meet marigold poc": "meet marigold",
    "[apache]": "apache (internal)",
    "[rtr]": "apache (internal)",
    "[internal]": "apache (internal)",
    "[dms]": "dms",
    "[libra solutions]": "libra solutions",
    "[ooredoo]": "ooredoo",
    "[tencent]": "tencent",
    "[meet marigold poc]": "meet marigold",
}


def _resolve_customer_from_summary(db: Session, summary: str):
    """
    Match customer name from the ticket summary prefix.
    Handles patterns like 'PDO |', 'Etisalat -', 'MubCap -', '[Apache]', aliases.
    Returns (customer_id, customer_name) or (None, None).
    """
    from app.models.customer import Customer

    if not summary:
        return None, None

    s_lower = summary.lower().strip()

    # Build a name→customer lookup (cached per call, small table)
    customers = db.query(Customer).all()
    name_map = {c.name.lower(): c for c in customers}

    # Step 1: Try bracket patterns like [Apache], [RTR], [DMS]
    if s_lower.startswith("["):
        import re
        m = re.match(r'^\[([^\]]+)\]', s_lower)
        if m:
            bracket = f"[{m.group(1)}]"
            canonical = _CUSTOMER_ALIASES.get(bracket)
            if canonical and canonical in name_map:
                c = name_map[canonical]
                return c.id, c.name

    # Step 2: Extract prefix before first delimiter (| or -)
    import re
    m = re.match(r'^([^|\-\[]+?)\s*[|\-]', s_lower)
    prefix = m.group(1).strip() if m else None

    if prefix:
        # Check alias map first
        canonical = _CUSTOMER_ALIASES.get(prefix)
        if canonical and canonical in name_map:
            c = name_map[canonical]
            return c.id, c.name

        # Check direct name match
        if prefix in name_map:
            c = name_map[prefix]
            return c.id, c.name

        # Check if prefix contains a known customer name
        for name_lower, cust in sorted(name_map.items(), key=lambda x: -len(x[0])):
            if name_lower in prefix and len(name_lower) >= 3:
                return cust.id, cust.name

    # Step 3: Check if any customer name appears near the start (within first 40 chars)
    for name_lower, cust in sorted(name_map.items(), key=lambda x: -len(x[0])):
        if len(name_lower) >= 3 and name_lower in s_lower[:40]:
            return cust.id, cust.name

    return None, None
