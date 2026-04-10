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

        # Re-warm DB connection after long company resolution phase (prevents Neon SSL timeout)
        try:
            from sqlalchemy import text as sa_text
            db.execute(sa_text("SELECT 1"))
            db.commit()
        except Exception:
            db.rollback()

        # Enrich existing customers with HubSpot company data (contact, industry, etc.)
        _enrich_existing_customers(db, deals, customer_cache)
        db.commit()

        # Auto-create prospect Customer records for unlinked companies
        _ensure_prospect_customers(db, deals, customer_cache, company_cache)
        db.commit()

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
                # Rollback broken transaction (Neon SSL timeout recovery)
                try:
                    db.rollback()
                except Exception:
                    pass

            if (i + 1) % BATCH_SIZE == 0:
                try:
                    db.commit()
                except Exception:
                    db.rollback()
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

        # Activate prospect customers whose deals just reached Closed Won
        if closed_won_deals:
            _activate_closed_won_customers(db, closed_won_deals)
            db.commit()

        # Populate contract_start from Closed Won deal dates
        _populate_contract_dates(db)
        db.commit()

        # Populate renewal_date from Closed Won deal contract end dates
        _populate_renewal_dates(db)
        db.commit()

        # Populate CS manager from deal owners
        _populate_cs_managers(db)
        db.commit()

        # Clean up any duplicate prospect records (from previous buggy syncs)
        _cleanup_duplicate_prospects(db)
        db.commit()

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
            # Activate prospect if deal reached Closed Won
            new_stage = result.get("new_stage", "")
            if "closedwon" in new_stage.lower().replace(" ", ""):
                _activate_closed_won_customers(db, [result])
                db.commit()

        # Also activate if this is a newly created deal already at Closed Won
        if result["action"] == "created":
            stage = result.get("new_stage", "")
            if "closedwon" in stage.lower().replace(" ", ""):
                _activate_closed_won_customers(db, [result])
                db.commit()

        logger.info(f"[HubSpotSync] Single sync: deal {deal_id} -> {result['action']}")
        return result
    finally:
        db.close()


def _build_customer_cache(db: Session) -> dict:
    """Pre-load all customers into a lookup dict (name.lower() -> Customer)."""
    from app.models.customer import Customer
    customers = db.query(Customer).all()
    return {c.name.lower(): c for c in customers}


def _ensure_prospect_customers(
    db: Session,
    deals: list[dict],
    customer_cache: dict,
    company_cache: dict[str, str | None],
) -> int:
    """
    Auto-create Customer records with tier='prospect' for companies
    that have deals but no matching customer.

    Fetches enriched company details + primary contact from HubSpot.
    Returns count of prospects created.
    """
    from app.models.customer import Customer
    from app.models.deal import Deal

    # Build set of hubspot_company_ids that already have a linked customer in deals table
    linked_companies = set()
    linked_rows = (
        db.query(Deal.hubspot_company_id)
        .filter(Deal.hubspot_company_id.isnot(None), Deal.customer_id.isnot(None))
        .distinct()
        .all()
    )
    for row in linked_rows:
        linked_companies.add(row[0])

    # Also build set of existing prospect company IDs (from metadata) to avoid duplicates
    existing_prospect_company_ids = set()
    existing_prospects = db.query(Customer).filter(Customer.tier == "prospect").all()
    for p in existing_prospects:
        meta = p.metadata_ or {}
        cid = meta.get("hubspot_company_id")
        if cid:
            existing_prospect_company_ids.add(cid)

    # Collect unique companies without a customer match
    seen_companies: dict[str, str] = {}  # company_id -> company_name
    for deal in deals:
        company_id = deal.get("_company_id")
        company_name = deal.get("_company_name")
        if not company_id or not company_name:
            continue
        # Skip if this company already has deals linked to a customer
        if company_id in linked_companies:
            continue
        # Skip if a prospect already exists for this company
        if company_id in existing_prospect_company_ids:
            continue
        # Skip if company name matches an existing customer
        cust_id, _ = _resolve_customer(company_name, customer_cache)
        if cust_id:
            continue
        if company_id not in seen_companies:
            seen_companies[company_id] = company_name

    if not seen_companies:
        return 0

    created = 0
    for company_id, company_name in seen_companies.items():
        try:
            # Fetch enriched company data from HubSpot
            details = hubspot_service.get_company_details(company_id)
            contacts = hubspot_service.get_company_contacts(company_id)
            primary_contact = contacts[0] if contacts else {}

            prospect = Customer(
                id=uuid.uuid4(),
                name=details.get("name") or company_name,
                industry=details.get("industry"),
                tier="prospect",
                is_active=False,
                primary_contact_name=primary_contact.get("name"),
                primary_contact_email=primary_contact.get("email"),
                metadata_={
                    "hubspot_company_id": company_id,
                    "domain": details.get("domain"),
                    "city": details.get("city"),
                    "state": details.get("state"),
                    "country": details.get("country"),
                    "phone": details.get("phone") or primary_contact.get("phone"),
                    "employees": details.get("employees"),
                    "description": details.get("description"),
                    "lead_status": details.get("lead_status"),
                    "lifecycle_stage": details.get("lifecycle_stage"),
                    "contact_title": primary_contact.get("title"),
                },
            )
            db.add(prospect)
            db.flush()

            # Add to cache so deals link to this new prospect
            customer_cache[prospect.name.lower()] = prospect
            created += 1
            logger.info(f"[HubSpotSync] Created prospect '{prospect.name}' from company {company_id}")

        except Exception as e:
            logger.warning(f"[HubSpotSync] Failed to create prospect for company {company_id}: {e}")

    if created:
        db.flush()
        logger.info(f"[HubSpotSync] Created {created} prospect customers from HubSpot companies")

    return created


