"""
H.Huddair's Nexus-Pulse - Level 2
Comprehensive Verification Test Suite
Validates all Technical Requirements for Level 2 Enterprise Build:
  1. Desktop App Launcher & Shortcut
  2. Animated High-Tech Login & RBAC (Admin vs Operator)
  3. Human Approval Gate
  4. Backup Web-Form Outreach
  5. Time-Zone Smart Scheduler & Inbox Rotator
  6. IMAP Reply Listener, Hot Lead Alerts & GDPR Blacklisting
  7. Autonomous 7-Day Follow-Up Engine
  8. Visual Kanban CRM & Cyber-Pulse Agent Icon States
"""

import os
import sys
import uuid
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from auth.jwt_handler import hash_password, verify_password, create_access_token, decode_access_token
from auth.user_manager import get_user_manager
from core.outreach.approval_gate import get_approval_gate
from core.outreach.scheduler import get_scheduler
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.reply_listener import get_reply_listener, ReplyClassifier
from core.agents.webform_agent import BackupWebFormAgent
from core.agents.followup_engine import get_followup_engine
from database.db_engine import get_db_engine


class TestNexusPulseLevel2(unittest.TestCase):

    def setUp(self):
        self.root_dir = PROJECT_ROOT
        self.db = get_db_engine()
        self.user_manager = get_user_manager()
        self.user_manager.seed_default_users()  # Ensure test fixtures exist for Level 2 verification tests
        self.gate = get_approval_gate()
        self.scheduler = get_scheduler()
        self.rotator = get_inbox_rotator()
        self.reply_listener = get_reply_listener()
        self.followup_engine = get_followup_engine()

    # -------------------------------------------------------------
    # 1. Desktop App Launcher & Shortcut Verification
    # -------------------------------------------------------------
    def test_01_launcher_and_desktop_shortcut(self):
        """Verifies Launch_Nexus_Pulse.bat and Desktop shortcut existence."""
        bat_launcher = self.root_dir / "Launch_Nexus_Pulse.bat"
        self.assertTrue(bat_launcher.exists(), "Launch_Nexus_Pulse.bat must exist in Desktop/rabbi")

        vbs_launcher = self.root_dir / "Launch_Nexus_Pulse.vbs"
        self.assertTrue(vbs_launcher.exists(), "Launch_Nexus_Pulse.vbs must exist in Desktop/rabbi")

        run_server = self.root_dir / "run_server.py"
        self.assertTrue(run_server.exists(), "run_server.py must exist in Desktop/rabbi")

        desktop_shortcut = Path(os.environ.get("USERPROFILE", "C:/Users/STONE")) / "Desktop" / "H.Huddair Nexus-Pulse.lnk"
        self.assertTrue(desktop_shortcut.exists(), "Desktop shortcut 'H.Huddair Nexus-Pulse.lnk' must exist on Desktop")
        self.assertGreater(desktop_shortcut.stat().st_size, 100, "Shortcut file must not be empty")

    # -------------------------------------------------------------
    # 2. Animated High-Tech Login & RBAC
    # -------------------------------------------------------------
    def test_02_auth_and_role_management(self):
        """Tests password hashing, JWT creation/validation, and Admin vs Operator RBAC."""
        # Test Password Hashing
        plain = "SecretPassword2026!"
        h = hash_password(plain)
        self.assertNotEqual(plain, h)
        self.assertTrue(verify_password(plain, h))
        self.assertFalse(verify_password("WrongPassword", h))

        # Test JWT Creation and Decoding
        token = create_access_token(
            user_id="user-123",
            username="h.huddair",
            role="admin",
            full_name="H.Huddair"
        )
        self.assertIsInstance(token, str)
        payload = decode_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["username"], "h.huddair")
        self.assertEqual(payload["role"], "admin")

        # Test Expired / Tampered Token
        tampered = token[:-4] + "abcd"
        self.assertIsNone(decode_access_token(tampered))

        # Test Master Admin Login (H.Huddair)
        admin_auth = self.user_manager.authenticate_user("h.huddair", "NexusPulse2026!")
        self.assertIsNotNone(admin_auth)
        self.assertEqual(admin_auth["user"]["role"], "admin")

        # Test Operator Login (Restricted)
        op_auth = self.user_manager.authenticate_user("operator", "Operator2026!")
        self.assertIsNotNone(op_auth)
        self.assertEqual(op_auth["user"]["role"], "operator")

    # -------------------------------------------------------------
    # 3. Human Approval Gate
    # -------------------------------------------------------------
    def test_03_human_approval_gate(self):
        """Tests authorization hold: no outreach dispatched without approval from H.Huddair."""
        mock_lead_id = f"lead-{uuid.uuid4().hex[:6]}"
        q_res = self.gate.queue_outreach(
            lead_id=mock_lead_id,
            company_name="Hochbau Test GmbH",
            recipient="kalkulation@hochbau-test.de",
            country="Germany",
            niche="Commercial Construction",
            channel="EMAIL"
        )

        q_id = q_res["queue_id"]
        self.assertEqual(q_res["status"], "PENDING_APPROVAL")
        self.assertIn("Human Approval Gate", q_res["hold_message"])

        # Attempting dispatch while in PENDING_APPROVAL must raise PermissionError
        with self.assertRaises(PermissionError):
            self.gate.dispatch_approved_outreach(q_id)

        # Admin Authorizes Item with edited subject
        custom_subj = "Authorized Tender Package Submittal // Hochbau Test"
        app_res = self.gate.approve_outreach_item(
            queue_id=q_id,
            approver="h.huddair",
            edited_subject=custom_subj
        )
        self.assertTrue(app_res["success"])
        self.assertEqual(app_res["status"], "APPROVED")

        # Now dispatch succeeds
        dispatch_res = self.gate.dispatch_approved_outreach(q_id)
        self.assertTrue(dispatch_res["success"])
        self.assertEqual(dispatch_res["status"], "SENT")
        self.assertIn("@", dispatch_res["dispatched_via"])

    # -------------------------------------------------------------
    # 4. Backup Web-Form Outreach
    # -------------------------------------------------------------
    def test_04_backup_web_form_outreach(self):
        """Tests fallback formatting for websites without direct email."""
        mock_comp = "Modern Glass Facades GmbH"
        mock_url = "https://www.modern-glass-facades.de"

        payload = BackupWebFormAgent.format_web_form_payload(
            company_name=mock_comp,
            website_url=mock_url,
            niche="Architectural Glazing",
            country="Germany"
        )

        self.assertEqual(payload["channel"], "WEB_FORM")
        self.assertIn("contact", payload["form_url"])
        self.assertIn("name", payload["fields"])
        self.assertIn("email", payload["fields"])
        self.assertIn("message", payload["fields"])
        self.assertIn("H.Huddair", payload["fields"]["name"])

        # Test queueing web form outreach into Human Approval Gate
        gate_res = BackupWebFormAgent.queue_web_form_in_approval_gate(
            lead_id=str(uuid.uuid4()),
            company_name=mock_comp,
            website_url=mock_url,
            niche="Architectural Glazing",
            country="Germany"
        )
        self.assertTrue(gate_res["success"])
        self.assertEqual(gate_res["status"], "PENDING_APPROVAL")
        self.assertEqual(gate_res["channel"], "WEB_FORM")

    # -------------------------------------------------------------
    # 5. Time-Zone Smart Scheduler & Inbox Rotator
    # -------------------------------------------------------------
    def test_05_timezone_scheduler_and_inbox_rotator(self):
        """Tests 9-11 AM office hours calculation and 40-50/day mailbox limits."""
        # Timezone scheduler
        tz_de = self.scheduler.get_target_local_time("Germany")
        self.assertEqual(tz_de["timezone_code"], "CET")
        self.assertIn("current_local_hour", tz_de)
        self.assertIsInstance(tz_de["is_in_send_window"], bool)

        tz_uk = self.scheduler.get_target_local_time("United Kingdom")
        self.assertEqual(tz_uk["timezone_code"], "GMT")

        # Inbox Rotator daily quota
        all_mb = self.rotator.get_all_mailboxes_status()
        self.assertGreater(len(all_mb), 0)
        first_mb = all_mb[0]
        self.assertLessEqual(first_mb["daily_limit"], 50)
        self.assertGreaterEqual(first_mb["daily_limit"], 40)

        # Available mailbox selection
        next_mb = self.rotator.get_next_available_mailbox()
        self.assertIsNotNone(next_mb)
        self.assertLess(next_mb["sent_today"], next_mb["daily_limit"])

    # -------------------------------------------------------------
    # 6. IMAP Reply Listener, AI Classifier & GDPR DNC
    # -------------------------------------------------------------
    def test_06_reply_listener_and_hot_leads(self):
        """Tests response classification (Interested vs Unsubscribe), Hot Lead alerts, and DNC."""
        # 1. Hot Lead / Interested reply
        hot_reply = self.reply_listener.process_incoming_reply(
            sender_email="estimating@leading-contractor.de",
            subject="Re: Tender Submissions",
            body="Thank you H.Huddair, please send more info and tender docs. What are your rates?",
            company_name="Leading Contractor"
        )
        self.assertEqual(hot_reply["classification"], "INTERESTED")
        self.assertTrue(hot_reply["is_hot_lead"])
        self.assertIn("H.Huddair", hot_reply["ai_suggested_reply"])

        # Check Hot Lead alerts query
        hot_alerts = self.reply_listener.get_hot_lead_alerts()
        self.assertTrue(any(a["sender_email"] == "estimating@leading-contractor.de" for a in hot_alerts))

        # 2. Unsubscribe / DNC reply
        optout_email = "optout@blacklisted-contractor.de"
        dnc_reply = self.reply_listener.process_incoming_reply(
            sender_email=optout_email,
            subject="Unsubscribe",
            body="Please unsubscribe and remove us from your list. GDPR DNC."
        )
        self.assertEqual(dnc_reply["classification"], "UNSUBSCRIBE")
        self.assertTrue(dnc_reply["blacklisted"])

        # Verify permanent blacklisting
        self.assertTrue(self.reply_listener.is_blacklisted(optout_email))
        self.assertTrue(self.reply_listener.is_blacklisted("blacklisted-contractor.de"))

    # -------------------------------------------------------------
    # 7. Autonomous 7-Day Follow-Up Engine
    # -------------------------------------------------------------
    def test_07_autonomous_followup_engine(self):
        """Tests automated follow-up sequence generation after 7 days."""
        mock_seq_id = str(uuid.uuid4())
        mock_lead_id = str(uuid.uuid4())
        recipient = f"bids-{uuid.uuid4().hex[:6]}@construction-firm.com"

        # Insert a simulated sequence sent 8 days ago
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO followup_sequences (
                    id, lead_id, initial_outreach_id, recipient_email,
                    initial_sent_at, followup_due_at, status
                ) VALUES (?, ?, ?, ?, datetime(CURRENT_TIMESTAMP, '-8 days'), datetime(CURRENT_TIMESTAMP, '-1 day'), 'PENDING')
            """, (mock_seq_id, mock_lead_id, "outreach-initial", recipient))
            conn.commit()

        # Trigger follow-up scanner
        scan_res = self.followup_engine.scan_and_trigger_due_followups(force_all_pending=False)
        self.assertGreater(scan_res["followups_triggered"], 0)
        self.assertTrue(any(item["recipient"] == recipient for item in scan_res["triggered_items"]))

    # -------------------------------------------------------------
    # 8. Visual Kanban CRM & Cyber-Pulse States
    # -------------------------------------------------------------
    def test_08_kanban_and_cyber_pulse_states(self):
        """Verifies Kanban data mapping and agent icon state models."""
        from core.models import AgentIconState, KanbanStage
        self.assertEqual(AgentIconState.IDLE.value, "IDLE")
        self.assertEqual(AgentIconState.HUNTING.value, "HUNTING")
        self.assertEqual(AgentIconState.HOT_ALERT.value, "HOT_ALERT")
        self.assertEqual(KanbanStage.HOT_LEAD.value, "HOT_LEAD")
        self.assertEqual(KanbanStage.PENDING_APPROVAL.value, "PENDING_APPROVAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
