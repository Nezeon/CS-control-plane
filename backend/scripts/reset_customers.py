"""
Reset customer database with 36 active customers.

Wipes ALL customer-related data from PostgreSQL (14 tables) and stale
ChromaDB collections (5 of 6), then inserts the 36 active customers
from the manager's list.

Usage:
    cd backend
    python -m scripts.reset_customers

WARNING: This is destructive. All existing customer data will be deleted.
"""

import json
import sys
import uuid
from pathlib import Path

# Ensure backend/ is on the Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text

from app.database import get_sync_session

# ── 36 Active Customers (deal-closed, from manager's list) ──────────────

ACTIVE_CUSTOMERS = [
    {"name": "Adyen N.V.", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Al Raedah Finance", "remarks": None},
    {"name": "Australian Museum", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Badan Nasional Penanggulangan Bencana (BNPB)", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "ConnexPay", "remarks": "3 Years Deal - Billing Annually"},
    {"name": "Direct Marketing Solutions (DMS)", "remarks": "2 Years Deal - Billing Annually"},
    {"name": "Dubai International Financial Centre (DIFC)", "remarks": None},
    {"name": "Eagle Hills", "remarks": "3 Years Deal - Billing Annually"},
    {"name": "Engineering Office", "remarks": None},
    {"name": "Eskan Bank B.S.C", "remarks": None},
    {"name": "ETISALAT", "remarks": "3 Years Deal - Billing Annually"},
    {"name": "Formica Corp", "remarks": None},
    {"name": "Goosehead Insurance", "remarks": "3 Years Deal - Billing Annually"},
    {"name": "ICS Arabia", "remarks": None},
    {"name": "IT Monkey, South Africa", "remarks": None},
    {"name": "Jeraisy Electronic Services", "remarks": None},
    {"name": "King Salman Global Academy of Arabic Language (KSGAA)", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Libra Solutions", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Majan University College", "remarks": None},
    {"name": "Metro", "remarks": None},
    {"name": "Ministry of Finance (MOF)", "remarks": None},
    {"name": "Mubadala Capital", "remarks": None},
    {"name": "Nova Water", "remarks": "2 Years Deal - Billed in Advance"},
    {"name": "Oman Investment Authority (OIA)", "remarks": None},
    {"name": "Ooredoo", "remarks": None},
    {"name": "Petroleum Development Oman (PDO)", "remarks": None},
    {"name": "Rabdan Academy", "remarks": None},
    {"name": "Riyadh International Airways", "remarks": "3 Years Deal - Billing Annually"},
    {"name": "Saudi Authority for Industrial Cities and Technology Zones (MODON)", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Saudi Exim Bank", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "Tasheel Finance", "remarks": None},
    {"name": "Tencent America", "remarks": None},
    {"name": "The General Presidency for the affairs of the Grand Mosque and the Prophet's Mosque (GPH) - Phase 1", "remarks": "3 Years Deal - Billed in Advance"},
    {"name": "The General Presidency for the affairs of the Grand Mosque and the Prophet's Mosque (GPH) - Phase 2", "remarks": "2 Years Deal - Billed in Advance"},
    {"name": "Vision Bank", "remarks": None},
    {"name": "YAS Holdings", "remarks": None},
]

# FK-safe deletion order (children before parents)
TABLES_TO_DELETE = [
    "chat_messages",
    "chat_conversations",
    "agent_messages",          # self-ref FK + FK → events
    "agent_execution_rounds",
    "agent_drafts",
    "action_items",
    "agent_logs",
    "tickets",
    "call_insights",
    "reports",
    "events",
    "health_scores",
    "alerts",
    "audit_log",
    "customers",
]

# ChromaDB collections to clear (NOT meeting_knowledge)
COLLECTIONS_TO_CLEAR = [
    "ticket_embeddings",
    "call_insight_embeddings",
    "problem_embeddings",
    "episodic_memory",
    "shared_knowledge",
]


def clear_chromadb():
    """Delete and recreate stale ChromaDB collections."""
    try:
        import chromadb
        from app.config import settings

        chroma_path = settings.CHROMADB_PATH
        client = chromadb.PersistentClient(path=chroma_path)

        for name in COLLECTIONS_TO_CLEAR:
            try:
                client.delete_collection(name)
                client.get_or_create_collection(name=name)
                print(f"  ChromaDB: cleared {name}")
            except Exception as e:
                print(f"  ChromaDB: skip {name} ({e})")

        print("  ChromaDB: kept meeting_knowledge (curated, not customer-specific)")
    except Exception as e:
        print(f"  ChromaDB: could not clear ({e})")


def main():
    print("=" * 60)
    print("RESET CUSTOMERS — 36 Active Customers")
    print("=" * 60)
    print()

    # Confirm
    answer = input("This will DELETE all customer-related data. Continue? [y/N] ")
    if answer.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    db = get_sync_session()
    try:
        # Step 1: Delete all customer-related data
        print("\n[1/3] Deleting customer-related data...")
        for table in TABLES_TO_DELETE:
            result = db.execute(text(f"DELETE FROM {table}"))
            count = result.rowcount
            print(f"  {table}: {count} rows deleted")

        db.commit()
        print("  Committed.")

        # Step 2: Insert 36 active customers
        print(f"\n[2/3] Inserting {len(ACTIVE_CUSTOMERS)} active customers...")
        for cust in ACTIVE_CUSTOMERS:
            metadata = {}
            if cust["remarks"]:
                metadata["deal_remarks"] = cust["remarks"]

            db.execute(
                text(
                    "INSERT INTO customers (id, name, metadata, is_active) VALUES (:id, :name, :metadata, true)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "name": cust["name"],
                    "metadata": json.dumps(metadata),
                },
            )
            print(f"  + {cust['name']}")

        db.commit()
        print("  Committed.")

        # Step 3: Clear ChromaDB
        print("\n[3/3] Clearing stale ChromaDB collections...")
        clear_chromadb()

        # Summary
        count = db.execute(text("SELECT count(*) FROM customers")).scalar()
        print(f"\nDone! {count} customers in database.")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        print("Rolled back all changes.")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
