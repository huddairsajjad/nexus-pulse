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


def is_historically_seen(
    domain: str,
    email: str,
    conn,
    owner_username: Optional[str] = None,
    operator_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Checks whether a domain/email has been previously processed, rejected, or archived.
    Strictly scoped by owner_username / operator_id so one user's history never blocks another user.

    Checks (in order):
      1. dedup_registry — hash fingerprint OR normalized key (scoped by owner_username)
      2. vault_leads    — domain column OR primary_email (scoped by owner_username/operator_id)
      3. outreach_queue — recipient email OR domain suffix match (scoped by owner_username/operator_id)
      4. suppressed_entities — entity match (scoped by owner_username/operator_id or global)
      5. blacklist_rules — exact domain match (global system rules)

    Returns:
      (True, reason_string)  if previously seen by this user
      (False, "")            if clean/new for this user
    """
    if not domain and not email:
        return False, ""

    canon = _canonical_domain(domain) if domain else ""
    email_lower = (email or "").strip().lower()
    fingerprint = _domain_fingerprint(domain) if domain else ""
    owner = (owner_username or "").strip().lower()
    op_id = (operator_id or "").strip()

    try:
        # 1. dedup_registry — hash fingerprint OR normalized key scoped by owner_username
        if fingerprint or canon:
            conditions = []
            params = []
            if fingerprint:
                conditions.append("hash_fingerprint = ?")
                params.append(fingerprint)
            if canon:
                conditions.append("normalized_key = ?")
                params.append(canon)

            if owner:
                sql = f"SELECT status, normalized_key FROM dedup_registry WHERE ({' OR '.join(conditions)}) AND lower(owner_username) = ? LIMIT 1"
                params.append(owner)
            else:
                sql = f"SELECT status, normalized_key FROM dedup_registry WHERE {' OR '.join(conditions)} LIMIT 1"

            row = conn.execute(sql, params).fetchone()
            if row:
                status = row[0] if isinstance(row, (list, tuple)) else row["status"]
                key = row[1] if isinstance(row, (list, tuple)) else row["normalized_key"]
                return True, f"Domain '{canon or key}' previously seen in dedup registry (status={status})"

        # 2. vault_leads — domain OR email scoped by owner_username / operator_id
        if canon:
            if owner or op_id:
                row = conn.execute(
                    "SELECT id FROM vault_leads WHERE lower(domain) = ? AND (lower(owner_username) = ? OR operator_id = ?) LIMIT 1",
                    (canon, owner, op_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM vault_leads WHERE lower(domain) = ? LIMIT 1", (canon,)
                ).fetchone()
            if row:
                return True, f"Domain '{canon}' already exists in your vault leads"

        if email_lower:
            if owner or op_id:
                row = conn.execute(
                    "SELECT id FROM vault_leads WHERE lower(primary_email) = ? AND (lower(owner_username) = ? OR operator_id = ?) LIMIT 1",
                    (email_lower, owner, op_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM vault_leads WHERE lower(primary_email) = ? LIMIT 1", (email_lower,)
                ).fetchone()
            if row:
                return True, f"Email '{email_lower}' already exists in your vault leads"

        # 3. outreach_queue — recipient exact match OR domain suffix scoped by owner
        if email_lower:
            if owner or op_id:
                row = conn.execute(
                    "SELECT id FROM outreach_queue WHERE lower(recipient) = ? AND (lower(owner_username) = ? OR operator_id = ?) LIMIT 1",
                    (email_lower, owner, op_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM outreach_queue WHERE lower(recipient) = ? LIMIT 1", (email_lower,)
                ).fetchone()
            if row:
                return True, f"Email '{email_lower}' already in your outreach queue"

        if canon:
            if owner or op_id:
                row = conn.execute(
                    "SELECT id FROM outreach_queue WHERE lower(recipient) LIKE ? AND (lower(owner_username) = ? OR operator_id = ?) LIMIT 1",
                    (f"%@{canon}", owner, op_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM outreach_queue WHERE lower(recipient) LIKE ? LIMIT 1",
                    (f"%@{canon}",)
                ).fetchone()
            if row:
                return True, f"Domain '{canon}' already has an outreach queue entry in your workspace"

        # 4. suppressed_entities — check entity match for this user or global
        checks = [v for v in [canon, email_lower] if v]
        for check_val in checks:
            if owner or op_id:
                row = conn.execute("""
                    SELECT id FROM suppressed_entities
                    WHERE lower(entity) = ? AND (lower(owner_username) = ? OR operator_id = ? OR owner_username = '' OR owner_username IS NULL)
                    LIMIT 1
                """, (check_val, owner, op_id)).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM suppressed_entities WHERE lower(entity) = ? LIMIT 1", (check_val,)
                ).fetchone()
            if row:
                return True, f"'{check_val}' is in suppressed entities"

        # 5. blacklist_rules — exact domain match (system-wide exclusion rules)
        if canon:
            row = conn.execute(
                "SELECT id FROM blacklist_rules WHERE lower(pattern) = ? LIMIT 1", (canon,)
            ).fetchone()
            if row:
                return True, f"Domain '{canon}' is in blacklist rules"

    except Exception as e:
        logger.debug(f"[DEDUP] is_historically_seen error for domain='{domain}', email='{email}': {e}")
        # On DB error, do not block the lead — fail open
        return False, ""

    return False, ""


def register_domain_seen(
    domain: str,
    email: str,
    lead_id: Optional[str],
    conn,
    owner_username: Optional[str] = None
) -> None:
    """
    Registers a newly scraped domain/email in dedup_registry to prevent future reprocessing by this user.
    Uses INSERT OR REPLACE on composite unique key (normalized_key, owner_username).
    """
    if not domain and not email:
        return
    canon = _canonical_domain(domain) if domain else (email or "").strip().lower()
    if not canon:
        return
    fingerprint = hashlib.sha256(canon.encode()).hexdigest()
    owner = (owner_username or "").strip()
    try:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO dedup_registry
                    (entity_type, normalized_key, hash_fingerprint, status, lead_id, domain, owner_username)
                VALUES (?, ?, ?, 'SCRAPED', ?, ?, ?)
            """, ("domain" if domain else "email", canon, fingerprint, lead_id, canon, owner))
        except sqlite3.OperationalError as oe:
            if "owner_username" in str(oe).lower():
                conn.execute("""
                    INSERT OR REPLACE INTO dedup_registry
                        (entity_type, normalized_key, hash_fingerprint, status, lead_id, domain)
                    VALUES (?, ?, ?, 'SCRAPED', ?, ?)
                """, ("domain" if domain else "email", canon, fingerprint, lead_id, canon))
            else:
                raise
        conn.commit()
        logger.debug(f"[DEDUP] Registered '{canon}' for owner='{owner}' (lead_id={lead_id})")
    except Exception as e:
        logger.debug(f"[DEDUP] register_domain_seen failed for '{canon}': {e}")


def register_domain_alias(canonical: str, alias: str, conn, owner_username: Optional[str] = None) -> None:
    """
    Groups a domain alias under a canonical key.
    Both are registered in dedup_registry so future lookups for either hit for this user.
    """
    for d in [canonical, alias]:
        if d:
            register_domain_seen(d, "", None, conn, owner_username=owner_username)
