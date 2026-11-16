"""
Nexus-Pulse Production Build
Outreach Engine: APScheduler Background Management & Feedback Loops
Configures automated daily send-cap resets, 2-day trial expiration checks,
and automated bounce/spam feedback loop handling.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from database.db_engine import get_db_engine
from core.outreach.reply_listener import get_reply_listener

logger = logging.getLogger("nexus.apscheduler")

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    BackgroundScheduler = None


class APSchedulerManager:
    """
    Automated background task manager powered by APScheduler.
    Executes:
      1. Daily Mailbox Send-Cap Resets (resets sent_today=0 and decrements/refreshes capacity)
      2. 2-Day Free Trial Expiration Audits (marks expired trials as 'expired')
      3. Automated Bounce & Spam Feedback Loop Handling (auto-suppresses bounced recipients)
    """

    def __init__(self):
        self.db = get_db_engine()
        self.scheduler = None
        self._is_running = False

    def reset_daily_send_caps(self) -> Dict[str, Any]:
        """
        Resets daily send-caps for all active mailboxes (sent_today = 0).
        Refreshes daily quota for outbound dispatching.
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                UPDATE mailbox_rotator
                SET sent_today = 0, last_reset_date = ?
                WHERE is_active = 1
            """, (today_str,))
            conn.commit()
            count = cur.rowcount

        logger.info(f"[APSCHEDULER] Daily mailbox send-caps reset for {count} mailboxes. (Date: {today_str})")
        return {"success": True, "reset_count": count, "reset_date": today_str}

    def check_trial_expirations(self) -> Dict[str, Any]:
        """
        Checks all operator accounts on 2-Day Free Trial.
        Updates trial_status = 'expired' if expiry_date has passed.
        """
        now_utc = datetime.now(timezone.utc)
        now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            cur = conn.execute("""
                UPDATE users
                SET trial_status = 'expired'
                WHERE role = 'operator'
                  AND trial_status = 'active'
                  AND expiry_date IS NOT NULL
                  AND expiry_date < ?
            """, (now_str,))
            conn.commit()
            count = cur.rowcount

        logger.info(f"[APSCHEDULER] Trial expiration check complete: {count} accounts updated to 'expired'.")
        return {"success": True, "expired_count": count, "checked_at": now_str}

    def handle_bounce_feedback(self) -> Dict[str, Any]:
        """
        Automated bounce & spam feedback loop:
        Scans inbox_replies and outreach_queue for recorded bounces and spam complaints.
        Automatically enrolls the bounced recipient and domain in the global suppression list
        and updates MongoDB state.
        """
        listener = get_reply_listener()
        suppressed_count = 0

        with self.db.get_connection() as conn:
            # 1. Check inbox_replies with classification 'BOUNCE'
            bounce_replies = conn.execute("""
                SELECT sender_email, lead_id FROM inbox_replies
                WHERE classification = 'BOUNCE'
            """).fetchall()

            for br in bounce_replies:
                email = (br["sender_email"] or "").strip().lower()
                if email and not listener.is_suppressed(email):
                    listener.suppress_entity(email, reason="BOUNCE")
                    domain = email.split("@")[-1] if "@" in email else ""
                    if domain:
                        listener.suppress_entity(domain, reason="BOUNCE")
                    suppressed_count += 1

            # 2. Check outreach_queue marked as 'BOUNCED' or 'FAILED' with bounce reason
            bounced_queue = conn.execute("""
                SELECT recipient, bounce_reason FROM outreach_queue
                WHERE status = 'BOUNCED' OR (status = 'FAILED' AND lower(bounce_reason) LIKE '%bounce%')
            """).fetchall()

            for bq in bounced_queue:
                email = (bq["recipient"] or "").strip().lower()
                if email and not listener.is_suppressed(email):
                    listener.suppress_entity(email, reason="BOUNCE")
                    suppressed_count += 1

        # Sync unsubscriptions to MongoDB
        try:
            from database.mongo_engine import get_mongo_engine
            mongo = get_mongo_engine()
            # If any new suppressions, ensure MongoDB reflects unsubscribed
            with self.db.get_connection() as conn:
                supp_rows = conn.execute("SELECT entity FROM suppressed_entities").fetchall()
                for sr in supp_rows:
                    mongo.set_unsubscribed(sr["entity"])
        except Exception:
            pass

        logger.info(f"[APSCHEDULER] Bounce feedback loop processed: {suppressed_count} new entities suppressed.")
        return {"success": True, "suppressed_new_count": suppressed_count}

    def start(self) -> bool:
        """Starts APScheduler with all automated recurring jobs."""
        if self._is_running or not BackgroundScheduler:
            return False

        try:
            self.scheduler = BackgroundScheduler(daemon=True)

            # Job 1: Daily Send-Cap Reset at midnight UTC
            self.scheduler.add_job(
                self.reset_daily_send_caps,
                trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
                id="daily_send_cap_reset",
                name="Reset Daily Mailbox Send Caps",
                replace_existing=True
            )

            # Job 2: 2-Day Trial Expiration Audit every 30 minutes
            self.scheduler.add_job(
                self.check_trial_expirations,
                trigger=IntervalTrigger(minutes=30),
                id="check_trial_expirations",
                name="Audit 2-Day Free Trial Expirations",
                replace_existing=True
            )

            # Job 3: Automated Bounce Feedback Loop every 15 minutes
            self.scheduler.add_job(
                self.handle_bounce_feedback,
                trigger=IntervalTrigger(minutes=15),
                id="handle_bounce_feedback",
                name="Bounce and Spam Feedback Loop",
                replace_existing=True
            )

            self.scheduler.start()
            self._is_running = True
            logger.info("[APSCHEDULER] Scheduler started with 3 automated recurring jobs.")
            return True
        except Exception as ex:
            logger.warning(f"[APSCHEDULER] Startup warning: {ex}")
            return False

    def shutdown(self):
        """Gracefully stops the scheduler."""
        if self.scheduler and self._is_running:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
            self._is_running = False
            logger.info("[APSCHEDULER] Scheduler stopped.")


_global_apscheduler_manager = None

def get_apscheduler_manager() -> APSchedulerManager:
    global _global_apscheduler_manager
    if _global_apscheduler_manager is None:
        _global_apscheduler_manager = APSchedulerManager()
    return _global_apscheduler_manager
