"""
Nexus-Pulse Enterprise Build
Outreach Engine: Inbox Rotator & Daily Quota Manager
Rotates sending mailboxes across domains, enforcing daily caps (40-50 emails/day)
with multi-tenant isolation and automated switching between enrolled SMTP profiles.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine


class InboxRotator:
    """
    Manages sending mailboxes, multi-tenant mailbox isolation,
    round-robin load balancing, and auto-switching across daily send limits.
    Zero-seed clean startup: No default mailboxes are populated upon initialization.
    """

    def __init__(self):
        self.db = get_db_engine()
        # Zero-seed policy: Do NOT seed hardcoded default mailboxes upon initialization.

    def _reset_quotas_if_new_day(self, conn) -> None:
        """Resets sent_today counters if wall-clock day has rolled over."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn.execute("""
            UPDATE mailbox_rotator
            SET sent_today = 0, last_reset_date = ?
            WHERE last_reset_date != ?
        """, (today_str, today_str))

    def get_next_available_mailbox(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-switching load balancer:
        Selects the next active mailbox that has not exceeded its daily cap (e.g., 40-50).
        Automatically transitions to the next available SMTP profile once an inbox hits its cap,
        preventing workflow interruption.
        Supports strict multi-tenant tenant_id, operator and user isolation.
        """
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)

            query = """
                SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                       operator_id, owner_username, smtp_host, smtp_port, smtp_username, smtp_password,
                       imap_host, imap_port, imap_username, imap_password,
                       COALESCE(webhook_url, '') as webhook_url,
                       COALESCE(tenant_id, operator_id) as tenant_id
                FROM mailbox_rotator
                WHERE is_active = 1 AND sent_today < daily_limit
            """
            params: List[Any] = []
            t_id = (tenant_id or "").strip()
            owner = (owner_username or "").strip().lower()
            op_id = (operator_id or "").strip()
            if t_id or owner or op_id:
                query += " AND (tenant_id = ? OR lower(owner_username) = ? OR operator_id = ?)"
                params.extend([t_id or op_id, owner or t_id, op_id or t_id])

            query += " ORDER BY sent_today ASC, email_address ASC LIMIT 1"
            row = conn.execute(query, params).fetchone()

            if row:
                return dict(row)
            return None

    def record_email_dispatched(
        self,
        mailbox_id_or_email: str,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        conn=None,
    ) -> Optional[Dict[str, Any]]:
        """
        Increments sent_today count for the used mailbox (SQLite + MongoDB),
        strictly scoped to the current user/tenant when provided.
        """
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        updated_mb: Optional[Dict[str, Any]] = None

        def _do_update(active_conn) -> Optional[Dict[str, Any]]:
            self._reset_quotas_if_new_day(active_conn)
            if owner or op_id:
                active_conn.execute("""
                    UPDATE mailbox_rotator
                    SET sent_today = sent_today + 1
                    WHERE (id = ? OR lower(email_address) = lower(?))
                      AND (
                          lower(owner_username) = ?
                          OR operator_id = ?
                          OR ((owner_username IS NULL OR owner_username = '') AND (operator_id IS NULL OR operator_id = ''))
                      )
                """, (mailbox_id_or_email, mailbox_id_or_email, owner, op_id))
                row = active_conn.execute("""
                    SELECT id, email_address, sent_today, daily_limit, operator_id, owner_username
                    FROM mailbox_rotator
                    WHERE (id = ? OR lower(email_address) = lower(?))
                      AND (
                          lower(owner_username) = ?
                          OR operator_id = ?
                          OR ((owner_username IS NULL OR owner_username = '') AND (operator_id IS NULL OR operator_id = ''))
                      )
                    LIMIT 1
                """, (mailbox_id_or_email, mailbox_id_or_email, owner, op_id)).fetchone()
            else:
                active_conn.execute("""
                    UPDATE mailbox_rotator
                    SET sent_today = sent_today + 1
                    WHERE id = ? OR lower(email_address) = lower(?)
                """, (mailbox_id_or_email, mailbox_id_or_email))
                row = active_conn.execute("""
                    SELECT id, email_address, sent_today, daily_limit, operator_id, owner_username
                    FROM mailbox_rotator
                    WHERE id = ? OR lower(email_address) = lower(?)
                    LIMIT 1
                """, (mailbox_id_or_email, mailbox_id_or_email)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            updated_mb = _do_update(conn)
        else:
            with self.db.get_connection() as owned_conn:
                updated_mb = _do_update(owned_conn)
                owned_conn.commit()

        if updated_mb:
            try:
                from database.mongo_engine import get_mongo_engine
                mongo = get_mongo_engine()
                mongo.increment_mailbox_sent_today(
                    mailbox_id=updated_mb["id"],
                    email_address=updated_mb["email_address"],
                    owner_username=owner or (updated_mb.get("owner_username") or "").strip().lower(),
                    operator_id=op_id or (updated_mb.get("operator_id") or "").strip(),
                    sent_today=updated_mb["sent_today"],
                    daily_limit=updated_mb["daily_limit"],
                )
            except Exception:
                pass

        return updated_mb

    def get_all_mailboxes_status(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns live statistics across enrolled sending inboxes.
        Strictly filters by tenant_id / owner_username / operator_id for total multi-tenant isolation.
        """
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)

            query = """
                SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                       (daily_limit - sent_today) as remaining_quota, is_active,
                       operator_id, owner_username,
                       COALESCE(smtp_host, '') as smtp_host,
                       COALESCE(smtp_port, 587) as smtp_port,
                       COALESCE(smtp_username, '') as smtp_username,
                       COALESCE(smtp_password, '') as smtp_password,
                       COALESCE(imap_host, '') as imap_host,
                       COALESCE(imap_port, 993) as imap_port,
                       COALESCE(imap_username, '') as imap_username,
                       COALESCE(imap_password, '') as imap_password,
                       COALESCE(webhook_url, '') as webhook_url,
                       COALESCE(tenant_id, operator_id) as tenant_id
                FROM mailbox_rotator
            """
            params: List[Any] = []
            t_id = (tenant_id or "").strip()
            owner = (owner_username or "").strip().lower()
            op_id = (operator_id or "").strip()
            if t_id or owner or op_id:
                query += " WHERE (tenant_id = ? OR lower(owner_username) = ? OR operator_id = ?)"
                params.extend([t_id or op_id, owner or t_id, op_id or t_id])

            query += " ORDER BY domain ASC, email_address ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def enroll_mailbox(
        self,
        email_address: str,
        display_name: str,
        domain: Optional[str] = None,
        daily_limit: int = 45,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_username: str = "",
        smtp_password: str = "",
        imap_host: str = "",
        imap_port: int = 993,
        imap_username: str = "",
        imap_password: str = "",
        webhook_url: str = "",
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrolls a new SMTP/IMAP mailbox profile bound to tenant_id, operator and owner_username."""
        email = email_address.strip().lower()
        if not email or "@" not in email:
            raise ValueError("Valid email address is required.")

        dom = (domain or email.split("@")[-1]).strip().lower()
        mb_id = str(uuid.uuid4())
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        owner = (owner_username or "").strip()
        t_id = (tenant_id or operator_id or owner or "").strip()

        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id FROM mailbox_rotator WHERE lower(email_address) = ?", (email,)).fetchone()
            if existing:
                raise ValueError(f"Mailbox '{email}' is already registered in the rotator.")

            conn.execute("""
                INSERT INTO mailbox_rotator (
                    id, email_address, display_name, domain, daily_limit, sent_today,
                    last_reset_date, is_active, operator_id, owner_username, tenant_id,
                    smtp_host, smtp_port, smtp_username, smtp_password,
                    imap_host, imap_port, imap_username, imap_password,
                    webhook_url
                ) VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mb_id, email, display_name.strip(), dom, daily_limit, today_str,
                operator_id, owner, t_id,
                smtp_host.strip(), smtp_port, smtp_username.strip(), smtp_password,
                imap_host.strip(), imap_port, imap_username.strip(), imap_password,
                webhook_url.strip()
            ))
            conn.commit()

        # Persist to MongoDB mailboxes collection
        try:
            from database.mongo_engine import get_mongo_engine
            mongo = get_mongo_engine()
            if mongo and mongo.db is not None:
                mongo.db.mailboxes.update_one(
                    {"mailbox_id": mb_id},
                    {"$set": {
                        "mailbox_id": mb_id,
                        "tenant_id": t_id,
                        "email_address": email,
                        "display_name": display_name.strip(),
                        "domain": dom,
                        "daily_limit": daily_limit,
                        "sent_today": 0,
                        "is_active": 1,
                        "operator_id": operator_id,
                        "owner_username": owner,
                        "webhook_url": webhook_url.strip(),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
        except Exception:
            pass

        return {
            "id": mb_id,
            "tenant_id": t_id,
            "email_address": email,
            "display_name": display_name.strip(),
            "domain": dom,
            "daily_limit": daily_limit,
            "operator_id": operator_id,
            "owner_username": owner,
            "webhook_url": webhook_url.strip()
        }

    def seed_test_mailboxes_for_tests(self, operator_id: Optional[str] = None) -> None:
        """Explicit fixture helper strictly for automated unit tests."""
        is_test_env = bool(
            os.getenv("PYTEST_CURRENT_TEST") or
            os.getenv("NEXUS_TEST_MODE") or
            os.getenv("TESTING")
        )
        if not is_test_env:
            # Strictly prohibited in production to guarantee zero dummy data
            return

        test_mailboxes = [
            ("test-alpha@outreach-test.io", "Test Sender Alpha", "outreach-test.io", 45),
            ("test-beta@outreach-test.io", "Test Sender Beta", "outreach-test.io", 45)
        ]
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            for email, name, domain, limit in test_mailboxes:
                existing = conn.execute("SELECT id FROM mailbox_rotator WHERE email_address = ?", (email,)).fetchone()
                if not existing:
                    mb_id = str(uuid.uuid4())
                    conn.execute("""
                        INSERT INTO mailbox_rotator (
                            id, email_address, display_name, domain, daily_limit, sent_today,
                            last_reset_date, is_active, operator_id,
                            smtp_host, smtp_port, smtp_username, smtp_password
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, 'smtp.gmail.com', 587, ?, 'test-app-password')
                    """, (mb_id, email, name, domain, limit, today_str, operator_id, email))
                else:
                    conn.execute("""
                        UPDATE mailbox_rotator
                        SET smtp_host = 'smtp.gmail.com', smtp_port = 587,
                            smtp_username = ?, smtp_password = 'test-app-password'
                        WHERE email_address = ?
                    """, (email, email))
            conn.commit()


_global_inbox_rotator = None

def get_inbox_rotator() -> InboxRotator:
    global _global_inbox_rotator
    if _global_inbox_rotator is None:
        _global_inbox_rotator = InboxRotator()
    return _global_inbox_rotator
