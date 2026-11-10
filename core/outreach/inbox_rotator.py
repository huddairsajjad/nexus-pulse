"""
H.Huddair's Nexus-Pulse - Level 2
Outreach Engine: Inbox Rotator & Daily Quota Manager
Rotates secondary mailboxes across domains, strictly enforcing 40-50 emails/day per domain limit.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine


class InboxRotator:
    """
    Manages sending mailboxes, round-robin rotation, and daily send limits.
    """

    def __init__(self):
        self.db = get_db_engine()
        self.seed_default_mailboxes()

    def seed_default_mailboxes(self) -> None:
        """Seeds default sending mailboxes if none exist."""
        default_mailboxes = [
            ("outreach-de@huddair-nexus.de", "H.Huddair B2B Lead Engine (DE)", "huddair-nexus.de", 45),
            ("tenders-uk@huddair-nexus.co.uk", "H.Huddair Commercial Estimating", "huddair-nexus.co.uk", 45),
            ("bids-eu@huddair-global.com", "H.Huddair Tender Submissions", "huddair-global.com", 45),
            ("director@huddair-nexus.com", "H.Huddair Executive Office", "huddair-nexus.com", 40)
        ]

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        with self.db.get_connection() as conn:
            for email, name, domain, limit in default_mailboxes:
                existing = conn.execute("SELECT id FROM mailbox_rotator WHERE email_address = ?", (email,)).fetchone()
                if not existing:
                    mb_id = str(uuid.uuid4())
                    conn.execute("""
                        INSERT INTO mailbox_rotator (id, email_address, display_name, domain, daily_limit, sent_today, last_reset_date, is_active)
                        VALUES (?, ?, ?, ?, ?, 0, ?, 1)
                    """, (mb_id, email, name, domain, limit, today_str))
            conn.commit()

    def _reset_quotas_if_new_day(self, conn) -> None:
        """Resets sent_today counters if wall-clock day has rolled over."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn.execute("""
            UPDATE mailbox_rotator
            SET sent_today = 0, last_reset_date = ?
            WHERE last_reset_date != ?
        """, (today_str, today_str))

    def get_next_available_mailbox(self) -> Optional[Dict[str, Any]]:
        """
        Selects the next active mailbox that has not exceeded its daily cap (40-50).
        Prioritizes the mailbox with the lowest sent_today count.
        """
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)
            row = conn.execute("""
                SELECT id, email_address, display_name, domain, daily_limit, sent_today
                FROM mailbox_rotator
                WHERE is_active = 1 AND sent_today < daily_limit
                ORDER BY sent_today ASC, email_address ASC
                LIMIT 1
            """).fetchone()

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

    def get_all_mailboxes_status(self) -> List[Dict[str, Any]]:
        """Returns live statistics across all rotated sending inboxes."""
        with self.db.get_connection() as conn:
            self._reset_quotas_if_new_day(conn)
            rows = conn.execute("""
                SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                       (daily_limit - sent_today) as remaining_quota, is_active,
                       COALESCE(smtp_host, '') as smtp_host,
                       COALESCE(smtp_port, 587) as smtp_port,
                       COALESCE(smtp_username, '') as smtp_username,
                       COALESCE(smtp_password, '') as smtp_password
                FROM mailbox_rotator
                ORDER BY domain ASC
            """).fetchall()
            return [dict(r) for r in rows]


_global_inbox_rotator = None

def get_inbox_rotator() -> InboxRotator:
    global _global_inbox_rotator
    if _global_inbox_rotator is None:
        _global_inbox_rotator = InboxRotator()
    return _global_inbox_rotator