def _enrich_existing_customers(
    db: Session,
    deals: list[dict],
    customer_cache: dict,
) -> int:
    """
    For companies that match an existing active customer, fill in missing
    contact/industry/metadata from HubSpot company data.
    Only updates fields that are currently NULL/empty.
    """
    enriched = 0
    seen_company_ids: set[str] = set()

    for deal in deals:
        company_id = deal.get("_company_id")
        company_name = deal.get("_company_name")
        if not company_id or not company_name or company_id in seen_company_ids:
            continue
        seen_company_ids.add(company_id)

        cust_id, _ = _resolve_customer(company_name, customer_cache)
        if not cust_id:
            continue

        customer = customer_cache.get(company_name.lower().strip())
        if not customer:
            # Find via containment match
            for _, c in customer_cache.items():
                if c.id == cust_id:
                    customer = c
                    break
        if not customer or (customer.tier or "").lower() == "prospect":
            continue

        # Check if enrichment is needed (any key field or metadata missing)
        existing_meta = customer.metadata_ or {}
        needs_update = (
            not customer.primary_contact_name
            or not customer.primary_contact_email
            or not customer.industry
            or not existing_meta.get("hubspot_company_id")
        )
        if not needs_update:
            continue

        try:
            details = hubspot_service.get_company_details(company_id)
            contacts = hubspot_service.get_company_contacts(company_id)
            primary_contact = contacts[0] if contacts else {}

            changed = False
            if not customer.primary_contact_name and primary_contact.get("name"):
                customer.primary_contact_name = primary_contact["name"]
                changed = True
            if not customer.primary_contact_email and primary_contact.get("email"):
                customer.primary_contact_email = primary_contact["email"]
                changed = True
            if not customer.industry and details.get("industry"):
                customer.industry = details["industry"]
                changed = True

            # Store HubSpot metadata for the overview
            # Must create a new dict — SQLAlchemy JSONB doesn't detect in-place mutations
            old_meta = customer.metadata_ or {}
            if not old_meta.get("hubspot_company_id"):
                new_meta = {
                    **old_meta,
                    "hubspot_company_id": company_id,
                    "domain": details.get("domain"),
                    "city": details.get("city"),
                    "state": details.get("state"),
                    "country": details.get("country"),
                    "phone": details.get("phone") or primary_contact.get("phone"),
                    "employees": details.get("employees"),
                    "contact_title": primary_contact.get("title"),
                }
                customer.metadata_ = new_meta
                changed = True

            if changed:
                enriched += 1
                logger.info(f"[HubSpotSync] Enriched customer '{customer.name}' with HubSpot data")

        except Exception as e:
            logger.debug(f"[HubSpotSync] Could not enrich customer '{customer.name}': {e}")

    if enriched:
        db.flush()
        logger.info(f"[HubSpotSync] Enriched {enriched} existing customers from HubSpot")

    return enriched


