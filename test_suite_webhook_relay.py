"""
Nexus-Pulse Test Suite: Multi-Mailbox Google Apps Script HTTPS Webhook Relay
Tests:
1. Enrollment of unlimited mailboxes with optional webhook_url
2. Updating mailbox webhook_url
3. Dispatch via webhook relay (JSON payload, status=success check, sent_today increment)
4. Automatic fallback to SMTP when webhook fails or returns non-success
5. Automatic fallback to SMTP when webhook_url is empty
6. Multi-mailbox rotation across unlimited mailboxes with independent quotas
7. Clean teardown ensuring 0 mock records remain
"""

import os
import sys
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_engine import get_db_engine
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.approval_gate import get_approval_gate, _send_webhook_request
from api.routes import MailboxCreateRequest, MailboxUpdateRequest
from auth.jwt_handler import create_access_token
from fastapi.testclient import TestClient
from api.app import create_app


class TestWebhookRelay(unittest.TestCase):

    def setUp(self):
        self.db = get_db_engine()
        self.rotator = get_inbox_rotator()
        self.gate = get_approval_gate()
        self.app = create_app()
        self.client = TestClient(self.app)
        self.test_ids = []

    def tearDown(self):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM outreach_queue WHERE recipient LIKE '%@webhook-test.io' OR operator_id LIKE 'tenant_%'")
            conn.execute("DELETE FROM mailbox_rotator WHERE email_address LIKE '%@webhook-test.io' OR operator_id LIKE 'tenant_%'")
            conn.execute("DELETE FROM followup_sequences WHERE recipient_email LIKE '%@webhook-test.io'")
            conn.execute("DELETE FROM vault_leads WHERE primary_email LIKE '%@webhook-test.io' OR operator_id LIKE 'tenant_%'")
            conn.execute("DELETE FROM operator_sessions WHERE user_id LIKE 'tenant_%'")
            conn.commit()
        try:
            from database.mongo_engine import get_mongo_engine
            mongo = get_mongo_engine()
            if mongo and mongo.db is not None:
                for coll in ("leads", "outreach", "mailboxes"):
                    mongo.db[coll].delete_many({"owner_username": {"$in": ["tenant_alpha", "tenant_beta"]}})
                    mongo.db[coll].delete_many({"primary_email": {"$regex": "@webhook-test\\.io$"}})
                    mongo.db[coll].delete_many({"email_address": {"$regex": "@webhook-test\\.io$"}})
        except Exception:
            pass

    def test_01_enroll_and_update_mailbox_with_webhook(self):
        """Tests that mailbox can be enrolled with webhook_url and updated."""
        email = f"sender-{uuid.uuid4().hex[:6]}@webhook-test.io"
        webhook = "https://script.google.com/macros/s/AKfycbx_test_script/exec"

        res = self.rotator.enroll_mailbox(
            email_address=email,
            display_name="Webhook Dispatcher",
            domain="webhook-test.io",
            daily_limit=50,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username=email,
            smtp_password="testpassword",
            webhook_url=webhook
        )
        self.assertEqual(res["webhook_url"], webhook)
        mb_id = res["id"]

        # Check in get_all_mailboxes_status
        all_mb = self.rotator.get_all_mailboxes_status()
        found = next((m for m in all_mb if m["id"] == mb_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["webhook_url"], webhook)

        # Update webhook via API
        token = create_access_token("test_admin", "admin_user", "admin", "Admin User")
        new_webhook = "https://script.google.com/macros/s/AKfycbx_updated_script/exec"
        resp = self.client.put(
            f"/api/mailboxes/{mb_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"webhook_url": new_webhook, "daily_limit": 60}
        )
        self.assertEqual(resp.status_code, 200)

        all_mb2 = self.rotator.get_all_mailboxes_status()
        found2 = next((m for m in all_mb2 if m["id"] == mb_id), None)
        self.assertEqual(found2["webhook_url"], new_webhook)
        self.assertEqual(found2["daily_limit"], 60)

    def test_02_webhook_dispatch_success(self):
        """Verifies successful dispatch via Google Apps Script Webhook increments sent_today."""
        email = f"sender-{uuid.uuid4().hex[:6]}@webhook-test.io"
        webhook = "https://script.google.com/macros/s/AKfycbx_success/exec"

        mb = self.rotator.enroll_mailbox(
            email_address=email,
            display_name="Enterprise Webhook Relay",
            domain="webhook-test.io",
            daily_limit=50,
            webhook_url=webhook
        )

        q_id = str(uuid.uuid4())
        recip = f"lead-{uuid.uuid4().hex[:6]}@webhook-test.io"
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, mailbox_used
                ) VALUES (?, ?, 'Bau Tech GmbH', 'Partnership Proposal', 'Hello team',
                          'APPROVED', 'Germany', 'CET', ?)
            """, (q_id, recip, email))
            conn.commit()

        # Mock _send_webhook_request to return success
        with patch("core.outreach.approval_gate._send_webhook_request") as mock_wh:
            mock_wh.return_value = {"status": "success", "message": "Email sent successfully"}

            res = self.gate.dispatch_approved_outreach(q_id)
            self.assertTrue(res["success"])
            self.assertEqual(res["status"], "SENT")
            self.assertEqual(res["delivery_method"], "WEBHOOK")

            # Verify payload passed to webhook
            mock_wh.assert_called_once()
            called_url, called_payload = mock_wh.call_args[0]
            self.assertEqual(called_url, webhook)
            self.assertEqual(called_payload["to"], recip)
            self.assertEqual(called_payload["subject"], "Partnership Proposal")
            self.assertEqual(called_payload["sender_name"], "Enterprise Webhook Relay")
            self.assertEqual(called_payload["secret"], "NEXUS_PULSE_2026")

        # Verify sent_today incremented in database
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT sent_today FROM mailbox_rotator WHERE id = ?", (mb["id"],)).fetchone()
            self.assertEqual(row["sent_today"], 1)

    def test_03_webhook_fallback_to_smtp_on_failure(self):
        """Verifies automatic fallback to SMTP when webhook request returns non-success."""
        email = f"sender-{uuid.uuid4().hex[:6]}@webhook-test.io"
        webhook = "https://script.google.com/macros/s/AKfycbx_failing/exec"

        mb = self.rotator.enroll_mailbox(
            email_address=email,
            display_name="Fallback Sender",
            domain="webhook-test.io",
            daily_limit=50,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username=email,
            smtp_password="app-password-123",
            webhook_url=webhook
        )

        q_id = str(uuid.uuid4())
        recip = f"lead-{uuid.uuid4().hex[:6]}@webhook-test.io"
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, mailbox_used
                ) VALUES (?, ?, 'Failing Webhook AG', 'Subject line', 'Body text',
                          'APPROVED', 'Germany', 'CET', ?)
            """, (q_id, recip, email))
            conn.commit()

        # Webhook raises connection error; SMTP succeeds
        with patch("core.outreach.approval_gate._send_webhook_request") as mock_wh:
            mock_wh.side_effect = Exception("Connection timed out to Google Apps Script")

            with patch("smtplib.SMTP") as mock_smtp:
                instance = mock_smtp.return_value
                instance.sendmail.return_value = {}  # 250 OK

                res = self.gate.dispatch_approved_outreach(q_id)
                self.assertTrue(res["success"])
                self.assertEqual(res["status"], "SENT")
                self.assertEqual(res["delivery_method"], "SMTP")
                instance.sendmail.assert_called_once()

    def test_04_multi_mailbox_smart_rotation(self):
        """Verifies unlimited accounts are enrolled and rotated based on quota."""
        mb_ids = []
        for i in range(4):
            email = f"acc-{i}-{uuid.uuid4().hex[:6]}@webhook-test.io"
            mb = self.rotator.enroll_mailbox(
                email_address=email,
                display_name=f"Rotator Account {i+1}",
                domain="webhook-test.io",
                daily_limit=2,
                webhook_url=f"https://script.google.com/macros/s/acc_{i}/exec"
            )
            mb_ids.append(mb["id"])

        # Pick next available: should pick the first with sent_today=0
        picked1 = self.rotator.get_next_available_mailbox()
        self.assertIsNotNone(picked1)
        self.assertEqual(picked1["sent_today"], 0)

        # Simulate 2 dispatches on picked1
        self.rotator.record_email_dispatched(picked1["id"])
        self.rotator.record_email_dispatched(picked1["id"])

        # Next available should not be picked1 (at limit of 2)
        picked2 = self.rotator.get_next_available_mailbox()
        self.assertIsNotNone(picked2)
        self.assertNotEqual(picked2["id"], picked1["id"])
        self.assertEqual(picked2["sent_today"], 0)

    def test_05_apps_script_302_redirect_and_html_rejection(self):
        """Verifies _send_webhook_request follows 302 redirects with 15s timeout and rejects HTML pages."""
        import httpx

        captured = {}

        def mock_handler(request: httpx.Request) -> httpx.Response:
            captured.setdefault("methods", []).append((request.method, str(request.url)))
            if "script.google.com" in str(request.url):
                return httpx.Response(
                    302,
                    headers={"Location": "https://script.googleusercontent.com/macros/echo?key=abc123"},
                )
            return httpx.Response(200, json={"status": "success", "sent": True})

        real_client_cls = httpx.Client

        def transport_client(*args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            captured["follow_redirects"] = kwargs.get("follow_redirects")
            kwargs["transport"] = httpx.MockTransport(mock_handler)
            return real_client_cls(*args, **kwargs)

        with patch("httpx.Client", side_effect=transport_client):
            res = _send_webhook_request(
                "https://script.google.com/macros/s/AKfycbx_redirect/exec",
                {"to": "target@webhook-test.io", "subject": "Hi", "body": "Test"},
                max_retries=1,
            )

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(captured.get("timeout"), 15.0)
        self.assertTrue(captured.get("follow_redirects"))
        self.assertEqual(len(captured["methods"]), 2)
        self.assertEqual(captured["methods"][0][0], "POST")
        self.assertEqual(captured["methods"][1][0], "GET")

        # HTML login / error page returned with HTTP 200 containing 'cookie'/'token' must be rejected
        def html_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<!DOCTYPE html><html><body>Sign in with cookie token</body></html>")

        def html_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(html_handler)
            return real_client_cls(*args, **kwargs)

        with patch("httpx.Client", side_effect=html_client):
            bad_res = _send_webhook_request(
                "https://script.google.com/macros/s/AKfycbx_html/exec",
                {"to": "target@webhook-test.io"},
                max_retries=1,
            )
        self.assertEqual(bad_res.get("status"), "error")

    def test_06_modal_edit_persist_mongo_dispatch_and_engine_reset(self):
        """Verifies edited fields persist to MongoDB+SQLite before dispatch, webhook increments mailbox, and engine resets in try/finally."""
        from database.mongo_engine import get_mongo_engine
        from core.outreach.dispatcher_worker import get_dispatcher_worker

        mongo = get_mongo_engine()
        worker = get_dispatcher_worker()

        op_id = "tenant_alpha_id"
        owner = "tenant_alpha"
        token = create_access_token(op_id, owner, "admin", "Tenant Alpha")

        mb_email = f"alpha-{uuid.uuid4().hex[:6]}@webhook-test.io"
        mb = self.rotator.enroll_mailbox(
            email_address=mb_email,
            display_name="Alpha Sender",
            domain="webhook-test.io",
            daily_limit=50,
            operator_id=op_id,
            owner_username=owner,
            webhook_url="https://script.google.com/macros/s/alpha_exec/exec",
        )

        lead_id = f"lead-{uuid.uuid4().hex[:8]}"
        q_id = str(uuid.uuid4())
        orig_email = f"orig-{uuid.uuid4().hex[:6]}@webhook-test.io"
        edited_email = f"edited-{uuid.uuid4().hex[:6]}@webhook-test.io"

        mongo.insert_lead({
            "lead_id": lead_id,
            "domain": "webhook-test.io",
            "primary_email": orig_email,
            "company_name": "Original Corp",
            "operator_id": op_id,
            "owner_username": owner,
        })

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, lead_id, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, operator_id, owner_username, mailbox_used
                ) VALUES (?, ?, ?, 'Original Corp', 'Old Subj', 'Old Body\nUnsub: https://example.com/api/unsubscribe?token=t1&email=orig',
                          'PENDING_APPROVAL', 'Germany', 'CET', ?, ?, ?)
            """, (q_id, lead_id, orig_email, op_id, owner, mb_email))
            conn.commit()

        # 1. Approve with edited fields (modal persistence before dispatch)
        app_resp = self.client.post(
            "/api/outreach/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "queue_id": q_id,
                "approver": owner,
                "edited_recipient": edited_email,
                "edited_company_name": "Updated Corp GmbH",
                "edited_subject": "Updated Tender Proposal",
                "edited_body": "Updated Proposal Body\nhttps://example.com/api/unsubscribe?token=t1&email=orig%40webhook-test.io",
            },
        )
        self.assertEqual(app_resp.status_code, 200, app_resp.text)
        self.assertTrue(app_resp.json()["success"])

        # Verify MongoDB persisted all edited fields BEFORE dispatch
        lead_doc = mongo.db.leads.find_one({"lead_id": lead_id, "owner_username": owner})
        self.assertIsNotNone(lead_doc)
        self.assertEqual(lead_doc["primary_email"], edited_email)
        self.assertEqual(lead_doc["company_name"], "Updated Corp GmbH")
        self.assertEqual(lead_doc["subject"], "Updated Tender Proposal")
        self.assertEqual(lead_doc["status"], "approved")

        # 2. Failed/timeout webhook must leave status != dispatched, sent_today == 0, and reset engine to RUNNING
        with patch("core.outreach.approval_gate._send_webhook_request", side_effect=TimeoutError("15s relay timeout")):
            fail_resp = self.client.post(
                "/api/outreach/dispatch-now",
                headers={"Authorization": f"Bearer {token}"},
                json={"bypass_window": True, "queue_id": q_id},
            )
        self.assertEqual(fail_resp.status_code, 400)
        st_after_err = self.client.get("/api/dispatcher/status", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(st_after_err["status"], "RUNNING")
        mb_doc_after_err = self.rotator.get_all_mailboxes_status(operator_id=op_id, owner_username=owner)[0]
        self.assertEqual(mb_doc_after_err["sent_today"], 0)

        # 3. Verified webhook success updates MongoDB status='dispatched', SQLite='SENT', increments sent_today, resets to RUNNING
        with patch("core.outreach.approval_gate._send_webhook_request", return_value={"status": "success"}):
            ok_resp = self.client.post(
                "/api/outreach/dispatch-now",
                headers={"Authorization": f"Bearer {token}"},
                json={"bypass_window": True, "queue_id": q_id},
            )
        self.assertEqual(ok_resp.status_code, 200, ok_resp.text)
        self.assertEqual(ok_resp.json()["dispatched_count"], 1)

        lead_doc_done = mongo.db.leads.find_one({"lead_id": lead_id, "owner_username": owner})
        self.assertEqual(lead_doc_done["status"], "dispatched")
        mb_mongo = mongo.db.mailboxes.find_one({"mailbox_id": mb["id"], "owner_username": owner})
        self.assertIsNotNone(mb_mongo)
        self.assertEqual(mb_mongo["sent_today"], 1)
        mb_sql = self.rotator.get_all_mailboxes_status(operator_id=op_id, owner_username=owner)[0]
        self.assertEqual(mb_sql["sent_today"], 1)

        st_final = worker.get_telemetry(operator_id=op_id, owner_username=owner)
        self.assertEqual(st_final["status"], "RUNNING")

    def test_07_strict_tenant_isolation_across_gate_mailboxes_and_engine(self):
        """Verifies Tenant B cannot mutate Tenant A leads, mailboxes, or engine status."""
        from core.outreach.dispatcher_worker import get_dispatcher_worker

        worker = get_dispatcher_worker()
        op_a, owner_a = "tenant_alpha_id", "tenant_alpha"
        op_b, owner_b = "tenant_beta_id", "tenant_beta"
        tok_a = create_access_token(op_a, owner_a, "operator", "Alpha")
        tok_b = create_access_token(op_b, owner_b, "operator", "Beta")

        mb_a = self.rotator.enroll_mailbox(
            email_address=f"mb-a-{uuid.uuid4().hex[:6]}@webhook-test.io",
            display_name="Alpha MB",
            operator_id=op_a,
            owner_username=owner_a,
            webhook_url="https://script.google.com/macros/s/a/exec",
        )
        mb_b = self.rotator.enroll_mailbox(
            email_address=f"mb-b-{uuid.uuid4().hex[:6]}@webhook-test.io",
            display_name="Beta MB",
            operator_id=op_b,
            owner_username=owner_b,
            webhook_url="https://script.google.com/macros/s/b/exec",
        )

        q_a = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, operator_id, owner_username, mailbox_used
                ) VALUES (?, ?, 'Alpha Client', 'Subj A', 'Body A',
                          'PENDING_APPROVAL', 'Germany', ?, ?, ?)
            """, (q_a, f"client-a-{uuid.uuid4().hex[:6]}@webhook-test.io", op_a, owner_a, mb_a["email_address"]))
            conn.commit()

        # Tenant B cannot approve, dispatch, delete, unblock, or update status of Tenant A's item
        self.assertEqual(
            self.client.post("/api/outreach/approve", headers={"Authorization": f"Bearer {tok_b}"}, json={"queue_id": q_a}).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete(f"/api/outreach/queue/{q_a}", headers={"Authorization": f"Bearer {tok_b}"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/outreach/lead-status", headers={"Authorization": f"Bearer {tok_b}"}, json={"queue_id": q_a, "status": "SENT"}).status_code,
            403,
        )

        # Tenant A engine DISPATCHING does not change Tenant B engine status
        worker.begin_tenant_dispatch(operator_id=op_a, owner_username=owner_a)
        try:
            st_a = self.client.get("/api/dispatcher/status", headers={"Authorization": f"Bearer {tok_a}"}).json()
            st_b = self.client.get("/api/dispatcher/status", headers={"Authorization": f"Bearer {tok_b}"}).json()
            self.assertEqual(st_a["status"], "DISPATCHING")
            self.assertEqual(st_b["status"], "RUNNING")
            self.assertEqual(st_a["pending_count"], 1)
            self.assertEqual(st_b["pending_count"], 0)
        finally:
            worker.end_tenant_dispatch(operator_id=op_a, owner_username=owner_a)

        # Tenant A approves & dispatches -> only mb_a sent_today increments; mb_b stays 0
        self.assertEqual(
            self.client.post("/api/outreach/approve", headers={"Authorization": f"Bearer {tok_a}"}, json={"queue_id": q_a}).status_code,
            200,
        )
        with patch("core.outreach.approval_gate._send_webhook_request", return_value={"status": "success"}):
            d_resp = self.client.post(
                "/api/outreach/dispatch-now",
                headers={"Authorization": f"Bearer {tok_a}"},
                json={"bypass_window": True, "queue_id": q_a},
            )
        self.assertEqual(d_resp.status_code, 200)
        self.assertEqual(self.rotator.get_all_mailboxes_status(operator_id=op_a, owner_username=owner_a)[0]["sent_today"], 1)
        self.assertEqual(self.rotator.get_all_mailboxes_status(operator_id=op_b, owner_username=owner_b)[0]["sent_today"], 0)

    def test_08_regional_working_hours_windows_and_non_bypass_queue(self):
        """Verifies timezone resolution, 9-5 boundaries, weekends, half-hour offsets, and bypass vs non-bypass queue."""
        from datetime import datetime, timezone
        from core.outreach.scheduler import TimezoneScheduler

        # 1. Region disambiguation & punctuation normalization (no false 'oman'->'romania' hit!)
        self.assertEqual(TimezoneScheduler.detect_timezone_info("Oman")[:2], (4.0, "GST"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("U.S.A.")[:2], (-5.0, "EST"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("U.K.")[:2], (0.0, "GMT"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("U.A.E.")[:2], (4.0, "GST"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("United States", city="Austin")[:2], (-6.0, "CST_US"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("United States", city="Los Angeles")[:2], (-8.0, "PST"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("India")[:2], (5.5, "IST"))
        self.assertEqual(TimezoneScheduler.detect_timezone_info("Pakistan")[:2], (5.0, "PKT"))

        # 2. Boundary checks at Wednesday 2026-11-25 12:00 UTC
        # UK (0): 12:00 -> IN window
        # UAE (+4): 16:00 -> IN window
        # PKT (+5): 17:00 -> OUTSIDE window (>= 17:00)
        # US EST (-5): 07:00 -> OUTSIDE window (< 09:00)
        wed_noon_utc = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
        self.assertTrue(TimezoneScheduler.get_target_local_time("United Kingdom", now_utc=wed_noon_utc)["is_in_send_window"])
        self.assertTrue(TimezoneScheduler.get_target_local_time("UAE", now_utc=wed_noon_utc)["is_in_send_window"])
        self.assertFalse(TimezoneScheduler.get_target_local_time("Pakistan", now_utc=wed_noon_utc)["is_in_send_window"])
        self.assertFalse(TimezoneScheduler.get_target_local_time("United States", now_utc=wed_noon_utc)["is_in_send_window"])

        # India (+5.5) at 03:29 UTC -> 08:59 IST (blocked); at 03:30 UTC -> 09:00 IST (allowed)
        ist_0859 = datetime(2026, 11, 25, 3, 29, tzinfo=timezone.utc)
        ist_0900 = datetime(2026, 11, 25, 3, 30, tzinfo=timezone.utc)
        self.assertFalse(TimezoneScheduler.get_target_local_time("India", now_utc=ist_0859)["is_in_send_window"])
        self.assertTrue(TimezoneScheduler.get_target_local_time("India", now_utc=ist_0900)["is_in_send_window"])
        next_ist = TimezoneScheduler.calculate_next_send_slot("India", now_utc=ist_0859)
        self.assertEqual(next_ist, ist_0900)

        # Weekend check (Saturday 2026-11-28 11:00 UTC in London) -> scheduled for Monday 09:00 UTC; bypass overrides
        sat_utc = datetime(2026, 11, 28, 11, 0, tzinfo=timezone.utc)
        self.assertFalse(TimezoneScheduler.get_target_local_time("United Kingdom", bypass_window=False, now_utc=sat_utc)["is_in_send_window"])
        self.assertTrue(TimezoneScheduler.get_target_local_time("United Kingdom", bypass_window=True, now_utc=sat_utc)["is_in_send_window"])
        mon_slot = TimezoneScheduler.calculate_next_send_slot("United Kingdom", bypass_window=False, now_utc=sat_utc)
        self.assertEqual(mon_slot, datetime(2026, 11, 30, 9, 0, tzinfo=timezone.utc))

        # 3. Live non-bypass dispatch_ready_queue run (verifies sqlite3.Row dict conversion & mixed windows)
        op_id, owner = "tenant_alpha_id", "tenant_alpha"
        mb_email = f"tz-{uuid.uuid4().hex[:6]}@webhook-test.io"
        self.rotator.enroll_mailbox(
            email_address=mb_email,
            display_name="TZ Sender",
            operator_id=op_id,
            owner_username=owner,
            webhook_url="https://script.google.com/macros/s/tz/exec",
        )
        q_in = str(uuid.uuid4())
        q_out = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, operator_id, owner_username, mailbox_used
                ) VALUES (?, ?, 'London In', 'S1', 'B1', 'APPROVED', 'United Kingdom', ?, ?, ?)
            """, (q_in, f"in-{uuid.uuid4().hex[:6]}@webhook-test.io", op_id, owner, mb_email))
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, operator_id, owner_username, mailbox_used
                ) VALUES (?, ?, 'NY Out', 'S2', 'B2', 'APPROVED', 'United States', ?, ?, ?)
            """, (q_out, f"out-{uuid.uuid4().hex[:6]}@webhook-test.io", op_id, owner, mb_email))
            conn.commit()

        # Freeze scheduler evaluation via get_target_local_time side_effect using wed_noon_utc
        orig_get = TimezoneScheduler.get_target_local_time
        orig_slot = TimezoneScheduler.calculate_next_send_slot
        with patch.object(TimezoneScheduler, "get_target_local_time", side_effect=lambda *a, **kw: orig_get(*a, now_utc=wed_noon_utc, **kw)), \
             patch.object(TimezoneScheduler, "calculate_next_send_slot", side_effect=lambda *a, **kw: orig_slot(*a, now_utc=wed_noon_utc, **kw)), \
             patch("core.outreach.approval_gate._send_webhook_request", return_value={"status": "success"}):
            q_res = self.gate.dispatch_ready_queue(bypass_window=False, operator_id=op_id, owner_username=owner)

        self.assertTrue(q_res["success"])
        self.assertEqual(q_res["dispatched_count"], 1)
        self.assertEqual(q_res["scheduled_count"], 1)
        self.assertEqual(q_res["dispatched_items"][0]["queue_id"], q_in)
        self.assertEqual(q_res["scheduled_items"][0]["queue_id"], q_out)


if __name__ == "__main__":
    unittest.main()
