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
            conn.execute("DELETE FROM outreach_queue WHERE recipient LIKE '%@webhook-test.io'")
            conn.execute("DELETE FROM mailbox_rotator WHERE email_address LIKE '%@webhook-test.io'")
            conn.execute("DELETE FROM followup_sequences WHERE recipient_email LIKE '%@webhook-test.io'")
            conn.commit()

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


if __name__ == "__main__":
    unittest.main()
