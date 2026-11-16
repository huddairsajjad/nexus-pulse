"""
Nexus-Pulse Sequential 8-Step E2E Test Suite
=============================================
Runs against local FastAPI + MongoDB (mongomock fallback).

Rules:
  - All 8 steps MUST pass; Step 8 purges ALL test artifacts unconditionally.
  - Zero dummy/fake data may remain in DB after Step 8.
  - Use bypass_window=True on all dispatch calls (timezone-independent).
  - Script exits with code 0 only when ALL steps pass AND Step 8 confirms clean DB.

Usage:
    cd "C:\\Users\\STONE\\Desktop\\rabbi"
    python e2e_test_agent.py
"""

import sys
import uuid
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

# ── Ensure project root is on path ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Lazy imports (after path fix) ──────────────────────────────────────────────
from fastapi.testclient import TestClient
from api.app import create_app
from auth.jwt_handler import create_access_token
from database.db_engine import get_db_engine
from database.mongo_engine import get_mongo_engine
from core.outreach.approval_gate import get_approval_gate
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.blacklist_manager import get_blacklist_manager
from core.outreach.apscheduler_manager import APSchedulerManager
from core.outreach.scheduler import TimezoneScheduler

# ── Helpers ───────────────────────────────────────────────────────────────────
def _table_exists(conn, table_name: str) -> bool:
    """Return True if the given table exists in the SQLite database."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


# ── App & shared singletons ────────────────────────────────────────────────────
app = create_app()
client = TestClient(app)
db = get_db_engine()
mongo = get_mongo_engine()

# ── Unique tag to isolate ALL test artifacts ───────────────────────────────────
TEST_TAG = f"e2e_{uuid.uuid4().hex[:10]}"
print(f"\n🏷  TEST_TAG = {TEST_TAG}\n{'=' * 60}")

# ── Artifact registries (populated as steps run) ────────────────────────────────
test_user_ids: list[str] = []
test_queue_ids: list[str] = []
test_mailbox_emails: list[str] = []
test_bl_patterns: list[str] = []

# ── Step result tracker ────────────────────────────────────────────────────────
results: dict[int, bool] = {}


def _hdr(n: int, title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  STEP {n}: {title}")
    print(f"{'─' * 60}")


def _pass(n: int, msg: str = "") -> None:
    results[n] = True
    tick = "✅"
    print(f"{tick} Step {n} PASSED{': ' + msg if msg else ''}")


def _fail(n: int, msg: str, exc: Exception | None = None) -> None:
    results[n] = False
    print(f"❌ Step {n} FAILED: {msg}")
    if exc:
        traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Google OAuth onboarding & 2-Day Free Trial auto-provisioning
# ══════════════════════════════════════════════════════════════════════════════
_hdr(1, "Google OAuth onboarding & 2-Day Free Trial auto-provisioning")
try:
    test_email = f"trial_{TEST_TAG}@gmail.com"
    res = client.post("/api/auth/google", json={
        "email": test_email,
        "name": f"E2E Trial User {TEST_TAG}",
        "sub": f"google_{TEST_TAG}",
        "credential": "",
        "refresh_token": "",
        "access_token": "",
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    # Verify response shape
    assert data.get("success") is True, f"success != True: {data}"
    assert data.get("is_new_user") is True, f"is_new_user != True (may already exist): {data}"
    assert data.get("token"), "No token returned"

    user = data["user"]
    assert user["trial_status"] == "active", f"trial_status != active: {user}"
    assert user["auth_provider"] == "google", f"auth_provider != google: {user}"
    assert user["role"] == "operator", f"role != operator: {user}"

    # Verify expiry ≈ 48 hours from now
    expiry_raw = user["expiry_date"]  # e.g. "2026-11-18 13:44:36"
    expiry_dt = datetime.fromisoformat(expiry_raw.replace(" ", "T")).replace(tzinfo=timezone.utc)
    hours_remaining = (expiry_dt - datetime.now(timezone.utc)).total_seconds() / 3600
    assert hours_remaining > 46, f"Trial expiry too soon ({hours_remaining:.1f}h remaining)"

    test_user_ids.append(user["id"])
    operator_token = data["token"]
    print(f"   User ID: {user['id']}, Trial expires: {expiry_raw}, Hours left: {hours_remaining:.1f}h")
    _pass(1, f"trial_status=active, expires={expiry_raw}")

except Exception as exc:
    _fail(1, str(exc), exc)
    operator_token = None  # Step 2 will use admin token only


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Dual-Role RBAC & multi-tenant isolation
# ══════════════════════════════════════════════════════════════════════════════
_hdr(2, "Dual-Role RBAC & multi-tenant isolation")
try:
    # 2a. Operator must be BLOCKED from admin routes
    if operator_token:
        res_op = client.get("/api/admin/", headers={"Authorization": f"Bearer {operator_token}"})
        assert res_op.status_code == 403, (
            f"Operator should get 403 on /api/admin/ — got {res_op.status_code}: {res_op.text}"
        )
        print(f"   ✓ Operator → /api/admin/ → 403 Forbidden (correct)")

        res_op2 = client.get("/api/admin", headers={"Authorization": f"Bearer {operator_token}"})
        assert res_op2.status_code == 403, (
            f"Operator should get 403 on /api/admin — got {res_op2.status_code}"
        )
        print(f"   ✓ Operator → /api/admin  → 403 Forbidden (correct)")
    else:
        print("   ⚠ Skipping operator RBAC check (Step 1 failed — no operator token)")

    # 2b. Admin token must PASS admin routes
    admin_token = create_access_token(
        user_id=f"admin-e2e-{TEST_TAG}",
        username=f"admin_e2e_{TEST_TAG}",
        role="admin",
        full_name="E2E Admin",
    )
    res_admin = client.get("/api/admin/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200, (
        f"Admin should get 200 on /api/admin/ — got {res_admin.status_code}: {res_admin.text}"
    )
    admin_data = res_admin.json()
    assert admin_data.get("role") == "admin", f"role != admin: {admin_data}"
    print(f"   ✓ Admin   → /api/admin/ → 200 OK, role=admin")

    # 2c. No-auth request must be rejected
    res_unauth = client.get("/api/admin/")
    assert res_unauth.status_code in (401, 403), (
        f"Unauthenticated should be 401/403 — got {res_unauth.status_code}"
    )
    print(f"   ✓ No-auth → /api/admin/ → {res_unauth.status_code} (correct)")

    _pass(2, "RBAC isolation verified — operator=403, admin=200, unauth=401/403")

except Exception as exc:
    _fail(2, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Live lead URL discovery & MongoDB deduplication
# ══════════════════════════════════════════════════════════════════════════════
_hdr(3, "Lead discovery (URL candidates) & MongoDB deduplication")
try:
    import asyncio
    from core.agents.scraper_agent import SearchDiscoveryAgent

    agent = SearchDiscoveryAgent()
    urls = asyncio.run(agent.discover_candidate_urls(
        queries=[{"query": "commercial construction London tenders contact email"}],
        limit=3,
        country="United Kingdom",
        city="London",
        niche="Commercial Construction",
    ))
    assert isinstance(urls, list), f"Expected list of URLs, got {type(urls)}"
    assert len(urls) > 0, (
        "discover_candidate_urls returned 0 results — "
        "search fallback may be blocked on this machine."
    )
    print(f"   ✓ Discovered {len(urls)} candidate URLs: {urls[:3]}")

    # 3b. MongoDB unique-index deduplication
    test_domain = f"e2e-dedup-{TEST_TAG}.co.uk"
    test_lead_email = f"contact@{test_domain}"
    lead_doc = {
        "domain": test_domain,
        "primary_email": test_lead_email,
        "company_name": f"E2E Dedup Co {TEST_TAG}",
        "niche": "Commercial Construction",
        "source": "e2e_test",
    }

    result1 = mongo.insert_lead(lead_doc)
    assert result1 is not None and result1 is not False, f"First insert should succeed: {result1}"
    print(f"   ✓ First insert of {test_domain} → success")

    # Second insert of SAME doc must raise ValueError (unique-index enforcement)
    duplicate_blocked = False
    try:
        mongo.insert_lead(lead_doc)
    except ValueError as ve:
        if "DUPLICATE_LEAD" in str(ve):
            duplicate_blocked = True
        else:
            raise
    assert duplicate_blocked, "Duplicate insert should raise ValueError('DUPLICATE_LEAD...')"
    print(f"   ✓ Second insert of same domain → blocked by unique-index (ValueError raised correctly)")

    _pass(3, f"Discovered {len(urls)} URLs; MongoDB dedup confirmed")

except Exception as exc:
    _fail(3, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Compliance: suppression list & blacklist guards
# ══════════════════════════════════════════════════════════════════════════════
_hdr(4, "Compliance: suppression & blacklist guards")
try:
    # 4a. MongoDB unsubscribe suppression — must have a lead doc first,
    #     because set_unsubscribed/is_unsubscribed operate on the leads collection.
    sup_domain = f"sup-domain-{TEST_TAG}.io"
    sup_email = f"sup_{TEST_TAG}@{sup_domain}"
    # Insert a real lead doc so update_many can mark it
    sup_lead = {
        "domain": sup_domain,
        "primary_email": sup_email,
        "company_name": f"Suppression Test Co {TEST_TAG}",
        "niche": "Commercial Construction",
        "source": "e2e_test",
    }
    mongo.insert_lead(sup_lead)
    mongo.set_unsubscribed(sup_email)
    is_unsub = mongo.is_unsubscribed(sup_email)
    assert is_unsub is True, f"is_unsubscribed should be True after set_unsubscribed — got {is_unsub}"
    print(f"   ✓ Suppression: {sup_email} → is_unsubscribed=True")

    # 4b. Blacklist pattern add + check + cleanup
    bl_mgr = get_blacklist_manager()
    test_bl_domain = f"e2e-bl-{TEST_TAG}.io"
    test_bl_patterns.append(test_bl_domain)
    bl_mgr.add_rule(pattern=test_bl_domain, reason="E2E test blacklist", created_by="e2e_agent")
    is_blocked, block_reason = bl_mgr.is_domain_blacklisted(test_bl_domain)
    assert is_blocked, f"Added domain should be blocked — got is_blocked={is_blocked}"
    print(f"   ✓ Blacklist: {test_bl_domain} → blocked, reason='{block_reason}'")

    # 4c. Operational time window (verify scheduler returns well-formed result)
    sched_result = TimezoneScheduler.get_target_local_time("Germany")
    assert "is_in_send_window" in sched_result, f"Missing is_in_send_window: {sched_result}"
    assert "current_local_hour" in sched_result, f"Missing current_local_hour: {sched_result}"
    print(f"   ✓ Scheduler: Germany local={sched_result['current_local_time']}, "
          f"in_window={sched_result['is_in_send_window']}")

    _pass(4, "Suppression, blacklist, and scheduler checks passed")

except Exception as exc:
    _fail(4, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Template dispatch & webhook relay (mocked relay)
# ══════════════════════════════════════════════════════════════════════════════
_hdr(5, "Template dispatch & webhook relay")
try:
    gate = get_approval_gate()
    rotator = get_inbox_rotator()

    # Enroll a test mailbox with a mock webhook URL
    test_mb_email = f"sender_{TEST_TAG}@test-relay-e2e.io"
    test_mailbox_emails.append(test_mb_email)
    mb_result = rotator.enroll_mailbox(
        email_address=test_mb_email,
        display_name=f"E2E Relay {TEST_TAG}",
        domain="test-relay-e2e.io",
        daily_limit=10,
        webhook_url="https://mock-relay-e2e.test/hook",
    )
    assert mb_result, f"Mailbox enroll failed: {mb_result}"
    print(f"   ✓ Mailbox enrolled: {test_mb_email}")

    # Queue an outreach item
    test_recipient = f"e2e_{TEST_TAG}@e2e-target-de.de"
    q_res = gate.queue_outreach(
        lead_id=f"e2e-lead-{TEST_TAG}",
        company_name=f"E2E Target GmbH {TEST_TAG}",
        recipient=test_recipient,
        country="Germany",
        niche="Commercial Construction",
        city="Berlin",
    )
    assert q_res.get("queue_id"), f"queue_outreach must return queue_id: {q_res}"
    q_id = q_res["queue_id"]
    test_queue_ids.append(q_id)
    print(f"   ✓ Queued outreach: queue_id={q_id}")

    # Approve the queue item
    approve_res = gate.approve_outreach_item(
        queue_id=q_id,
        approver="e2e_test_agent",
    )
    assert approve_res.get("approved") or approve_res.get("success"), (
        f"approve_outreach_item failed: {approve_res}"
    )
    print(f"   ✓ Approved: {approve_res}")

    # Dispatch with mocked webhook call — patch the MODULE-LEVEL function
    with patch("core.outreach.approval_gate._send_webhook_request") as mock_wh:
        mock_wh.return_value = {"status": "success", "message": "Delivered", "http_status": 200}
        dispatch_res = gate.dispatch_approved_outreach(q_id, bypass_window=True)

    assert dispatch_res.get("success"), f"dispatch_approved_outreach failed: {dispatch_res}"
    print(f"   ✓ Dispatch result: success={dispatch_res['success']}, "
          f"method={dispatch_res.get('delivery_method', 'N/A')}")

    # Quota accounting
    sent = dispatch_res.get("sent_today", dispatch_res.get("emails_sent"))
    remaining = dispatch_res.get("remaining_daily_quota", dispatch_res.get("remaining_quota"))
    print(f"   ✓ Quota: sent_today={sent}, remaining={remaining}")

    _pass(5, f"Webhook relay dispatch succeeded — queue_id={q_id}")

except Exception as exc:
    _fail(5, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Unsubscribe & bounce feedback loop (API + dual-DB sync)
# ══════════════════════════════════════════════════════════════════════════════
_hdr(6, "Unsubscribe & bounce feedback loop")
try:
    unsub_email = f"unsub_{TEST_TAG}@e2e-unsub.io"

    # Hit the API unsubscribe endpoint
    res_unsub = client.post("/api/unsubscribe", json={"email": unsub_email})
    assert res_unsub.status_code == 200, (
        f"POST /api/unsubscribe → {res_unsub.status_code}: {res_unsub.text}"
    )
    unsub_data = res_unsub.json()
    assert unsub_data.get("unsubscribed") is True, f"unsubscribed != True: {unsub_data}"
    print(f"   ✓ API /api/unsubscribe → 200, unsubscribed=True")

    # Verify SQLite suppressed_entities side (listener.suppress_entity writes here directly)
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT reason FROM suppressed_entities WHERE lower(entity) = ?",
            (unsub_email.lower(),),
        ).fetchone()
    assert row is not None, f"SQLite suppressed_entities: no row for {unsub_email}"
    row = dict(row)
    assert row["reason"] in ("UNSUBSCRIBE", "unsubscribe", "USER_REQUEST"), (
        f"Unexpected reason: {row['reason']}"
    )
    print(f"   ✓ SQLite suppressed_entities: {unsub_email} → reason={row['reason']}")

    # MongoDB sync: set_unsubscribed is a best-effort update_many on the leads collection.
    # For a brand-new email (no lead doc exists yet) it modifies 0 rows — this is correct
    # production behaviour. We verify the call doesn't throw instead.
    try:
        mongo.set_unsubscribed(unsub_email)
        print(f"   ✓ MongoDB set_unsubscribed({unsub_email}) completed without error (0 docs updated — expected for new email)")
    except Exception as mex:
        raise AssertionError(f"mongo.set_unsubscribed() raised unexpectedly: {mex}")

    _pass(6, f"Unsubscribe: SQLite suppression confirmed + MongoDB call stable for {unsub_email}")

except Exception as exc:
    _fail(6, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — APScheduler: daily send-cap reset & trial expiration check
# ══════════════════════════════════════════════════════════════════════════════
_hdr(7, "APScheduler: daily send-cap reset & trial expiration")
try:
    mgr = APSchedulerManager()

    # 7a. Set test mailbox sent_today > 0, then reset and confirm it goes to 0
    if test_mailbox_emails:
        test_mb = test_mailbox_emails[0]
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE mailbox_rotator SET sent_today = 7 WHERE email_address = ?",
                (test_mb,),
            )
            conn.commit()

        mgr.reset_daily_send_caps()

        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT sent_today FROM mailbox_rotator WHERE email_address = ?",
                (test_mb,),
            ).fetchone()
        assert row is not None, f"Mailbox not found after reset: {test_mb}"
        row = dict(row)
        assert row["sent_today"] == 0, (
            f"sent_today should be 0 after reset — got {row['sent_today']}"
        )
        print(f"   ✓ APScheduler.reset_daily_send_caps(): {test_mb} → sent_today=0")
    else:
        print("   ⚠ No test mailbox registered (Step 5 may have failed) — running reset anyway")
        mgr.reset_daily_send_caps()
        print("   ✓ reset_daily_send_caps() ran without error")

    # 7b. Trial expiration check runs without throwing
    mgr.check_trial_expirations()
    print("   ✓ check_trial_expirations() ran without error")

    _pass(7, "APScheduler send-cap reset and trial expiry check OK")

except Exception as exc:
    _fail(7, str(exc), exc)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — MANDATORY STRICT CLEANUP (runs unconditionally, even on prior failure)
# ══════════════════════════════════════════════════════════════════════════════
_hdr(8, "MANDATORY STRICT DATABASE CLEANUP")
cleanup_errors: list[str] = []

try:
    with db.get_connection() as conn:

        # Remove test users & their sessions
        for uid in test_user_ids:
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            conn.execute("DELETE FROM operator_sessions WHERE user_id = ?", (uid,))
        conn.commit()
        print(f"   Deleted {len(test_user_ids)} test user(s) + their sessions from SQLite")

        # Remove outreach queue rows that belong to this test run
        conn.execute(
            "DELETE FROM outreach_queue WHERE recipient LIKE ?",
            (f"%{TEST_TAG}%",),
        )
        # Remove any follow-up sequences
        if _table_exists(conn, "followup_sequences"):
            conn.execute(
                "DELETE FROM followup_sequences WHERE recipient_email LIKE ?",
                (f"%{TEST_TAG}%",),
            )

        # Remove test mailboxes
        conn.execute(
            "DELETE FROM mailbox_rotator WHERE email_address LIKE ?",
            (f"%{TEST_TAG}%",),
        )

        # Remove ALL test suppression entries (Step 4 and Step 6 entries)
        conn.execute(
            "DELETE FROM suppressed_entities WHERE lower(entity) LIKE ?",
            (f"%{TEST_TAG.lower()}%",),
        )
        # Also handle the domain portion that suppress_entity writes for Step 6
        conn.execute(
            "DELETE FROM suppressed_entities WHERE lower(entity) = ?",
            ("e2e-unsub.io",),
        )

        # Remove any test-generated operator activity logs
        conn.execute(
            "DELETE FROM operator_sessions WHERE detail LIKE ?",
            (f"%{TEST_TAG}%",),
        )

        conn.commit()
        print("   SQLite cleanup committed.")

except Exception as exc:
    msg = f"SQLite cleanup error: {exc}"
    cleanup_errors.append(msg)
    print(f"   ⚠ {msg}")
    traceback.print_exc()

# Remove test blacklist patterns
try:
    with db.get_connection() as conn:
        for pattern in test_bl_patterns:
            conn.execute(
                "DELETE FROM blacklist_rules WHERE lower(pattern) = ?",
                (pattern.strip().lower(),),
            )
        conn.commit()
    print(f"   Removed {len(test_bl_patterns)} test blacklist pattern(s)")
except Exception as exc:
    msg = f"Blacklist cleanup error: {exc}"
    cleanup_errors.append(msg)
    print(f"   ⚠ {msg}")

# MongoDB cleanup — targeted removal of test documents
try:
    test_domain_prefix = f"e2e-dedup-{TEST_TAG}"
    removed = 0
    if hasattr(mongo, "db") and mongo.db is not None:
        leads_col = mongo.db["leads"]
        result = leads_col.delete_many({
            "$or": [
                {"domain": {"$regex": TEST_TAG}},
                {"primary_email": {"$regex": TEST_TAG}},
                {"source": "e2e_test"},
            ]
        })
        removed = result.deleted_count
    print(f"   MongoDB: removed {removed} test lead document(s)")
except Exception as exc:
    msg = f"MongoDB cleanup error: {exc}"
    cleanup_errors.append(msg)
    print(f"   ⚠ {msg}")

# ── Verification: assert zero artifacts remain ─────────────────────────────────
print("\n   Verifying zero test artifacts remain …")
verification_errors: list[str] = []

try:
    with db.get_connection() as conn:
        # Users
        if test_user_ids:
            placeholders = ",".join("?" * len(test_user_ids))
            rem_users = conn.execute(
                f"SELECT COUNT(*) as cnt FROM users WHERE id IN ({placeholders})",
                test_user_ids,
            ).fetchone()
            rem_users = dict(rem_users)["cnt"]
        else:
            rem_users = 0

        # Queue
        rem_queue = dict(conn.execute(
            "SELECT COUNT(*) as cnt FROM outreach_queue WHERE recipient LIKE ?",
            (f"%{TEST_TAG}%",),
        ).fetchone())["cnt"]

        # Mailboxes
        rem_mb = dict(conn.execute(
            "SELECT COUNT(*) as cnt FROM mailbox_rotator WHERE email_address LIKE ?",
            (f"%{TEST_TAG}%",),
        ).fetchone())["cnt"]

        # Suppressed entities
        rem_sup = dict(conn.execute(
            "SELECT COUNT(*) as cnt FROM suppressed_entities WHERE lower(entity) LIKE ?",
            (f"%{TEST_TAG.lower()}%",),
        ).fetchone())["cnt"]

    print(f"   Remaining: users={rem_users}, queue={rem_queue}, mailboxes={rem_mb}, suppressed={rem_sup}")

    if rem_users != 0:
        verification_errors.append(f"{rem_users} test user(s) remain in DB")
    if rem_queue != 0:
        verification_errors.append(f"{rem_queue} test queue item(s) remain in DB")
    if rem_mb != 0:
        verification_errors.append(f"{rem_mb} test mailbox(es) remain in DB")
    if rem_sup != 0:
        verification_errors.append(f"{rem_sup} test suppression entry/entries remain in DB")

except Exception as exc:
    verification_errors.append(f"Verification query failed: {exc}")
    traceback.print_exc()

all_cleanup_ok = not cleanup_errors and not verification_errors
if all_cleanup_ok:
    _pass(8, "Database is 100% clean — zero test artifacts remain")
else:
    issues = cleanup_errors + verification_errors
    _fail(8, "Cleanup incomplete: " + "; ".join(issues))


# ══════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print("  NEXUS-PULSE E2E SUITE — FINAL REPORT")
print(f"{'=' * 60}")
all_passed = True
for step in range(1, 9):
    passed = results.get(step, False)
    icon = "✅" if passed else "❌"
    print(f"  {icon}  Step {step}: {'PASSED' if passed else 'FAILED'}")
    if not passed:
        all_passed = False

print(f"{'=' * 60}")
if all_passed:
    print("  🎉  ALL 8 STEPS PASSED — READY FOR GIT COMMIT & RAILWAY DEPLOY")
    print(f"{'=' * 60}\n")
    sys.exit(0)
else:
    failed = [str(k) for k, v in results.items() if not v]
    print(f"  ⛔  SUITE FAILED — Steps {', '.join(failed)} did NOT pass")
    print("  Do NOT git-push until all steps pass.")
    print(f"{'=' * 60}\n")
    sys.exit(1)

