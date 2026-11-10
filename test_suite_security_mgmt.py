"""
H.Huddair's Nexus-Pulse - Level 2
User & Security Management Suite Automated Test Suite
Validates:
  1. Dynamic Admin Profile Control (Username, Email, Bcrypt Password Re-Hashing)
  2. Role-Based Operator Management (Create, Edit, Toggle Revocation, Reset Password, Device Lock)
  3. License & Expiry Control Module (Subscription Extension, Daily Quotas)
"""

import os
import sys
import uuid
import unittest
from pathlib import Path
import bcrypt

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from auth.user_manager import get_user_manager
from auth.jwt_handler import hash_password, verify_password
from security.machine_fingerprint import generate_machine_fingerprint
from database.db_engine import get_db_engine


class TestUserAndSecurityManagement(unittest.TestCase):

    def setUp(self):
        self.um = get_user_manager()
        self.um.seed_default_users()  # Ensure test fixtures exist for Level 2 verification tests
        self.db = get_db_engine()
        self.host_device = generate_machine_fingerprint()["machine_id"]

    # -------------------------------------------------------------
    # 1. Dynamic Admin Profile Control & Bcrypt Re-Hashing
    # -------------------------------------------------------------
    def test_01_dynamic_admin_profile_and_bcrypt(self):
        """Admin can change Username, Email, and Password with Bcrypt re-hashing."""
        # Find Admin ID
        with self.db.get_connection() as conn:
            admin_row = conn.execute("SELECT id, username, password_hash FROM users WHERE username = 'h.huddair'").fetchone()
            self.assertIsNotNone(admin_row, "Admin account 'h.huddair' must exist")
            admin_id = admin_row["id"]

        # 1. Update Profile Information & Re-hash Password
        test_new_pass = "HuddairNewMaster2026!"
        update_res = self.um.update_admin_profile(
            admin_id=admin_id,
            new_username="h.huddair",
            new_email="executive.huddair@nexus-pulse.io",
            new_full_name="H.Huddair (Executive Commander)",
            current_password="NexusPulse2026!",
            new_password=test_new_pass
        )

        self.assertTrue(update_res["success"])
        self.assertIn("Bcrypt", update_res["message"])

        # 2. Verify Database Persistence & Bcrypt Signature ($2b$)
        with self.db.get_connection() as conn:
            updated_row = conn.execute("SELECT email, full_name, password_hash FROM users WHERE id = ?", (admin_id,)).fetchone()
            self.assertEqual(updated_row["email"], "executive.huddair@nexus-pulse.io")
            self.assertEqual(updated_row["full_name"], "H.Huddair (Executive Commander)")
            # Verify Bcrypt prefix
            self.assertTrue(
                updated_row["password_hash"].startswith("$2b$") or updated_row["password_hash"].startswith("$2a$"),
                "Password must be hashed with standard Bcrypt ($2b$ or $2a$)"
            )
            # Verify bcrypt checkpw directly
            self.assertTrue(
                bcrypt.checkpw(test_new_pass.encode("utf-8"), updated_row["password_hash"].encode("utf-8")),
                "Bcrypt direct signature check must succeed"
            )

        # 3. Test Authentication with New Password
        auth_res = self.um.authenticate_user("h.huddair", test_new_pass)
        self.assertIsNotNone(auth_res)
        self.assertEqual(auth_res["user"]["email"], "executive.huddair@nexus-pulse.io")

        # 4. Revert to standard default password for convenience in pair programming
        self.um.update_admin_profile(
            admin_id=admin_id,
            current_password=test_new_pass,
            new_password="NexusPulse2026!"
        )

    # -------------------------------------------------------------
    # 2. Role-Based User Management Portal
    # -------------------------------------------------------------
    def test_02_operator_management_portal(self):
        """Admin creates, revokes, resets, and locks operator accounts."""
        unique_id = uuid.uuid4().hex[:6]
        op_username = f"op_{unique_id}"
        op_pass = "OpPass123!"
        op_email = f"operator_{unique_id}@nexus-pulse.io"

        # 1. Create New Operator Account
        create_res = self.um.create_operator_account(
            username=op_username,
            password=op_pass,
            full_name=f"Field Operator {unique_id}",
            email=op_email,
            device_lock_id=self.host_device,
            device_lock_enabled=True,
            expiry_days=60,
            daily_scrape_quota=300,
            daily_send_quota=60
        )

        self.assertTrue(create_res["success"])
        op_id = create_res["user_id"]
        self.assertIn("NEXUS-LIC", create_res["license_key"])

        # 2. Operator Authenticates Successfully on Authorized Device
        auth_success = self.um.authenticate_user(op_username, op_pass, client_machine_id=self.host_device)
        self.assertIsNotNone(auth_success)
        self.assertEqual(auth_success["user"]["role"], "operator")

        # 3. Test Device Lock Enforcement: Login with Rogue Machine ID must be blocked
        with self.assertRaises(PermissionError) as ctx:
            self.um.authenticate_user(op_username, op_pass, client_machine_id="ROGUE-DEVICE-UNAUTHORIZED-9999")
        self.assertIn("DEVICE_LOCK_ALERT", str(ctx.exception))

        # 4. Test Single Toggle Switch: Revoke Operator Access
        revoke_res = self.um.toggle_user_active_status(op_id)
        self.assertTrue(revoke_res["success"])
        self.assertEqual(revoke_res["is_active"], 0)
        self.assertEqual(revoke_res["status_label"], "REVOKED")

        # 5. Revoked Operator Login must be rejected
        with self.assertRaises(PermissionError) as ctx:
            self.um.authenticate_user(op_username, op_pass, client_machine_id=self.host_device)
        self.assertIn("ACCOUNT_REVOKED", str(ctx.exception))

        # 6. Re-Activate Operator
        activate_res = self.um.toggle_user_active_status(op_id)
        self.assertEqual(activate_res["is_active"], 1)

        # 7. Admin Resets Operator Password directly with Bcrypt
        new_op_pass = "BrandNewBcryptPass2026!"
        reset_res = self.um.reset_operator_password(op_id, new_op_pass)
        self.assertTrue(reset_res["success"])

        # Operator can log in with new password
        auth_new = self.um.authenticate_user(op_username, new_op_pass, client_machine_id=self.host_device)
        self.assertIsNotNone(auth_new)

    # -------------------------------------------------------------
    # 3. License & Expiry Control Module
    # -------------------------------------------------------------
    def test_03_license_and_quota_management(self):
        """Admin can issue, modify, and extend subscription expiry and operational quotas."""
        unique_id = uuid.uuid4().hex[:6]
        op_username = f"sub_{unique_id}"
        create_res = self.um.create_operator_account(
            username=op_username,
            password="SubPass2026!",
            full_name=f"Subscriber {unique_id}",
            email=f"sub_{unique_id}@nexus-pulse.io",
            expiry_days=10,
            daily_scrape_quota=100,
            daily_send_quota=25
        )
        user_id = create_res["user_id"]

        # Modify quotas & extend subscription by +90 days
        mod_res = self.um.modify_license_and_quotas(
            user_id=user_id,
            extend_days=90,
            daily_scrape_quota=750,
            daily_send_quota=120
        )

        self.assertTrue(mod_res["success"])
        self.assertEqual(mod_res["daily_scrape_quota"], 750)
        self.assertEqual(mod_res["daily_send_quota"], 120)

        # Verify Database
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT daily_scrape_quota, daily_send_quota, license_key FROM users WHERE id = ?", (user_id,)).fetchone()
            self.assertEqual(row["daily_scrape_quota"], 750)
            self.assertEqual(row["daily_send_quota"], 120)
            self.assertTrue(row["license_key"].startswith("NEXUS-LIC"))

    # -------------------------------------------------------------
    # 4. Fresh Database Reset & Clean State Admin Initialization
    # -------------------------------------------------------------
    def test_04_fresh_database_reset_and_first_run_admin_initialization(self):
        """Tests complete database wipe/purge and first-run brand-new Admin registration."""
        # 1. Purge all database tables
        purged = self.um.purge_all_data()
        self.assertIn("users", purged)
        self.assertIn("vault_leads", purged)
        self.assertIn("outreach_queue", purged)
        self.assertIn("operator_sessions", purged)

        # 2. Verify Database is in 100% clean/fresh state
        self.assertFalse(self.um.has_admin(), "has_admin must return False after purge")
        with self.db.get_connection() as conn:
            u_cnt = conn.execute("SELECT count(*) as cnt FROM users").fetchone()["cnt"]
            self.assertEqual(u_cnt, 0, "Users table must have 0 rows after purge")
            l_cnt = conn.execute("SELECT count(*) as cnt FROM vault_leads").fetchone()["cnt"]
            self.assertEqual(l_cnt, 0, "Vault leads table must have 0 rows after purge")
            q_cnt = conn.execute("SELECT count(*) as cnt FROM outreach_queue").fetchone()["cnt"]
            self.assertEqual(q_cnt, 0, "Outreach queue table must have 0 rows after purge")

        # 3. Initialize brand-new Admin account on fresh database
        init_res = self.um.initialize_admin(
            username="prod_master_admin",
            password="ProductionVault2026!",
            full_name="Executive Director",
            email="director@enterprise-vault.io"
        )
        self.assertTrue(init_res["success"])
        self.assertEqual(init_res["user"]["username"], "prod_master_admin")
        self.assertEqual(init_res["user"]["role"], "admin")
        self.assertTrue(len(init_res["token"]) > 20)

        # 4. has_admin must now return True
        self.assertTrue(self.um.has_admin())

        # 5. Subsequent attempts to re-initialize admin must be blocked
        with self.assertRaises(PermissionError):
            self.um.initialize_admin(
                username="hacker_admin",
                password="HackerPass123!",
                full_name="Impostor"
            )

        # 6. Authenticate freshly registered Admin
        auth_res = self.um.authenticate_user("prod_master_admin", "ProductionVault2026!")
        self.assertIsNotNone(auth_res)
        self.assertEqual(auth_res["user"]["role"], "admin")

        # Clean up by re-seeding default users for other tests
        self.um.seed_default_users()


if __name__ == "__main__":
    unittest.main(verbosity=2)
