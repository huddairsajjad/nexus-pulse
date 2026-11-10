"""
H.Huddair's Nexus-Pulse - Level 2
Outreach Engine: IMAP Reply Listener, AI Classifier & Hot Lead Alerts
Monitors inbound replies, classifies sentiment, issues instant Hot Lead Alerts
with 1-click response templates, and enforces permanent GDPR/DNC blacklisting.
"""

import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from database.db_engine import get_db_engine

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
    r"(?:sounds good|happy to connect|please forward)"
]

# DNC / GDPR Opt-out signals
UNSUBSCRIBE_PATTERNS = [
    r"unsubscribe",
    r"remove (?:me|us|this email)",
    r"do not (?:contact|email|reach out)",
    r"\bdnc\b",
    r"\bgdpr\b",
    r"(?:stop emailing|leave us alone|take me off)",
    r"(?:not interested|cease and desist|reported as spam)"
]

# Bounce & Out of Office signals
BOUNCE_PATTERNS = [
    r"delivery status notification",
    r"undelivered mail",
    r"mailbox (?:unavailable|full|not found)",
    r"user unknown",
    r"out of (?:the )?office",
    r"abwesenheitsnotiz",
    r"auto(?:mated)? reply"
]


class ReplyClassifier:
    """Classifies incoming business responses and drafts 1-click responses."""

    @classmethod
    def classify(cls, subject: str, body: str) -> Tuple[str, bool]:
        """
        Returns: (classification: str, is_hot_lead: bool)
        Classifications: 'INTERESTED', 'UNSUBSCRIBE', 'BOUNCE', 'NEUTRAL'
        """
        combined = f"{subject}\n{body}".lower()

        # 1. Check Unsubscribe / DNC (Highest priority for GDPR compliance)
        for pat in UNSUBSCRIBE_PATTERNS:
            if re.search(pat, combined):
                return "UNSUBSCRIBE", False

        # 2. Check Bounce / Auto-Reply
        for pat in BOUNCE_PATTERNS:
            if re.search(pat, combined):
                return "BOUNCE", False

        # 3. Check Hot Lead / Interested
        for pat in HOT_LEAD_PATTERNS:
            if re.search(pat, combined):
                return "INTERESTED", True

        return "NEUTRAL", False

    @classmethod
    def draft_1click_response(cls, sender_email: str, company_name: str, incoming_body: str) -> str:
        """Generates contextual AI response template ready for 1-click dispatch."""
        return (
            f"Dear Commercial Team at {company_name},\n\n"
            f"Thank you for getting back to us. We would be delighted to review the tender specifications.\n\n"
            f"Please forward the bill of quantities / drawings to this email address, or let us know if you prefer to upload them to a secure portal.\n\n"
            f"Our team is prepared to turn around a comprehensive, competitive pricing estimate within 48-72 hours.\n\n"
            f"Looking forward to collaborating on this project.\n\n"
            f"Warm regards,\n"
            f"H.Huddair\n"
            f"Commercial Director | Nexus-Pulse Enterprise Solutions"
        )


