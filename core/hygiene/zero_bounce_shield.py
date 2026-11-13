"""
H.Huddair's Nexus-Pulse - Level 1
Hygiene Engine: Zero-Bounce 3-Stage Hygiene Shield
Stage 1: RFC 5322 Syntax Validation & Disposable Domain Shield
Stage 2: DNS MX Record Verification & Null-MX Detection
Stage 3: Silent SMTP Ping Test (Zero-Send Handshake HELO/MAIL FROM/RCPT TO)
Adapted for cloud/container environments (Railway, Render, AWS) with port 25 restriction handling.
"""

import logging
import os
import re
import socket
import smtplib
from typing import Dict, List, Optional, Tuple, Set
import dns.resolver

from ..models import HygieneReport, HygieneStatus
from database.db_engine import get_db_engine

logger = logging.getLogger("nexus.hygiene")

# RFC 5322 Compliant Email Regex
EMAIL_SYNTAX_PATTERN = re.compile(
    r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
    r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
    re.IGNORECASE
)

# Known Disposable & Temporary Email Domains
DISPOSABLE_DOMAINS: Set[str] = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "sharklasers.com", "grr.la", "tempmail.com", "temp-mail.org", "10minutemail.com",
    "throwawaymail.com", "trashmail.com", "trashmail.net", "yopmail.com", "yopmail.fr",
    "dispostable.com", "getairmail.com", "fakeinbox.com", "mytemp.email", "mohmal.com",
    "burnermail.io", "maildrop.cc", "crazymailing.com", "nada.ltd", "dropmail.me",
    "tempr.email", "discard.email", "spambox.us", "fake-box.com", "inboxkitten.com"
}

# Role addresses that reject automated communication
DO_NOT_REPLY_PREFIXES = {"noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon"}


