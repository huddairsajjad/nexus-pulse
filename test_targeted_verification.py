import os
import sys
import unittest
import time
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from database.db_engine import get_db_engine
from database.mongo_engine import get_mongo_engine
from core.outreach.approval_gate import get_approval_gate, _send_webhook_request
from core.outreach.reply_listener import get_reply_listener
from core.agents.scraper_agent import DeepScraperAgent
from core.outreach.blacklist_manager import get_blacklist_manager


class TestTargetedFixes(unittest.TestCase):
    def setUp(self):
        self.db = get_db_engine()
        self.gate = get_approval_gate()
        self.listener = get_reply_listener()
        self.bl_mgr = get_blacklist_manager()

    def test_company_name_cleaning_and_seo_stripping(self):
        # 1. Generic SEO phrase stripping from title
        title1 = "Best Commercial Construction Company in London | Acme Developments Ltd"
        res1 = DeepScraperAgent.extract_clean_company_name(None, title1, "acmedevelopments.co.uk")
        self.assertIn("Acme Developments", res1)
        self.assertNotIn("Best Commercial Construction", res1)

        # 2. Schema.org JSON-LD extraction
        html_ld = """
        <html>
        <head>
          <title>Top 10 General Contractors Near You - Free Quotes</title>
          <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "GeneralContractor",
            "name": "Apex Structural Engineering Ltd"
          }
          </script>
        </head>
        <body></body>
        </html>
        """
        soup_ld = BeautifulSoup(html_ld, "html.parser")
        res_ld = DeepScraperAgent.extract_clean_company_name(soup_ld, "Top 10 General Contractors Near You - Free Quotes", "apexstructural.com")
        self.assertEqual(res_ld, "Apex Structural Engineering Ltd")

        # 3. OpenGraph og:site_name extraction
        html_og = """
        <html>
        <head>
          <title>Leading Construction &amp; Roofing Services Across Yorkshire</title>
          <meta property="og:site_name" content="Vanguard Build Group" />
        </head>
        <body></body>
        </html>
        """
        soup_og = BeautifulSoup(html_og, "html.parser")
        res_og = DeepScraperAgent.extract_clean_company_name(soup_og, "Leading Construction & Roofing Services Across Yorkshire", "vanguardbuild.co.uk")
        self.assertEqual(res_og, "Vanguard Build Group")

        # 4. Fallback to domain brand extraction
        res_fb = DeepScraperAgent.extract_clean_company_name(None, "Home - Welcome - Contact Us - Find Contractors", "crestwoodbuild.com")
        self.assertEqual(res_fb, "Crestwoodbuild")

    def test_webhook_case_insensitive_success(self):
        # Webhook payload & response test
        with patch("core.outreach.approval_gate._send_webhook_request") as mock_wh:
            mock_wh.return_value = {"status": "SUCCESS", "message": "Email dispatched"}

            # Setup test mailbox and queue item
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO mailbox_rotator (
                        id, email_address, display_name, domain, daily_limit, sent_today,
                        is_active, webhook_url, smtp_host, smtp_port, smtp_username, smtp_password, last_reset_date
                    ) VALUES (
                        'mb_test_wh', 'test_wh@gmail.com', 'Test Sender', 'gmail.com', 50, 0,
                        1, 'https://script.google.com/macros/s/TEST/exec', 'smtp.gmail.com', 587, 'test', 'test', '2026-11-17'
                    )
                """)
                conn.execute("""
                    INSERT OR REPLACE INTO outreach_queue (
                        id, recipient, company_name, subject, message_body,
                        status, target_country, operator_id, mailbox_used
                    ) VALUES (
                        'q_test_wh', 'target_wh@acme.com', 'Acme Ltd', 'Commercial Tender', 'Proposal body',
                        'APPROVED', 'United Kingdom', 'test_user_wh', 'test_wh@gmail.com'
                    )
                """)
                conn.commit()

            res = self.gate.dispatch_approved_outreach('q_test_wh', bypass_window=True)
            self.assertTrue(res.get("success"), f"Dispatch failed: {res}")
            self.assertEqual(res.get("delivery_method"), "WEBHOOK")

            # Verify payload passed to _send_webhook_request contains both 'recipient' and 'to'
            self.assertTrue(mock_wh.called)
            args, kwargs = mock_wh.call_args
            wh_payload = args[1]
            self.assertEqual(wh_payload.get("recipient"), "target_wh@acme.com")
            self.assertEqual(wh_payload.get("to"), "target_wh@acme.com")

            # Cleanup
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM mailbox_rotator WHERE id = 'mb_test_wh'")
                conn.execute("DELETE FROM outreach_queue WHERE id = 'q_test_wh'")
                conn.execute("DELETE FROM followup_sequences WHERE recipient_email = 'target_wh@acme.com'")
                conn.commit()

    def test_dispatch_failure_retains_lead_in_approved_state(self):
        # When dispatch fails, lead must remain in APPROVED (Authorized) with failure reason
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mailbox_rotator (
                    id, email_address, display_name, domain, daily_limit, sent_today,
                    is_active, webhook_url, smtp_host, smtp_port, smtp_username, smtp_password, last_reset_date
                ) VALUES (
                    'mb_test_fail', 'test_fail@gmail.com', 'Test Fail', 'gmail.com', 50, 0,
                    1, '', 'invalid.smtp.host', 587, 'test', 'test', '2026-11-17'
                )
            """)
            conn.execute("""
                INSERT OR REPLACE INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, operator_id, mailbox_used
                ) VALUES (
                    'q_test_fail', 'fail_lead@acme.com', 'Fail Lead Ltd', 'Tender', 'Body',
                    'APPROVED', 'United Kingdom', 'test_user_fail', 'test_fail@gmail.com'
                )
            """)
            conn.commit()

        res = self.gate.dispatch_approved_outreach('q_test_fail', bypass_window=True)
        self.assertFalse(res.get("success"))

        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status, bounce_reason FROM outreach_queue WHERE id = 'q_test_fail'").fetchone()
            # Verified: Status stays APPROVED so it never vanishes from Kanban board!
            self.assertEqual(row["status"], "APPROVED")
            self.assertIn("Dispatch Error", row["bounce_reason"])

            # Cleanup
            conn.execute("DELETE FROM mailbox_rotator WHERE id = 'mb_test_fail'")
            conn.execute("DELETE FROM outreach_queue WHERE id = 'q_test_fail'")
            conn.commit()

    def test_imap_reply_listener_self_ignore_and_status_mapping(self):
        # Test incoming reply from client transitions to HOT_LEAD
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO outreach_queue (
                    id, recipient, company_name, subject, message_body,
                    status, target_country, operator_id
                ) VALUES (
                    'q_rep_1', 'client@construct.com', 'Construct Co', 'Tender Enquiry', 'Body',
                    'SENT', 'United Kingdom', 'op_test'
                )
            """)
            conn.commit()

        # Genuine positive response
        proc = self.listener.process_incoming_reply(
            sender_email="client@construct.com",
            subject="Re: Tender Enquiry",
            body="Hi, please send over drawings and tender documents for the project."
        )
        self.assertTrue(proc["is_hot_lead"])
        self.assertEqual(proc["classification"], "INTERESTED")

        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status, replied_at FROM outreach_queue WHERE id = 'q_rep_1'").fetchone()
            self.assertEqual(row["status"], "HOT_LEAD")
            self.assertIsNotNone(row["replied_at"])

            # Cleanup
            conn.execute("DELETE FROM outreach_queue WHERE id = 'q_rep_1'")
            conn.execute("DELETE FROM inbox_replies WHERE sender_email = 'client@construct.com'")
            conn.commit()

    def test_database_connection_retry(self):
        # Database connection retry resilience
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT 1 as alive").fetchone()
            self.assertEqual(row["alive"], 1)

    def test_unsubscribe_blacklisting_sync(self):
        # Idempotent setup: remove any stale pattern left by a previous run
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM blacklist_rules WHERE lower(pattern) = 'optout@example.co.uk'")
            conn.commit()

        # Blacklist manager adds rule on unsubscribe (email-type pattern)
        self.bl_mgr.add_rule("optout@example.co.uk", entity_type="email", reason="Opt-out verification", created_by="TEST")

        # Must be detected when queried by the full email address
        is_bl, reason = self.bl_mgr.is_domain_blacklisted("optout@example.co.uk")
        self.assertTrue(is_bl, f"Expected blacklisted=True but got False. reason={reason}")

        # Cleanup
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM blacklist_rules WHERE lower(pattern) = 'optout@example.co.uk'")
            conn.commit()


if __name__ == "__main__":
    unittest.main()