class IMAPReplyListener:
    """
    Manages incoming replies, triggers Hot Lead alerts, and enforces DNC/GDPR blacklisting.
    """

    def __init__(self):
        self.db = get_db_engine()

    def is_blacklisted(self, email_or_domain: str) -> bool:
        """Checks if entity has been added to DNC blacklist."""
        clean = email_or_domain.strip().lower()
        domain = clean.split("@")[-1] if "@" in clean else clean
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT id FROM dnc_blacklist WHERE entity = ? OR entity = ?
            """, (clean, domain)).fetchone()
            return row is not None

    def blacklist_entity(self, entity: str, reason: str = "GDPR / DNC Opt-Out Request") -> None:
        """Permanently blacklists an email or domain across all system layers."""
        clean = entity.strip().lower()
        entity_type = "email" if "@" in clean else "domain"

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO dnc_blacklist (entity, entity_type, reason)
                VALUES (?, ?, ?)
            """, (clean, entity_type, reason))

            # Mark in deduplication registry as BLACKLISTED
            conn.execute("""
                UPDATE dedup_registry
                SET status = 'BLACKLISTED', last_processed_at = CURRENT_TIMESTAMP
                WHERE normalized_key = ?
            """, (clean,))

            # Terminate any active follow-up sequences
            conn.execute("""
                UPDATE followup_sequences
                SET status = 'TERMINATED'
                WHERE recipient_email = ?
            """, (clean,))

            conn.commit()

    def process_incoming_reply(
        self,
        sender_email: str,
        subject: str,
        body: str,
        lead_id: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming response, runs AI classification, enforces DNC if opted out,
        and logs Hot Lead alerts with 1-click reply templates.
        """
        clean_sender = sender_email.strip().lower()
        comp = company_name or clean_sender.split("@")[-1].capitalize()

        classification, is_hot = ReplyClassifier.classify(subject, body)
        ai_reply = ReplyClassifier.draft_1click_response(clean_sender, comp, body) if is_hot else ""

        # Enforce Permanent DNC / GDPR Blacklist
        if classification == "UNSUBSCRIBE":
            self.blacklist_entity(clean_sender, "User requested unsubscribe / DNC opt-out")
            domain_part = clean_sender.split("@")[-1]
            self.blacklist_entity(domain_part, "Company-wide DNC opt-out")

        reply_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO inbox_replies (
                    id, lead_id, sender_email, company_name, subject,
                    message_body, classification, is_hot_lead, ai_suggested_reply
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reply_id, lead_id, clean_sender, comp, subject,
                body, classification, 1 if is_hot else 0, ai_reply
            ))

            # Update outreach queue status if matching recipient exists
            if is_hot:
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'HOT_LEAD'
                    WHERE recipient = ?
                """, (clean_sender,))
            elif classification == "UNSUBSCRIBE":
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'REJECTED'
                    WHERE recipient = ?
                """, (clean_sender,))
            else:
                conn.execute("""
                    UPDATE outreach_queue
                    SET status = 'REPLIED'
                    WHERE recipient = ? AND status = 'SENT'
                """, (clean_sender,))

            # If replied, terminate follow-up sequences
            conn.execute("""
                UPDATE followup_sequences
                SET status = 'TERMINATED'
                WHERE recipient_email = ?
            """, (clean_sender,))

            conn.commit()

        return {
            "reply_id": reply_id,
            "sender_email": clean_sender,
            "company_name": comp,
            "classification": classification,
            "is_hot_lead": is_hot,
            "ai_suggested_reply": ai_reply,
            "blacklisted": classification == "UNSUBSCRIBE",
            "alert": "HOT LEAD DETECTED - 1-Click Response Ready" if is_hot else ("DNC OPT-OUT - Permanently Blacklisted" if classification == "UNSUBSCRIBE" else "Standard Reply Logged")
        }

    def get_hot_lead_alerts(self) -> List[Dict[str, Any]]:
        """Returns all Hot Lead replies requiring executive attention."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, lead_id, sender_email, company_name, subject,
                       message_body, classification, ai_suggested_reply, received_at, status
                FROM inbox_replies
                WHERE is_hot_lead = 1
                ORDER BY received_at DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_all_replies(self) -> List[Dict[str, Any]]:
        """Returns all logged replies."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, lead_id, sender_email, company_name, subject,
                       message_body, classification, is_hot_lead, received_at, status
                FROM inbox_replies
                ORDER BY received_at DESC
            """).fetchall()
            return [dict(r) for r in rows]


_global_reply_listener = None

def get_reply_listener() -> IMAPReplyListener:
    global _global_reply_listener
    if _global_reply_listener is None:
        _global_reply_listener = IMAPReplyListener()
    return _global_reply_listener
