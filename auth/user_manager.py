"""
H.Huddair's Nexus-Pulse - Level 2
User Management, Security Suite & Role-Based Access Control
Handles:
  1. Dynamic Admin Profile Control (Username, Email, Bcrypt Password Re-Hashing)
  2. Role-Based Operator Management (Create, Edit, Revoke/Enable Toggle, Reset Password)
  3. Device Lock & Session Tracking (Hardware GUID Binding)
  4. License & Quota Allocation (Daily Scrape/Send Caps, Expiry Extension)
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from database.db_engine import get_db_engine
from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import generate_license_key
from .jwt_handler import hash_password, verify_password, create_access_token


class UserManager:
    """Enterprise User, Security & License Management Controller."""

    def __init__(self):
        self.db = get_db_engine()
        # NOTE: Default operators and demo credentials are NOT pre-populated on startup.
        # This guarantees a clean, fresh state for production first-run admin initialization.

    def has_admin(self) -> bool:
        """Checks if an administrator account has already been registered."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT count(*) as cnt FROM users WHERE role = 'admin'").fetchone()
            return bool(row and row["cnt"] > 0)

    def initialize_admin(
        self,
        username: str,
        password: str,
        full_name: str,
        email: Optional[str] = None,
        device_lock_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers the initial Master Admin account on first run.
        Allowed ONLY if no admin accounts currently exist in the database.
        """
        clean_user = username.strip()
        if not clean_user:
            raise ValueError("Administrator username is required.")
        if len(clean_user) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if len(password) < 6:
            raise ValueError("Passphrase must be at least 6 characters.")
        if not full_name or not full_name.strip():
            raise ValueError("Full name is required.")

        with self.db.get_connection() as conn:
            admin_count = conn.execute("SELECT count(*) as cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
            if admin_count > 0:
                raise PermissionError("SETUP_COMPLETED: An administrator account has already been initialized.")

            existing = conn.execute("SELECT id FROM users WHERE lower(username) = lower(?)", (clean_user,)).fetchone()
            if existing:
                raise ValueError(f"Username '{clean_user}' already exists.")

            admin_id = str(uuid.uuid4())
            pass_hash = hash_password(password)
            target_device = device_lock_id or generate_machine_fingerprint()["machine_id"]
            admin_email = email.strip().lower() if (email and email.strip()) else f"{clean_user.lower()}@nexus-pulse.io"

            admin_license = generate_license_key(
                machine_id=target_device,
                client_name=f"{full_name.strip()} (Master Admin)",
                tier="Level-2-Enterprise"
            )

            conn.execute("""
                INSERT INTO users (
                    id, username, password_hash, role, full_name, email,
                    is_active, device_lock_id, device_lock_enabled, expiry_date,
                    daily_scrape_quota, daily_send_quota, license_key
                ) VALUES (?, ?, ?, 'admin', ?, ?, 1, ?, 1, '2099-12-31 23:59:59', 5000, 1000, ?)
            """, (
                admin_id, clean_user, pass_hash, full_name.strip(), admin_email,
                target_device, admin_license
            ))

            try:
                conn.execute("""
                    INSERT INTO operator_sessions (user_id, username, action, detail, device_id)
                    VALUES (?, ?, 'INITIAL_SETUP', 'First-run master administrator initialized', ?)
                """, (admin_id, clean_user, target_device))
            except Exception:
                pass

            conn.commit()

        token = create_access_token(
            user_id=admin_id,
            username=clean_user,
            role="admin",
            full_name=full_name.strip(),
            device_id=target_device
        )

        return {
            "success": True,
            "token": token,
            "user": {
                "id": admin_id,
                "username": clean_user,
                "role": "admin",
                "full_name": full_name.strip(),
                "email": admin_email,
                "device_lock_id": target_device,
                "daily_scrape_quota": 5000,
                "daily_send_quota": 1000,
                "expiry_date": "2099-12-31 23:59:59"
            }
        }

    def register_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str = "operator",
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registers a new user (admin on fresh install or operator)."""
        if role == "admin" and not self.has_admin():
            return self.initialize_admin(username, password, full_name, email)
        return self.create_operator_account(
            username=username,
            password=password,
            full_name=full_name,
            email=email or f"{username.strip().lower()}@nexus-pulse.io"
        )

    def purge_all_data(self) -> Dict[str, int]:
        """
        Wipes all users, leads, audit logs, queues, and histories.
        Resets the database to a completely clean fresh state for production.
        """
        counts = {}
        with self.db.get_connection() as conn:
            tables_to_purge = [
                "users",
                "vault_leads",
                "dedup_registry",
                "hygiene_audit_log",
                "outreach_queue",
                "inbox_replies",
                "followup_sequences",
                "operator_sessions",
                "dnc_blacklist"
            ]
            for tbl in tables_to_purge:
                cnt = conn.execute(f"SELECT count(*) as cnt FROM {tbl}").fetchone()["cnt"]
                counts[tbl] = cnt
                conn.execute(f"DELETE FROM {tbl};")

            conn.execute("UPDATE mailbox_rotator SET sent_today = 0;")
            conn.commit()
            conn.execute("VACUUM;")
        return counts

    def seed_default_users(self) -> None:
        """Seeds master Admin and default Operator accounts (for automated verification tests)."""
        fp = generate_machine_fingerprint()
        host_id = fp["machine_id"]

        with self.db.get_connection() as conn:
            # 1. Master Admin (H.Huddair)
            admin_row = conn.execute("SELECT id, password_hash FROM users WHERE username = 'h.huddair'").fetchone()
            if not admin_row:
                admin_id = str(uuid.uuid4())
                admin_pass_hash = hash_password("NexusPulse2026!")
                admin_license = generate_license_key(host_id, client_name="H.Huddair (Master Admin)", tier="Level-2-Enterprise")
                conn.execute("""
                    INSERT INTO users (
                        id, username, password_hash, role, full_name, email,
                        is_active, device_lock_id, device_lock_enabled, expiry_date,
                        daily_scrape_quota, daily_send_quota, license_key
                    ) VALUES (?, 'h.huddair', ?, 'admin', 'H.Huddair (Master Admin)', 'h.huddair@nexus-pulse.io',
                             1, ?, 1, '2099-12-31 23:59:59', 5000, 1000, ?)
                """, (admin_id, admin_pass_hash, host_id, admin_license))

            # 2. Operator (Field User)
            op_row = conn.execute("SELECT id, password_hash FROM users WHERE username = 'operator'").fetchone()
            if not op_row:
                op_id = str(uuid.uuid4())
                op_pass_hash = hash_password("Operator2026!")
                op_expiry = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
                op_license = generate_license_key(host_id, client_name="Nexus Field Operator", tier="Level-2-Operator", days_valid=90)
                conn.execute("""
                    INSERT INTO users (
                        id, username, password_hash, role, full_name, email,
                        is_active, device_lock_id, device_lock_enabled, expiry_date,
                        daily_scrape_quota, daily_send_quota, license_key
                    ) VALUES (?, 'operator', ?, 'operator', 'Nexus Field Operator', 'operator@nexus-pulse.io',
                             1, ?, 1, ?, 200, 50, ?)
                """, (op_id, op_pass_hash, host_id, op_expiry, op_license))

            conn.commit()

    def authenticate_user(
        self,
        username: str,
        password: str,
        client_machine_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Validates credentials, checks account active status, expiry, device lock,
        and generates authenticated JWT session token.
        """
        clean_user = username.strip().lower()
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT id, username, password_hash, role, full_name, email,
                       is_active, device_lock_id, device_lock_enabled, expiry_date,
                       daily_scrape_quota, daily_send_quota, license_key
                FROM users WHERE lower(username) = ?
            """, (clean_user,)).fetchone()

            if not row:
                return None

            # 1. Verify Password with Bcrypt
            if not verify_password(password, row["password_hash"]):
                return None

            # 2. Check if Account Revoked / Inactive
            if row["is_active"] != 1:
                raise PermissionError("ACCOUNT_REVOKED: Your account access has been revoked by H.Huddair.")

            # 3. Check Account Expiry
            if row["expiry_date"]:
                try:
                    exp_dt = datetime.fromisoformat(row["expiry_date"].replace(" ", "T"))
                    if datetime.now(timezone.utc).replace(tzinfo=None) > exp_dt:
                        raise PermissionError(f"ACCOUNT_EXPIRED: Subscription expired on {row['expiry_date']}. Contact H.Huddair.")
                except ValueError:
                    pass

            # 4. Enforce Device Lock
            host_device = client_machine_id or generate_machine_fingerprint()["machine_id"]
            if row["device_lock_enabled"] == 1:
                registered_device = row["device_lock_id"]
                if not registered_device:
                    # Bind on first login
                    conn.execute("UPDATE users SET device_lock_id = ? WHERE id = ?", (host_device, row["id"]))
                elif registered_device.strip().upper() != host_device.strip().upper():
                    raise PermissionError(
                        f"DEVICE_LOCK_ALERT: Account is locked to device '{registered_device}', "
                        f"but host fingerprint is '{host_device}'. Execution blocked."
                    )

            # Update login telemetry
            conn.execute("""
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP, last_login_device = ?
                WHERE id = ?
            """, (host_device, row["id"]))
            conn.commit()

            token = create_access_token(
                user_id=row["id"],
                username=row["username"],
                role=row["role"],
                full_name=row["full_name"],
                device_id=host_device
            )

            return {
                "token": token,
                "user": {
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"],
                    "full_name": row["full_name"],
                    "email": row["email"],
                    "device_lock_id": row["device_lock_id"] or host_device,
                    "daily_scrape_quota": row["daily_scrape_quota"],
                    "daily_send_quota": row["daily_send_quota"],
                    "expiry_date": row["expiry_date"]
                }
            }

    # -------------------------------------------------------------
    # REQUIREMENT 1: Dynamic Admin Profile Control
    # -------------------------------------------------------------
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches sanitized user profile."""
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT id, username, role, full_name, email, is_active,
                       device_lock_id, device_lock_enabled, expiry_date,
                       daily_scrape_quota, daily_send_quota, license_key,
                       created_at, last_login, last_login_device
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def update_admin_profile(
        self,
        admin_id: str,
        new_username: Optional[str] = None,
        new_email: Optional[str] = None,
        new_full_name: Optional[str] = None,
        current_password: Optional[str] = None,
        new_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically updates Admin's profile without touching code.
        Re-hashes new password using Bcrypt after verifying current password.
        """
        with self.db.get_connection() as conn:
            admin_row = conn.execute("SELECT id, username, password_hash FROM users WHERE id = ?", (admin_id,)).fetchone()
            if not admin_row:
                raise ValueError("Admin account not found.")

            updates = []
            params = []

            # Update Username
            if new_username and new_username.strip():
                clean_name = new_username.strip()
                # Check uniqueness
                dup = conn.execute("SELECT id FROM users WHERE lower(username) = lower(?) AND id != ?", (clean_name, admin_id)).fetchone()
                if dup:
                    raise ValueError(f"Username '{clean_name}' is already taken.")
                updates.append("username = ?")
                params.append(clean_name)

            # Update Email
            if new_email and new_email.strip():
                updates.append("email = ?")
                params.append(new_email.strip().lower())

            # Update Full Name
            if new_full_name and new_full_name.strip():
                updates.append("full_name = ?")
                params.append(new_full_name.strip())

            # Password Change
            if new_password and new_password.strip():
                if len(new_password) < 6:
                    raise ValueError("New password must be at least 6 characters.")
                if not current_password:
                    raise ValueError("Current password is required to verify identity before updating password.")
                if not verify_password(current_password, admin_row["password_hash"]):
                    raise ValueError("Current password verification failed.")

                # RE-HASH USING BCRYPT
                new_bcrypt_hash = hash_password(new_password)
                updates.append("password_hash = ?")
                params.append(new_bcrypt_hash)

            if not updates:
                return {"success": True, "message": "No profile updates requested."}

            params.append(admin_id)
            conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

            # Return refreshed profile
            refreshed = conn.execute("""
                SELECT id, username, role, full_name, email, created_at, last_login
                FROM users WHERE id = ?
            """, (admin_id,)).fetchone()

            return {
                "success": True,
                "message": "Admin profile successfully updated. Passwords re-hashed with Bcrypt.",
                "user": dict(refreshed)
            }

    # -------------------------------------------------------------
    # REQUIREMENT 2: Role-Based User Management Portal
    # -------------------------------------------------------------
    def get_all_operators(self) -> List[Dict[str, Any]]:
        """Lists all operator accounts with security and device lock telemetry."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, role, full_name, email, is_active,
                       device_lock_id, device_lock_enabled, expiry_date,
                       daily_scrape_quota, daily_send_quota, license_key,
                       created_at, last_login, last_login_device
                FROM users
                ORDER BY role ASC, created_at DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def create_operator_account(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        device_lock_id: Optional[str] = None,
        device_lock_enabled: bool = True,
        expiry_days: int = 90,
        daily_scrape_quota: int = 200,
        daily_send_quota: int = 50
    ) -> Dict[str, Any]:
        """
        Creates new Operator account with custom device locking, quotas,
        and cryptographically signed license key.
        """
        clean_user = username.strip()
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id FROM users WHERE lower(username) = lower(?)", (clean_user,)).fetchone()
            if existing:
                raise ValueError(f"Username '{clean_user}' already exists.")

            user_id = str(uuid.uuid4())
            pass_hash = hash_password(password)  # BCRYPT
            exp_date = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).strftime("%Y-%m-%d %H:%M:%S")

            target_device = device_lock_id or generate_machine_fingerprint()["machine_id"]
            license_token = generate_license_key(
                machine_id=target_device,
                client_name=f"Operator: {full_name}",
                tier="Level-2-Operator",
                days_valid=expiry_days
            )

            conn.execute("""
                INSERT INTO users (
                    id, username, password_hash, role, full_name, email,
                    is_active, device_lock_id, device_lock_enabled, expiry_date,
                    daily_scrape_quota, daily_send_quota, license_key
                ) VALUES (?, ?, ?, 'operator', ?, ?, 1, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, clean_user, pass_hash, full_name.strip(), email.strip().lower(),
                target_device, 1 if device_lock_enabled else 0, exp_date,
                daily_scrape_quota, daily_send_quota, license_token
            ))
            conn.commit()

        return {
            "success": True,
            "user_id": user_id,
            "username": clean_user,
            "role": "operator",
            "device_lock_id": target_device,
            "expiry_date": exp_date,
            "license_key": license_token
        }

    def toggle_user_active_status(self, user_id: str) -> Dict[str, Any]:
        """Single toggle switch to instantly revoke or re-activate access."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT username, role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("User not found.")
            if row["role"] == "admin":
                raise ValueError("Master Administrator accounts cannot be revoked.")

            new_status = 0 if row["is_active"] == 1 else 1
            conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
            conn.commit()

            return {
                "success": True,
                "user_id": user_id,
                "username": row["username"],
                "is_active": new_status,
                "status_label": "ACTIVE" if new_status == 1 else "REVOKED"
            }

    def reset_operator_password(self, user_id: str, new_password: str) -> Dict[str, Any]:
        """Admin resets operator password directly from UI using Bcrypt."""
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters.")

        with self.db.get_connection() as conn:
            row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError("User not found.")

            new_hash = hash_password(new_password)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            conn.commit()

            return {
                "success": True,
                "username": row["username"],
                "message": "Password successfully reset with Bcrypt encryption."
            }

    # -------------------------------------------------------------
    # REQUIREMENT 3: License & Expiry Control Module
    # -------------------------------------------------------------
    def modify_license_and_quotas(
        self,
        user_id: str,
        extend_days: Optional[int] = None,
        daily_scrape_quota: Optional[int] = None,
        daily_send_quota: Optional[int] = None,
        device_lock_id: Optional[str] = None,
        device_lock_enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Admin issues, modifies, or extends subscription expiry dates
        and daily scraping/sending quotas.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT username, full_name, expiry_date, daily_scrape_quota,
                       daily_send_quota, device_lock_id
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()

            if not row:
                raise ValueError("User not found.")

            updates = []
            params = []

            # Extend Expiry
            new_exp_str = row["expiry_date"]
            if extend_days is not None and extend_days > 0:
                current_exp = datetime.now(timezone.utc)
                if row["expiry_date"]:
                    try:
                        parsed = datetime.fromisoformat(row["expiry_date"].replace(" ", "T")).replace(tzinfo=timezone.utc)
                        if parsed > current_exp:
                            current_exp = parsed
                    except Exception:
                        pass
                new_exp = current_exp + timedelta(days=extend_days)
                new_exp_str = new_exp.strftime("%Y-%m-%d %H:%M:%S")
                updates.append("expiry_date = ?")
                params.append(new_exp_str)

                # Re-issue cryptographic license token
                target_mid = row["device_lock_id"] or generate_machine_fingerprint()["machine_id"]
                new_license = generate_license_key(
                    machine_id=target_mid,
                    client_name=f"Subscriber: {row['full_name']}",
                    tier="Level-2-Enterprise",
                    days_valid=extend_days
                )
                updates.append("license_key = ?")
                params.append(new_license)

            if daily_scrape_quota is not None:
                updates.append("daily_scrape_quota = ?")
                params.append(daily_scrape_quota)

            if daily_send_quota is not None:
                updates.append("daily_send_quota = ?")
                params.append(daily_send_quota)

            if device_lock_id is not None:
                updates.append("device_lock_id = ?")
                params.append(device_lock_id.strip())

            if device_lock_enabled is not None:
                updates.append("device_lock_enabled = ?")
                params.append(1 if device_lock_enabled else 0)

            if updates:
                params.append(user_id)
                conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()

            return {
                "success": True,
                "username": row["username"],
                "new_expiry_date": new_exp_str,
                "daily_scrape_quota": daily_scrape_quota or row["daily_scrape_quota"],
                "daily_send_quota": daily_send_quota or row["daily_send_quota"],
                "message": "License & Quotas successfully updated."
            }


_global_user_manager = None

def get_user_manager() -> UserManager:
    global _global_user_manager
    if _global_user_manager is None:
        _global_user_manager = UserManager()
    return _global_user_manager
