"""
Nexus-Pulse Enterprise Build
Outreach Engine: Human Approval Gate & Multi-Tenant Queue
Enforces the mandatory authorization hold: no email or contact form is dispatched
without manual human confirmation.
Integrates with Multi-Service Template Pool, Inbox Rotator with auto-switching,
and Timezone Smart Scheduler.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine
from .scheduler import get_scheduler
from .inbox_rotator import get_inbox_rotator
from .template_manager import get_template_manager
from .blacklist_manager import get_blacklist_manager


def generate_personalized_copy(
    company_name: str,
    recipient_email: str,
    niche: str,
    country: str,
    tech_stack: Optional[List[str]] = None,
    operator_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Generates dynamic personalized proposal copy using the Multi-Service Template Pool.
    Interpolates variables without hardcoded sender text.
    """
    tm = get_template_manager()
    return tm.match_and_render_template(
        operator_id=operator_id,
        niche=niche,
        company_name=company_name,
        recipient_email=recipient_email,
        country=country,
        tech_stack=tech_stack
    )


class HumanApprovalGate:
    """
    Mandatory human-in-the-loop authorization gate governing all outbound outreach channels.
    Holds leads in PENDING_APPROVAL until approved by operator or admin.
    """

    def __init__(self):
        self.db = get_db_engine()
        self.scheduler = get_scheduler()
        self.rotator = get_inbox_rotator()
        self.template_manager = get_template_manager()
        self.blacklist_manager = get_blacklist_manager()

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
        custom_body: Optional[str] = None,
        operator_id: Optional[str] = None,
        city: str = ""
    ) -> Dict[str, Any]:
        """
        Places a lead into the mandatory Human Approval Gate (status: PENDING_APPROVAL).
        Computes regional working hours and renders custom or matched template copy.
        """
        # 1. Compliance: Check Blacklist & Suppression
        is_bl, bl_reason = self.blacklist_manager.is_domain_blacklisted(recipient)
        if is_bl:
            return {
                "queue_id": None,
                "status": "SUPPRESSED",
                "reason": bl_reason,
                "message": f"Recipient '{recipient}' is blocked by blacklist rule."
            }

        with self.db.get_connection() as conn:
            suppressed = conn.execute("""
                SELECT reason FROM suppressed_entities
                WHERE lower(entity) = lower(?) OR lower(entity) = lower(?)
            """, (recipient.lower(), recipient.split("@")[-1].lower() if "@" in recipient else recipient.lower())).fetchone()
            if suppressed:
                return {
                    "queue_id": None,
                    "status": "SUPPRESSED",
                    "reason": suppressed["reason"],
                    "message": f"Recipient '{recipient}' is on global suppression list ({suppressed['reason']})."
                }

        # 2. Regional timezone calculations
        domain = recipient.split("@")[-1] if "@" in recipient else None
        tz_info = self.scheduler.get_target_local_time(country=country, domain=domain)
        scheduled_for = self.scheduler.calculate_next_send_slot(country=country, domain=domain).isoformat()

        queue_id = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        unsub_link = f"/api/unsubscribe?token={tracking_id}&email={recipient}"

        # 3. Dynamic Template Matching (User-defined or parameters)
        if custom_subject and custom_body:
            subject = custom_subject.replace("{{unsubscribe_link}}", unsub_link)
            body = custom_body.replace("{{unsubscribe_link}}", unsub_link)
        else:
            rendered = self.template_manager.match_and_render_template(
                operator_id=operator_id,
                niche=niche,
                company_name=company_name,
                recipient_email=recipient,
                country=country,
                city=city,
                tech_stack=tech_stack,
                unsubscribe_url=unsub_link
            )
            subject = rendered["subject"]
            body = rendered["body"]

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, lead_id, channel, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, scheduled_for, operator_id,
                    tracking_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL', ?, ?, ?, ?, ?)
            """, (
                queue_id, lead_id, channel, recipient, company_name, subject, body,
                country, tz_info["timezone_code"], scheduled_for, operator_id,
                tracking_id
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
            "operator_id": operator_id,
            "hold_message": "Item held in Human Approval Gate. Requires manual human authorization before dispatch."
        }

    def approve_outreach_item(
        self,
        queue_id: str,
        approver: str = "operator",
        edited_subject: Optional[str] = None,
        edited_body: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually authorizes an outreach item.
        Transitions status from PENDING_APPROVAL to APPROVED.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Outreach queue item '{queue_id}' not found.")

            # Tenant check
            if operator_id and row["operator_id"] and row["operator_id"] != operator_id:
                raise PermissionError("Access denied: You cannot approve outreach for another tenant.")

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

    def batch_approve_all(self, approver: str = "operator", operator_id: Optional[str] = None) -> Dict[str, Any]:
        """Approves all currently pending items in the gate for this tenant or globally for admin."""
        with self.db.get_connection() as conn:
            if operator_id:
                cur = conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                    WHERE status = 'PENDING_APPROVAL' AND (operator_id = ? OR operator_id IS NULL)
                """, (approver, operator_id))
            else:
                cur = conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                    WHERE status = 'PENDING_APPROVAL'
                """, (approver,))

            conn.commit()
            return {"success": True, "items_approved": cur.rowcount, "approved_by": approver}

    def reject_outreach_item(self, queue_id: str, approver: str = "operator", operator_id: Optional[str] = None) -> Dict[str, Any]:
        """Rejects outreach item, preventing dispatch."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT operator_id FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Item '{queue_id}' not found.")
            if operator_id and row["operator_id"] and row["operator_id"] != operator_id:
                raise PermissionError("Access denied: You cannot reject outreach for another tenant.")

            conn.execute("""
                UPDATE outreach_queue
                SET status = 'REJECTED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approver, queue_id))
            conn.commit()
            return {"success": True, "queue_id": queue_id, "status": "REJECTED"}

    def dispatch_approved_outreach(self, queue_id: str, operator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Dispatches an approved outreach item through the Inbox Rotator.
        Enforces daily domain caps and auto-switching across active profiles.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Queue item '{queue_id}' not found.")

            target_op = operator_id or row["operator_id"]
            if operator_id and row["operator_id"] and row["operator_id"] != operator_id:
                raise PermissionError("Access denied: You cannot dispatch outreach for another tenant.")

            if row["status"] not in ("APPROVED", "SCHEDULED"):
                raise PermissionError(f"CANNOT DISPATCH: Item is in '{row['status']}' state. Manual approval required.")

            # Select available sending mailbox with auto-switching
            mb = self.rotator.get_next_available_mailbox(operator_id=target_op)
            if not mb:
                return {
                    "success": False,
                    "reason": "ALL_MAILBOXES_AT_CAPACITY",
                    "message": "All sending inboxes have reached their daily limit (40-50). Queued for next quota reset."
                }

            # Increment mailbox quota count
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

    def dispatch_ready_queue(
        self,
        bypass_window: bool = False,
        operator_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dispatches all approved or scheduled outreach leads whose target local window
        is currently active (9:00 AM - 5:00 PM local time on weekdays) OR if bypass_window is True.
        """
        with self.db.get_connection() as conn:
            query = """
                SELECT id, target_country, recipient, status, operator_id, scheduled_for
                FROM outreach_queue
                WHERE status IN ('APPROVED', 'SCHEDULED')
            """
            params: List[Any] = []
            if operator_id:
                query += " AND (operator_id = ? OR operator_id IS NULL)"
                params.append(operator_id)
            query += " ORDER BY created_at ASC"
            if limit:
                query += f" LIMIT {int(limit)}"

            rows = conn.execute(query, params).fetchall()

        dispatched = []
        scheduled = []
        errors = []

        for r in rows:
            q_id = r["id"]
            country = r["target_country"]
            recipient = r["recipient"]
            domain = recipient.split("@")[-1] if recipient and "@" in recipient else None

            # Check if within local working hours
            tz_eval = self.scheduler.get_target_local_time(country=country, domain=domain, bypass_window=bypass_window)

            if tz_eval["is_in_send_window"]:
                # Attempt dispatch
                try:
                    res = self.dispatch_approved_outreach(q_id, operator_id=r["operator_id"])
                    if res.get("success"):
                        dispatched.append({
                            "queue_id": q_id,
                            "recipient": recipient,
                            "dispatched_via": res.get("dispatched_via")
                        })
                    else:
                        errors.append({
                            "queue_id": q_id,
                            "reason": res.get("reason", "DISPATCH_FAILED"),
                            "message": res.get("message")
                        })
                        if res.get("reason") == "ALL_MAILBOXES_AT_CAPACITY":
                            # Stop attempting remaining dispatches if mailboxes are full
                            break
                except Exception as e:
                    errors.append({"queue_id": q_id, "reason": "EXCEPTION", "message": str(e)})
            else:
                # Update scheduled_for to next valid window
                next_slot = self.scheduler.calculate_next_send_slot(country=country, domain=domain, bypass_window=False)
                with self.db.get_connection() as conn:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'SCHEDULED', scheduled_for = ?
                        WHERE id = ? AND status = 'APPROVED'
                    """, (next_slot.isoformat(), q_id))
                    conn.commit()
                scheduled.append({
                    "queue_id": q_id,
                    "recipient": recipient,
                    "scheduled_for": next_slot.isoformat(),
                    "target_country": country
                })

        return {
            "success": True,
            "dispatched_count": len(dispatched),
            "scheduled_count": len(scheduled),
            "error_count": len(errors),
            "dispatched_items": dispatched,
            "scheduled_items": scheduled,
            "errors": errors,
            "bypass_window": bypass_window
        }

    def get_pending_approvals(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists items held in the approval gate, filtered by tenant."""
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, target_timezone,
                           scheduled_for, operator_id, created_at
                    FROM outreach_queue
                    WHERE status = 'PENDING_APPROVAL' AND (operator_id = ? OR operator_id IS NULL)
                    ORDER BY created_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, target_timezone,
                           scheduled_for, operator_id, created_at
                    FROM outreach_queue
                    WHERE status = 'PENDING_APPROVAL'
                    ORDER BY created_at DESC
                """).fetchall()
            return [dict(r) for r in rows]

    def get_all_queue_items(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns full queue items, filtered by tenant."""
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, scheduled_for,
                           approved_by, sent_at, mailbox_used, operator_id,
                           opened_at, bounced_at, bounce_reason, created_at
                    FROM outreach_queue
                    WHERE operator_id = ? OR operator_id IS NULL
                    ORDER BY created_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, scheduled_for,
                           approved_by, sent_at, mailbox_used, operator_id,
                           opened_at, bounced_at, bounce_reason, created_at
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
