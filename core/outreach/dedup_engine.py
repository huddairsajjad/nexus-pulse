"""
Nexus-Pulse: Domain Alias Deduplication & Historical Check Engine
Prevents reprocessing of previously seen/rejected/archived leads.

Features:
  - Checks dedup_registry, vault_leads, outreach_queue, suppressed_entities, blacklist_rules
  - Canonical domain normalisation (strips www., mail., cdn., etc.)
  - SHA-256 fingerprinting for fast O(1) lookup
  - register_domain_seen() upsert to mark new scraped domains
  - register_domain_alias() groups aliases under a canonical key
"""
import hashlib
import logging
from typing import Optional, Tuple

logger = logging.getLogger("NexusPulse.DedupEngine")

# Common subdomain prefixes to strip before computing canonical domain
_STRIP_PREFIXES = (
    "www.", "mail.", "smtp.", "mx.", "ftp.", "cdn.", "static.",
    "app.", "api.", "portal.", "web.", "m.", "mobile.",
)


def _canonical_domain(domain: str) -> str:
    """Returns a normalised canonical key for a domain, stripping common subdomain prefixes."""
    d = domain.strip().lower().split(":")[0]  # strip port
    for pfx in _STRIP_PREFIXES:
        if d.startswith(pfx):
            d = d[len(pfx):]
            break
    return d


def _domain_fingerprint(domain: str) -> str:
    """SHA-256 hex digest of the canonical domain string."""
    return hashlib.sha256(_canonical_domain(domain).encode()).hexdigest()


def is_historically_seen(domain: str, email: str, conn) -> Tuple[bool, str]:
    """
    Checks whether a domain/email has been previously processed, rejected, or archived.

    Checks (in order):
      1. dedup_registry — hash fingerprint OR normalized key
      2. vault_leads    — domain column OR primary_email
      3. outreach_queue — recipient email OR domain suffix match
      4. suppressed_entities — entity match
      5. blacklist_rules — exact domain match

    Returns:
      (True, reason_string)  if previously seen
      (False, "")            if clean/new
    """
    if not domain and not email:
        return False, ""

    canon = _canonical_domain(domain) if domain else ""
    email_lower = (email or "").strip().lower()
    fingerprint = _domain_fingerprint(domain) if domain else ""

    try:
        # 1. dedup_registry — hash fingerprint OR normalized key
        if fingerprint or canon:
            conditions = []
            params = []
            if fingerprint:
                conditions.append("hash_fingerprint = ?")
                params.append(fingerprint)
            if canon:
                conditions.append("normalized_key = ?")
                params.append(canon)
            sql = f"SELECT status, normalized_key FROM dedup_registry WHERE {' OR '.join(conditions)} LIMIT 1"
            row = conn.execute(sql, params).fetchone()
            if row:
                status = row[0] if isinstance(row, (list, tuple)) else row["status"]
                key = row[1] if isinstance(row, (list, tuple)) else row["normalized_key"]
                return True, f"Domain '{canon or key}' previously seen in dedup registry (status={status})"

        # 2. vault_leads — domain OR email
        if canon:
            row = conn.execute(
                "SELECT id FROM vault_leads WHERE lower(domain) = ? LIMIT 1", (canon,)
            ).fetchone()
            if row:
                return True, f"Domain '{canon}' already exists in vault_leads"
        if email_lower:
            row = conn.execute(
                "SELECT id FROM vault_leads WHERE lower(primary_email) = ? LIMIT 1", (email_lower,)
            ).fetchone()
            if row:
                return True, f"Email '{email_lower}' already exists in vault_leads"

        # 3. outreach_queue — recipient exact match OR domain suffix
        if email_lower:
            row = conn.execute(
                "SELECT id FROM outreach_queue WHERE lower(recipient) = ? LIMIT 1", (email_lower,)
            ).fetchone()
            if row:
                return True, f"Email '{email_lower}' already in outreach_queue"
        if canon:
            row = conn.execute(
                "SELECT id FROM outreach_queue WHERE lower(recipient) LIKE ? LIMIT 1",
                (f"%@{canon}",)
            ).fetchone()
            if row:
                return True, f"Domain '{canon}' already has an outreach_queue entry"

        # 4. suppressed_entities
        checks = [v for v in [canon, email_lower] if v]
        for check_val in checks:
            row = conn.execute(
                "SELECT id FROM suppressed_entities WHERE lower(entity) = ? LIMIT 1", (check_val,)
            ).fetchone()
            if row:
                return True, f"'{check_val}' is in suppressed_entities"

        # 5. blacklist_rules — exact domain match
        if canon:
            row = conn.execute(
                "SELECT id FROM blacklist_rules WHERE lower(pattern) = ? LIMIT 1", (canon,)
            ).fetchone()
            if row:
                return True, f"Domain '{canon}' is in blacklist_rules"

    except Exception as e:
        logger.debug(f"[DEDUP] is_historically_seen error for domain='{domain}', email='{email}': {e}")
        # On DB error, do not block the lead — fail open
        return False, ""

    return False, ""


def register_domain_seen(domain: str, email: str, lead_id: Optional[str], conn) -> None:
    """
    Registers a newly scraped domain/email in dedup_registry to prevent future reprocessing.
    Uses INSERT OR IGNORE to handle concurrent insertions gracefully.
    """
    if not domain and not email:
        return
    canon = _canonical_domain(domain) if domain else (email or "").strip().lower()
    if not canon:
        return
    fingerprint = hashlib.sha256(canon.encode()).hexdigest()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO dedup_registry
                (entity_type, normalized_key, hash_fingerprint, status, lead_id)
            VALUES (?, ?, ?, 'SCRAPED', ?)
        """, ("domain" if domain else "email", canon, fingerprint, lead_id))
        conn.commit()
        logger.debug(f"[DEDUP] Registered '{canon}' (lead_id={lead_id})")
    except Exception as e:
        logger.debug(f"[DEDUP] register_domain_seen failed for '{canon}': {e}")


def register_domain_alias(canonical: str, alias: str, conn) -> None:
    """
    Groups a domain alias under a canonical key.
    Both are registered in dedup_registry so future lookups for either hit.
    """
    for d in [canonical, alias]:
        if d:
            register_domain_seen(d, "", None, conn)
