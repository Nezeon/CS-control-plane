"""
HubSpot Sync -- Bulk and single deal synchronization.

Pulls deals from HubSpot CRM, maps them to our Deal model,
upserts into PostgreSQL, and fires events for stage changes.

Usage:
  - Full sync:        sync_hubspot_deals()
  - Single deal:      sync_single_deal("12345678")
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.hubspot_service import hubspot_service

logger = logging.getLogger("tasks.hubspot_sync")


def sync_hubspot_deals(trigger_events: bool = True) -> dict:
    """
    Pull deals from HubSpot and upsert into our database.

    Returns:
        {created: int, updated: int, skipped: int, errors: int, total: int}
    """
    from app.database import get_sync_session

    if not hubspot_service.configured:
        logger.warning("[HubSpotSync] HubSpot not configured, skipping sync")
        return {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": 0}

    db = get_sync_session()
    try:
        # Load pipeline stages for label resolution
        hubspot_service.load_stage_cache()

        # Fetch all deals
        deals = hubspot_service.list_all_deals()
        logger.info(f"[HubSpotSync] Starting sync: {len(deals)} deals from HubSpot")

        # Pre-build caches
        customer_cache = _build_customer_cache(db)
        company_cache: dict[str, str | None] = {}  # company_id -> company_name

        # Resolve companies for deals (batch)
        for deal in deals:
            deal_id = str(deal.get("id", ""))
            if not deal_id:
                continue
            try:
                company_ids = hubspot_service.get_deal_associations(deal_id, "companies")
                if company_ids:
                    cid = company_ids[0]  # Primary company
                    if cid not in company_cache:
                        try:
                            company = hubspot_service.get_company(cid)
                            company_cache[cid] = company.get("properties", {}).get("name", "")
                        except Exception:
                            company_cache[cid] = None
                    deal["_company_id"] = cid
                    deal["_company_name"] = company_cache.get(cid)
            except Exception as e:
                logger.debug(f"[HubSpotSync] Could not resolve company for deal {deal_id}: {e}")

        # Upsert each deal
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "total": len(deals)}
        stage_changed_deals = []
        closed_won_deals = []

        BATCH_SIZE = 50
        for i, deal in enumerate(deals):
            try:
                company_name = deal.get("_company_name")
                company_id = deal.get("_company_id")
                mapped = hubspot_service.map_deal_to_internal(deal, company_name=company_name)
                mapped["hubspot_company_id"] = company_id

                result = _upsert_deal(db, mapped, customer_cache=customer_cache)
                stats[result["action"]] += 1

                if result.get("stage_changed") and trigger_events:
                    stage_changed_deals.append(result)
                    # Check for Closed Won
                    new_stage = result.get("new_stage", "")
                    if "closedwon" in new_stage.lower().replace(" ", ""):
                        closed_won_deals.append(result)

                # New deals that are already Closed Won (only if stage didn't change,
                # otherwise the block above already handled it)
                elif result["action"] == "created" and trigger_events:
                    stage = mapped.get("stage", "")
                    if "closedwon" in stage.lower().replace(" ", ""):
                        closed_won_deals.append(result)

            except Exception as e:
                logger.error(f"[HubSpotSync] Failed to upsert deal {deal.get('id')}: {e}")
                stats["errors"] += 1

            if (i + 1) % BATCH_SIZE == 0:
                db.commit()
                logger.info(f"[HubSpotSync] Progress: {i + 1}/{len(deals)} deals processed")

        db.commit()
        logger.info(
            f"[HubSpotSync] Sync complete: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['skipped']} skipped, "
            f"{stats['errors']} errors"
        )

        # Fire events for stage changes
        if stage_changed_deals and trigger_events:
            _fire_deal_events(db, stage_changed_deals, "deal_stage_changed")

        # Fire events for newly Closed Won deals
        if closed_won_deals and trigger_events:
            _fire_deal_events(db, closed_won_deals, "new_customer")

        return stats

    finally:
        db.close()


def sync_single_deal(deal_id: str, trigger_events: bool = True) -> dict:
    """
    Sync a single deal by HubSpot ID.
    Returns {action: "created"|"updated"|"skipped", deal_id: UUID}
    """
    from app.database import get_sync_session

    if not hubspot_service.configured:
        raise RuntimeError("HubSpot not configured")

    deal = hubspot_service.get_deal(deal_id)

    # Resolve company
    company_name = None
    company_id = None
    try:
        company_ids = hubspot_service.get_deal_associations(deal_id, "companies")
        if company_ids:
            company_id = company_ids[0]
            company = hubspot_service.get_company(company_id)
            company_name = company.get("properties", {}).get("name", "")
    except Exception as e:
        logger.debug(f"[HubSpotSync] Could not resolve company for deal {deal_id}: {e}")

    mapped = hubspot_service.map_deal_to_internal(deal, company_name=company_name)
    mapped["hubspot_company_id"] = company_id

    db = get_sync_session()
    try:
        customer_cache = _build_customer_cache(db)
        result = _upsert_deal(db, mapped, customer_cache=customer_cache)
        db.commit()

        if trigger_events and result.get("stage_changed"):
            _fire_deal_events(db, [result], "deal_stage_changed")

        logger.info(f"[HubSpotSync] Single sync: deal {deal_id} -> {result['action']}")
        return result
    finally:
        db.close()


def _build_customer_cache(db: Session) -> dict:
    """Pre-load all customers into a lookup dict (name.lower() -> Customer)."""
    from app.models.customer import Customer
    customers = db.query(Customer).all()
    return {c.name.lower(): c for c in customers}


def _resolve_customer(company_name: str | None, customer_cache: dict) -> tuple:
    """
    Match HubSpot company name to a customer.
    Uses case-insensitive containment matching (same as Jira sync).
    Returns (customer_id, customer_name) or (None, None).
    """
    if not company_name:
        return None, None

    name_lower = company_name.lower().strip()

    # Exact match first
    if name_lower in customer_cache:
        c = customer_cache[name_lower]
        return c.id, c.name

    # Containment match: only if the shorter string is >= 5 chars to avoid
    # false positives (e.g. "Metro" matching "Metro Fiber Networks")
    MIN_CONTAINMENT_LEN = 5
    for cust_name_lower, cust in customer_cache.items():
        shorter = min(len(name_lower), len(cust_name_lower))
        if shorter >= MIN_CONTAINMENT_LEN:
            if name_lower in cust_name_lower or cust_name_lower in name_lower:
                return cust.id, cust.name

    return None, None


def _upsert_deal(db: Session, mapped: dict, customer_cache: dict | None = None) -> dict:
    """
    Insert or update a Deal from mapped HubSpot data.
    Returns {action: "created"|"updated"|"skipped", deal_id: UUID, stage_changed: bool, ...}
    """
    from app.models.deal import Deal

    hubspot_deal_id = mapped["hubspot_deal_id"]
    deal = db.query(Deal).filter_by(hubspot_deal_id=hubspot_deal_id).first()

    # Resolve customer from company name
    customer_id, customer_name = _resolve_customer(
        mapped.get("company_name"), customer_cache or {}
    )

    if deal:
        # Update existing deal
        changed = False
        old_stage = deal.stage

        for field in ("deal_name", "stage", "pipeline", "amount", "close_date",
                      "owner_name", "company_name", "hubspot_company_id",
                      "properties", "hubspot_updated_at"):
            new_val = mapped.get(field)
            if new_val is not None and getattr(deal, field) != new_val:
                setattr(deal, field, new_val)
                changed = True

        if customer_id and not deal.customer_id:
            deal.customer_id = customer_id
            changed = True

        if not changed:
            return {"action": "skipped", "deal_id": deal.id, "stage_changed": False}

        stage_changed = old_stage != deal.stage
        return {
            "action": "updated",
            "deal_id": deal.id,
            "deal_name": deal.deal_name,
            "stage_changed": stage_changed,
            "old_stage": old_stage,
            "new_stage": deal.stage,
            "customer_id": str(deal.customer_id) if deal.customer_id else None,
            "company_name": deal.company_name,
        }
    else:
        # Create new deal
        deal = Deal(
            id=uuid.uuid4(),
            hubspot_deal_id=hubspot_deal_id,
            deal_name=mapped["deal_name"],
            stage=mapped.get("stage"),
            pipeline=mapped.get("pipeline"),
            amount=mapped.get("amount"),
            close_date=mapped.get("close_date"),
            owner_name=mapped.get("owner_name"),
            customer_id=customer_id,
            company_name=mapped.get("company_name"),
            hubspot_company_id=mapped.get("hubspot_company_id"),
            properties=mapped.get("properties", {}),
            hubspot_created_at=mapped.get("hubspot_created_at"),
            hubspot_updated_at=mapped.get("hubspot_updated_at"),
        )
        db.add(deal)
        db.flush()
        return {
            "action": "created",
            "deal_id": deal.id,
            "deal_name": deal.deal_name,
            "stage_changed": False,
            "new_stage": deal.stage,
            "customer_id": str(deal.customer_id) if deal.customer_id else None,
            "company_name": deal.company_name,
        }


def _fire_deal_events(db: Session, deal_results: list, event_type: str):
    """Create events for deal stage changes and dispatch to agent pipeline."""
    from app.models.event import Event
    from app.tasks.agent_tasks import process_event

    events_to_dispatch = []

    for result in deal_results:
        event = Event(
            id=uuid.uuid4(),
            event_type=event_type,
            source="hubspot_sync",
            payload={
                "deal_id": str(result["deal_id"]),
                "deal_name": result.get("deal_name", ""),
                "old_stage": result.get("old_stage", ""),
                "new_stage": result.get("new_stage", ""),
                "company_name": result.get("company_name", ""),
            },
            customer_id=uuid.UUID(result["customer_id"]) if result.get("customer_id") else None,
            status="pending",
        )
        db.add(event)
        events_to_dispatch.append({
            "event_id": str(event.id),
            "event_type": event.event_type,
            "source": event.source,
            "payload": event.payload,
            "customer_id": result.get("customer_id"),
        })

    db.commit()
    logger.info(f"[HubSpotSync] Created {len(events_to_dispatch)} '{event_type}' events")

    for event_dict in events_to_dispatch:
        try:
            process_event(event_dict)
        except Exception as e:
            logger.error(f"[HubSpotSync] Failed to dispatch event: {e}")
