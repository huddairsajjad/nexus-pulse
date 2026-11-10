"""
H.Huddair's Nexus-Pulse - Level 1
Hygiene Engine: Zero-Bounce 3-Stage Hygiene Shield
Stage 1: RFC 5322 Syntax Validation & Disposable Domain Shield
Stage 2: DNS MX Record Verification & Null-MX Detection
Stage 3: Silent SMTP Ping Test (Zero-Send Handshake HELO/MAIL FROM/RCPT TO)
"""

import re
import socket
import smtplib
from typing import Dict, List, Optional, Tuple, Set
import dns.resolver

from ..models import HygieneReport, HygieneStatus
from database.db_engine import get_db_engine

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

    def __init__(
        self,
        smtp_timeout: float = 5.0,
        helo_hostname: str = "nexus-pulse.huddair.io",
        log_to_db: bool = True
    ):
        self.smtp_timeout = smtp_timeout
        self.helo_hostname = helo_hostname
        self.log_to_db = log_to_db
        self.db = get_db_engine() if log_to_db else None

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
            resolver.timeout = 4.0
            resolver.lifetime = 4.0
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
        Returns: (is_deliverable: Optional[bool], smtp_code: Optional[int], message: str)
        """
        clean_email = email.strip().lower()

        try:
            # Connect on standard SMTP port 25 with short timeout
            server = smtplib.SMTP(timeout=self.smtp_timeout)
            server.connect(mx_host, 25)
            server.helo(self.helo_hostname)
            server.mail(f"probe@{self.helo_hostname}")

            # RCPT TO is the critical mailbox existence test
            code, resp_bytes = server.rcpt(clean_email)
            resp_msg = resp_bytes.decode("utf-8", errors="ignore").strip()

            # Clean exit without sending data
            try:
                server.rset()
                server.quit()
            except Exception:
                pass

            # Status code evaluation
            if code in (250, 251):
                return True, code, f"SMTP Ping SUCCESS ({code}): Mailbox exists and accepts mail. Details: {resp_msg}"
            elif code in (550, 551, 552, 553, 554, 501):
                return False, code, f"DEAD ADDRESS REJECTED ({code}): Recipient address rejected by mail server ({resp_msg})"
            elif code == 450 or code == 451:
                return True, code, f"Greylisted / Rate-limited ({code}): Mailbox likely valid but deferred ({resp_msg})"
            else:
                return None, code, f"Indeterminate SMTP response code {code}: {resp_msg}"

        except (socket.timeout, TimeoutError):
            return None, None, f"SMTP connection timed out connecting to {mx_host}:25 (likely port 25 blocked by local network)"
        except (ConnectionRefusedError, OSError) as os_err:
            return None, None, f"SMTP connection refused on port 25 for {mx_host}: {str(os_err)}"
        except smtplib.SMTPServerDisconnected:
            return None, None, f"SMTP server disconnected prematurely from {mx_host}"
        except Exception as ex:
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
            # Indeterminate (e.g. port 25 blocked locally) - retains high MX confidence
            report.status = HygieneStatus.SMTP_INDETERMINATE

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
        except Exception:
            pass


_global_hygiene_shield = None

def get_hygiene_shield() -> ZeroBounceHygieneShield:
    global _global_hygiene_shield
    if _global_hygiene_shield is None:
        _global_hygiene_shield = ZeroBounceHygieneShield()
    return _global_hygiene_shield
