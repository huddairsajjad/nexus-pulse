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


if __name__ == "__main__":
    unittest.main()
