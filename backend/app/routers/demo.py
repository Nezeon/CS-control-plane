"""
Demo trigger endpoint -- runs demo scenarios via API for frontend integration.

POST /api/demo/trigger
Body: {"scenario": "ticket" | "meeting" | "all", "customer_id": optional UUID}

Runs route_direct() in-process (not via Celery) so WebSocket broadcasts
reach the frontend in real-time.
"""

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.demo_data import DEMO_TRANSCRIPT, DEMO_TICKET
from app.models.customer import Customer
from app.models.health_score import HealthScore

from app.services.event_service import route_direct

router = APIRouter(prefix="/api/demo", tags=["demo"])

logger = logging.getLogger("demo")

_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)


class DemoTriggerRequest(BaseModel):
    scenario: str = "all"  # ticket | meeting | all
    customer_id: str | None = None


class DemoTriggerResponse(BaseModel):
    scenario: str
    success: bool
    results: dict


def _get_customer(db: Session, customer_id: str | None) -> Customer:
    """Get customer by ID or pick an at-risk one."""
    if customer_id:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if customer:
            return customer

    customer = (
        db.query(Customer)
        .join(HealthScore, Customer.id == HealthScore.customer_id)
        .filter(HealthScore.risk_level.in_(["at_risk", "critical"]))
        .order_by(HealthScore.score)
        .first()
    )
    if not customer:
        customer = db.query(Customer).first()
    if not customer:
        raise HTTPException(status_code=404, detail="No customers found in database.")
    return customer


def _run_ticket(db: Session, customer: Customer) -> dict:
    """Run ticket triage scenario."""
    event = {
        "event_type": "jira_ticket_created",
        "source": "demo_api",
        "customer_id": customer.id,
        "payload": DEMO_TICKET,
    }
    start = time.perf_counter()
    result = route_direct(db, event)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "scenario": "ticket",
        "customer": customer.name,
        "elapsed_ms": elapsed_ms,
        "result": _serialize(result),
    }


def _run_meeting(db: Session, customer: Customer) -> dict:
    """Run meeting followup scenario."""
    event = {
        "event_type": "meeting_ended",
        "source": "demo_api",
        "customer_id": customer.id,
        "payload": {
            "title": f"Q1 2026 Review Call - {customer.name}",
            "transcript": DEMO_TRANSCRIPT,
            "participants": [
                {"name": "Vignesh Kumar", "email": "vignesh@hivepro.com", "role": "CSM"},
                {"name": "Sarah Chen", "email": f"sarah@{customer.name.lower().replace(' ', '')}.com", "role": "VP Security"},
                {"name": "Mike Torres", "email": f"mike@{customer.name.lower().replace(' ', '')}.com", "role": "Security Analyst"},
            ],
            "duration_minutes": 16,
            "call_date": "2026-03-05T10:30:00Z",
        },
    }
    start = time.perf_counter()
    result = route_direct(db, event)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "scenario": "meeting",
        "customer": customer.name,
        "elapsed_ms": elapsed_ms,
        "result": _serialize(result),
    }


def _serialize(obj) -> dict:
    """Make result JSON-serializable."""
    import json

    def default(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        return str(o)

    try:
        return json.loads(json.dumps(obj, default=default))
    except Exception:
        return {"raw": str(obj)[:2000]}


@router.post("/trigger", response_model=DemoTriggerResponse)
def trigger_demo(req: DemoTriggerRequest):
    """Trigger a demo scenario. Runs in-process for WebSocket broadcasting."""
    if req.scenario not in ("ticket", "meeting", "all"):
        raise HTTPException(status_code=400, detail="scenario must be: ticket, meeting, or all")

    with Session(_engine) as db:
        customer = _get_customer(db, req.customer_id)
        results = {}

        if req.scenario in ("ticket", "all"):
            results["ticket"] = _run_ticket(db, customer)

        if req.scenario in ("meeting", "all"):
            results["meeting"] = _run_meeting(db, customer)

        success = all(
            r.get("result", {}).get("orchestrator_result", {}).get("success", False)
            or r.get("result", {}).get("result", {}).get("success", False)
            for r in results.values()
        )

        return DemoTriggerResponse(
            scenario=req.scenario,
            success=success,
            results=results,
        )


@router.get("/scenarios")
def list_scenarios():
    """List available demo scenarios."""
    return {
        "scenarios": [
            {
                "id": "ticket",
                "name": "Ticket Triage",
                "description": "Simulates a P1 Jira ticket for scanner failure. Shows full triage pipeline.",
                "agents": ["Naveen Kapoor (T1)", "Rachel Torres (T2)", "Kai Nakamura (T3)", "Atlas (T4)"],
            },
            {
                "id": "meeting",
                "name": "Meeting Followup",
                "description": "Simulates a Q1 review call ending. Generates summary + email draft.",
                "agents": ["Naveen Kapoor (T1)", "Damon Reeves (T2)", "Riley Park (T3)", "Atlas (T4)"],
            },
            {
                "id": "all",
                "name": "Full Demo",
                "description": "Runs both scenarios sequentially.",
                "agents": ["All 3 lanes engaged"],
            },
        ]
    }
