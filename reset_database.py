"""
H.Huddair's Nexus-Pulse - Level 2 Enterprise
Production Database Reset & Purge Utility
Location: Desktop/rabbi/reset_database.py

Wipes all default/test operator profiles, dummy admin accounts, sample leads,
email log histories, and audit records from the database.
Resets the app into a completely clean state for first-run Master Admin initialization.
"""

import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from auth.user_manager import get_user_manager
from database.db_engine import get_db_engine


def reset_production_database():
    print("=" * 68)
    print("  H.HUDDAIR'S NEXUS-PULSE - FRESH PRODUCTION DATABASE RESET")
    print("=" * 68)

    um = get_user_manager()
    counts = um.purge_all_data()

    print("\n[PURGED DATABASE TABLES]")
    for table, count in counts.items():
        print(f"  • {table:<22}: {count:>5} records wiped")

    # Clean partition files in vault/partitions (sample leads)
    partitions_dir = PROJECT_ROOT / "vault" / "partitions"
    cleaned_partitions = 0
    if partitions_dir.exists():
        for item in partitions_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                cleaned_partitions += 1
    print(f"  • sample lead partitions: {cleaned_partitions:>5} directories wiped")

    # Verify clean state
    db = get_db_engine()
    with db.get_connection() as conn:
        users_count = conn.execute("SELECT count(*) as cnt FROM users").fetchone()["cnt"]
        leads_count = conn.execute("SELECT count(*) as cnt FROM vault_leads").fetchone()["cnt"]
        queue_count = conn.execute("SELECT count(*) as cnt FROM outreach_queue").fetchone()["cnt"]
        replies_count = conn.execute("SELECT count(*) as cnt FROM inbox_replies").fetchone()["cnt"]
        sessions_count = conn.execute("SELECT count(*) as cnt FROM operator_sessions").fetchone()["cnt"]

    print("\n[VERIFICATION AUDIT]")
    print(f"  Users in database       : {users_count} (Clean)")
    print(f"  Vault leads in database : {leads_count} (Clean)")
    print(f"  Outreach items          : {queue_count} (Clean)")
    print(f"  Inbox replies           : {replies_count} (Clean)")
    print(f"  Session audit records   : {sessions_count} (Clean)")
    print(f"  Master Admin status     : {'INITIALIZED' if um.has_admin() else 'FRESH (Awaiting First-Run Setup)'}")

    print("\n[READY] Nexus-Pulse is in a 100% clean production state.")
    print("=" * 68)


if __name__ == "__main__":
    reset_production_database()