class ZeroBounceHygieneShield:
    """
    3-Stage Email Hygiene Verification Shield.
    Eliminates bounced, dead, or non-existent email addresses before outreach.
    """

    _port_25_probe_checked: Optional[bool] = None
    _port_25_available: bool = False

    def __init__(
        self,
        smtp_timeout: float = 3.0,
        helo_hostname: str = "nexus-pulse.huddair.io",
        log_to_db: bool = True
    ):
        self.smtp_timeout = smtp_timeout
        self.helo_hostname = helo_hostname
        self.log_to_db = log_to_db
        self.db = get_db_engine() if log_to_db else None

    @classmethod
    def is_port_25_available(cls, timeout: float = 1.5) -> bool:
        """
        Fast cached pre-check to determine if outbound SMTP port 25 is permitted by hosting network.
        Cloud container environments like Railway, AWS, and GCP restrict outbound port 25.
        """
        if cls._port_25_probe_checked is not None:
            return cls._port_25_available

        # Check cloud environment indicators
        is_cloud = bool(
            os.environ.get("RAILWAY_ENVIRONMENT") or
            os.environ.get("RAILWAY_PROJECT_ID") or
            os.environ.get("PORT") or
            os.environ.get("NEXUS_CLOUD_MODE") == "1"
        )
        if is_cloud:
            cls._port_25_probe_checked = True
            cls._port_25_available = False
            logger.info("[HYGIENE] Cloud environment detected (Railway/container). Outbound SMTP port 25 is restricted by host policy.")
            return False

        # Fast socket probe on local or unblocked environments
        test_hosts = ["gmail-smtp-in.l.google.com", "smtp.gmail.com"]
        for th in test_hosts:
            try:
                with socket.create_connection((th, 25), timeout=timeout):
                    cls._port_25_probe_checked = True
                    cls._port_25_available = True
                    logger.info("[HYGIENE] Outbound SMTP port 25 verified accessible.")
                    return True
            except (socket.timeout, TimeoutError, ConnectionRefusedError, OSError):
                continue
            except Exception:
                continue

        cls._port_25_probe_checked = True
        cls._port_25_available = False
        logger.info("[HYGIENE] Outbound SMTP port 25 is closed or restricted by local network firewall.")
        return False

    # ---------------------------------------------------------
    # STAGE 1: Syntax & Disposable Email Verification
    # ---------------------------------------------------------
    def verify_stage_1_syntax(self, email: str) -> Tuple[bool, bool, str]:
        """
        Validates RFC 5322 syntax and checks disposable domain list.
        Returns: (is_syntax_valid: bool, is_disposable: bool, message: str)
        """
        if not email or len(email) > 254:
            return False, False, "Email exceeds max RFC 5322 length (254 chars) or empty"

        clean = email.strip().lower()

        if not EMAIL_SYNTAX_PATTERN.match(clean):
            return False, False, "Invalid RFC 5322 email syntax structure"

        prefix, domain = clean.split("@", 1)

        if prefix in DO_NOT_REPLY_PREFIXES:
            return False, False, f"Automated dead-end role prefix detected: {prefix}@"

        if domain in DISPOSABLE_DOMAINS:
            return True, True, f"Disposable temporary email provider detected: {domain}"

        # Ensure TLD is at least 2 chars and not purely digits
        tld = domain.split(".")[-1]
        if len(tld) < 2 or tld.isdigit():
            return False, False, f"Invalid top-level domain: .{tld}"

        return True, False, "Stage 1 Syntax & Disposable check PASSED"

    # ---------------------------------------------------------
    # STAGE 2: DNS MX Record Verification
    # ---------------------------------------------------------
    def verify_stage_2_mx(self, domain: str) -> Tuple[bool, List[str], str]:
        """
        Queries DNS MX records for domain.
        Returns: (is_mx_valid: bool, mx_hosts: List[str], message: str)
        """
        clean_domain = domain.strip().lower()

        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3.5
            resolver.lifetime = 3.5
            answers = resolver.resolve(clean_domain, "MX")

            # Sort by MX preference (lowest preference number first)
            sorted_records = sorted(answers, key=lambda r: r.preference)
            mx_hosts = [str(r.exchange).rstrip(".") for r in sorted_records]

            # RFC 7505 Null MX check: a single MX with hostname "." means explicitly no email service
            if len(mx_hosts) == 1 and (mx_hosts[0] == "" or mx_hosts[0] == "."):
                return False, [], "Domain explicitly advertises RFC 7505 Null MX (No email reception)"

            if not mx_hosts:
                return False, [], f"No active MX records found for domain '{clean_domain}'"

            return True, mx_hosts, f"Found {len(mx_hosts)} active MX records. Primary: {mx_hosts[0]}"

        except dns.resolver.NXDOMAIN:
            return False, [], f"Domain '{clean_domain}' does not exist (NXDOMAIN)"
        except dns.resolver.NoAnswer:
            # Fallback check for A record (RFC 5321 allows direct A record delivery if MX is absent)
            try:
                a_answers = resolver.resolve(clean_domain, "A")
                if a_answers:
                    a_host = str(a_answers[0])
                    return True, [clean_domain], f"Fallback: No MX record, but active A record exists ({a_host})"
            except Exception:
                pass
            return False, [], f"No MX or A records found for domain '{clean_domain}'"
        except (dns.resolver.Timeout, dns.resolver.LifetimeTimeout):
            return False, [], f"DNS resolution timed out for domain '{clean_domain}'"
        except Exception as e:
            return False, [], f"DNS lookup failed: {str(e)}"

    # ---------------------------------------------------------
    # STAGE 3: Silent SMTP Ping Test (Zero-Send Handshake)
    # ---------------------------------------------------------
    def verify_stage_3_smtp_ping(
        self,
        email: str,
        mx_host: str
    ) -> Tuple[Optional[bool], Optional[int], str]:
        """
        Executes a zero-send SMTP probe (HELO -> MAIL FROM -> RCPT TO -> RSET/QUIT).
        Handles cloud environment restrictions (port 25 blocked) and server IP reputation blocks.
        Returns: (is_deliverable: Optional[bool], smtp_code: Optional[int], message: str)
        """
        clean_email = email.strip().lower()

        # Check if outbound port 25 is available
        if not self.is_port_25_available():
            msg = "Cloud environment: Outbound port 25 restricted by hosting network. High deliverability confidence via verified DNS MX records."
            logger.debug(f"[HYGIENE S3] Port 25 restricted for {clean_email}: {msg}")
            return None, None, msg

        effective_timeout = min(self.smtp_timeout, 2.5)

        # Resolve authentic HELO hostname
        helo = self.helo_hostname
        if "huddair.io" in helo:
            try:
                fqdn = socket.getfqdn()
                if fqdn and "." in fqdn:
                    helo = fqdn
                else:
                    domain_part = clean_email.split("@")[1]
                    helo = f"mail.{domain_part}"
            except Exception:
                helo = "mail.gmail.com"

        try:
            server = smtplib.SMTP(timeout=effective_timeout)
            server.connect(mx_host, 25)
            server.helo(helo)
            server.mail(f"probe@{helo}")

            # RCPT TO is the mailbox existence test
            code, resp_bytes = server.rcpt(clean_email)
            resp_msg = resp_bytes.decode("utf-8", errors="ignore").strip()

            try:
                server.rset()
                server.quit()
            except Exception:
                pass

            logger.info(f"[HYGIENE S3] Response for {clean_email} on {mx_host}: {code} - {resp_msg}")

            if code in (250, 251):
                return True, code, f"SMTP Ping SUCCESS ({code}): Mailbox exists and accepts mail. Details: {resp_msg}"
            elif code in (450, 451):
                return True, code, f"Greylisted / Rate-limited ({code}): Mailbox likely valid but deferred ({resp_msg})"
            elif code in (550, 551, 552, 553, 554, 501):
                resp_lower = resp_msg.lower()
                # Check if server blocked the connection/IP rather than the mailbox
                is_policy_block = any(k in resp_lower for k in [
                    "spamhaus", "blacklist", "block", "reputation", "relay",
                    "policy", "prohibition", "denied", "unavailable", "ptr",
                    "dnsbl", "client host", "helo", "administrative", "spf", "dmarc"
                ])
                if is_policy_block:
                    logger.warning(f"[HYGIENE S3] Server policy block on probe for {clean_email} ({code}): {resp_msg}")
                    return None, code, f"SMTP probe deferred by server policy/IP reputation ({code}): {resp_msg}"

                # Actual dead mailbox check
                is_dead_mailbox = any(k in resp_lower for k in [
                    "user unknown", "no such user", "mailbox not found", "recipient unknown",
                    "invalid recipient", "does not exist", "undeliverable", "unknown user",
                    "recipient rejected", "not found"
                ])
                if is_dead_mailbox:
                    logger.warning(f"[HYGIENE S3] Mailbox rejected as dead for {clean_email} ({code}): {resp_msg}")
                    return False, code, f"DEAD ADDRESS REJECTED ({code}): Recipient address rejected by mail server ({resp_msg})"

                return None, code, f"Indeterminate SMTP response code {code}: {resp_msg}"
            else:
                return None, code, f"Indeterminate SMTP response code {code}: {resp_msg}"

        except (socket.timeout, TimeoutError):
            logger.info(f"[HYGIENE S3] Connection timed out to {mx_host}:25 (port 25 blocked by network)")
            return None, None, f"SMTP connection timed out connecting to {mx_host}:25 (likely port 25 blocked by local network)"
        except (ConnectionRefusedError, OSError) as os_err:
            logger.info(f"[HYGIENE S3] Connection refused on port 25 for {mx_host}: {os_err}")
            return None, None, f"SMTP connection refused on port 25 for {mx_host}: {str(os_err)}"
        except smtplib.SMTPServerDisconnected:
            logger.info(f"[HYGIENE S3] SMTP server disconnected prematurely from {mx_host}")
            return None, None, f"SMTP server disconnected prematurely from {mx_host}"
        except Exception as ex:
            logger.warning(f"[HYGIENE S3] SMTP probe error for {clean_email} on {mx_host}: {ex}")
            return None, None, f"SMTP probe error: {str(ex)}"

    # ---------------------------------------------------------
    # Comprehensive 3-Stage Pipeline
    # ---------------------------------------------------------
    def validate_lead_email(self, email: str) -> HygieneReport:
        """
        Runs the full 3-Stage Zero-Bounce validation pipeline on an email address.
        """
        clean_email = email.strip().lower()
        report = HygieneReport(email=clean_email, status=HygieneStatus.VERIFIED)

        # STAGE 1: Syntax & Disposable Check
        s1_valid, is_disposable, s1_msg = self.verify_stage_1_syntax(clean_email)
        report.stage_1_syntax_valid = s1_valid
        report.is_disposable_domain = is_disposable

        if not s1_valid or is_disposable:
            report.status = HygieneStatus.SYNTAX_INVALID
            report.smtp_diagnostic_message = s1_msg
            logger.info(f"[HYGIENE] {clean_email} failed Stage 1: {s1_msg}")
            self._record_audit(report)
            return report

        # STAGE 2: DNS MX Record Verification
        domain = clean_email.split("@")[1]
        s2_valid, mx_hosts, s2_msg = self.verify_stage_2_mx(domain)
        report.stage_2_mx_valid = s2_valid
        report.mx_records = mx_hosts

        if not s2_valid or not mx_hosts:
            report.status = HygieneStatus.DOMAIN_NO_MX
            report.smtp_diagnostic_message = s2_msg
            logger.info(f"[HYGIENE] {clean_email} failed Stage 2 (MX): {s2_msg}")
            self._record_audit(report)
            return report

        # STAGE 3: Silent SMTP Ping Test
        primary_mx = mx_hosts[0]
        s3_valid, smtp_code, s3_msg = self.verify_stage_3_smtp_ping(clean_email, primary_mx)
        report.stage_3_smtp_valid = s3_valid
        report.smtp_response_code = smtp_code
        report.smtp_diagnostic_message = s3_msg

        if s3_valid is False:
            report.status = HygieneStatus.SMTP_REJECTED
        elif s3_valid is True:
            report.status = HygieneStatus.VERIFIED
        else:
            # Indeterminate (e.g. port 25 blocked in cloud) - retains high MX confidence
            report.status = HygieneStatus.SMTP_INDETERMINATE

        logger.info(f"[HYGIENE] Completed {clean_email} -> {report.status.value} (S1: {s1_valid}, S2: {s2_valid}, S3: {s3_valid})")
        self._record_audit(report)
        return report

    def _record_audit(self, report: HygieneReport) -> None:
        """Logs verification outcome to SQLite audit table."""
        if not self.db:
            return
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO hygiene_audit_log (
                        email, status, stage_1_syntax, is_disposable,
                        stage_2_mx, stage_3_smtp, smtp_code, smtp_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.email,
                    report.status.value,
                    1 if report.stage_1_syntax_valid else 0,
                    1 if report.is_disposable_domain else 0,
                    1 if report.stage_2_mx_valid else 0,
                    1 if report.stage_3_smtp_valid else (0 if report.stage_3_smtp_valid is False else -1),
                    report.smtp_response_code or 0,
                    report.smtp_diagnostic_message or ""
                ))
                conn.commit()
        except Exception as ex:
            logger.debug(f"[HYGIENE] Failed to record hygiene audit: {ex}")


_global_hygiene_shield = None

def get_hygiene_shield() -> ZeroBounceHygieneShield:
    global _global_hygiene_shield
    if _global_hygiene_shield is None:
        _global_hygiene_shield = ZeroBounceHygieneShield()
    return _global_hygiene_shield
