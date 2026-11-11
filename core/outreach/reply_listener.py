"""
Nexus-Pulse Enterprise Build
Outreach Engine: IMAP Reply Listener, Bounce Detector & Compliance Suppression
Monitors inbound responses, classifies sentiment, issues instant Hot Lead alerts,
flags delivery bounces with lead suppression, and enforces CAN-SPAM / GDPR opt-out compliance.
"""

import re
import uuid
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from database.db_engine import get_db_engine
from .blacklist_manager import get_blacklist_manager

# High-intent positive signals
HOT_LEAD_PATTERNS = [
    r"send (?:more|through|over) (?:info|information|details|pricing)",
    r"tender (?:docs|documents|specifications|package|drawings)",
    r"(?:bill of quantities|boq|takeoffs)",
    r"(?:call me|give me a call|let's (?:talk|speak|chat)|meeting)",
    r"(?:schedule|book) (?:a call|a meeting|time)",
    r"(?:interested|send pricing|what are your rates)",
    r"(?:pre-qualification|pqe|subcontractor questionnaire)",
    r"(?:when can you|availability|start date)",
    r"(?:sounds good|happy to connect|please forward)",
    r"(?:quote|proposal|rate card|scope of work)"
]

# DNC / GDPR Opt-out signals
UNSUBSCRIBE_PATTERNS = [
    r"unsubscribe",
    r"remove (?:me|us|this email)",
    r"do not (?:contact|email|reach out)",
    r"\bdnc\b",
    r"\bgdpr\b",
    r"(?:stop emailing|leave us alone|take me off)",
    r"(?:not interested|cease and desist|reported as spam)",
    r"opt[ -]?out"
]

# Bounce & Delivery Failure signals
BOUNCE_PATTERNS = [
    r"delivery status notification",
    r"undelivered mail",
    r"mail delivery failed",
    r"mailbox (?:unavailable|full|not found|disabled)",
    r"user unknown",
    r"550 (?:user|mailbox|requested action not taken)",
    r"recipient address rejected",
    r"mailer-daemon",
    r"postmaster@",
    r"address rejected",
    r"host not found",
    r"no such user"
]


class ReplyClassifier:
    """Classifies incoming business responses and drafts contextual 1-click responses."""

    @classmethod
    def classify(cls, subject: str, body: str, sender: str = "") -> Tuple[str, bool]:
        """
        Returns: (classification: str, is_hot_lead: bool)
        Classifications: 'INTERESTED', 'UNSUBSCRIBE', 'BOUNCE', 'NEUTRAL'
        """
        combined = f"{sender}\n{subject}\n{body}".lower()

        # 1. Check Unsubscribe / Opt-Out (Top Priority for GDPR/CAN-SPAM)
        for pat in UNSUBSCRIBE_PATTERNS:
            if re.search(pat, combined):
                return "UNSUBSCRIBE", False

        # 2. Check Bounce / Delivery Failure
        for pat in BOUNCE_PATTERNS:
            if re.search(pat, combined):
                return "BOUNCE", False

        # 3. Check Hot Lead / High-Intent Interest
        for pat in HOT_LEAD_PATTERNS:
            if re.search(pat, combined):
                return "INTERESTED", True

        return "NEUTRAL", False

    @classmethod
    def draft_1click_response(cls, sender_email: str, company_name: str, incoming_body: str) -> str:
        """Generates dynamic AI response template ready for 1-click dispatch."""
        return (
            f"Dear Commercial Team at {company_name},\n\n"
            f"Thank you for your response. We would be pleased to review the tender specifications.\n\n"
            f"Please forward the bill of quantities / drawings to this address or provide access to your procurement portal.\n\n"
            f"Our team will turn around an estimate within 48-72 hours.\n\n"
            f"Best regards,\n"
            f"H.Huddair Commercial Estimating Team"
        )


