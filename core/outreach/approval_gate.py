"""
H.Huddair's Nexus-Pulse - Level 2
Outreach Engine: Human Approval Gate
Enforces the mandatory authorization hold: no email or contact form is dispatched
without manual Review & Approve authorization from H.Huddair.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine
from .scheduler import get_scheduler
from .inbox_rotator import get_inbox_rotator


def generate_personalized_copy(
    company_name: str,
    recipient_email: str,
    niche: str,
    country: str,
    tech_stack: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generates high-conversion, professional B2B outreach tailored
    specifically for estimating, tenders, and commercial contracting.
    """
    clean_niche = niche or "Commercial Contracting"
    stack_mention = f" We noted your current digital infrastructure ({', '.join(tech_stack[:2])})." if tech_stack else ""

    # Check recipient prefix to customize hook
    prefix = recipient_email.split("@")[0].lower() if "@" in recipient_email else ""
    if any(k in prefix for k in ["estimating", "kalkulation", "chiffrage"]):
        subject = f"Tender Estimation & Subcontractor Prequalification // {company_name}"
        body = (
            f"Dear Estimating Team at {company_name},\n\n"
            f"We are reaching out to submit our pre-qualification credentials and commercial capacity for upcoming "
            f"{clean_niche} tender packages in {country}.{stack_mention}\n\n"
            f"Our team handles detailed bill-of-quantities takeoff, competitive subcontractor package pricing, and rapid estimating turnaround.\n\n"
            f"Could you please confirm the current email address or portal for receiving your open tender documentation?\n\n"
            f"Best regards,\n"
            f"H.Huddair\n"
            f"Commercial Director | Nexus-Pulse Enterprise Solutions"
        )
    elif any(k in prefix for k in ["bids", "tender", "qs"]):
        subject = f"Commercial Bidding & Quantity Surveying Partner // {company_name}"
        body = (
            f"Dear Commercial & QS Department,\n\n"
            f"In reviewing major commercial projects across {country}, we would like to present our subcontracting and estimating capabilities to {company_name}.\n\n"
            f"We specialize in rapid tender pricing, value engineering, and high-precision commercial takeoffs for {clean_niche}.\n\n"
            f"Would you be available for a brief introductory call this week, or should we send through our capability profile directly?\n\n"
            f"Warm regards,\n"
            f"H.Huddair\n"
            f"Nexus-Pulse Lead Engine"
        )
    else:
        subject = f"Strategic Commercial Partnership // {company_name}"
        body = (
            f"Hello {company_name} Leadership,\n\n"
            f"We have been following your commercial project footprint across {country}.{stack_mention}\n\n"
            f"Nexus-Pulse provides enterprise-grade estimating support, direct subcontractor pricing, and tender capacity for leading {clean_niche} enterprises.\n\n"
            f"Please let us know the right contact in your estimating/procurement department to forward our credentials.\n\n"
            f"Sincerely,\n"
            f"H.Huddair"
        )

    return {"subject": subject, "body": body}


