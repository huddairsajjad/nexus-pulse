"""
Unit & Integration Test Suite for Production Fixes:
1. Railway IPv4 Socket Enforcement
2. Scraper Hygiene (Junk Domains & Invalid System Prefixes)
3. Title Sanitization (Separators, Generic Words, HTTP Error Titles)
4. Dynamic Live Mailbox Credential Resolution & Stuck State Clearing
5. IMAP Reply Parsing (Recipient Email, In-Reply-To, Re: Subject) & Live Dashboard Sync
"""

import os
import sys
import uuid
import socket
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure main entrypoint is loaded and socket getaddrinfo is patched
import main
from core.hygiene.lead_validator import LeadValidationFilter
from core.hygiene.zero_bounce_shield import get_hygiene_shield, DO_NOT_REPLY_PREFIXES
from core.agents.scraper_agent import DeepScraperAgent, SearchDiscoveryAgent
from core.outreach.approval_gate import get_approval_gate
from core.outreach.reply_listener import get_reply_listener
from core.outreach.inbox_rotator import get_inbox_rotator
from database.db_engine import get_db_engine
from auth.user_manager import get_user_manager
from auth.jwt_handler import create_access_token
from fastapi.testclient import TestClient
from api.app import create_app


class TestProductionFixes(unittest.TestCase):

    def setUp(self):
        self.db = get_db_engine()
        self.um = get_user_manager()
        self.rotator = get_inbox_rotator()
        self.gate = get_approval_gate()
        self.listener = get_reply_listener()
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM outreach_queue WHERE recipient LIKE '%client-firm%' OR recipient LIKE '%facade-systems%' OR company_name IN ('Client Firm GmbH', 'Facade Systems GmbH')")
            conn.execute("DELETE FROM mailbox_rotator WHERE email_address LIKE '%outreach-test.io%'")
            conn.execute("DELETE FROM inbox_replies WHERE sender_email LIKE '%facade-systems%' OR company_name IN ('Client Firm GmbH', 'Facade Systems GmbH')")
            conn.execute("DELETE FROM followup_sequences WHERE recipient_email LIKE '%client-firm%' OR recipient_email LIKE '%facade-systems%'")
            conn.commit()

    # =========================================================================
    # 1. RAILWAY IPV4 SOCKET ENFORCEMENT
    # =========================================================================
    def test_01_ipv4_socket_enforcement(self):
        """Verifies socket.getaddrinfo globally forces socket.AF_INET (IPv4 only)."""
        addrinfo = socket.getaddrinfo("smtp.gmail.com", 587)
        self.assertTrue(len(addrinfo) > 0)
        for entry in addrinfo:
            family = entry[0]
            sockaddr = entry[4]
            # Family must strictly be AF_INET (IPv4)
            self.assertEqual(family, socket.AF_INET)
            # IP address in sockaddr must be IPv4 (dotted decimal notation)
            ip_str = sockaddr[0]
            self.assertRegex(ip_str, r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

        # Explicitly passing AF_INET6 must also be coerced to AF_INET
        addrinfo_forced = socket.getaddrinfo("smtp.gmail.com", 587, socket.AF_INET6, socket.SOCK_STREAM)
        for entry in addrinfo_forced:
            self.assertEqual(entry[0], socket.AF_INET)

    # =========================================================================
    # 2. SCRAPER HYGIENE & DOMAIN / PREFIX FILTERING
    # =========================================================================
    def test_02_junk_domain_and_invalid_prefix_dropping(self):
        """Verifies junk domains and invalid/system prefixes are dropped."""
        junk_domains = [
            "wixpress.com",
            "sentry-next.wixpress.com",
            "sentry.io",
            "sub.wixpress.com",
            "app.sentry.io"
        ]
        for jd in junk_domains:
            self.assertTrue(LeadValidationFilter.is_junk_domain(jd), f"Domain {jd} should be recognized as junk")
            is_valid, _, reason = LeadValidationFilter.sanitize_and_validate_email(f"info@{jd}")
            self.assertFalse(is_valid, f"Email with domain {jd} must be dropped: {reason}")
            is_allowed, blocker_reason = LeadValidationFilter.check_role_and_domain_blocker(f"info@{jd}", jd)
            self.assertFalse(is_allowed, f"Domain {jd} must be blocked: {blocker_reason}")

        # Invalid/system email prefixes: nosub_, no-reply@, noreply@, bounce@
        invalid_prefixes = [
            "nosub_abc123@target.de",
            "nosub@target.de",
            "no-reply@target.de",
            "noreply@target.de",
            "bounce@target.de",
            "bounce-mail@target.de"
        ]
        for bad_em in invalid_prefixes:
            is_valid, _, reason = LeadValidationFilter.sanitize_and_validate_email(bad_em)
            self.assertFalse(is_valid, f"Email {bad_em} must be rejected: {reason}")
            is_allowed, reason = LeadValidationFilter.check_role_and_domain_blocker(bad_em, "target.de")
            self.assertFalse(is_allowed, f"Email {bad_em} must be blocked by role blocker: {reason}")

        # Valid legitimate B2B email passes
        is_valid, clean, _ = LeadValidationFilter.sanitize_and_validate_email("estimating@apex-construction.de")
        self.assertTrue(is_valid)
        self.assertEqual(clean, "estimating@apex-construction.de")

    # =========================================================================
    # 3. TITLE SANITIZATION & HTTP ERROR REJECTION
    # =========================================================================
    def test_03_title_sanitization_and_http_error_rejection(self):
        """Verifies cleaning company names removing separators and generic words, and rejecting HTTP errors."""
        # 1. HTTP error titles rejected
        error_titles = [
            "404 Not Found",
            "Error 404 - Page Not Found",
            "Access Denied - 403 Forbidden",
            "403 Forbidden",
            "500 Internal Server Error",
            "Attention Required! | Cloudflare",
            "Checking your browser before accessing"
        ]
        for err_title in error_titles:
            is_valid, comp, reason = LeadValidationFilter.evaluate_page_title(err_title, "target-firm.de")
            self.assertFalse(is_valid, f"Title '{err_title}' must be rejected: {reason}")

        # 2. Separators and generic words cleaned
        test_cases = [
            ("Home - Modern Glass Facades: Official Site", "Modern Glass Facades"),
            ("Welcome to Acme Construction | Commercial Builders", "Acme Construction"),
            ("Acme Construction - Official Site", "Acme Construction"),
            ("Bauunternehmen Schmidt GmbH | Hochbau & Tiefbau", "Bauunternehmen Schmidt GmbH"),
            ("Welcome to Powerlifting Equipment : Home", "Powerlifting Equipment"),
            ("Home | Official Site", "Apex Contracting")  # Generic terms stripped -> fallback to domain brand
        ]
        for raw_title, expected in test_cases:
            is_valid, clean_name, _ = LeadValidationFilter.evaluate_page_title(raw_title, "apex-contracting.de")
            self.assertTrue(is_valid)
            self.assertEqual(clean_name, expected)

    # =========================================================================
    # 4. DYNAMIC MAILBOX RESOLUTION & STUCK FAILED STATE CLEARING
    # =========================================================================
    def test_04_live_dispatch_reads_credentials_and_clears_stuck_states(self):
        """Verifies dispatch reads credentials dynamically and clears stuck FAILED states."""
        # Enroll test mailbox
        mb_email = f"sender-{uuid.uuid4().hex[:6]}@outreach-test.io"
        mb_info = self.rotator.enroll_mailbox(
            email_address=mb_email,
            display_name="Enterprise Dispatcher",
            daily_limit=50,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username=mb_email,
            smtp_password="app-password-test",
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username=mb_email,
            imap_password="app-password-test"
        )
        mb_id = mb_info["id"]

        # Insert a lead stuck in FAILED state (e.g. from prior network unreachable)
        q_id = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, tracking_id, mailbox_used, bounce_reason
                ) VALUES (?, 'target@client-firm.de', 'Client Firm GmbH', 'Tender Proposal', 'Proposal body',
                          'FAILED', 'Germany', 'CET', ?, ?, 'SMTP Failure: [Errno 101] Network is unreachable')
            """, (q_id, tracking_id, mb_email))
            conn.commit()

        # Mock smtplib.SMTP connection to simulate successful 250 OK live dispatch
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            instance.sendmail.return_value = {}  # 250 OK

            res = self.gate.dispatch_approved_outreach(q_id)
            self.assertTrue(res["success"])
            self.assertEqual(res["status"], "SENT")

        # Verify stuck state cleared in database: status is SENT and bounce_reason is cleared (NULL)
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status, bounce_reason, mailbox_used, message_id FROM outreach_queue WHERE id = ?", (q_id,)).fetchone()
            self.assertEqual(row["status"], "SENT")
            self.assertIsNone(row["bounce_reason"])
            self.assertEqual(row["mailbox_used"], mb_email)
            self.assertTrue(row["message_id"].startswith("<") and row["message_id"].endswith(">"))

    # =========================================================================
    # 5. IMAP PARSING VIA RECIPIENT, IN-REPLY-TO & RE: SUBJECT + DASHBOARD SYNC
    # =========================================================================
    def test_05_imap_poller_multi_vector_matching_and_live_dashboard_counters(self):
        """Verifies IMAP poller parses In-Reply-To, Re: subjects, and recipient emails, updating dashboard counters."""
        # 1. Setup a sent queue item
        q_id = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        lead_id = str(uuid.uuid4())
        recipient = f"procurement-{uuid.uuid4().hex[:6]}@facade-systems.de"
        subject = "Commercial Facade Estimation & Tenders"
        msg_id = f"<{tracking_id}@outreach-test.io>"

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, lead_id, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, tracking_id, message_id, sent_at
                ) VALUES (?, ?, ?, 'Facade Systems GmbH', ?, 'Body text',
                          'SENT', 'Germany', 'CET', ?, ?, CURRENT_TIMESTAMP)
            """, (q_id, lead_id, recipient, subject, tracking_id, msg_id))
            conn.commit()

        # Check initial analytics dashboard counters using admin JWT
        admin_token = create_access_token(user_id="admin_test_id", username="admin_tester", role="admin", full_name="Admin Tester")
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp_before = self.client.get("/api/analytics/deliverability", headers=headers)
        data_before = resp_before.json()
        initial_sent = data_before["total_sent"]
        initial_replied = data_before["total_replied"]
        initial_hot = data_before["total_hot_leads"]

        # 2. Simulate incoming Hot Lead reply matching via In-Reply-To and Re: subject
        reply_result = self.listener.process_incoming_reply(
            sender_email=recipient,
            subject=f"Re: {subject}",
            body="Thank you. Please send through the tender documents and pricing drawings. We would like to schedule a call.",
            in_reply_to=msg_id
        )

        self.assertEqual(reply_result["classification"], "INTERESTED")
        self.assertTrue(reply_result["is_hot_lead"])
        self.assertEqual(reply_result["alert"], "HOT_LEAD_DETECTED")

        # 3. Verify outreach_queue status was directly updated to HOT_LEAD
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status FROM outreach_queue WHERE id = ?", (q_id,)).fetchone()
            self.assertEqual(row["status"], "HOT_LEAD")

        # 4. Verify live dashboard counters directly reflect the updated metrics
        resp_after = self.client.get("/api/analytics/deliverability", headers=headers)
        data_after = resp_after.json()

        self.assertGreaterEqual(data_after["total_sent"], initial_sent)
        self.assertEqual(data_after["total_replied"], initial_replied + 1)
        self.assertEqual(data_after["total_hot_leads"], initial_hot + 1)

    # =========================================================================
    # 6. OFF-NICHE DOMAIN & DUMMY EMAIL BLOCKING
    # =========================================================================
    def test_06_off_niche_domain_and_dummy_email_blocking(self):
        """Verifies off-niche magazine/directory domains and dummy emails are strictly rejected."""
        off_domains = [
            "sqmagazine.com", "sqmagazine.co.uk", "fashionmagazine.net",
            "construction-news-blog.org", "businessdirectory.co", "techreviews.com"
        ]
        for dom in off_domains:
            is_off, reason = LeadValidationFilter.is_off_niche_domain(dom)
            self.assertTrue(is_off, f"Domain {dom} must be detected as off-niche: {reason}")
            is_allowed, blocker_reason = LeadValidationFilter.check_role_and_domain_blocker(f"editor@{dom}", dom)
            self.assertFalse(is_allowed, f"Domain {dom} must be blocked by check_role_and_domain_blocker: {blocker_reason}")

        dummy_emails = [
            "you@company.com", "user@example.com", "email@example.com",
            "test@example.com", "test@test.com", "placeholder@company.com"
        ]
        for dem in dummy_emails:
            is_valid, _, reason = LeadValidationFilter.sanitize_and_validate_email(dem)
            self.assertFalse(is_valid, f"Dummy email {dem} must be rejected: {reason}")
            is_allowed, blocker_reason = LeadValidationFilter.check_role_and_domain_blocker(dem, dem.split("@")[-1])
            self.assertFalse(is_allowed, f"Dummy email {dem} must be blocked: {blocker_reason}")

    # =========================================================================
    # 7. COMPANY NAME SHORT FRAGMENT ('AI') NORMALIZATION
    # =========================================================================
    def test_07_company_name_ai_fragment_normalization(self):
        """Verifies raw fragments like 'AI' or short abbreviations normalize into clean names from domain."""
        cleaned_ai = LeadValidationFilter.clean_company_name("AI", domain="jasper.ai")
        self.assertNotEqual(cleaned_ai, "AI")
        self.assertTrue("Jasper" in cleaned_ai)

        cleaned_title = LeadValidationFilter.clean_company_name("AI | Enterprise Automation", domain="synthflow.ai")
        self.assertNotEqual(cleaned_title, "AI")

        is_valid, name, reason = LeadValidationFilter.evaluate_page_title("AI", domain="anthropic.com")
        self.assertTrue(is_valid)
        self.assertEqual(name, "Anthropic")

    # =========================================================================
    # 8. PER-OPERATOR INDEPENDENT QUOTAS & LICENSE EXTENSION
    # =========================================================================
    def test_08_per_operator_quotas_and_license_extension(self):
        """Verifies admin can set 1000 daily scrape quota and extend days for an operator."""
        admin_token = create_access_token(user_id="admin_test_id", username="admin_tester", role="admin", full_name="Admin Tester")
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Create test operator
        op_res = self.um.create_operator_account(
            username=f"op_{uuid.uuid4().hex[:6]}",
            password="TestPassword123!",
            full_name="Quota Test Operator",
            email="quotatest@example-domain.org",
            daily_scrape_quota=200,
            daily_send_quota=50
        )
        op_id = op_res["user_id"]

        try:
            # Update quota to 1000/day and extend 30 days
            resp = self.client.put(
                f"/api/operators/{op_id}/quotas",
                headers=headers,
                json={
                    "extend_days": 30,
                    "daily_scrape_quota": 1000,
                    "daily_send_quota": 250
                }
            )
            self.assertEqual(resp.status_code, 200, f"Quota update failed: {resp.text}")
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["daily_scrape_quota"], 1000)
            self.assertEqual(data["daily_send_quota"], 250)

            # Verify in DB
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT daily_scrape_quota, daily_send_quota FROM users WHERE id = ?", (op_id,)).fetchone()
                self.assertEqual(row["daily_scrape_quota"], 1000)
                self.assertEqual(row["daily_send_quota"], 250)
        finally:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM users WHERE id = ?", (op_id,))
                conn.commit()

    # =========================================================================
    # 9. UNSUBSCRIBE FULL URL & RECIPIENT OVERRIDE ACCURACY
    # =========================================================================
    def test_09_unsubscribe_full_url_and_recipient_override(self):
        """Verifies unsubscribe links use full base URL and override recipient email when edited."""
        os.environ["APP_BASE_URL"] = "https://nexus-pulse-production.up.railway.app"
        q_res = self.gate.queue_outreach(
            lead_id="test_lead_unsub_1",
            recipient="original@clientfirm.de",
            company_name="Client Firm GmbH",
            country="Germany",
            niche="Enterprise SaaS",
            custom_subject="Initial Subject {{unsubscribe_link}}",
            custom_body="Please review {{unsubscribe_link}}"
        )
        q_id = q_res["queue_id"]

        try:
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT message_body FROM outreach_queue WHERE id = ?", (q_id,)).fetchone()
                self.assertIn("https://nexus-pulse-production.up.railway.app/api/unsubscribe", row["message_body"])
                self.assertIn("email=original%40clientfirm.de", row["message_body"])

            # Edit recipient in approval gate
            appr_res = self.gate.approve_outreach_item(
                queue_id=q_id,
                approver="admin",
                edited_recipient="override@clientfirm.de"
            )
            self.assertTrue(appr_res["success"])

            with self.db.get_connection() as conn:
                row = conn.execute("SELECT recipient, message_body FROM outreach_queue WHERE id = ?", (q_id,)).fetchone()
                self.assertEqual(row["recipient"], "override@clientfirm.de")
                self.assertIn("email=override%40clientfirm.de", row["message_body"])
                self.assertNotIn("email=original%40clientfirm.de", row["message_body"])
        finally:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM outreach_queue WHERE id = ?", (q_id,))
                conn.commit()


if __name__ == "__main__":
    unittest.main()
