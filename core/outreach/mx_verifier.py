"""
Nexus-Pulse: MX Record & SMTP Banner Verifier
Validates that a target domain has live mail exchange infrastructure
before the lead enters the outreach pipeline.

Design principles:
  - Public email providers (gmail.com, etc.) always pass — no DNS overhead
  - DNS timeout → treated as deliverable (lenient, don't penalise slow DNS)
  - Generic DNS errors → treated as deliverable (fail open, don't block pipeline)
  - NXDOMAIN or NoAnswer → not deliverable (definitive negative)
  - SMTP banner check is best-effort; port 25 blocked in many cloud envs is fine
"""
import logging
import socket
import smtplib
from typing import Dict, Any, List

logger = logging.getLogger("NexusPulse.MXVerifier")

# Public/free email providers — always have MX, skip DNS overhead
_ALWAYS_DELIVERABLE = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com", "aol.com",
    "protonmail.com", "proton.me", "zoho.com", "fastmail.com",
    "fastmail.fm", "hey.com", "tutanota.com", "tutanota.de",
}


def verify_mx_record(domain: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Performs MX DNS lookup and optional SMTP banner check for a domain.

    Args:
        domain: The target domain to verify (e.g. 'company.co.uk')
        timeout: DNS/SMTP timeout in seconds (default 5)

    Returns dict:
      {
        "has_mx": bool,       # True if at least one MX record exists
        "mx_host": str,       # Primary MX hostname (empty string if none)
        "smtp_banner": str,   # SMTP EHLO banner if reachable (empty if not)
        "deliverable": bool,  # True if domain has valid mail infrastructure
        "error": str          # Error message if check failed (empty if ok)
      }
    """
    if not domain:
        return {
            "has_mx": False, "mx_host": "", "smtp_banner": "",
            "deliverable": False, "error": "No domain provided"
        }

    # Normalise: strip port, lowercase
    domain = domain.strip().lower().split(":")[0].rstrip(".")

    # Short-circuit: known public email providers always have MX
    if domain in _ALWAYS_DELIVERABLE:
        return {
            "has_mx": True, "mx_host": f"mx.{domain}",
            "smtp_banner": "", "deliverable": True, "error": ""
        }

    try:
        import dns.resolver  # type: ignore[import]
        import dns.exception  # type: ignore[import]
    except ImportError:
        # dnspython not installed — be lenient, don't block pipeline
        logger.warning("[MX] dnspython not available — skipping MX verification, treating as deliverable")
        return {
            "has_mx": True, "mx_host": "", "smtp_banner": "",
            "deliverable": True, "error": "dnspython not installed"
        }

    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=float(timeout))
    except dns.resolver.NXDOMAIN:
        logger.info(f"[MX] NXDOMAIN for '{domain}' — not deliverable")
        return {
            "has_mx": False, "mx_host": "", "smtp_banner": "",
            "deliverable": False, "error": f"NXDOMAIN: {domain}"
        }
    except dns.resolver.NoAnswer:
        logger.info(f"[MX] No MX answer for '{domain}' — not deliverable")
        return {
            "has_mx": False, "mx_host": "", "smtp_banner": "",
            "deliverable": False, "error": f"No MX records found for {domain}"
        }
    except dns.exception.Timeout:
        # DNS timeout is common in cloud envs — be lenient
        logger.warning(f"[MX] DNS timeout for '{domain}' — treating as deliverable")
        return {
            "has_mx": True, "mx_host": "", "smtp_banner": "",
            "deliverable": True, "error": "DNS timeout — assumed deliverable"
        }
    except Exception as e:
        # Any other DNS error (SERVFAIL, etc.) — fail open
        logger.warning(f"[MX] DNS error for '{domain}': {e} — treating as deliverable")
        return {
            "has_mx": True, "mx_host": "", "smtp_banner": "",
            "deliverable": True, "error": str(e)
        }

    # Sort MX records by preference (lowest preference = highest priority)
    try:
        sorted_records = sorted(records, key=lambda r: r.preference)
        mx_host = str(sorted_records[0].exchange).rstrip(".")
    except Exception as e:
        logger.warning(f"[MX] Could not parse MX records for '{domain}': {e}")
        return {
            "has_mx": True, "mx_host": "", "smtp_banner": "",
            "deliverable": True, "error": str(e)
        }

    # Optional: SMTP banner check on port 25 (best-effort, non-blocking)
    smtp_banner = ""
    try:
        with smtplib.SMTP(timeout=timeout) as s:
            s.connect(mx_host, 25)
            code, banner_bytes = s.ehlo()
            if code == 250 and isinstance(banner_bytes, bytes):
                smtp_banner = banner_bytes.decode("utf-8", errors="ignore")[:200]
    except (socket.timeout, ConnectionRefusedError, OSError):
        # Port 25 is commonly blocked in cloud/VPS environments — perfectly normal
        pass
    except Exception:
        pass

    logger.info(f"[MX] ✓ '{domain}' → MX={mx_host}, deliverable=True")
    return {
        "has_mx": True,
        "mx_host": mx_host,
        "smtp_banner": smtp_banner,
        "deliverable": True,
        "error": ""
    }


def bulk_verify_mx(domains: List[str], timeout: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Verifies MX records for a list of domains.
    Returns dict keyed by domain name.
    """
    return {d: verify_mx_record(d, timeout=timeout) for d in domains if d}