class HumanApprovalGate:
    """
    Authoritative hold mechanism governing all outbound outreach channels.
    """

    def __init__(self):
        self.db = get_db_engine()
        self.scheduler = get_scheduler()
        self.rotator = get_inbox_rotator()

    def queue_outreach(
        self,
        lead_id: str,
        company_name: str,
        recipient: str,
        country: str,
        niche: str,
        channel: str = "EMAIL",
        tech_stack: Optional[List[str]] = None,
        custom_subject: Optional[str] = None,
        custom_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Places a lead into the mandatory Human Approval Gate (status: PENDING_APPROVAL).
        Computes the target country's local office hours.
        """
        tz_info = self.scheduler.get_target_local_time(country)
        copy = generate_personalized_copy(company_name, recipient, niche, country, tech_stack)
        subject = custom_subject or copy["subject"]
        body = custom_body or copy["body"]

        queue_id = str(uuid.uuid4())
        scheduled_for = self.scheduler.calculate_next_send_slot(country).isoformat()

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, lead_id, channel, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, scheduled_for
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL', ?, ?, ?)
            """, (
                queue_id, lead_id, channel, recipient, company_name, subject, body,
                country, tz_info["timezone_code"], scheduled_for
            ))
            conn.commit()

        return {
            "queue_id": queue_id,
            "status": "PENDING_APPROVAL",
            "company_name": company_name,
            "recipient": recipient,
            "channel": channel,
            "subject": subject,
            "target_country": country,
            "target_local_time": tz_info["current_local_time"],
            "scheduled_for": scheduled_for,
            "hold_message": "Item held in Human Approval Gate. Requires manual authorization from H.Huddair."
        }

    def approve_outreach_item(
        self,
        queue_id: str,
        approver: str = "h.huddair",
        edited_subject: Optional[str] = None,
        edited_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually approves an outreach item. Updates copy if edited.
        Status moves from PENDING_APPROVAL to APPROVED.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Outreach queue item '{queue_id}' not found.")

            if row["status"] not in ("PENDING_APPROVAL", "REJECTED"):
                return {"success": False, "message": f"Item is already in status: {row['status']}"}

            subj = edited_subject if edited_subject is not None else row["subject"]
            body = edited_body if edited_body is not None else row["message_body"]

            conn.execute("""
                UPDATE outreach_queue
                SET status = 'APPROVED',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    subject = ?,
                    message_body = ?
                WHERE id = ?
            """, (approver, subj, body, queue_id))
            conn.commit()

            return {
                "success": True,
                "queue_id": queue_id,
                "status": "APPROVED",
                "approved_by": approver,
                "recipient": row["recipient"]
            }

    def batch_approve_all(self, approver: str = "h.huddair") -> Dict[str, Any]:
        """Approves all currently pending items in the gate."""
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                UPDATE outreach_queue
                SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE status = 'PENDING_APPROVAL'
            """, (approver,))
            conn.commit()
            count = cur.rowcount
            return {"success": True, "items_approved": count, "approved_by": approver}

    def reject_outreach_item(self, queue_id: str, approver: str = "h.huddair") -> Dict[str, Any]:
        """Rejects outreach item, preventing dispatch."""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'REJECTED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approver, queue_id))
            conn.commit()
            return {"success": True, "queue_id": queue_id, "status": "REJECTED"}

    def dispatch_approved_outreach(self, queue_id: str) -> Dict[str, Any]:
        """
        Dispatches an approved outreach item through the Inbox Rotator.
        Enforces daily domain caps and schedules follow-up tracker.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Queue item '{queue_id}' not found.")

            if row["status"] not in ("APPROVED", "SCHEDULED"):
                raise PermissionError(f"CANNOT DISPATCH: Item is in '{row['status']}' state. Manual approval by H.Huddair required.")

            # Select available sending mailbox
            mb = self.rotator.get_next_available_mailbox()
            if not mb:
                return {
                    "success": False,
                    "reason": "ALL_MAILBOXES_AT_CAPACITY",
                    "message": "All sending inboxes have reached their daily limit (40-50). Queued for next reset."
                }

            # Increment mailbox count
            self.rotator.record_email_dispatched(mb["id"])

            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'SENT', sent_at = CURRENT_TIMESTAMP, mailbox_used = ?
                WHERE id = ?
            """, (mb["email_address"], queue_id))

            # Initialize 7-Day Follow-Up Sequence
            followup_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO followup_sequences (
                    id, lead_id, initial_outreach_id, recipient_email,
                    initial_sent_at, followup_due_at, status
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, datetime(CURRENT_TIMESTAMP, '+7 days'), 'PENDING')
            """, (followup_id, row["lead_id"] or queue_id, queue_id, row["recipient"]))

            conn.commit()

            return {
                "success": True,
                "queue_id": queue_id,
                "status": "SENT",
                "recipient": row["recipient"],
                "channel": row["channel"],
                "dispatched_via": mb["email_address"],
                "sent_at": now_iso,
                "followup_scheduled_for_days": 7
            }

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Lists all items currently held in the approval gate."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, lead_id, channel, recipient, company_name, subject,
                       message_body, status, target_country, target_timezone,
                       scheduled_for, created_at
                FROM outreach_queue
                WHERE status = 'PENDING_APPROVAL'
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_all_queue_items(self) -> List[Dict[str, Any]]:
        """Returns full queue including Approved, Sent, and Rejected items."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, lead_id, channel, recipient, company_name, subject,
                       message_body, status, target_country, scheduled_for,
                       approved_by, sent_at, mailbox_used, created_at
                FROM outreach_queue
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(r) for r in rows]


_global_approval_gate = None

def get_approval_gate() -> HumanApprovalGate:
    global _global_approval_gate
    if _global_approval_gate is None:
        _global_approval_gate = HumanApprovalGate()
    return _global_approval_gate
