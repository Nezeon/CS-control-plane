"""
Demo Runner -- Triggers demo scenarios for CTO presentation.

Usage:
    cd backend
    python -m app.demo_runner                    # runs all scenarios
    python -m app.demo_runner --scenario ticket   # ticket triage only
    python -m app.demo_runner --scenario meeting  # meeting followup only

Requires:
    - At least one customer in the database
    - ANTHROPIC_API_KEY set in .env
"""

import argparse
import json
import logging
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.agents.demo_logger import install_demo_formatter, email_draft_display, result_summary
from app.config import settings
from app.demo_data import DEMO_TRANSCRIPT, DEMO_TICKET
from app.models.customer import Customer
from app.models.health_score import HealthScore

# Install rich logging before any agent imports
install_demo_formatter()

# Now import agents (triggers registration)
from app.services.event_service import route_direct  # noqa: E402

engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)

logger = logging.getLogger("demo_runner")

# DEMO_TRANSCRIPT and DEMO_TICKET imported from app.demo_data


def _pick_customer(db: Session) -> Customer:
    """Pick an at-risk customer from seed data for maximum demo impact."""
    # Try to find an at-risk customer
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
        print("\n  ERROR: No customers found in database.\n")
        sys.exit(1)
    return customer


def run_ticket_triage(db: Session) -> dict:
    """Scenario 1: Ticket triage for a critical support issue."""
    customer = _pick_customer(db)

    print(f"\n{'*' * 72}")
    print(f"  DEMO SCENARIO: Ticket Triage")
    print(f"  Customer: {customer.name} (ID: {customer.id})")
    print(f"{'*' * 72}\n")

    event = {
        "event_type": "jira_ticket_created",
        "source": "demo_runner",
        "customer_id": customer.id,
        "payload": DEMO_TICKET,
    }

    start = time.perf_counter()
    result = route_direct(db, event)
    elapsed = time.perf_counter() - start

    print(result_summary(result.get("orchestrator_result", result.get("result", {}))))
    print(f"  Total demo time: {elapsed:.1f}s\n")

    return result


def run_meeting_followup(db: Session) -> dict:
    """Scenario 2: Meeting followup with email draft generation."""
    customer = _pick_customer(db)

    print(f"\n{'*' * 72}")
    print(f"  DEMO SCENARIO: Meeting Followup + Email Draft")
    print(f"  Customer: {customer.name} (ID: {customer.id})")
    print(f"{'*' * 72}\n")

    event = {
        "event_type": "meeting_ended",
        "source": "demo_runner",
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
    elapsed = time.perf_counter() - start

    print(result_summary(result.get("orchestrator_result", result.get("result", {}))))

    # Also try to extract and display draft email from deep in the result
    orch_result = result.get("orchestrator_result", {})
    output = orch_result.get("output", {})
    if isinstance(output, dict):
        _print_draft_from_output(output)

    print(f"  Total demo time: {elapsed:.1f}s\n")

    return result


def _print_draft_from_output(output: dict, depth: int = 0):
    """Recursively search for and print draft_email."""
    if depth > 6 or not isinstance(output, dict):
        return
    if "draft_email" in output:
        print(email_draft_display(output["draft_email"]))
        return
    for key in ("output", "deliverables", "specialist_outputs"):
        nested = output.get(key, {})
        if isinstance(nested, dict):
            for v in nested.values():
                if isinstance(v, dict):
                    _print_draft_from_output(v, depth + 1)


def run_all(db: Session):
    """Run all demo scenarios."""
    print("\n" + "=" * 72)
    print("  HIVEPRO CS CONTROL PLANE -- CTO DEMO")
    print("  3 Agents: Ticket Triage + Customer Memory + Email Drafting")
    print("=" * 72)

    print("\n  Running Scenario 1: Ticket Triage...")
    run_ticket_triage(db)

    print("\n  " + "-" * 68)
    print("  Running Scenario 2: Meeting Followup + Email Draft...")
    run_meeting_followup(db)

    print("\n" + "=" * 72)
    print("  DEMO COMPLETE")
    print("=" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(description="CS Control Plane Demo Runner")
    parser.add_argument(
        "--scenario",
        choices=["ticket", "meeting", "all"],
        default="all",
        help="Which demo scenario to run (default: all)",
    )
    args = parser.parse_args()

    with Session(engine) as db:
        if args.scenario == "ticket":
            run_ticket_triage(db)
        elif args.scenario == "meeting":
            run_meeting_followup(db)
        else:
            run_all(db)


if __name__ == "__main__":
    main()