class IMAPReplyListener:
    """
    Background polling service & reply processor:
    Monitors enrolled SMTP/IMAP inboxes, catches delivery failures/bounces,
    suppresses affected leads, flags hot leads, and manages compliance opt-outs.
    """

    def __init__(self):
        self.db = get_db_engine()
        self.blacklist_mgr = get_blacklist_manager()

    def is_suppressed(self, email_or_domain: str) -> bool:
        """Checks if entity exists in global suppression table or DNC list."""
        clean = email_or_domain.strip().lower()
        domain = clean.split("@")[-1] if "@" in clean else clean

        # Also check blacklist patterns
        is_bl, _ = self.blacklist_mgr.is_domain_blacklisted(clean)
        if is_bl:
            return True

        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT id FROM suppressed_entities WHERE lower(entity) = ? OR lower(entity) = ?
            """, (clean, domain)).fetchone()
            if row:
                return True

            dnc_row = conn.execute("""
                SELECT id FROM dnc_blacklist WHERE lower(entity) = ? OR lower(entity) = ?
            """, (clean, domain)).fetchone()
            return dnc_row is not None

    def is_blacklisted(self, email_or_domain: str) -> bool:
        """Alias for is_suppressed to check blacklisted / suppressed recipients."""
        return self.is_suppressed(email_or_domain)

    def _do_suppress(
        self,
        conn: Any,
        clean: str,
        entity_type: str,
        reason: str,
        operator_id: Optional[str]
    ) -> None:
        # 1. Insert into suppressed_entities
        conn.execute("""
            INSERT OR IGNORE INTO suppressed_entities (entity, entity_type, reason, operator_id)
            VALUES (?, ?, ?, ?)
        """, (clean, entity_type, reason, operator_id))

        # 2. Maintain dnc_blacklist for backwards compatibility
        conn.execute("""
            INSERT OR IGNORE INTO dnc_blacklist (entity, entity_type, reason)
            VALUES (?, ?, ?)
        """, (clean, entity_type, reason))

        # 3. Update deduplication registry
        conn.execute("""
            UPDATE dedup_registry
            SET status = 'BLACKLISTED', last_processed_at = CURRENT_TIMESTAMP
            WHERE normalized_key = ?
        """, (clean,))

        # 4. Terminate followup sequences
        conn.execute("""
            UPDATE followup_sequences
            SET status = 'TERMINATED'
            WHERE lower(recipient_email) = ? OR lower(recipient_email) LIKE ?
        """, (clean, f"%@{clean}"))

        # 5. Suppress pending items in outreach queue
        conn.execute("""
            UPDATE outreach_queue
            SET status = 'SUPPRESSED'
            WHERE (lower(recipient) = ? OR lower(recipient) LIKE ?)
              AND status IN ('PENDING_APPROVAL', 'APPROVED', 'SCHEDULED')
        """, (clean, f"%@{clean}"))

    def suppress_entity(
        self,
        entity: str,
        reason: str = "OPT_OUT",
        operator_id: Optional[str] = None,
        conn: Optional[Any] = None
    ) -> None:
        """
        Adds entity (email or domain) to Global Suppressed Domains/Emails table.
        Terminates pending outreach and sequences.
        """
        clean = entity.strip().lower()
        entity_type = "email" if "@" in clean else "domain"

        if conn is not None:
            self._do_suppress(conn, clean, entity_type, reason, operator_id)
        else:
            with self.db.get_connection() as c:
                self._do_suppress(c, clean, entity_type, reason, operator_id)
                c.commit()

    def process_incoming_reply(
        self,
        sender_email: str,
        subject: str,
        body: str,
        lead_id: Optional[str] = None,
        company_name: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming response:
        - Detects bounces -> flags lead as BOUNCED and suppresses email/domain
        - Detects unsubscribes -> flags as SUPPRESSED and adds to suppressed_entities
        - Detects hot leads -> routes to Hot Leads with 1-click draft
        """
        clean_sender = sender_email.strip().lower()
        domain_part = clean_sender.split("@")[-1] if "@" in clean_sender else clean_sender
        comp = company_name or domain_part.capitalize()

        classification, is_hot = ReplyClassifier.classify(subject, body, clean_sender)
        ai_reply = ReplyClassifier.draft_1click_response(clean_sender, comp, body) if is_hot else ""

        reply_id = str(uuid.uuid4())

        with self.db.get_connection() as conn:
            # Detect associated operator if not provided
            if not operator_id:
                matching_q = conn.execute("""
                    SELECT operator_id FROM outreach_queue
                    WHERE lower(recipient) = ? ORDER BY created_at DESC LIMIT 1
                """, (clean_sender,)).fetchone()
                if matching_q and matching_q["operator_id"]:
                    operator_id = matching_q["operator_id"]

            # Case 1: BOUNCE
            if classification == "BOUNCE":
                # Extract bounced recipient from body if present
                found_emails_raw = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body)
                # Strip trailing dots/punctuation that get captured from sentence endings
                found_emails = [e.rstrip('.') for e in found_emails_raw]
                bounced_recipients = [
                    e.lower() for e in found_emails 
                    if not any(ign in e.lower() for ign in ("mailer-daemon", "postmaster", "mail-server", clean_sender))
                ]
                for br in bounced_recipients:
                    self.suppress_entity(br, reason="BOUNCE", operator_id=operator_id, conn=conn)
                    br_dom = br.split("@")[-1]
                    self.suppress_entity(br_dom, reason="BOUNCE", operator_id=operator_id, conn=conn)
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'BOUNCED',
                            bounced_at = CURRENT_TIMESTAMP,
                            bounce_reason = ?
                        WHERE lower(recipient) = ?
                    """, (subject[:100], br))

                self.suppress_entity(clean_sender, reason="BOUNCE", operator_id=operator_id, conn=conn)
                self.suppress_entity(domain_part, reason="BOUNCE", operator_id=operator_id, conn=conn)

                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'BOUNCED',
                        bounced_at = CURRENT_TIMESTAMP,
                        bounce_reason = ?
                    WHERE lower(recipient) = ?
                """, (subject[:100], clean_sender))

            # Case 2: UNSUBSCRIBE / OPT-OUT
            elif classification == "UNSUBSCRIBE":
                self.suppress_entity(clean_sender, reason="UNSUBSCRIBE", operator_id=operator_id, conn=conn)
                self.suppress_entity(domain_part, reason="UNSUBSCRIBE", operator_id=operator_id, conn=conn)

                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'SUPPRESSED'
                    WHERE lower(recipient) = ?
                """, (clean_sender,))

            # Case 3: HOT LEAD
            elif is_hot:
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'HOT_LEAD'
                    WHERE lower(recipient) = ?
                """, (clean_sender,))

            # Case 4: NEUTRAL REPLY
            else:
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'REPLIED'
                    WHERE lower(recipient) = ? AND status = 'SENT'
                """, (clean_sender,))

            # Log into inbox_replies
            conn.execute("""
                INSERT INTO inbox_replies (
                    id, lead_id, sender_email, company_name, subject,
                    message_body, classification, is_hot_lead, ai_suggested_reply,
                    operator_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reply_id, lead_id, clean_sender, comp, subject,
                body, classification, 1 if is_hot else 0, ai_reply,
                operator_id
            ))

            # Terminate active follow-up sequences for this recipient
            conn.execute("""
                UPDATE followup_sequences
                SET status = 'TERMINATED'
                WHERE lower(recipient_email) = ?
            """, (clean_sender,))

            conn.commit()

        alert_msg = "STANDARD_REPLY"
        if is_hot:
            alert_msg = "HOT_LEAD_DETECTED"
        elif classification == "BOUNCE":
            alert_msg = "DELIVERY_BOUNCE_SUPPRESSED"
        elif classification == "UNSUBSCRIBE":
            alert_msg = "OPT_OUT_SUPPRESSED"

        return {
            "reply_id": reply_id,
            "sender_email": clean_sender,
            "company_name": comp,
            "classification": classification,
            "is_hot_lead": is_hot,
            "ai_suggested_reply": ai_reply,
            "operator_id": operator_id,
            "alert": alert_msg,
            "blacklisted": classification in ("UNSUBSCRIBE", "BOUNCE")
        }

    def poll_enrolled_inboxes(self) -> Dict[str, Any]:
        """
        Background polling service monitoring active enrolled IMAP inboxes.
        Connects safely, inspects recent messages for bounces and responses,
        and triggers classification.
        """
        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        with self.db.get_connection() as conn:
            mailboxes = conn.execute("""
                SELECT id, email_address, imap_host, imap_port, imap_username, imap_password, operator_id
                FROM mailbox_rotator
                WHERE is_active = 1 AND imap_host != '' AND imap_username != ''
            """).fetchall()

        for mb in mailboxes:
            mb_email = mb["email_address"]
            host = mb["imap_host"]
            port = mb["imap_port"] or 993
            user = mb["imap_username"]
            pwd = mb["imap_password"]
            op_id = mb["operator_id"]

            try:
                mail = imaplib.IMAP4_SSL(host, port)
                mail.login(user, pwd)
                mail.select("INBOX")
                status, messages = mail.search(None, "UNSEEN")
                if status == "OK" and messages[0]:
                    for msg_id in messages[0].split():
                        res, msg_data = mail.fetch(msg_id, "(RFC822)")
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                sender = msg.get("From", "")
                                subject_raw = msg.get("Subject", "")
                                body_text = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == "text/plain":
                                            body_text += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                else:
                                    body_text = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                                # Extract email from sender string
                                sender_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
                                clean_sender = sender_match.group(0) if sender_match else sender

                                proc = self.process_incoming_reply(
                                    sender_email=clean_sender,
                                    subject=subject_raw,
                                    body=body_text,
                                    operator_id=op_id
                                )
                                results.append(proc)
                mail.logout()
            except Exception as e:
                errors.append(f"{mb_email}: {str(e)}")

        return {
            "processed_count": len(results),
            "processed": results,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_hot_lead_alerts(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns hot lead replies requiring action, filtered by tenant."""
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, ai_suggested_reply, received_at, status,
                           operator_id
                    FROM inbox_replies
                    WHERE is_hot_lead = 1 AND (operator_id = ? OR operator_id IS NULL)
                    ORDER BY received_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, ai_suggested_reply, received_at, status,
                           operator_id
                    FROM inbox_replies
                    WHERE is_hot_lead = 1
                    ORDER BY received_at DESC
                """).fetchall()
            return [dict(r) for r in rows]

    def get_all_replies(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all logged replies, filtered by tenant."""
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, is_hot_lead, received_at, status,
                           operator_id
                    FROM inbox_replies
                    WHERE operator_id = ? OR operator_id IS NULL
                    ORDER BY received_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, is_hot_lead, received_at, status,
                           operator_id
                    FROM inbox_replies
                    ORDER BY received_at DESC
                """).fetchall()
            return [dict(r) for r in rows]

    def get_suppressed_entities(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of suppressed entities for CAN-SPAM / GDPR compliance."""
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("""
                    SELECT id, entity, entity_type, reason, operator_id, suppressed_at
                    FROM suppressed_entities
                    WHERE operator_id = ? OR operator_id IS NULL
                    ORDER BY suppressed_at DESC
                """, (operator_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, entity, entity_type, reason, operator_id, suppressed_at
                    FROM suppressed_entities
                    ORDER BY suppressed_at DESC
                """).fetchall()
            return [dict(r) for r in rows]


_global_reply_listener = None

def get_reply_listener() -> IMAPReplyListener:
    global _global_reply_listener
    if _global_reply_listener is None:
        _global_reply_listener = IMAPReplyListener()
    return _global_reply_listener
