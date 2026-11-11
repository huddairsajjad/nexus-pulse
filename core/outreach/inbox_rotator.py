"""
Nexus-Pulse Enterprise Build
Outreach Engine: Inbox Rotator & Daily Quota Manager
Rotates sending mailboxes across domains, enforcing daily caps (40-50 emails/day)
with multi-tenant isolation and automated switching between enrolled SMTP profiles.
"""

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

    def get_next_available_mailbox(self, operator_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Auto-switching load balancer:
        Selects the next active mailbox that has not exceeded its daily cap (e.g., 40-50).
        Automatically transitions to the next available SMTP profile once an inbox hits its cap,
        preventing workflow interruption.
        Supports multi-tenant operator isolation.
        """
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)

            query = """
                SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                       operator_id, smtp_host, smtp_port, smtp_username, smtp_password,
                       imap_host, imap_port, imap_username, imap_password
                FROM mailbox_rotator
                WHERE is_active = 1 AND sent_today < daily_limit
            """
            params: List[Any] = []
            if operator_id:
                query += " AND (operator_id = ? OR operator_id IS NULL OR operator_id = '')"
                params.append(operator_id)

            query += " ORDER BY sent_today ASC, email_address ASC LIMIT 1"
            row = conn.execute(query, params).fetchone()

            if row:
                return dict(row)
            return None

    def record_email_dispatched(self, mailbox_id_or_email: str) -> None:
        """Increments sent_today count for the used mailbox."""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE mailbox_rotator
                SET sent_today = sent_today + 1
                WHERE id = ? OR email_address = ?
            """, (mailbox_id_or_email, mailbox_id_or_email))
            conn.commit()

    def get_all_mailboxes_status(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns live statistics across enrolled sending inboxes.
        Filters by operator_id for paying clients, or returns all for super admins.
        """
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)

            query = """
                SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                       (daily_limit - sent_today) as remaining_quota, is_active,
                       operator_id,
                       COALESCE(smtp_host, '') as smtp_host,
                       COALESCE(smtp_port, 587) as smtp_port,
                       COALESCE(smtp_username, '') as smtp_username,
                       COALESCE(smtp_password, '') as smtp_password,
                       COALESCE(imap_host, '') as imap_host,
                       COALESCE(imap_port, 993) as imap_port,
                       COALESCE(imap_username, '') as imap_username,
                       COALESCE(imap_password, '') as imap_password
                FROM mailbox_rotator
            """
            params: List[Any] = []
            if operator_id:
                query += " WHERE operator_id = ? OR operator_id IS NULL OR operator_id = ''"
                params.append(operator_id)

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
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_username: str = "",
        smtp_password: str = "",
        imap_host: str = "",
        imap_port: int = 993,
        imap_username: str = "",
        imap_password: str = ""
    ) -> Dict[str, Any]:
        """Enrolls a new SMTP/IMAP mailbox profile bound to an operator."""
        email = email_address.strip().lower()
        if not email or "@" not in email:
            raise ValueError("Valid email address is required.")

        dom = (domain or email.split("@")[-1]).strip().lower()
        mb_id = str(uuid.uuid4())
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id FROM mailbox_rotator WHERE lower(email_address) = ?", (email,)).fetchone()
            if existing:
                raise ValueError(f"Mailbox '{email}' is already registered in the rotator.")

            conn.execute("""
                INSERT INTO mailbox_rotator (
                    id, email_address, display_name, domain, daily_limit, sent_today,
                    last_reset_date, is_active, operator_id,
                    smtp_host, smtp_port, smtp_username, smtp_password,
                    imap_host, imap_port, imap_username, imap_password
                ) VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mb_id, email, display_name.strip(), dom, daily_limit, today_str,
                operator_id,
                smtp_host.strip(), smtp_port, smtp_username.strip(), smtp_password,
                imap_host.strip(), imap_port, imap_username.strip(), imap_password
            ))
            conn.commit()

        return {
            "id": mb_id,
            "email_address": email,
            "display_name": display_name.strip(),
            "domain": dom,
            "daily_limit": daily_limit,
            "operator_id": operator_id
        }

    def seed_test_mailboxes_for_tests(self, operator_id: Optional[str] = None) -> None:
        """Explicit fixture helper strictly for automated unit tests."""
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
                            last_reset_date, is_active, operator_id
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?)
                    """, (mb_id, email, name, domain, limit, today_str, operator_id))
            conn.commit()


_global_inbox_rotator = None

def get_inbox_rotator() -> InboxRotator:
    global _global_inbox_rotator
    if _global_inbox_rotator is None:
        _global_inbox_rotator = InboxRotator()
    return _global_inbox_rotator
