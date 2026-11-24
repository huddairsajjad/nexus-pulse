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
from email.utils import parseaddr
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from database.db_engine import get_db_engine
from .blacklist_manager import get_blacklist_manager, is_public_email_domain, PUBLIC_EMAIL_DOMAINS

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

# DNC / GDPR Opt-out signals — STRICT patterns only; require explicit opt-out intent
# Positive/neutral context must NOT trigger these patterns
UNSUBSCRIBE_PATTERNS = [
    r"\bunsubscribe\b",
    r"(?<!\w)stop\s+(?:emails?|emailing|contact(?:ing)?|sending|all\s+emails?)(?!\s+by|\s+at|\s+before|\s+when|\s+if)",
    r"^stop$",
    r"remove (?:me|us|our (?:email|address|company)) (?:from|off)",
    r"do not (?:contact|email|reach out to) (?:me|us)\b",
    r"\bdnc\b",
    r"\bgdpr\s+(?:removal|request|delete)\b",
    r"(?:stop emailing|leave us alone|take me off (?:your|the) (?:list|database))",
    r"(?:cease and desist|reported (?:as|for) spam)",
    r"\bopt[ -]?out\b"
]

# Positive engagement signals — if matched, ALWAYS bypass UNSUBSCRIBE classification
POSITIVE_ENGAGEMENT_PATTERNS = [
    r"(?:send|forward|provide|share) (?:more|through|over|us|me) (?:info|details|pricing|specs|documents?|quote|proposal)",
    r"(?:call me|give me a call|let's (?:talk|speak|chat|connect)|set up a (?:call|meeting))",
    r"(?:schedule|book) (?:a call|a meeting|time|an appointment)",
    r"(?:interested|please send|happy to|sounds good|look forward)",
    r"(?:what(?:'s| is) (?:your|the) (?:rate|price|cost|availability))",
    r"(?:tender|rfq|rfp|quote|proposal|estimate|scope)",
    r"(?:when (?:can|are|will) you|your availability|start date)",
    r"(?:pre-qual|prequalif|subcontractor questionnaire|vendor list)",
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


def decode_mime_header(header_val: Optional[str]) -> str:
    """Decodes MIME encoded header strings into clean UTF-8 text."""
    if not header_val:
        return ""
    try:
        decoded_parts = []
        for fragment, encoding in decode_header(header_val):
            if isinstance(fragment, bytes):
                decoded_parts.append(fragment.decode(encoding or "utf-8", errors="ignore"))
            else:
                decoded_parts.append(str(fragment))
        return "".join(decoded_parts).strip()
    except Exception:
        return str(header_val).strip()


class ReplyClassifier:
    """Classifies incoming business responses and drafts contextual 1-click responses."""

    @classmethod
    def classify(cls, subject: str, body: str, sender: str = "") -> Tuple[str, bool]:
        """
        Returns: (classification: str, is_hot_lead: bool)
        Classifications: 'INTERESTED', 'UNSUBSCRIBE', 'BOUNCE', 'NEUTRAL'

        Priority order:
          0. If positive engagement detected → bypass UNSUBSCRIBE, go straight to INTERESTED/NEUTRAL
          1. UNSUBSCRIBE check (strict patterns only)
          2. BOUNCE check
          3. HOT_LEAD / INTERESTED check
          4. NEUTRAL fallback
        """
        combined = f"{sender}\n{subject}\n{body}".lower()
        body_lower = (body or "").lower()

        # 0. Check positive engagement FIRST — if present, never classify as UNSUBSCRIBE
        is_positive = any(re.search(pat, body_lower, re.IGNORECASE) for pat in POSITIVE_ENGAGEMENT_PATTERNS)

        if not is_positive:
            # 1. Check Unsubscribe / Opt-Out (GDPR/CAN-SPAM)
            for pat in UNSUBSCRIBE_PATTERNS:
                if re.search(pat, combined, re.IGNORECASE):
                    return "UNSUBSCRIBE", False

        # 2. Check Bounce / Delivery Failure
        for pat in BOUNCE_PATTERNS:
            if re.search(pat, combined, re.IGNORECASE):
                return "BOUNCE", False

        # 3. Check Hot Lead / High-Intent Interest
        for pat in HOT_LEAD_PATTERNS:
            if re.search(pat, combined, re.IGNORECASE):
                return "INTERESTED", True

        return "NEUTRAL", False

    @classmethod
    def clean_incoming_inquiry_body(cls, text: str) -> str:
        """
        Removes quoted previous email thread lines (> ...), reply headers
        (On ... wrote:), and email disclaimers so only the new message remains.
        """
        if not text:
            return ""
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            # Stop or skip quoted lines
            if stripped.startswith(">"):
                continue
            if re.match(r'^-+\s*(?:original message|forwarded message)\s*-+', stripped, re.IGNORECASE):
                break
            if re.match(r'^on\s+.+wrote\s*:\s*$', stripped, re.IGNORECASE):
                break
            if re.match(r'^(?:from|sent|to|subject)\s*:\s*.+', stripped, re.IGNORECASE) and len(lines) > 0:
                break
            lines.append(line)
        cleaned = "\n".join(lines).strip()
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned or text.strip()

    @classmethod
    def draft_1click_response(cls, sender_email: str, company_name: str, incoming_body: str, niche: Optional[str] = None) -> str:
        """Generates dynamic AI response template adapted to lead's niche and inquiry."""
        clean_inquiry = cls.clean_incoming_inquiry_body(incoming_body)
        n = (niche or "").strip().lower()

        if "real estate" in n or "property" in n or "brokerage" in n:
            return (
                f"Dear Team at {company_name},\n\n"
                f"Thank you for reaching out regarding luxury property opportunities. We would be delighted to provide full portfolio details, availability, and arrange a private consultation.\n\n"
                f"Please let us know your preferred timeline and specific requirements so we can tailor our presentation.\n\n"
                f"Best regards,\n"
                f"H.Huddair Executive Client Advisory"
            )
        elif "saas" in n or "software" in n or "tech" in n or "api" in n:
            return (
                f"Dear Team at {company_name},\n\n"
                f"Thank you for your response. We would be pleased to schedule a 15-minute product walkthrough to explore how our workflow automation aligns with your product goals.\n\n"
                f"Please let us know your availability this week for a brief call.\n\n"
                f"Best regards,\n"
                f"H.Huddair Strategic Accounts Team"
            )
        elif "gym" in n or "fitness" in n:
            return (
                f"Dear Commercial Procurement Team at {company_name},\n\n"
                f"Thank you for your response regarding commercial fitness outfitting and supply. We would be pleased to share our commercial catalog and trade volume pricing.\n\n"
                f"Please let us know if you have upcoming facility upgrades or specific equipment needs.\n\n"
                f"Best regards,\n"
                f"H.Huddair Commercial Fitness Team"
            )
        elif "construction" in n or "contractor" in n or "mep" in n or "roofing" in n:
            return (
                f"Dear Commercial Team at {company_name},\n\n"
                f"Thank you for your response. We would be pleased to review the tender specifications and project requirements.\n\n"
                f"Please forward the bill of quantities or project scope, and our team will turn around an estimate within 48-72 hours.\n\n"
                f"Best regards,\n"
                f"H.Huddair Commercial Estimating Team"
            )
        else:
            return (
                f"Dear Team at {company_name},\n\n"
                f"Thank you for your response. We would be delighted to connect and explore commercial collaboration opportunities with {company_name}.\n\n"
                f"Please let us know your availability for a brief 10-15 minute introductory conversation this week.\n\n"
                f"Best regards,\n"
                f"H.Huddair Commercial Executive Team"
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
        # Purge any false-positive suppression entries that may have been created
        # by IMAP poller from enrolled sending mailbox addresses
        self._purge_enrolled_sender_suppressions()

    def _purge_enrolled_sender_suppressions(self) -> None:
        """
        Removes any suppression/blacklist entries that were incorrectly created
        for enrolled sending mailbox addresses. Runs once at startup.
        """
        try:
            with self.db.get_connection() as conn:
                enrolled = conn.execute(
                    "SELECT lower(email_address) FROM mailbox_rotator WHERE is_active = 1"
                ).fetchall()
                for row in enrolled:
                    addr = (row[0] or "").strip()
                    if not addr:
                        continue
                    conn.execute(
                        "DELETE FROM suppressed_entities WHERE lower(entity) = ?", (addr,)
                    )
                    conn.execute(
                        "DELETE FROM dnc_blacklist WHERE lower(entity) = ?", (addr,)
                    )
                    conn.execute(
                        "DELETE FROM blacklist_rules WHERE lower(pattern) = ? AND created_by = 'IMAP_POLLER'",
                        (addr,)
                    )
                conn.commit()
        except Exception:
            pass  # Non-fatal startup cleanup

    def is_suppressed(self, email_or_domain: str) -> bool:
        """Checks if entity exists in global suppression table or DNC list."""
        if not email_or_domain:
            return False
        clean = email_or_domain.strip().lower()
        domain = clean.split("@")[-1] if "@" in clean else clean

        # Never treat root public email providers as suppressed
        if "@" not in clean and clean in PUBLIC_EMAIL_DOMAINS:
            return False

        # Also check blacklist patterns
        is_bl, _ = self.blacklist_mgr.is_domain_blacklisted(clean)
        if is_bl:
            return True

        is_pub = is_public_email_domain(domain)

        with self.db.get_connection() as conn:
            if is_pub:
                # For public webmail (e.g. gmail.com), ONLY check exact email
                row = conn.execute("""
                    SELECT id FROM suppressed_entities WHERE lower(entity) = ?
                """, (clean,)).fetchone()
                if row:
                    return True

                dnc_row = conn.execute("""
                    SELECT id FROM dnc_blacklist WHERE lower(entity) = ?
                """, (clean,)).fetchone()
                return dnc_row is not None
            else:
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
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> None:
        # Never store or suppress root public email provider domains (e.g. gmail.com)
        if "@" not in clean and clean in PUBLIC_EMAIL_DOMAINS:
            return

        domain = clean.split("@")[-1] if "@" in clean else clean
        is_pub = is_public_email_domain(domain)
        owner = (owner_username or "").strip().lower()

        # 1. Insert into suppressed_entities
        conn.execute("""
            INSERT OR IGNORE INTO suppressed_entities (entity, entity_type, reason, operator_id, owner_username)
            VALUES (?, ?, ?, ?, ?)
        """, (clean, entity_type, reason, operator_id, owner))

        # 2. Maintain dnc_blacklist for backwards compatibility
        conn.execute("""
            INSERT OR IGNORE INTO dnc_blacklist (entity, entity_type, reason, owner_username)
            VALUES (?, ?, ?, ?)
        """, (clean, entity_type, reason, owner))

        # 3. Update deduplication registry
        conn.execute("""
            UPDATE dedup_registry
            SET status = 'BLACKLISTED', last_processed_at = CURRENT_TIMESTAMP
            WHERE normalized_key = ?
        """, (clean,))

        # 4. Terminate followup sequences (exact for public domains, wildcard for custom corporate domains)
        if is_pub or "@" in clean:
            conn.execute("""
                UPDATE followup_sequences
                SET status = 'TERMINATED'
                WHERE lower(recipient_email) = ?
            """, (clean,))
        else:
            conn.execute("""
                UPDATE followup_sequences
                SET status = 'TERMINATED'
                WHERE lower(recipient_email) = ? OR lower(recipient_email) LIKE ?
            """, (clean, f"%@{clean}"))

        # 5. Suppress pending items in outreach queue and strip scheduled_for
        if is_pub or "@" in clean:
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'SUPPRESSED', scheduled_for = NULL, bounce_reason = ?
                WHERE lower(recipient) = ?
                  AND status IN ('PENDING_APPROVAL', 'APPROVED', 'SCHEDULED')
            """, (f"Suppressed: {reason}", clean))
        else:
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'SUPPRESSED', scheduled_for = NULL, bounce_reason = ?
                WHERE (lower(recipient) = ? OR lower(recipient) LIKE ?)
                  AND status IN ('PENDING_APPROVAL', 'APPROVED', 'SCHEDULED')
            """, (f"Suppressed: {reason}", clean, f"%@{clean}"))

    def suppress_entity(
        self,
        entity: str,
        reason: str = "OPT_OUT",
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        conn: Optional[Any] = None
    ) -> None:
        """
        Adds entity (email or domain) to Global Suppressed Domains/Emails table.
        Terminates pending outreach and sequences.
        Guards against suppressing root public webmail domains.
        """
        if not entity:
            return
        clean = entity.strip().lower()
        if "@" not in clean and clean in PUBLIC_EMAIL_DOMAINS:
            return

        entity_type = "email" if "@" in clean else "domain"

        if conn is not None:
            self._do_suppress(conn, clean, entity_type, reason, operator_id, owner_username)
        else:
            with self.db.get_connection() as c:
                self._do_suppress(c, clean, entity_type, reason, operator_id, owner_username)
                c.commit()

    def process_incoming_reply(
        self,
        sender_email: str,
        subject: str,
        body: str,
        lead_id: Optional[str] = None,
        company_name: Optional[str] = None,
        operator_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        message_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming response:
        - Resolves originating lead & queue item via recipient email, In-Reply-To, or Re: subjects scoped per workspace.
        - Detects bounces -> flags lead as BOUNCED and suppresses email/domain
        - Detects unsubscribes -> flags as SUPPRESSED and adds to suppressed_entities
        - Detects hot leads -> updates outreach_queue to HOT_LEAD, routes to Hot Leads with 1-click draft
        - Detects neutral replies -> updates outreach_queue to REPLIED
        - Updates live dashboard counters (Sent, Replies, Hot Leads)
        """
        clean_sender = sender_email.strip().lower()
        domain_part = clean_sender.split("@")[-1] if "@" in clean_sender else clean_sender
        public_providers = {"gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "outlook.com", "hotmail.com", "live.com", "icloud.com", "aol.com", "mail.com", "proton.me", "protonmail.com"}
        if domain_part in public_providers:
            local_user = clean_sender.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ").title()
            comp = company_name or (f"{local_user} (Direct Inquirer)" if len(local_user) > 2 else "Direct Commercial Inquirer")
        else:
            comp = company_name or domain_part.capitalize()
        clean_subject = re.sub(r'^(?:(?:re|aw|wg|fwd|fw|antwort)\s*:\s*)+', '', subject, flags=re.IGNORECASE).strip()

        classification, is_hot = ReplyClassifier.classify(subject, body, clean_sender)
        reply_id = str(uuid.uuid4())
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        with self.db.get_connection() as conn:
            # 1. Multi-vector match against outreach_queue (In-Reply-To, recipient email, or Re: subject)
            matching_q = None

            owner_filter_sql = ""
            owner_params: List[Any] = []
            if owner or op_id:
                owner_filter_sql = " AND (lower(owner_username) = ? OR operator_id = ?)"
                owner_params = [owner, op_id]

            # Vector A: In-Reply-To or References matching tracking_id or message_id
            if in_reply_to:
                clean_irt = in_reply_to.strip().strip("<>")
                sql_a = f"""
                    SELECT * FROM outreach_queue
                    WHERE (tracking_id = ?
                       OR (message_id IS NOT NULL AND (message_id = ? OR message_id = ?))
                       OR ? LIKE '%' || tracking_id || '%')
                       {owner_filter_sql}
                    ORDER BY created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_a, [clean_irt, in_reply_to.strip(), f"<{clean_irt}>", in_reply_to] + owner_params).fetchone()

            if not matching_q and references:
                clean_ref = references.strip().strip("<>")
                sql_ref = f"""
                    SELECT * FROM outreach_queue
                    WHERE (tracking_id = ?
                       OR (message_id IS NOT NULL AND message_id LIKE ?)
                       OR ? LIKE '%' || tracking_id || '%')
                       {owner_filter_sql}
                    ORDER BY created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_ref, [clean_ref, f"%{clean_ref}%", references] + owner_params).fetchone()

            # Vector B: Recipient email match (case-insensitive)
            if not matching_q and clean_sender:
                sql_b = f"""
                    SELECT * FROM outreach_queue
                    WHERE lower(recipient) = ?
                       {owner_filter_sql}
                    ORDER BY created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_b, [clean_sender] + owner_params).fetchone()

            # Vector C: Normalized Re: subject match
            if not matching_q and clean_subject and len(clean_subject) >= 3:
                sql_c = f"""
                    SELECT * FROM outreach_queue
                    WHERE (lower(trim(subject)) = lower(?)
                       OR lower(trim(subject)) LIKE lower(?)
                       OR lower(?) LIKE '%' || lower(trim(subject)) || '%')
                       {owner_filter_sql}
                    ORDER BY created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_c, [clean_subject, f"%{clean_subject}%", clean_subject] + owner_params).fetchone()

            # Vector D: Sender email matches a lead's recipient (most recent SENT/DISPATCHED first)
            if not matching_q and clean_sender:
                sql_d = f"""
                    SELECT * FROM outreach_queue
                    WHERE lower(recipient) = ?
                      AND status IN ('SENT', 'DISPATCHED', 'APPROVED', 'SCHEDULED')
                      {owner_filter_sql}
                    ORDER BY sent_at DESC, created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_d, [clean_sender] + owner_params).fetchone()

            # Vector E: Corporate domain fuzzy match (non-public domains only)
            if not matching_q and domain_part and not is_public_email_domain(domain_part):
                sql_e = f"""
                    SELECT * FROM outreach_queue
                    WHERE lower(recipient) LIKE ?
                      AND status IN ('SENT', 'DISPATCHED', 'APPROVED', 'SCHEDULED')
                      {owner_filter_sql}
                    ORDER BY sent_at DESC, created_at DESC LIMIT 1
                """
                matching_q = conn.execute(sql_e, [f"%@{domain_part}"] + owner_params).fetchone()

            if matching_q:
                matching_q_dict = dict(matching_q)
                if not lead_id:
                    lead_id = matching_q_dict.get("lead_id")
                if not company_name and matching_q_dict.get("company_name"):
                    comp = matching_q_dict["company_name"]
                if not op_id and matching_q_dict.get("operator_id"):
                    op_id = matching_q_dict["operator_id"]
                if not owner and matching_q_dict.get("owner_username"):
                    owner = matching_q_dict["owner_username"]
                matching_qid = matching_q_dict.get("id")
            else:
                matching_qid = None

            lead_niche = None
            if matching_q:
                try:
                    lead_niche = matching_q["industry_niche"]
                except Exception:
                    try:
                        lead_niche = matching_q["target_country"]
                    except Exception:
                        lead_niche = None

            cleaned_body = ReplyClassifier.clean_incoming_inquiry_body(body)
            ai_reply = ReplyClassifier.draft_1click_response(clean_sender, comp, body, niche=lead_niche) if is_hot else ""
            snippet = (cleaned_body or body or "").strip()[:280]

            # Determine if this is a newly detected reply on a currently dispatched lead
            is_new_reply = False
            if matching_q and matching_q["status"] in ("SENT", "DISPATCHED"):
                is_new_reply = True

            # Case 1: BOUNCE
            if classification == "BOUNCE":
                # Extract bounced recipient from body if present
                found_emails_raw = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body)
                found_emails = [e.rstrip('.') for e in found_emails_raw]
                bounced_recipients = [
                    e.lower() for e in found_emails 
                    if not any(ign in e.lower() for ign in ("mailer-daemon", "postmaster", "mail-server", clean_sender))
                ]
                for br in bounced_recipients:
                    self.suppress_entity(br, reason="BOUNCE", operator_id=op_id, conn=conn)
                    br_dom = br.split("@")[-1] if "@" in br else ""
                    if br_dom and not is_public_email_domain(br_dom):
                        self.suppress_entity(br_dom, reason="BOUNCE", operator_id=op_id, conn=conn)
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'BOUNCED',
                            scheduled_for = NULL,
                            bounced_at = CURRENT_TIMESTAMP,
                            bounce_reason = ?
                        WHERE lower(recipient) = ?
                    """, (subject[:100], br))

                self.suppress_entity(clean_sender, reason="BOUNCE", operator_id=op_id, conn=conn)
                if domain_part and not is_public_email_domain(domain_part):
                    self.suppress_entity(domain_part, reason="BOUNCE", operator_id=op_id, conn=conn)

                if matching_qid:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'BOUNCED', scheduled_for = NULL, bounced_at = CURRENT_TIMESTAMP, bounce_reason = ?
                        WHERE id = ?
                    """, (subject[:100], matching_qid))

            # Case 2: UNSUBSCRIBE / OPT-OUT
            elif classification == "UNSUBSCRIBE":
                self.suppress_entity(clean_sender, reason="UNSUBSCRIBE", operator_id=op_id, conn=conn)
                if domain_part and not is_public_email_domain(domain_part):
                    self.suppress_entity(domain_part, reason="UNSUBSCRIBE", operator_id=op_id, conn=conn)

                try:
                    existing_bl = conn.execute("SELECT id FROM blacklist_rules WHERE lower(pattern) = ?", (clean_sender,)).fetchone()
                    if not existing_bl:
                        conn.execute("""
                            INSERT INTO blacklist_rules (pattern, entity_type, reason, created_by)
                            VALUES (?, 'email', ?, 'IMAP_POLLER')
                        """, (clean_sender, f"Opt-Out / STOP Reply: {subject[:60]}"))
                except Exception:
                    pass

                if matching_qid:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'SUPPRESSED', scheduled_for = NULL, bounce_reason = 'Suppressed: UNSUBSCRIBE'
                        WHERE id = ?
                    """, (matching_qid,))
                elif owner or op_id:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'SUPPRESSED', scheduled_for = NULL, bounce_reason = 'Suppressed: UNSUBSCRIBE'
                        WHERE lower(recipient) = ? AND (lower(owner_username) = ? OR operator_id = ?)
                    """, (clean_sender, owner, op_id))

            # Case 3: HOT LEAD
            elif is_hot:
                if matching_qid:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'HOT_LEAD',
                            replied_at = CURRENT_TIMESTAMP,
                            reply_snippet = ?
                        WHERE id = ?
                    """, (snippet, matching_qid))
                elif owner or op_id:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'HOT_LEAD',
                            replied_at = CURRENT_TIMESTAMP,
                            reply_snippet = ?
                        WHERE lower(recipient) = ? AND (lower(owner_username) = ? OR operator_id = ?)
                    """, (snippet, clean_sender, owner, op_id))

            # Case 4: NEUTRAL / STANDARD REPLY
            else:
                if matching_qid:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'REPLIED',
                            replied_at = CURRENT_TIMESTAMP,
                            reply_snippet = ?
                        WHERE id = ?
                    """, (snippet, matching_qid))
                elif owner or op_id:
                    conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'REPLIED',
                            replied_at = CURRENT_TIMESTAMP,
                            reply_snippet = ?
                        WHERE lower(recipient) = ? AND (lower(owner_username) = ? OR operator_id = ?)
                          AND status IN ('SENT', 'DISPATCHED', 'APPROVED', 'SCHEDULED')
                    """, (snippet, clean_sender, owner, op_id))

            # Log into inbox_replies — upsert in place to prevent duplicate cards per user
            existing_rep = None
            if message_id:
                if owner or op_id:
                    existing_rep = conn.execute("""
                        SELECT id, is_hot_lead, status FROM inbox_replies
                        WHERE message_id = ? AND (lower(owner_username) = ? OR operator_id = ?)
                        LIMIT 1
                    """, (message_id, owner, op_id)).fetchone()
                else:
                    existing_rep = conn.execute(
                        "SELECT id, is_hot_lead, status FROM inbox_replies WHERE message_id = ? LIMIT 1",
                        (message_id,)
                    ).fetchone()

            if not existing_rep and lead_id:
                if owner or op_id:
                    existing_rep = conn.execute("""
                        SELECT id, is_hot_lead, status FROM inbox_replies
                        WHERE lead_id = ? AND (lower(owner_username) = ? OR operator_id = ?)
                        ORDER BY received_at DESC LIMIT 1
                    """, (lead_id, owner, op_id)).fetchone()
                else:
                    existing_rep = conn.execute(
                        "SELECT id, is_hot_lead, status FROM inbox_replies WHERE lead_id = ? ORDER BY received_at DESC LIMIT 1",
                        (lead_id,)
                    ).fetchone()

            if not existing_rep and clean_sender:
                if owner or op_id:
                    existing_rep = conn.execute("""
                        SELECT id, is_hot_lead, status FROM inbox_replies
                        WHERE lower(sender_email) = ? AND (lower(owner_username) = ? OR operator_id = ?)
                        ORDER BY received_at DESC LIMIT 1
                    """, (clean_sender, owner, op_id)).fetchone()
                else:
                    existing_rep = conn.execute("""
                        SELECT id, is_hot_lead, status FROM inbox_replies
                        WHERE lower(sender_email) = ?
                        ORDER BY received_at DESC LIMIT 1
                    """, (clean_sender,)).fetchone()

            if existing_rep:
                reply_id = existing_rep["id"]
                conn.execute("""
                    UPDATE inbox_replies
                    SET lead_id = COALESCE(?, lead_id),
                        company_name = COALESCE(?, company_name),
                        subject = ?,
                        message_body = ?,
                        classification = ?,
                        is_hot_lead = MAX(is_hot_lead, ?),
                        ai_suggested_reply = CASE WHEN ? != '' THEN ? ELSE ai_suggested_reply END,
                        received_at = CURRENT_TIMESTAMP,
                        operator_id = COALESCE(?, operator_id),
                        owner_username = CASE WHEN ? != '' THEN ? ELSE owner_username END,
                        message_id = COALESCE(?, message_id)
                    WHERE id = ?
                """, (
                    lead_id, comp, subject, body, classification,
                    1 if is_hot else 0,
                    ai_reply, ai_reply,
                    op_id or None, owner, owner, message_id or None,
                    reply_id
                ))
            else:
                conn.execute("""
                    INSERT INTO inbox_replies (
                        id, lead_id, sender_email, company_name, subject,
                        message_body, classification, is_hot_lead, ai_suggested_reply,
                        operator_id, owner_username, message_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reply_id, lead_id, clean_sender, comp, subject,
                    body, classification, 1 if is_hot else 0, ai_reply,
                    op_id or None, owner, message_id or None
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
            "is_new_reply": is_new_reply,
            "reply_snippet": snippet,
            "ai_suggested_reply": ai_reply,
            "operator_id": operator_id,
            "alert": alert_msg,
            "blacklisted": classification in ("UNSUBSCRIBE", "BOUNCE")
        }

    def poll_enrolled_inboxes(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inbound IMAP reply detection connecting to imap.gmail.com:993 (SSL/TLS).
        Scans recent messages (last 48 hours, both read and unread) in INBOX,
        matches incoming 'From' addresses against leads currently in 'Dispatched' (SENT) status,
        and transitions matched leads to 'REPLIED'.
        """
        from datetime import timedelta
        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        owner = (owner_username or "").strip().lower()
        op_id_filter = (operator_id or "").strip()

        with self.db.get_connection() as conn:
            if owner or op_id_filter:
                mailboxes = conn.execute("""
                    SELECT id, email_address, imap_host, imap_port, imap_username, imap_password, smtp_password, operator_id, owner_username
                    FROM mailbox_rotator
                    WHERE is_active = 1 AND (lower(owner_username) = ? OR operator_id = ?)
                """, (owner, op_id_filter)).fetchall()
            else:
                mailboxes = conn.execute("""
                    SELECT id, email_address, imap_host, imap_port, imap_username, imap_password, smtp_password, operator_id, owner_username
                    FROM mailbox_rotator
                    WHERE is_active = 1
                """).fetchall()

            # Build set of all enrolled sending mailbox addresses for whitelist
            all_enrolled = conn.execute(
                "SELECT lower(email_address) FROM mailbox_rotator WHERE is_active = 1"
            ).fetchall()
            enrolled_senders: set = {row[0].strip() for row in all_enrolled if row[0]}

        if not mailboxes:
            return {
                "success": True,
                "processed_count": 0,
                "new_replies_count": 0,
                "processed": [],
                "errors": ["No active mailboxes enrolled in rotator."],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=2)
        since_date_str = cutoff_dt.strftime("%d-%b-%Y")

        for mb in mailboxes:
            mb_email = mb["email_address"]
            host = (mb["imap_host"] or "").strip() or "imap.gmail.com"
            port = int(mb["imap_port"] or 993)
            user = (mb["imap_username"] or mb["email_address"] or "").strip()
            raw_pwd = mb["imap_password"] or mb["smtp_password"] or ""
            pwd = re.sub(r'\s+', '', raw_pwd)
            mb_owner = (mb["owner_username"] or owner or "").strip().lower()
            op_id = mb["operator_id"] or operator_id

            if not user or not pwd:
                err_msg = f"{mb_email}: Missing IMAP credentials (username or App Password)"
                errors.append(err_msg)
                continue

            try:
                mail = imaplib.IMAP4_SSL(host, port, timeout=15)
                mail.login(user, pwd)
                mail.select("INBOX")

                # Robust 48h scan: look for messages SINCE cutoff_date (both read and unread)
                status, messages = None, [b""]
                try:
                    status, messages = mail.search(None, f'SINCE "{since_date_str}"')
                except Exception:
                    pass

                if status != "OK" or not messages or not messages[0]:
                    try:
                        status, messages = mail.search(None, f'(SINCE {since_date_str})')
                    except Exception:
                        pass

                if status != "OK" or not messages or not messages[0]:
                    # Fallback to recent messages
                    try:
                        status, messages = mail.search(None, "ALL")
                    except Exception:
                        status, messages = ("NO", [b""])

                if status == "OK" and messages and messages[0]:
                    msg_ids = messages[0].split()
                    # Limit to the most recent 100 messages to maintain speed
                    if len(msg_ids) > 100:
                        msg_ids = msg_ids[-100:]

                    for msg_id in msg_ids:
                        try:
                            res, msg_data = mail.fetch(msg_id, "(RFC822)")
                            if not msg_data or res != "OK":
                                continue

                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    msg = email.message_from_bytes(response_part[1])
                                    sender = msg.get("From", "")
                                    subject_raw = decode_mime_header(msg.get("Subject", ""))
                                    in_reply_to = msg.get("In-Reply-To", "")
                                    references = msg.get("References", "")
                                    # Extract Message-ID for deduplication (Item 4)
                                    raw_message_id = (msg.get("Message-ID", "") or "").strip()
                                    body_text = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                payload = part.get_payload(decode=True)
                                                if payload:
                                                    body_text += payload.decode("utf-8", errors="ignore")
                                    else:
                                        payload = msg.get_payload(decode=True)
                                        if payload:
                                            body_text = payload.decode("utf-8", errors="ignore")

                                    # Parse sender strictly using parseaddr
                                    _, parsed_addr = parseaddr(sender)
                                    clean_sender = (parsed_addr or "").strip().lower()
                                    if not clean_sender:
                                        sender_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
                                        clean_sender = sender_match.group(0).lower().strip() if sender_match else sender.lower().strip()

                                    mb_email_clean = (mb_email or "").strip().lower()
                                    user_clean = (user or "").strip().lower()

                                    # 1. Ignore self-sent emails from the mailbox itself
                                    if clean_sender in (mb_email_clean, user_clean):
                                        continue

                                    # 2. Ignore emails from other enrolled sending mailboxes
                                    #    (prevents enrolled senders from being classified/suppressed)
                                    if clean_sender in enrolled_senders:
                                        continue

                                    # 3. Ignore automated system notifications unless they match bounce patterns
                                    system_noise = (
                                        "no-reply@", "noreply@", "notifications@", "googlecommunityteam",
                                        "mail-noreply@", "donotreply@", "do-not-reply@", "newsletter@"
                                    )
                                    if any(sn in clean_sender for sn in system_noise):
                                        combined_check = f"{subject_raw} {body_text}"
                                        is_bounce = any(re.search(bp, combined_check, re.IGNORECASE) for bp in BOUNCE_PATTERNS)
                                        if not is_bounce:
                                            continue

                                    # 4. Message-ID deduplication (Item 4)
                                    #    Skip if this exact message was already processed
                                    if raw_message_id:
                                        with self.db.get_connection() as dedup_conn:
                                            already_seen = dedup_conn.execute(
                                                "SELECT id FROM inbox_replies WHERE message_id = ? LIMIT 1",
                                                (raw_message_id,)
                                            ).fetchone()
                                        if already_seen:
                                            continue

                                    proc = self.process_incoming_reply(
                                        sender_email=clean_sender,
                                        subject=subject_raw,
                                        body=body_text,
                                        operator_id=op_id,
                                        in_reply_to=in_reply_to,
                                        references=references,
                                        message_id=raw_message_id,
                                        owner_username=mb_owner
                                    )
                                    results.append(proc)
                        except Exception as msg_err:
                            errors.append(f"{mb_email} msg fetch error: {str(msg_err)}")

                mail.logout()
            except Exception as e:
                err_msg = f"{mb_email} ({host}:{port}): {type(e).__name__} - {str(e)}"
                errors.append(err_msg)

        new_replies_count = sum(1 for r in results if r.get("is_new_reply"))

        return {
            "success": len(errors) == 0,
            "processed_count": len(results),
            "new_replies_count": new_replies_count,
            "processed": results,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_hot_lead_alerts(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        is_admin: bool = False
    ) -> List[Dict[str, Any]]:
        """Returns hot lead replies requiring action, filtered by tenant/user, strictly deduplicated by lead/sender."""
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        with self.db.get_connection() as conn:
            if is_admin and not op_id:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, ai_suggested_reply, received_at, status,
                           operator_id, owner_username
                    FROM inbox_replies
                    WHERE is_hot_lead = 1 AND (lower(owner_username) = ? OR operator_id = ? OR owner_username = '' OR owner_username IS NULL)
                    ORDER BY received_at DESC
                """, (owner, op_id)).fetchall()
            elif owner or op_id:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, ai_suggested_reply, received_at, status,
                           operator_id, owner_username
                    FROM inbox_replies
                    WHERE is_hot_lead = 1 AND (lower(owner_username) = ? OR operator_id = ?)
                    ORDER BY received_at DESC
                """, (owner, op_id)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, ai_suggested_reply, received_at, status,
                           operator_id, owner_username
                    FROM inbox_replies
                    WHERE is_hot_lead = 1
                    ORDER BY received_at DESC
                """).fetchall()

            seen = set()
            deduped = []
            for r in rows:
                item = dict(r)
                sender = (item.get("sender_email") or "").lower().strip()
                lid = item.get("lead_id")
                key = lid if lid else sender
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                if sender:
                    seen.add(sender)
                deduped.append(item)
            return deduped

    def get_all_replies(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns all logged replies, filtered by tenant/user, deduplicated by lead/sender."""
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        with self.db.get_connection() as conn:
            if owner or op_id:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, is_hot_lead, received_at, status,
                           operator_id, owner_username
                    FROM inbox_replies
                    WHERE (lower(owner_username) = ? OR operator_id = ?)
                    ORDER BY received_at DESC
                """, (owner, op_id)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, lead_id, sender_email, company_name, subject,
                           message_body, classification, is_hot_lead, received_at, status,
                           operator_id, owner_username
                    FROM inbox_replies
                    ORDER BY received_at DESC
                """).fetchall()

            seen = set()
            deduped = []
            for r in rows:
                item = dict(r)
                sender = (item.get("sender_email") or "").lower().strip()
                lid = item.get("lead_id")
                key = lid if lid else sender
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                if sender:
                    seen.add(sender)
                deduped.append(item)
            return deduped

    def get_suppressed_entities(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns list of suppressed entities for CAN-SPAM / GDPR compliance, filtered per user."""
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        with self.db.get_connection() as conn:
            if owner or op_id:
                rows = conn.execute("""
                    SELECT id, entity, entity_type, reason, operator_id, owner_username, suppressed_at
                    FROM suppressed_entities
                    WHERE (lower(owner_username) = ? OR operator_id = ?)
                    ORDER BY suppressed_at DESC
                """, (owner, op_id)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, entity, entity_type, reason, operator_id, owner_username, suppressed_at
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