def _populate_contract_dates(db: Session) -> int:
    """
    For active customers missing contract_start, derive it from the earliest
    Closed Won deal's close_date. Pure DB operation — no HubSpot API calls.
    """
    from app.models.customer import Customer
    from app.models.deal import Deal

    customers = db.query(Customer).filter(
        (Customer.tier.is_(None)) | (Customer.tier != "prospect"),
        Customer.is_active.is_(True),
        Customer.contract_start.is_(None),
    ).all()

    if not customers:
        return 0

    updated = 0
    for customer in customers:
        # Find earliest Closed Won deal
        earliest = (
            db.query(Deal.close_date)
            .filter(
                Deal.customer_id == customer.id,
                Deal.stage.ilike("%closed won%"),
                Deal.close_date.isnot(None),
            )
            .order_by(Deal.close_date.asc())
            .first()
        )
        if earliest and earliest[0]:
            customer.contract_start = earliest[0]
            updated += 1

    if updated:
        db.flush()
        logger.info(f"[HubSpotSync] Populated contract_start for {updated} customers from Closed Won deals")

    return updated


def _populate_renewal_dates(db: Session) -> int:
    """
    For active customers, derive renewal_date from their latest Closed Won deal.

    Priority:
      1. Deal's `ced` (Contract End Date) from HubSpot properties JSONB
      2. Deal's close_date + deal_terms (months) from HubSpot properties JSONB
      3. Deal's close_date + 12 months (default annual contract assumption)

    Always uses the LATEST Closed Won deal per customer (most recent contract).
    """
    from app.models.customer import Customer
    from app.models.deal import Deal

    def _add_months(d, months: int):
        """Add months to a date, clamping day to valid range."""
        import calendar
        month = d.month - 1 + months
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, calendar.monthrange(year, month)[1])
        return d.replace(year=year, month=month, day=day)

    customers = db.query(Customer).filter(
        Customer.is_active.is_(True),
        (Customer.tier.is_(None)) | (Customer.tier != "prospect"),
    ).all()

    if not customers:
        return 0

    updated = 0
    for customer in customers:
        # Find latest Closed Won deal for this customer
        latest = (
            db.query(Deal)
            .filter(
                Deal.customer_id == customer.id,
                Deal.stage.ilike("%closed won%"),
            )
            .order_by(Deal.close_date.desc().nullslast())
            .first()
        )
        if not latest:
            continue

        props = latest.properties or {}
        renewal = None

        # Priority 1: ced (Contract End Date) — stored as epoch ms or ISO string
        ced_raw = props.get("ced")
        if ced_raw:
            try:
                if isinstance(ced_raw, str) and "T" in ced_raw:
                    renewal = datetime.fromisoformat(ced_raw.replace("Z", "+00:00")).date()
                else:
                    renewal = datetime.fromtimestamp(int(ced_raw) / 1000, tz=timezone.utc).date()
            except (ValueError, TypeError, OSError):
                pass

        # Priority 2: close_date + deal_terms (months)
        if not renewal and latest.close_date:
            term_raw = props.get("deal_terms__months_")
            if term_raw:
                try:
                    months = int(float(term_raw))
                    if 1 <= months <= 120:
                        renewal = _add_months(latest.close_date, months)
                except (ValueError, TypeError):
                    pass

        # Priority 3: close_date + 12 months (default annual)
        if not renewal and latest.close_date:
            renewal = _add_months(latest.close_date, 12)

        if renewal and renewal != customer.renewal_date:
            customer.renewal_date = renewal
            updated += 1

    if updated:
        db.flush()
        logger.info(f"[HubSpotSync] Populated renewal_date for {updated} customers from Closed Won deals")

    return updated


