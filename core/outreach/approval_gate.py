"""
Nexus-Pulse Enterprise Build
Outreach Engine: Human Approval Gate & Multi-Tenant Queue
Enforces the mandatory authorization hold: no email or contact form is dispatched
without manual human confirmation.
Integrates with Multi-Service Template Pool, Inbox Rotator with auto-switching,
and Timezone Smart Scheduler.
"""

import os
import re
import uuid
import urllib.parse
import smtplib
import logging
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine
from .scheduler import get_scheduler
from .inbox_rotator import get_inbox_rotator
from .template_manager import get_template_manager
from .blacklist_manager import get_blacklist_manager, is_public_email_domain, PUBLIC_EMAIL_DOMAINS
from core.hygiene.lead_validator import LeadValidationFilter

logger = logging.getLogger("nexus.approval_gate")


def _send_webhook_request(webhook_url: str, payload: dict, max_retries: int = 3) -> dict:
    """
    Sends HTTPS POST request to Webhook relay with retry queue and exponential backoff.
    Follows redirects and validates live 200 OK payload confirmation.
    Handles errors cleanly to avoid spamming deploy logs.
    """
    import time
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            try:
                import httpx
                with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                    resp = client.post(webhook_url, json=payload)
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                            if isinstance(data, dict):
                                return data
                            return {"status": "success", "response": data}
                        except Exception:
                            return {"status": "success", "raw": resp.text}
                    else:
                        last_err = f"HTTP {resp.status_code}: {resp.text[:100]}"
            except ImportError:
                import requests
                resp = requests.post(webhook_url, json=payload, allow_redirects=True, timeout=15.0)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, dict):
                            return data
                        return {"status": "success", "response": data}
                    except Exception:
                        return {"status": "success", "raw": resp.text}
                else:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)}"

        if attempt < max_retries:
            backoff_sleep = 0.5 * (2 ** (attempt - 1))
            time.sleep(backoff_sleep)

    logger.warning(f"[WEBHOOK RELAY] Delivery attempt failed after {max_retries} retries ({last_err})")
    return {"status": "error", "message": f"Webhook relay failed after {max_retries} attempts: {last_err}"}


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
        domain = recipient.split("@")[-1] if "@" in recipient else None

        # 0. Drop junk domains & invalid system prefixes
        if domain and LeadValidationFilter.is_junk_domain(domain):
            return {
                "queue_id": None,
                "status": "DROPPED",
                "reason": "JUNK_DOMAIN",
                "message": f"Recipient domain '{domain}' dropped as junk/tracker domain."
            }
        is_em_valid, clean_recip, em_reason = LeadValidationFilter.sanitize_and_validate_email(recipient, domain)
        if not is_em_valid:
            return {
                "queue_id": None,
                "status": "DROPPED",
                "reason": "INVALID_EMAIL_PREFIX",
                "message": f"Recipient '{recipient}' dropped: {em_reason}"
            }
        recipient = clean_recip
        company_name = LeadValidationFilter.clean_company_name(company_name, domain or "")

        # 1. Compliance & Deduplication Guard: Check Pipeline, Sent history, Blacklist & Suppression
        with self.db.get_connection() as conn:
            is_dup_guard, guard_reason = LeadValidationFilter.is_lead_duplicate_or_blacklisted(
                recipient, conn, domain=domain
            )
            if is_dup_guard:
                return {
                    "queue_id": None,
                    "status": "DUPLICATE",
                    "reason": guard_reason,
                    "message": f"Recipient '{recipient}' blocked by Deduplication Guard: {guard_reason}"
                }

        is_bl, bl_reason = self.blacklist_manager.is_domain_blacklisted(recipient)
        if is_bl:
            return {
                "queue_id": None,
                "status": "SUPPRESSED",
                "reason": bl_reason,
                "message": f"Recipient '{recipient}' is blocked by blacklist rule."
            }

        with self.db.get_connection() as conn:
            recip_dom = recipient.split("@")[-1].lower() if "@" in recipient else recipient.lower()
            if is_public_email_domain(recip_dom):
                suppressed = conn.execute("""
                    SELECT reason FROM suppressed_entities
                    WHERE lower(entity) = lower(?)
                """, (recipient.lower(),)).fetchone()
            else:
                suppressed = conn.execute("""
                    SELECT reason FROM suppressed_entities
                    WHERE lower(entity) = lower(?) OR lower(entity) = lower(?)
                """, (recipient.lower(), recip_dom)).fetchone()
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
        # Use full application base URL so unsubscribe links work outside Railway's proxy
        _app_base = os.getenv("APP_BASE_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN", os.getenv("RAILWAY_STATIC_URL", "nexus-pulse-production.up.railway.app"))).strip()
        if _app_base and not _app_base.startswith("http"):
            _app_base = f"https://{_app_base}"
        _unsub_email = urllib.parse.quote(recipient, safe="")
        unsub_link = f"{_app_base}/api/unsubscribe?token={tracking_id}&email={_unsub_email}"

        # 3. Dynamic Template & Mailbox Matching
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

        # Automatically map lead to matching available mailbox
        mb = self.rotator.get_next_available_mailbox(operator_id=operator_id)
        mailbox_assigned = mb["email_address"] if mb else None

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO outreach_queue (
                    id, lead_id, channel, recipient, company_name, subject, message_body,
                    status, target_country, target_timezone, scheduled_for, operator_id,
                    tracking_id, mailbox_used, industry_niche
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL', ?, ?, ?, ?, ?, ?, ?)
            """, (
                queue_id, lead_id, channel, recipient, company_name, subject, body,
                country, tz_info["timezone_code"], scheduled_for, operator_id,
                tracking_id, mailbox_assigned, niche
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
        edited_recipient: Optional[str] = None,
        edited_company_name: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually authorizes an outreach item.
        Persists updated recipient_email, company_name, subject, and message_body before approving.
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
            recipient = edited_recipient.strip() if edited_recipient and edited_recipient.strip() else row["recipient"]
            company = edited_company_name.strip() if edited_company_name and edited_company_name.strip() else row["company_name"]

            # If recipient was edited, update unsubscribe link in message body so it reflects actual recipient
            if edited_recipient and edited_recipient.strip() and edited_recipient.strip().lower() != row["recipient"].strip().lower():
                old_enc = urllib.parse.quote(row["recipient"].strip(), safe="")
                new_enc = urllib.parse.quote(recipient, safe="")
                if f"email={old_enc}" in body:
                    body = body.replace(f"email={old_enc}", f"email={new_enc}")
                elif f"email={row['recipient'].strip()}" in body:
                    body = body.replace(f"email={row['recipient'].strip()}", f"email={new_enc}")
                else:
                    body = re.sub(r'(api/unsubscribe\?[^"\s\n]*email=)[^"&\s\n]+', rf'\g<1>{new_enc}', body)

            conn.execute("""
                UPDATE outreach_queue
                SET status = 'APPROVED',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    subject = ?,
                    message_body = ?,
                    recipient = ?,
                    company_name = ?
                WHERE id = ?
            """, (approver, subj, body, recipient, company, queue_id))
            conn.commit()

            return {
                "success": True,
                "queue_id": queue_id,
                "status": "APPROVED",
                "approved_by": approver,
                "recipient": recipient,
                "company_name": company
            }

    def delete_queue_item(self, queue_id: str, operator_id: Optional[str] = None) -> Dict[str, Any]:
        """Permanently deletes an individual lead from the outreach queue in 1 click."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT id, operator_id, recipient, company_name FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Queue item '{queue_id}' not found.")
            if operator_id and row["operator_id"] and row["operator_id"] != operator_id:
                raise PermissionError("Access denied: You cannot delete outreach for another tenant.")
            conn.execute("DELETE FROM outreach_queue WHERE id = ?", (queue_id,))
            conn.commit()
            return {"success": True, "deleted_id": queue_id, "recipient": row["recipient"]}

    def purge_unapproved_items(self, operator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk Purge ('Clear Unapproved Gate'):
        Wipes all pending/unapproved leads held in the gate so a fresh hunt can run cleanly.
        """
        with self.db.get_connection() as conn:
            if operator_id:
                cur = conn.execute("""
                    DELETE FROM outreach_queue
                    WHERE status = 'PENDING_APPROVAL' AND (operator_id = ? OR operator_id IS NULL)
                """, (operator_id,))
            else:
                cur = conn.execute("""
                    DELETE FROM outreach_queue
                    WHERE status = 'PENDING_APPROVAL'
                """)
            conn.commit()
            return {"success": True, "purged_count": cur.rowcount}

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

    def dispatch_approved_outreach(
        self,
        queue_id: str,
        operator_id: Optional[str] = None,
        bypass_window: bool = True
    ) -> Dict[str, Any]:
        """
        Dispatches an approved outreach item.
        Uses Google Apps Script HTTPS Webhook relay if configured (bypassing Railway SMTP port block),
        or falls back to live SMTP transmission.
        Enforces daily domain caps and auto-switching across active profiles.
        Accurately logs delivery only on confirmed dispatch.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Queue item '{queue_id}' not found.")

            # Convert sqlite3.Row to dict for safe attribute access
            row = dict(row)

            target_op = operator_id or row.get("operator_id")
            if operator_id and row.get("operator_id") and row.get("operator_id") != operator_id:
                raise PermissionError("Access denied: You cannot dispatch outreach for another tenant.")

            if row["status"] not in ("APPROVED", "SCHEDULED", "FAILED"):
                raise PermissionError(f"CANNOT DISPATCH: Item is in '{row['status']}' state. Manual approval required.")

            recip_clean = row["recipient"].strip().lower()
            recip_dom = recip_clean.split("@")[-1] if "@" in recip_clean else recip_clean
            is_pub = is_public_email_domain(recip_dom)

            # 1. Compliance & Unsubscribe Checks (MongoDB + SQLite + Blacklist)
            is_unsub = False
            try:
                from database.mongo_engine import get_mongo_engine
                mongo = get_mongo_engine()
                if mongo.is_unsubscribed(recip_clean) or (not is_pub and mongo.is_unsubscribed(recip_dom)):
                    is_unsub = True
            except Exception:
                pass

            if not is_unsub and row.get("unsubscribed"):
                is_unsub = True

            is_bl, bl_reason = self.blacklist_manager.is_domain_blacklisted(recip_clean)

            if is_pub:
                suppressed_entry = conn.execute("""
                    SELECT reason FROM suppressed_entities
                    WHERE lower(entity) = ?
                """, (recip_clean,)).fetchone()
            else:
                suppressed_entry = conn.execute("""
                    SELECT reason FROM suppressed_entities
                    WHERE lower(entity) = ? OR lower(entity) = ?
                """, (recip_clean, recip_dom)).fetchone()

            if is_unsub or is_bl or suppressed_entry:
                sup_reason = "UNSUBSCRIBE" if is_unsub else (bl_reason or suppressed_entry["reason"])
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'SUPPRESSED', scheduled_for = NULL, bounce_reason = ?
                    WHERE id = ?
                """, (f"Suppressed: {sup_reason}", queue_id))
                conn.commit()
                logger.info(f"[DISPATCH SUPPRESSED] {recip_clean} blocked by compliance guard ({sup_reason}).")
                return {
                    "success": False,
                    "status": "SUPPRESSED",
                    "reason": f"Recipient or domain is suppressed/unsubscribed: {sup_reason}",
                    "recipient": recip_clean
                }

            # 2. Operational Working Hours Check (9 AM - 5 PM local recipient time)
            country = row["target_country"] or "United Kingdom"
            tz_eval = self.scheduler.get_target_local_time(country=country, domain=recip_dom, bypass_window=bypass_window)
            if not tz_eval.get("is_in_send_window") and not bypass_window:
                next_slot = self.scheduler.calculate_next_send_slot(country=country, domain=recip_dom, bypass_window=False)
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'SCHEDULED', scheduled_for = ?
                    WHERE id = ?
                """, (next_slot.isoformat(), queue_id))
                conn.commit()
                logger.info(f"[DISPATCH OFF-HOURS] {recip_clean} is outside operational hours ({tz_eval.get('current_local_time')}). Scheduled for {next_slot.isoformat()}.")
                return {
                    "success": False,
                    "status": "SCHEDULED",
                    "reason": "OFF_HOURS_BLOCKED",
                    "message": f"Recipient local time is outside operational hours (9 AM - 5 PM). Scheduled for {next_slot.isoformat()}.",
                    "scheduled_for": next_slot.isoformat(),
                    "recipient": recip_clean
                }

            # Dynamic Mailbox Credential Lookup: Reads live credentials directly from database at execution time
            mb_record = None
            if row["mailbox_used"]:
                mb_record = conn.execute("""
                    SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                           operator_id, smtp_host, smtp_port, smtp_username, smtp_password,
                           COALESCE(webhook_url, '') as webhook_url
                    FROM mailbox_rotator
                    WHERE (email_address = ? OR id = ?) AND is_active = 1 AND sent_today < daily_limit
                """, (row["mailbox_used"], row["mailbox_used"])).fetchone()

            if not mb_record:
                mb_dyn = self.rotator.get_next_available_mailbox(operator_id=target_op)
                if mb_dyn:
                    mb_record = conn.execute("""
                        SELECT id, email_address, display_name, domain, daily_limit, sent_today,
                               operator_id, smtp_host, smtp_port, smtp_username, smtp_password,
                               COALESCE(webhook_url, '') as webhook_url
                        FROM mailbox_rotator
                        WHERE id = ? AND is_active = 1 AND sent_today < daily_limit
                    """, (mb_dyn["id"],)).fetchone()

            if not mb_record:
                any_mb = conn.execute("SELECT count(*) as cnt FROM mailbox_rotator WHERE is_active = 1").fetchone()
                if any_mb and any_mb["cnt"] > 0:
                    return {
                        "success": False,
                        "reason": "ALL_MAILBOXES_AT_CAPACITY",
                        "message": "All sending inboxes have reached their daily limit (40-50). Queued for next quota reset."
                    }
                else:
                    return {
                        "success": False,
                        "reason": "NO_ACTIVE_MAILBOX",
                        "message": "No active mailbox enrolled in rotator. Please add an active mailbox with SMTP credentials."
                    }

            mb = dict(mb_record)

            # Mailbox configuration
            smtp_host = (mb.get("smtp_host") or "").strip() or "smtp.gmail.com"
            smtp_port = int(mb.get("smtp_port") or 587)
            sender_email = (mb.get("email_address") or "").strip()
            smtp_user = (mb.get("smtp_username") or "").strip() or sender_email
            raw_pwd = mb.get("smtp_password") or ""
            # App Password Sanitization: strip all accidental whitespace
            smtp_pwd = re.sub(r'\s+', '', raw_pwd)
            display_name = (mb.get("display_name") or "").strip()

            # Unsubscribe / Opt-Out Compliance Footer & Base URL / Recipient Email Accuracy
            _app_base = os.getenv("APP_BASE_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN", "")).strip()
            if _app_base and not _app_base.startswith("http"):
                _app_base = f"https://{_app_base}"
            recip_actual = recip_clean
            recip_encoded = urllib.parse.quote(recip_actual, safe="")

            opt_out_footer = '\n\n---\nNot interested? Reply "STOP" and we will immediately remove you from our outreach list.'
            msg_body = row["message_body"] or ""
            if _app_base and "/api/unsubscribe" in msg_body:
                msg_body = re.sub(
                    r'(https?://[^\s"\'<>]+)?/api/unsubscribe',
                    lambda m: m.group(0) if (m.group(1) and m.group(1).startswith("http")) else f"{_app_base}/api/unsubscribe",
                    msg_body
                )
            if "api/unsubscribe?" in msg_body:
                msg_body = re.sub(r'(api/unsubscribe\?[^"\s\n]*email=)[^"&\s\n]+', rf'\g<1>{recip_encoded}', msg_body)

            if 'Reply "STOP"' not in msg_body and 'reply "stop"' not in msg_body.lower():
                msg_body = msg_body.rstrip() + opt_out_footer

            # Build MIME Message (used for message ID and SMTP fallback)
            msg = MIMEText(msg_body, "plain", "utf-8")
            if display_name:
                msg["From"] = f"{display_name} <{sender_email}>"
            else:
                msg["From"] = sender_email
            msg["To"] = recip_actual
            msg["Subject"] = row["subject"]
            msg["Date"] = formatdate(localtime=True)
            sender_domain = sender_email.split("@")[-1] if "@" in sender_email else "gmail.com"
            tracking_id = row["tracking_id"] or str(uuid.uuid4())
            msg_id_val = f"<{tracking_id}@{sender_domain}>"
            msg["Message-ID"] = msg_id_val

            # Priority 1: Check if Mailbox has its own Webhook URL, or fall back to GMAIL_WEBHOOK_URL env
            mailbox_webhook = (mb.get("webhook_url") or "").strip()
            env_webhook = os.getenv("GMAIL_WEBHOOK_URL", "").strip()
            active_webhook = mailbox_webhook or env_webhook

            dispatched_successfully = False
            dispatch_method = "SMTP"
            webhook_err_msg = None

            if active_webhook:
                webhook_secret = os.getenv("GMAIL_WEBHOOK_SECRET", "NEXUS_PULSE_2026")
                payload = {
                    "secret": webhook_secret,
                    "to": row["recipient"].strip(),
                    "recipient": row["recipient"].strip(),
                    "subject": row["subject"],
                    "body": msg_body,
                    "html_body": msg_body.replace("\n", "<br>"),
                    "sender_name": display_name or "H.Huddair"
                }
                try:
                    logger.info(f"[WEBHOOK DISPATCH] Posting to Apps Script relay for {sender_email} -> {row['recipient']}...")
                    resp_json = _send_webhook_request(active_webhook, payload)
                    is_success = False
                    if isinstance(resp_json, dict):
                        st = str(resp_json.get("status", "")).strip().lower()
                        ok_val = resp_json.get("ok")
                        succ_val = resp_json.get("success")
                        if (
                            ok_val is True
                            or succ_val is True
                            or st in ("success", "ok", "delivered", "sent")
                        ):
                            is_success = True
                        elif "raw" in resp_json and any(kw in str(resp_json["raw"]).lower() for kw in ("success", "ok")):
                            is_success = True

                    if is_success:
                        dispatched_successfully = True
                        dispatch_method = "WEBHOOK"
                        logger.info(f"[WEBHOOK RELAY 200 OK] Dispatched outreach to {row['recipient']} via {sender_email}.")
                    else:
                        webhook_err_msg = resp_json.get("message") or resp_json.get("error") if isinstance(resp_json, dict) else str(resp_json)
                        logger.warning(f"[WEBHOOK RELAY] Status: {webhook_err_msg}. Falling back to SMTP...")
                except Exception as wh_ex:
                    webhook_err_msg = f"{type(wh_ex).__name__}: {str(wh_ex)}"
                    logger.warning(f"[WEBHOOK RELAY] {webhook_err_msg}. Falling back to SMTP...")

            # Priority 2: Fallback to SMTP transmission if webhook was not active or failed
            if not dispatched_successfully:
                if not smtp_user or not smtp_pwd:
                    err_msg = f"Mailbox '{sender_email}' is missing SMTP credentials (username or App Password)."
                    if webhook_err_msg:
                        err_msg += f" (Webhook attempt also failed: {webhook_err_msg})"
                    logger.error(f"[DISPATCH FAILED] {err_msg}")
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'APPROVED', bounce_reason = ?
                        WHERE id = ?
                    """, (f"Dispatch Error: {err_msg}", queue_id))
                    try:
                        conn.execute("""
                            INSERT INTO operator_sessions (user_id, username, action, detail, device_id)
                            VALUES (?, ?, 'DISPATCH_ERROR', ?, 'CLOUD_RELAY')
                        """, (
                            target_op or "system",
                            row.get("approved_by") or "operator",
                            f"Missing credentials for {recip_clean} via {sender_email}: {err_msg}"
                        ))
                    except Exception:
                        pass
                    conn.commit()
                    return {
                        "success": False,
                        "reason": "MISSING_CREDENTIALS",
                        "message": err_msg,
                        "recipient": row["recipient"],
                        "dispatched_via": sender_email
                    }

                try:
                    logger.info(f"[SMTP DISPATCH] Connecting securely to {smtp_host}:{smtp_port} for {sender_email} -> {row['recipient']}...")
                    if smtp_port == 465:
                        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=25.0)
                        server.ehlo()
                    else:
                        server = smtplib.SMTP(smtp_host, smtp_port, timeout=25.0)
                        server.ehlo()
                        server.starttls()
                        server.ehlo()

                    server.login(smtp_user, smtp_pwd)
                    send_errs = server.sendmail(sender_email, [row["recipient"].strip()], msg.as_string())
                    server.quit()

                    if send_errs:
                        raise smtplib.SMTPException(f"Recipients refused by server: {send_errs}")

                    dispatched_successfully = True
                    dispatch_method = "SMTP"
                    logger.info(f"[SMTP DISPATCH SUCCESS 250 OK] Email dispatched to {row['recipient']} via {sender_email}.")

                except Exception as smtp_ex:
                    err_details = f"{type(smtp_ex).__name__}: {str(smtp_ex)}"
                    if webhook_err_msg:
                        err_details += f" (Webhook also failed: {webhook_err_msg})"
                    logger.error(f"[SMTP DISPATCH FAILED] Error transmitting to {row['recipient']}: {err_details}", exc_info=True)
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'APPROVED', bounce_reason = ?
                        WHERE id = ?
                    """, (f"Dispatch Error: {err_details}", queue_id))
                    try:
                        conn.execute("""
                            INSERT INTO operator_sessions (user_id, username, action, detail, device_id)
                            VALUES (?, ?, 'DISPATCH_ERROR', ?, 'CLOUD_RELAY')
                        """, (
                            target_op or "system",
                            row.get("approved_by") or "operator",
                            f"Dispatch failed for {recip_clean} via {sender_email}: {err_details}"
                        ))
                    except Exception:
                        pass
                    conn.commit()
                    return {
                        "success": False,
                        "reason": "DISPATCH_FAILED",
                        "message": f"Dispatch failed: {err_details}",
                        "recipient": row["recipient"],
                        "dispatched_via": sender_email
                    }

            # Increment daily send counter for this mailbox
            self.rotator.record_email_dispatched(mb["id"])
            new_sent_today = mb["sent_today"] + 1
            remaining_quota = max(0, mb["daily_limit"] - new_sent_today)

            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'SENT', sent_at = CURRENT_TIMESTAMP, dispatched_at = CURRENT_TIMESTAMP, mailbox_used = ?, message_body = ?, bounce_reason = NULL, message_id = ?
                WHERE id = ?
            """, (sender_email, msg_body, msg_id_val, queue_id))

            # Record in operator_sessions audit log
            try:
                conn.execute("""
                    INSERT INTO operator_sessions (user_id, username, action, detail, device_id)
                    VALUES (?, ?, 'DISPATCH_EMAIL', ?, 'CLOUD_RELAY')
                """, (
                    target_op or "system",
                    row.get("approved_by") or "operator",
                    f"Dispatched {dispatch_method} outreach to {recip_clean} via {sender_email} (queue_id: {queue_id})"
                ))
            except Exception:
                pass

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
                "dispatched_via": sender_email,
                "sent_at": now_iso,
                "followup_scheduled_for_days": 7,
                "delivery_method": dispatch_method,
                "mailbox_daily_limit": mb["daily_limit"],
                "sent_today": new_sent_today,
                "remaining_daily_quota": remaining_quota
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
                WHERE status IN ('APPROVED', 'SCHEDULED', 'FAILED')
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
        import time

        for idx, r in enumerate(rows):
            q_id = r["id"]
            country = r["target_country"]
            recipient = r["recipient"]
            domain = recipient.split("@")[-1] if recipient and "@" in recipient else None

            # Check if within local working hours
            tz_eval = self.scheduler.get_target_local_time(country=country, domain=domain, bypass_window=bypass_window)

            if tz_eval["is_in_send_window"]:
                # Attempt dispatch with forwarded bypass_window flag
                try:
                    res = self.dispatch_approved_outreach(q_id, operator_id=r["operator_id"], bypass_window=bypass_window)
                    if res.get("success"):
                        dispatched.append({
                            "queue_id": q_id,
                            "recipient": recipient,
                            "dispatched_via": res.get("dispatched_via")
                        })
                        # 1.5s sequential batch delay to prevent rate-limiting or concurrency conflicts
                        if idx < len(rows) - 1:
                            time.sleep(1.5)
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
                           scheduled_for, operator_id, created_at,
                           COALESCE(industry_niche, 'Commercial Construction') as industry_niche,
                           COALESCE(industry_niche, 'Commercial Construction') as niche
                    FROM outreach_queue
                    WHERE status = 'PENDING_APPROVAL' AND (operator_id = ? OR operator_id IS NULL)
                    ORDER BY created_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, target_timezone,
                           scheduled_for, operator_id, created_at,
                           COALESCE(industry_niche, 'Commercial Construction') as industry_niche,
                           COALESCE(industry_niche, 'Commercial Construction') as niche
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
                           opened_at, bounced_at, bounce_reason, created_at,
                           COALESCE(industry_niche, 'Commercial Construction') as industry_niche,
                           COALESCE(industry_niche, 'Commercial Construction') as niche
                    FROM outreach_queue
                    WHERE operator_id = ? OR operator_id IS NULL
                    ORDER BY created_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, channel, recipient, company_name, subject,
                           message_body, status, target_country, scheduled_for,
                           approved_by, sent_at, mailbox_used, operator_id,
                           opened_at, bounced_at, bounce_reason, created_at,
                           COALESCE(industry_niche, 'Commercial Construction') as industry_niche,
                           COALESCE(industry_niche, 'Commercial Construction') as niche
                    FROM outreach_queue
                    ORDER BY created_at DESC
                """).fetchall()
            return [dict(r) for r in rows]

    def unblock_lead(self, queue_id: str, operator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Unblocks a suppressed lead and restores it to PENDING_APPROVAL.
        Clears associated suppression records and blacklist rules for the exact recipient.
        """
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM outreach_queue WHERE id = ?", (queue_id,)).fetchone()
            if not row:
                raise ValueError(f"Queue item '{queue_id}' not found.")
            row = dict(row)

            if operator_id and row.get("operator_id") and row.get("operator_id") != operator_id:
                raise PermissionError("Access denied: You cannot unblock leads for another tenant.")

            recipient = row["recipient"].strip().lower()

            # 1. Reset outreach_queue
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL, scheduled_for = NULL
                WHERE id = ?
            """, (queue_id,))

            # 2. Clear exact email suppression in suppressed_entities and dnc_blacklist
            conn.execute("DELETE FROM suppressed_entities WHERE lower(entity) = ?", (recipient,))
            conn.execute("DELETE FROM dnc_blacklist WHERE lower(entity) = ?", (recipient,))

            # 3. Clear exact pattern from blacklist_rules
            conn.execute("DELETE FROM blacklist_rules WHERE lower(pattern) = ?", (recipient,))

            # 4. Clear unsubscription in vault_leads
            conn.execute("UPDATE vault_leads SET unsubscribed = 0 WHERE lower(primary_email) = ?", (recipient,))
            conn.commit()

        # 5. Clear unsubscription in MongoDB if connected
        try:
            from database.mongo_engine import get_mongo_engine
            mongo = get_mongo_engine()
            if mongo and mongo.db is not None:
                mongo.db.leads.update_many(
                    {"primary_email": recipient},
                    {"$set": {"unsubscribed": False, "unsubscribed_at": None}}
                )
        except Exception:
            pass

        return {
            "success": True,
            "message": f"Lead '{recipient}' unblocked and returned to Approval Hold.",
            "queue_id": queue_id,
            "status": "PENDING_APPROVAL",
            "recipient": recipient
        }


_global_approval_gate = None

def get_approval_gate() -> HumanApprovalGate:
    global _global_approval_gate
    if _global_approval_gate is None:
        _global_approval_gate = HumanApprovalGate()
    return _global_approval_gate
