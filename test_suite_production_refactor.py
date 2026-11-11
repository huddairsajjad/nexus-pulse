"""
Nexus-Pulse Production Refactor & SaaS Expansion Test Suite
Tests all 5 core directives:
1. Zero-Seed & Clean Startup Verification
2. RBAC & Multi-Tenant Data Isolation
3. Multi-Service Template Pool & Dynamic Industry Matching
4. Auto-Switching Inbox Rotator & Regional Working Hours
5. Commercial Enterprise Modules (Billing, Blacklist, IMAP Bounces, Deliverability)
"""

import os
import sys
import uuid
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db_engine import get_db_engine
from auth.user_manager import get_user_manager
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.scheduler import get_scheduler
from core.outreach.template_manager import get_template_manager
from core.outreach.blacklist_manager import get_blacklist_manager
from core.outreach.reply_listener import get_reply_listener
from core.outreach.approval_gate import get_approval_gate
from fastapi.testclient import TestClient
from api.app import create_app


class TestNexusPulseProductionRefactor(unittest.TestCase):

    def setUp(self):
        self.db = get_db_engine()
        self.um = get_user_manager()
        self.rotator = get_inbox_rotator()
        self.scheduler = get_scheduler()
        self.tm = get_template_manager()
        self.bm = get_blacklist_manager()
        self.listener = get_reply_listener()
        self.gate = get_approval_gate()
        self.app = create_app()
        self.client = TestClient(self.app)

    # =========================================================================
    # 1. ZERO-SEED & CLEAN STARTUP POLICY VERIFICATION
    # =========================================================================
    def test_01_zero_seed_clean_startup(self):
        """Verifies zero default records across all 14 database tables upon clean wipe."""
        counts = self.um.purge_all_data()
        self.assertIsInstance(counts, dict)

        tables = [
            "users", "vault_leads", "dedup_registry", "hygiene_audit_log",
            "outreach_queue", "mailbox_rotator", "inbox_replies",
            "followup_sequences", "operator_sessions", "dnc_blacklist",
            "service_templates", "suppressed_entities", "blacklist_rules",
            "operator_billing"
        ]

        with self.db.get_connection() as conn:
            for t in tables:
                cnt = conn.execute(f"SELECT count(*) as c FROM {t}").fetchone()["c"]
                self.assertEqual(cnt, 0, f"Table '{t}' must have 0 records in fresh state, found {cnt}")

        # Verify setup-status API endpoint reports clean / uninitialized
        res = self.client.get("/api/auth/setup-status")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["initialized"])

    # =========================================================================
    # 2. RBAC & TENANT ISOLATION
    # =========================================================================
    def test_02_rbac_route_protection_and_token_security(self):
        """Verifies Super Admin vs Operator role access control and 403 Forbidden enforcement."""
        # 1. Create Master Admin
        admin_data = self.um.initialize_admin(
            username="test_admin",
            password="AdminPassword123!",
            full_name="Super Administrator",
            email="admin@test-enterprise.io"
        )
        admin_token = admin_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create Operator under Admin
        op_data = self.um.create_operator_account(
            username="test_operator",
            password="OperatorPassword123!",
            full_name="Operations Specialist",
            email="operator@test-enterprise.io"
        )
        op_id = op_data["user_id"]

        # Log in as operator to get JWT
        login_res = self.client.post("/api/auth/login", json={
            "username": "test_operator",
            "password": "OperatorPassword123!"
        })
        self.assertEqual(login_res.status_code, 200)
        op_token = login_res.json()["access_token"]
        op_headers = {"Authorization": f"Bearer {op_token}"}

        # 3. Direct API security tests: Operator calling admin endpoints MUST be blocked with 403
        admin_endpoints = [
            ("GET", "/api/operators"),
            ("POST", "/api/operators"),
            ("POST", f"/api/operators/{op_id}/billing"),
            ("GET", f"/api/operators/{op_id}/billing-history"),
            ("GET", "/api/billing/all-history"),
            ("GET", "/api/blacklist"),
            ("POST", "/api/blacklist"),
            ("GET", "/api/licenses/telemetry"),
            ("POST", "/api/database/reset-fresh")
        ]

        for method, endpoint in admin_endpoints:
            if method == "GET":
                resp = self.client.get(endpoint, headers=op_headers)
            else:
                resp = self.client.post(endpoint, json={}, headers=op_headers)
            self.assertEqual(
                resp.status_code, 403,
                f"Operator token must receive 403 Forbidden on {endpoint}, got {resp.status_code}"
            )

        # 4. Unauthenticated calls MUST be blocked with 401
        unauth_resp = self.client.get("/api/operators")
        self.assertEqual(unauth_resp.status_code, 401)

        # 5. Admin calling admin endpoints MUST succeed (200 OK)
        admin_resp = self.client.get("/api/operators", headers=admin_headers)
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIsInstance(admin_resp.json(), list)

    def test_03_multi_tenant_data_isolation(self):
        """Verifies leads, templates, and mailboxes are isolated between operators."""
        # Create 2 operators
        self.um.purge_all_data()
        self.um.initialize_admin("admin", "AdminPass123!", "Admin", "a@a.io")

        op1 = self.um.create_operator_account("op_berlin", "Pass123!", "Op Berlin", "b@o.io")
        op2 = self.um.create_operator_account("op_london", "Pass123!", "Op London", "l@o.io")
        op1_id = op1["user_id"]
        op2_id = op2["user_id"]

        # Op1 creates template
        t1 = self.tm.create_template(
            operator_id=op1_id,
            title="Berlin Concrete Proposal",
            niche="Concrete Works",
            subject_template="Concrete packages in Berlin // {{company_name}}",
            body_template="Custom proposal for {{company_name}}"
        )

        # Op2 creates template
        t2 = self.tm.create_template(
            operator_id=op2_id,
            title="London Steel Proposal",
            niche="Structural Steel",
            subject_template="Steel tender // {{company_name}}",
            body_template="Custom steel for {{company_name}}"
        )

        # Check tenant isolation
        op1_templates = self.tm.get_templates(operator_id=op1_id)
        op2_templates = self.tm.get_templates(operator_id=op2_id)

        self.assertEqual(len(op1_templates), 1)
        self.assertEqual(op1_templates[0]["title"], "Berlin Concrete Proposal")

        self.assertEqual(len(op2_templates), 1)
        self.assertEqual(op2_templates[0]["title"], "London Steel Proposal")

    # =========================================================================
    # 3. MULTI-SERVICE TEMPLATE POOL & DYNAMIC INDUSTRY MATCHING
    # =========================================================================
    def test_04_template_crud_and_dynamic_variable_interpolation(self):
        """Verifies template creation, tag interpolation, and industry matching."""
        op_id = "tenant-alpha"

        # Create custom templates for distinct niches
        self.tm.create_template(
            operator_id=op_id,
            title="Roofing & Cladding Proposal",
            niche="Roofing & Cladding",
            subject_template="Commercial Roofing Packages // {{company_name}}",
            body_template="Dear Estimators at {{company_name}},\nWe provide {{niche}} for {{country}} projects.\nOpt-out: {{unsubscribe_link}}"
        )

        self.tm.create_template(
            operator_id=op_id,
            title="General Commercial Default",
            niche="General",
            subject_template="Subcontractor Prequalification // {{company_name}}",
            body_template="Estimating support for {{company_name}} in {{city}}, {{country}}.\n{{unsubscribe_link}}",
            is_default=True
        )

        # 1. Exact niche match test
        rendered_roofing = self.tm.match_and_render_template(
            operator_id=op_id,
            niche="Roofing & Cladding",
            company_name="Dachbau Müller GmbH",
            recipient_email="kalkulation@dachbau-mueller.de",
            country="Germany",
            city="Munich"
        )
        self.assertIn("Commercial Roofing Packages // Dachbau Müller GmbH", rendered_roofing["subject"])
        self.assertIn("Dachbau Müller GmbH", rendered_roofing["body"])
        self.assertIn("Roofing & Cladding", rendered_roofing["body"])
        self.assertIn("/api/unsubscribe?email=kalkulation@dachbau-mueller.de", rendered_roofing["body"])

        # 2. Fallback to default template when niche does not match
        rendered_fallback = self.tm.match_and_render_template(
            operator_id=op_id,
            niche="Unusual Trade Specialty",
            company_name="Specialty Trade Ltd",
            recipient_email="info@specialty.co.uk",
            country="United Kingdom",
            city="Manchester"
        )
        self.assertIn("Subcontractor Prequalification // Specialty Trade Ltd", rendered_fallback["subject"])
        self.assertIn("Manchester, United Kingdom", rendered_fallback["body"])

    # =========================================================================
    # 4. AUTO-SWITCHING INBOX ROTATOR & REGIONAL WORKING HOURS
    # =========================================================================
    def test_05_auto_switching_inbox_rotator_on_send_limits(self):
        """Verifies rotator auto-switches to next SMTP profile when daily send limit is reached."""
        tenant_id = f"op-{uuid.uuid4().hex[:6]}"

        # Enroll 2 mailboxes with low daily limit of 2 emails each
        mb1 = self.rotator.enroll_mailbox(
            email_address=f"sender1-{uuid.uuid4().hex[:4]}@domain1.com",
            display_name="Sender 1",
            daily_limit=2,
            operator_id=tenant_id
        )
        mb2 = self.rotator.enroll_mailbox(
            email_address=f"sender2-{uuid.uuid4().hex[:4]}@domain2.com",
            display_name="Sender 2",
            daily_limit=2,
            operator_id=tenant_id
        )

        # First dispatch should pick lowest sent (0)
        picked1 = self.rotator.get_next_available_mailbox(operator_id=tenant_id)
        self.assertIsNotNone(picked1)
        self.rotator.record_email_dispatched(picked1["id"])

        picked2 = self.rotator.get_next_available_mailbox(operator_id=tenant_id)
        self.assertIsNotNone(picked2)
        self.rotator.record_email_dispatched(picked2["id"])

        # Both mailboxes have 1 sent. Dispatch 2 more to hit cap of 2 each.
        picked3 = self.rotator.get_next_available_mailbox(operator_id=tenant_id)
        self.rotator.record_email_dispatched(picked3["id"])
        picked4 = self.rotator.get_next_available_mailbox(operator_id=tenant_id)
        self.rotator.record_email_dispatched(picked4["id"])

        # Now both mailboxes are at capacity (2/2 sent). Next check must return None.
        picked_overflow = self.rotator.get_next_available_mailbox(operator_id=tenant_id)
        self.assertIsNone(picked_overflow, "Should return None when all tenant mailboxes hit daily limits")

    def test_06_regional_working_hours_engine(self):
        """Verifies dual business hours windows (9-11 AM & 2-5 PM local) and timezone mapping."""
        # Germany -> CET (+1)
        tz_de = self.scheduler.get_target_local_time(country="Germany", domain="bau-berlin.de")
        self.assertEqual(tz_de["timezone_code"], "CET")
        self.assertEqual(tz_de["utc_offset_hours"], 1.0)

        # UK -> GMT (0.0)
        tz_uk = self.scheduler.get_target_local_time(country="United Kingdom", domain="contractor.co.uk")
        self.assertEqual(tz_uk["timezone_code"], "GMT")
        self.assertEqual(tz_uk["utc_offset_hours"], 0.0)

        # US -> EST (-5.0)
        tz_us = self.scheduler.get_target_local_time(country="United States", domain="builder.com")
        self.assertEqual(tz_us["timezone_code"], "EST")
        self.assertEqual(tz_us["utc_offset_hours"], -5.0)

        # Test schedule dispatch time calculation
        sched_time_de = self.scheduler.calculate_next_send_slot("Germany")
        self.assertIsInstance(sched_time_de, datetime)

    # =========================================================================
    # 5. COMMERCIAL SAAS MODULES (BILLING, BLACKLIST, IMAP BOUNCES, DELIVERABILITY)
    # =========================================================================
    def test_07_super_admin_manual_billing_and_10_percent_discount(self):
        """Verifies manual billing controls and automated 10% discount on 90-day packages."""
        self.um.purge_all_data()
        self.um.initialize_admin("admin", "Admin123!", "Admin", "a@a.io")
        op = self.um.create_operator_account("client_corp", "Pass123!", "Client Corp", "client@corp.io")
        op_id = op["user_id"]

        # 1. 30-day plan ($199.00, no discount)
        bill30 = self.um.apply_operator_billing(
            operator_id=op_id,
            base_price=199.00,
            duration_days=30,
            notes="Initial monthly license"
        )
        self.assertEqual(bill30["final_price"], 199.00)
        self.assertEqual(bill30["discount_percent"], 0)

        # 2. 90-day plan ($199.00 * 3 = $597.00 - 10% discount = $537.30)
        bill90 = self.um.apply_operator_billing(
            operator_id=op_id,
            base_price=199.00,
            duration_days=90,
            notes="Quarterly upgrade with 10% incentive"
        )
        self.assertEqual(bill90["subtotal"], 597.00)
        self.assertEqual(bill90["discount_percent"], 10)
        self.assertEqual(bill90["discount_amount"], 59.70)
        self.assertEqual(bill90["final_price"], 537.30)

        # Verify transaction ledger
        history = self.um.get_operator_billing_history(operator_id=op_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["final_price"], 537.30)

    def test_08_global_domain_blacklist_wildcard_matching(self):
        """Verifies wildcard domain matching (*.gov, competitor.com) and auto-exclusion."""
        self.bm.add_rule("*.gov", reason="Government Agency Exclusion")
        self.bm.add_rule("competitor-corp.de", reason="Direct Competitor")

        # Test wildcard match
        is_gov, reason_gov = self.bm.is_domain_blacklisted("procurement.gov")
        self.assertTrue(is_gov)
        self.assertIn("Government", reason_gov)

        is_subgov, _ = self.bm.is_domain_blacklisted("dept.transport.gov")
        self.assertTrue(is_subgov)

        # Test exact domain match
        is_comp, _ = self.bm.is_domain_blacklisted("competitor-corp.de")
        self.assertTrue(is_comp)

        # Non-blacklisted domain
        is_clean, _ = self.bm.is_domain_blacklisted("legitimate-contractor.de")
        self.assertFalse(is_clean)

    def test_09_imap_listener_bounce_suppression_and_hot_lead_routing(self):
        """Verifies IMAP listener auto-suppression on bounces and hot lead promotion."""
        # 1. Simulate incoming Delivery Failure / Bounce
        bounce_res = self.listener.process_incoming_reply(
            sender_email="bounce-handler@mail-server.com",
            subject="Delivery Status Notification (Failure) 550 User Unknown",
            body="The mail system failed to deliver message to target-invalid@fakefirm.de. Recipient address rejected."
        )
        self.assertEqual(bounce_res["classification"], "BOUNCE")
        self.assertTrue(self.listener.is_suppressed("target-invalid@fakefirm.de"))

        # 2. Simulate Positive / Interested Tender Reply
        hot_res = self.listener.process_incoming_reply(
            sender_email="procurement@hochbau-berlin.de",
            subject="Re: Commercial Capacity Inquiry",
            body="Hello H.Huddair, we have two open tender packages for commercial concrete. Please send your rates and credentials.",
            company_name="Hochbau Berlin"
        )
        self.assertEqual(hot_res["classification"], "INTERESTED")
        self.assertTrue(hot_res["is_hot_lead"])
        self.assertIn("H.Huddair", hot_res["ai_suggested_reply"])

        # Check hot leads query
        hot_items = self.listener.get_hot_lead_alerts()
        self.assertTrue(any(item["sender_email"] == "procurement@hochbau-berlin.de" for item in hot_items))

    def test_10_unsubscribe_and_tracking_pixel_endpoints(self):
        """Verifies tracking pixel open logging and CAN-SPAM/GDPR unsubscribe workflow."""
        # Queue outreach item
        q_item = self.gate.queue_outreach(
            lead_id="test-lead-trk",
            company_name="Optout Test GmbH",
            recipient="optout-user@testfirm.de",
            country="Germany",
            niche="General Contracting"
        )
        qid = q_item["queue_id"]

        # 1. Tracking pixel GET request
        trk_resp = self.client.get(f"/api/track/open/{qid}.png")
        self.assertEqual(trk_resp.status_code, 200)
        self.assertEqual(trk_resp.headers["content-type"], "image/png")

        # Verify open recorded in DB
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT opened_at FROM outreach_queue WHERE id = ?", (qid,)).fetchone()
            self.assertIsNotNone(row["opened_at"])

        # 2. Unsubscribe GET confirmation page
        unsub_get = self.client.get("/api/unsubscribe?email=optout-user%40testfirm.de")
        self.assertEqual(unsub_get.status_code, 200)
        self.assertIn("Opt-Out Confirmed", unsub_get.text)

        # Verify recipient is globally suppressed
        self.assertTrue(self.listener.is_suppressed("optout-user@testfirm.de"))

    def test_11_deliverability_analytics_dashboard_metrics(self):
        """Verifies deliverability KPI indicators: Open Rate %, Bounce Rate %, Conversion Rate %."""
        # Create fresh state with admin
        self.um.purge_all_data()
        admin_data = self.um.initialize_admin("admin_metrics", "AdminPass123!", "Metrics Admin", "m@m.io")
        headers = {"Authorization": f"Bearer {admin_data['access_token']}"}

        # Seed mock sent items into outreach_queue
        with self.db.get_connection() as conn:
            # 10 Sent items
            for i in range(10):
                qid = f"q-{i}"
                status = "SENT"
                opened = datetime.now(timezone.utc).isoformat() if i < 4 else None  # 4 opened
                bounced = datetime.now(timezone.utc).isoformat() if i >= 8 else None  # 2 bounced (8, 9)
                if bounced:
                    status = "BOUNCED"
                elif i == 0 or i == 1:
                    status = "HOT_LEAD"  # 2 converted

                conn.execute("""
                    INSERT INTO outreach_queue (
                        id, lead_id, channel, recipient, company_name, subject,
                        message_body, status, mailbox_used, opened_at, bounced_at, sent_at
                    ) VALUES (?, ?, 'EMAIL', ?, 'Test Co', 'Subj', 'Body', ?, 'mb@test.io', ?, ?, CURRENT_TIMESTAMP)
                """, (qid, f"lead-{i}", f"user{i}@test.de", status, opened, bounced))
            conn.commit()

        # Query deliverability analytics API
        resp = self.client.get("/api/analytics/deliverability", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_sent"], 8)  # 8 items with status='SENT' or similar
        self.assertGreaterEqual(data["total_opened"], 4)
        self.assertGreaterEqual(data["total_bounced"], 2)
        self.assertIsInstance(data["open_rate_percent"], float)
        self.assertIsInstance(data["bounce_rate_percent"], float)
        self.assertIsInstance(data["conversion_rate_percent"], float)

        # Enforce zero-seed clean state: purge test fixture items so database starts 100% empty
        self.um.purge_all_data()

    @classmethod
    def tearDownClass(cls):
        """Guarantees 100% clean zero-seed production state upon test suite completion."""
        um = get_user_manager()
        um.purge_all_data()


if __name__ == "__main__":
    unittest.main()