def _populate_cs_managers(db: Session) -> int:
    """
    For active customers, derive CS manager name from their most recent deal's
    owner_name and store in customer metadata JSONB under 'cs_manager'.
    """
    from sqlalchemy.orm.attributes import flag_modified

    from app.models.customer import Customer
    from app.models.deal import Deal

    customers = db.query(Customer).filter(
        Customer.is_active.is_(True),
        (Customer.tier.is_(None)) | (Customer.tier != "prospect"),
    ).all()

    if not customers:
        return 0

    updated = 0
    for customer in customers:
        # Find most recent deal with a resolved owner name (any stage)
        deal = (
            db.query(Deal.owner_name)
            .filter(
                Deal.customer_id == customer.id,
                Deal.owner_name.isnot(None),
            )
            .order_by(Deal.close_date.desc().nullslast())
            .first()
        )
        if not deal or not deal.owner_name:
            continue

        owner = deal.owner_name
        # Skip unresolved numeric HubSpot owner IDs
        if owner.isdigit():
            continue

        meta = dict(customer.metadata_ or {})
        if meta.get("cs_manager") != owner:
            meta["cs_manager"] = owner
            customer.metadata_ = meta
            flag_modified(customer, "metadata_")
            updated += 1

    if updated:
        db.flush()
        logger.info(f"[HubSpotSync] Populated cs_manager for {updated} customers from deal owners")

    return updated


def _cleanup_duplicate_prospects(db: Session) -> int:
    """
    Remove prospect Customer records that duplicate an existing active customer.
    A prospect is a duplicate if its hubspot_company_id matches a deal
    that is already linked to a non-prospect customer.
    """
    from app.models.customer import Customer
    from app.models.deal import Deal

    # Find prospect customers
    prospects = db.query(Customer).filter(Customer.tier == "prospect").all()
    if not prospects:
        return 0

    # Build map: hubspot_company_id -> active customer_id (from deals)
    linked = {}
    rows = (
        db.query(Deal.hubspot_company_id, Deal.customer_id)
        .filter(Deal.hubspot_company_id.isnot(None), Deal.customer_id.isnot(None))
        .distinct()
        .all()
    )
    for company_id, customer_id in rows:
        linked[company_id] = customer_id

    # Also build name-based lookup of active customers
    active_names = set()
    actives = db.query(Customer).filter(
        (Customer.tier.is_(None)) | (Customer.tier != "prospect"),
        Customer.is_active.is_(True),
    ).all()
    for c in actives:
        active_names.add(c.name.lower().strip())

    removed = 0
    for prospect in prospects:
        meta = prospect.metadata_ or {}
        company_id = meta.get("hubspot_company_id")
        is_dup = False

        # Check 1: company_id already linked to an active customer
        if company_id and company_id in linked:
            active_cust_id = linked[company_id]
            if active_cust_id != prospect.id:
                is_dup = True

        # Check 2: prospect name matches an active customer name
        if not is_dup and prospect.name.lower().strip() in active_names:
            is_dup = True

        if is_dup:
            # Relink any deals pointing to this prospect to the active customer
            if company_id and company_id in linked:
                active_id = linked[company_id]
                db.query(Deal).filter(
                    Deal.customer_id == prospect.id
                ).update({"customer_id": active_id})

            logger.info(f"[HubSpotSync] Removing duplicate prospect '{prospect.name}'")
            db.delete(prospect)
            removed += 1

    if removed:
        db.flush()
        logger.info(f"[HubSpotSync] Removed {removed} duplicate prospect records")

    return removed


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


def _activate_closed_won_customers(db: Session, closed_won_deals: list):
    """Promote prospect customers to active when their deal is Closed Won."""
    from app.models.customer import Customer

    activated = 0
    for result in closed_won_deals:
        customer_id = result.get("customer_id")
        if not customer_id:
            continue
        customer = db.query(Customer).filter(
            Customer.id == uuid.UUID(customer_id),
            Customer.tier == "prospect",
        ).first()
        if customer:
            customer.is_active = True
            customer.tier = None
            activated += 1
            logger.info(
                f"[HubSpotSync] Activated prospect '{customer.name}' "
                f"(deal: {result.get('deal_name', '?')})"
            )
    if activated:
        db.flush()  # caller owns the commit
        logger.info(f"[HubSpotSync] Activated {activated} prospect customers from Closed Won deals")


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
