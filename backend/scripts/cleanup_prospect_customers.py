"""
Cleanup junk prospect customers created by Fathom auto-create.

Removes customers with tier='prospect' and re-runs customer matching
on their orphaned call insights using summary-based matching.

Usage:
    cd backend
    python -m scripts.cleanup_prospect_customers
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text

from app.database import get_sync_session


def main():
    db = get_sync_session()
    try:
        # Step 1: Find all prospect customers
        prospects = db.execute(text("""
            SELECT id, name FROM customers WHERE tier = 'prospect'
        """)).fetchall()
        print(f"Found {len(prospects)} prospect customers to evaluate")

        if not prospects:
            print("Nothing to clean up.")
            return

        # Step 2: For each prospect, check if they have any linked data besides call_insights
        # (tickets, deals, health_scores = real data that shouldn't be orphaned)
        removed = 0
        reassigned = 0
        kept = 0

        # Load real customers for re-matching
        real_customers = db.execute(text("""
            SELECT id, name FROM customers WHERE tier != 'prospect' OR tier IS NULL
        """)).fetchall()
        real_map = {c[1].lower(): c[0] for c in real_customers}

        for prospect_id, prospect_name in prospects:
            pid = str(prospect_id)

            # Check for meaningful linked data (tickets with real Jira IDs)
            ticket_count = db.execute(text(
                "SELECT COUNT(*) FROM tickets WHERE customer_id = CAST(:id AS uuid) AND jira_id IS NOT NULL"
            ), {"id": pid}).scalar() or 0

            if ticket_count > 0:
                print(f"  KEEP: {prospect_name} (has {ticket_count} real Jira tickets)")
                kept += 1
                continue

            # Get call insights linked to this prospect
            insights = db.execute(text("""
                SELECT id, summary FROM call_insights
                WHERE customer_id = CAST(:id AS uuid)
            """), {"id": pid}).fetchall()

            # Try to re-match each insight to a real customer via summary
            for insight_id, summary in insights:
                matched_id = None
                if summary:
                    summary_lower = summary.lower()
                    for cname_lower, cid in real_map.items():
                        if len(cname_lower) >= 5 and cname_lower in summary_lower:
                            matched_id = cid
                            break

                # Update the call insight's customer_id
                if matched_id:
                    db.execute(text(
                        "UPDATE call_insights SET customer_id = CAST(:new_id AS uuid) WHERE id = CAST(:iid AS uuid)"
                    ), {"new_id": str(matched_id), "iid": str(insight_id)})
                    reassigned += 1
                else:
                    # Set to NULL — better than linking to a junk customer
                    db.execute(text(
                        "UPDATE call_insights SET customer_id = NULL WHERE id = CAST(:iid AS uuid)"
                    ), {"iid": str(insight_id)})

            # Unlink deals (set customer_id to NULL, don't delete deals)
            db.execute(text(
                "UPDATE deals SET customer_id = NULL WHERE customer_id = CAST(:id AS uuid)"
            ), {"id": pid})

            # Delete related records (FK constraints)
            # chat_messages must go before chat_conversations (FK)
            db.execute(text("""
                DELETE FROM chat_messages WHERE conversation_id IN (
                    SELECT id FROM chat_conversations WHERE customer_id = CAST(:id AS uuid)
                )
            """), {"id": pid})
            db.execute(text(
                "DELETE FROM chat_conversations WHERE customer_id = CAST(:id AS uuid)"
            ), {"id": pid})
            for table in ["health_scores", "tickets", "agent_logs", "events",
                          "alerts", "action_items", "reports"]:
                db.execute(text(
                    f"DELETE FROM {table} WHERE customer_id = CAST(:id AS uuid)"
                ), {"id": pid})

            # Delete the prospect customer
            db.execute(text(
                "DELETE FROM customers WHERE id = CAST(:id AS uuid)"
            ), {"id": pid})
            removed += 1
            print(f"  REMOVED: {prospect_name} ({len(insights)} insights re-matched)")

        db.commit()

        # Summary
        remaining = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        print(f"\nDone!")
        print(f"  Removed: {removed} junk prospects")
        print(f"  Kept: {kept} prospects with real data")
        print(f"  Reassigned: {reassigned} call insights to real customers")
        print(f"  Customers remaining: {remaining}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
