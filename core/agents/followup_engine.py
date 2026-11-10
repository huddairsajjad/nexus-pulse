"""
H.Huddair's Nexus-Pulse - Level 2
Agent Module: Autonomous 7-Day Follow-Up Engine
Monitors outbound dispatch logs and automatically triggers context-aware
follow-up sequences if no response is logged after 7 days.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from database.db_engine import get_db_engine
from ..outreach.approval_gate import get_approval_gate
from ..outreach.reply_listener import get_reply_listener


def generate_followup_copy(recipient_email: str, company_name: str) -> Dict[str, str]:
    """Generates polite, context-aware 7-day follow-up messaging."""
    subject = f"Following up: Estimating & Tender Capacity // {company_name}"
    body = (
        f"Dear Estimating Team at {company_name},\n\n"
        f"Following up briefly on our note from last week regarding subcontracting capacity and tender pricing.\n\n"
        f"We understand estimating deadlines can be demanding—we wanted to ensure our credentials reached the right "
        f"quantity surveyor or commercial estimator in your department.\n\n"
        f"If you have any open packages requiring competitive takeoffs or pricing support, we are prepared to review "
        f"the documentation immediately.\n\n"
        f"Best regards,\n"
        f"H.Huddair\n"
        f"Commercial Director | Nexus-Pulse"
    )
    return {"subject": subject, "body": body}


class AutonomousFollowupEngine:
    """
    Automates 7-day follow-up monitoring, suppression checks, and sequence dispatch.
    """

    def __init__(self):
        self.db = get_db_engine()
        self.gate = get_approval_gate()
        self.reply_listener = get_reply_listener()

    def scan_and_trigger_due_followups(self, force_all_pending: bool = False) -> Dict[str, Any]:
        """
        Scans for leads whose initial outreach was sent >= 7 days ago and has received no response.
        If force_all_pending is True, triggers immediate test/demo execution on pending sequences.
        """
        triggered: List[Dict[str, Any]] = []
        suppressed: List[Dict[str, Any]] = []

        query = """
            SELECT f.id, f.lead_id, f.initial_outreach_id, f.recipient_email,
                   f.initial_sent_at, f.followup_due_at, f.step_number,
                   q.company_name, q.target_country, q.target_timezone
            FROM followup_sequences f
            LEFT JOIN outreach_queue q ON f.initial_outreach_id = q.id
            WHERE f.status = 'PENDING'
        """
        if not force_all_pending:
            query += " AND datetime('now') >= f.followup_due_at"

        with self.db.get_connection() as conn:
            rows = conn.execute(query).fetchall()

            for row in rows:
                seq_id = row["id"]
                recipient = row["recipient_email"]
                comp = row["company_name"] or recipient.split("@")[-1].capitalize()
                country = row["target_country"] or "Germany"

                # 1. Suppression Check: Check if DNC blacklisted
                if self.reply_listener.is_blacklisted(recipient):
                    conn.execute("UPDATE followup_sequences SET status = 'TERMINATED' WHERE id = ?", (seq_id,))
                    suppressed.append({"recipient": recipient, "reason": "DNC_BLACKLISTED"})
                    continue

                # 2. Suppression Check: Check if already replied
                replied = conn.execute("SELECT id FROM inbox_replies WHERE sender_email = ?", (recipient,)).fetchone()
                if replied:
                    conn.execute("UPDATE followup_sequences SET status = 'TERMINATED' WHERE id = ?", (seq_id,))
                    suppressed.append({"recipient": recipient, "reason": "ALREADY_REPLIED"})
                    continue

                # 3. Generate Follow-Up Copy and Queue in Approval Gate
                copy = generate_followup_copy(recipient, comp)
                queue_res = self.gate.queue_outreach(
                    lead_id=row["lead_id"],
                    company_name=comp,
                    recipient=recipient,
                    country=country,
                    niche="Commercial Construction",
                    channel="EMAIL",
                    custom_subject=copy["subject"],
                    custom_body=copy["body"]
                )

                # Update sequence record
                conn.execute("""
                    UPDATE followup_sequences
                    SET status = 'QUEUED_FOR_APPROVAL', followup_sent_at = CURRENT_TIMESTAMP, step_number = step_number + 1
                    WHERE id = ?
                """, (seq_id,))

                triggered.append({
                    "sequence_id": seq_id,
                    "recipient": recipient,
                    "company_name": comp,
                    "step_number": 2,
                    "queue_id": queue_res["queue_id"],
                    "status": "QUEUED_IN_APPROVAL_GATE"
                })

            conn.commit()

        return {
            "total_scanned": len(rows),
            "followups_triggered": len(triggered),
            "followups_suppressed": len(suppressed),
            "triggered_items": triggered,
            "suppressed_items": suppressed
        }


_global_followup_engine = None

def get_followup_engine() -> AutonomousFollowupEngine:
    global _global_followup_engine
    if _global_followup_engine is None:
        _global_followup_engine = AutonomousFollowupEngine()
    return _global_followup_engine
