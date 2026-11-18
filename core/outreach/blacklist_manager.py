"""
Nexus-Pulse Enterprise Build
Outreach Engine: Global Domain Blacklist Manager
Defines and enforces exclusion rules (*.gov, *.edu, competitor domains, etc.)
Auto-filters blacklisted targets during the Hunt & Verify phase and scraper parsing.
"""

import fnmatch
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from database.db_engine import get_db_engine

logger = logging.getLogger("NexusPulse.Blacklist")

# Standard public / free email service providers
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "ymail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "zoho.com",
    "yandex.com",
    "mail.com",
    "gmx.com",
    "gmx.de",
    "web.de",
    "t-online.de",
}


def is_public_email_domain(domain_or_email: str) -> bool:
    """Returns True if the domain or email belongs to a public/free webmail provider."""
    if not domain_or_email:
        return False
    clean = str(domain_or_email).strip().lower()
    if "@" in clean:
        clean = clean.split("@")[-1]
    return clean in PUBLIC_EMAIL_DOMAINS


class BlacklistManager:
    """
    Manages global domain and email exclusion patterns.
    Enforces automatic exclusion across all operators during discovery and outreach.
    """

    def __init__(self):
        self.db = get_db_engine()

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Returns all registered blacklist patterns synchronized with lead-level
        and unsubscribe suppression records.
        """
        rules_out: List[Dict[str, Any]] = []
        seen_patterns = set()

        with self.db.get_connection() as conn:
            # 1. Fetch manual & hook blacklist rules
            rows = conn.execute("""
                SELECT id, pattern, entity_type, reason, created_by, created_at
                FROM blacklist_rules
                ORDER BY created_at DESC
            """).fetchall()
            for r in rows:
                p_lower = (r["pattern"] or "").lower()
                seen_patterns.add(p_lower)
                rules_out.append({
                    "id": r["id"],
                    "pattern": r["pattern"],
                    "entity_type": r["entity_type"] or ("email" if "@" in p_lower else "domain"),
                    "reason": r["reason"],
                    "created_by": r["created_by"],
                    "created_at": r["created_at"],
                    "source": "blacklist_rule"
                })

            # 2. Fetch active unsubscribe & bounce suppression records
            sup_rows = conn.execute("""
                SELECT id, entity, entity_type, reason, operator_id, suppressed_at
                FROM suppressed_entities
                ORDER BY suppressed_at DESC
            """).fetchall()
            for s in sup_rows:
                ent = (s["entity"] or "").lower()
                if ent and ent not in seen_patterns:
                    seen_patterns.add(ent)
                    rules_out.append({
                        "id": f"sup_{s['id']}",
                        "pattern": s["entity"],
                        "entity_type": s["entity_type"] or ("email" if "@" in ent else "domain"),
                        "reason": s["reason"] or "Suppressed Entity",
                        "created_by": s["operator_id"] or "SUPPRESSION_LIST",
                        "created_at": s["suppressed_at"],
                        "source": "suppressed_entities"
                    })

        return rules_out

    def add_rule(self, pattern: str, reason: str = "Excluded Domain", created_by: str = "admin", entity_type: str = "domain") -> Dict[str, Any]:
        """Registers a new blacklist rule pattern."""
        clean_pat = pattern.strip().lower()
        if not clean_pat:
            raise ValueError("Pattern is required.")

        # Guard against blacklisting root public email provider domains (e.g. gmail.com)
        if (entity_type == "domain" or "@" not in clean_pat) and clean_pat in PUBLIC_EMAIL_DOMAINS:
            raise ValueError(
                f"Cannot blacklist root public email provider domain '{clean_pat}'. "
                f"To suppress specific recipients, add the full exact email address."
            )

        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id FROM blacklist_rules WHERE lower(pattern) = ?", (clean_pat,)).fetchone()
            if existing:
                raise ValueError(f"Blacklist pattern '{clean_pat}' already exists.")

            conn.execute("""
                INSERT INTO blacklist_rules (pattern, entity_type, reason, created_by)
                VALUES (?, ?, ?, ?)
            """, (clean_pat, entity_type, reason.strip() or "Excluded Pattern", created_by))
            conn.commit()
            last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        return {
            "id": last_id,
            "pattern": clean_pat,
            "entity_type": entity_type,
            "reason": reason,
            "created_by": created_by
        }

    def remove_rule(self, rule_id: Union[int, str]) -> bool:
        """Removes a blacklist rule or suppression record."""
        rule_str = str(rule_id).strip()
        with self.db.get_connection() as conn:
            if rule_str.startswith("sup_"):
                # Suppression table ID
                try:
                    sup_id = int(rule_str.replace("sup_", ""))
                    row = conn.execute("SELECT id, entity FROM suppressed_entities WHERE id = ?", (sup_id,)).fetchone()
                    if row:
                        ent = row["entity"]
                        conn.execute("DELETE FROM suppressed_entities WHERE id = ?", (sup_id,))
                        # Also unsuppress in outreach_queue and vault_leads
                        conn.execute("UPDATE outreach_queue SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL WHERE lower(recipient) = lower(?)", (ent,))
                        conn.execute("UPDATE vault_leads SET unsubscribed = 0 WHERE lower(primary_email) = lower(?)", (ent,))
                        conn.commit()
                        return True
                except Exception as e:
                    logger.warning(f"Error removing suppressed entity {rule_id}: {e}")
                return False

            # Try numeric ID in blacklist_rules
            try:
                numeric_id = int(rule_str)
                row = conn.execute("SELECT id, pattern FROM blacklist_rules WHERE id = ?", (numeric_id,)).fetchone()
                if row:
                    pat = row["pattern"]
                    conn.execute("DELETE FROM blacklist_rules WHERE id = ?", (numeric_id,))
                    # Also unblock any leads matching this exact pattern
                    conn.execute("UPDATE outreach_queue SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL WHERE lower(recipient) = lower(?)", (pat,))
                    conn.execute("UPDATE vault_leads SET unsubscribed = 0 WHERE lower(primary_email) = lower(?)", (pat,))
                    conn.commit()
                    return True
            except ValueError:
                pass

            # Fallback: check if rule_id matches string pattern in either table
            conn.execute("DELETE FROM blacklist_rules WHERE lower(pattern) = lower(?)", (rule_str,))
            conn.execute("DELETE FROM suppressed_entities WHERE lower(entity) = lower(?)", (rule_str,))
            conn.execute("UPDATE outreach_queue SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL WHERE lower(recipient) = lower(?)", (rule_str,))
            conn.execute("UPDATE vault_leads SET unsubscribed = 0 WHERE lower(primary_email) = lower(?)", (rule_str,))
            conn.commit()
            return True

    def unblock_entity(self, entity_or_email: str) -> bool:
        """
        Completely clears suppression and blacklist status for a given email or domain,
        restoring affected outreach queue leads to PENDING_APPROVAL.
        """
        if not entity_or_email:
            return False
        clean = entity_or_email.strip().lower()
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM blacklist_rules WHERE lower(pattern) = ?", (clean,))
            conn.execute("DELETE FROM suppressed_entities WHERE lower(entity) = ?", (clean,))
            conn.execute("""
                UPDATE outreach_queue
                SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL
                WHERE lower(recipient) = ?
            """, (clean,))
            conn.execute("UPDATE vault_leads SET unsubscribed = 0 WHERE lower(primary_email) = ?", (clean,))
            conn.commit()

        try:
            from database.mongo_engine import get_mongo_engine
            mongo = get_mongo_engine()
            if mongo and mongo.db is not None:
                mongo.db.leads.update_many(
                    {"primary_email": clean},
                    {"$set": {"unsubscribed": False, "unsubscribed_at": None}}
                )
        except Exception:
            pass

        return True

    def is_domain_blacklisted(self, domain_or_email: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether a domain or email matches any registered blacklist rule.
        Rules:
          1. Exact full-string match (e.g. stored email 'optout@example.co.uk')
          2. For public webmail providers (gmail.com, yahoo.com, etc.), ONLY match exact email or wildcard on email.
             NEVER block all users on a public root domain!
          3. For custom corporate domains:
             - Domain-part exact match
             - Subdomain match
             - Wildcard fnmatch patterns
             - Dot-prefix suffix match
        Returns: (is_blacklisted: bool, matching_rule_or_reason: str)
        """
        if not domain_or_email:
            return False, None

        clean = domain_or_email.strip().lower()
        # Extract domain if full email provided
        if "@" in clean:
            domain = clean.split("@")[-1]
        else:
            domain = clean

        is_pub = is_public_email_domain(domain)

        with self.db.get_connection() as conn:
            rules = conn.execute("SELECT pattern, reason FROM blacklist_rules").fetchall()

            for rule in rules:
                pat = rule["pattern"].lower()
                reason = rule["reason"]

                # 1. Exact full-string match (e.g. stored email 'optout@gmail.com')
                if pat == clean:
                    return True, f"Matched blacklist rule (exact): {pat} ({reason})"

                # 2. If pattern itself is a public root domain and clean is an email on that domain,
                # NEVER block all users of that public provider!
                if pat in PUBLIC_EMAIL_DOMAINS and clean != pat:
                    continue

                # 3. For public webmail providers, skip all domain-level checks
                if is_pub:
                    # Allow explicit wildcard matching on the full email address only (e.g. *spammer*@gmail.com)
                    if "*" in pat and fnmatch.fnmatch(clean, pat):
                        return True, f"Matched wildcard pattern: {pat} ({reason})"
                    continue

                # 4. Custom domain matching:
                # Exact domain match
                if pat == domain:
                    return True, f"Matched blacklist rule: {pat} ({reason})"

                # Subdomain match (e.g. pat='competitor.com' matches 'sub.competitor.com')
                if domain.endswith(f".{pat}"):
                    return True, f"Subdomain of blacklisted entity: {pat} ({reason})"

                # Wildcard matching (e.g. '*.gov', '*.mil', '*bank*')
                if "*" in pat:
                    if fnmatch.fnmatch(domain, pat):
                        return True, f"Matched wildcard pattern: {pat} ({reason})"
                    if fnmatch.fnmatch(clean, pat):
                        return True, f"Matched wildcard pattern: {pat} ({reason})"
                    # Also match if pattern is *.gov and domain is something.gov
                    if pat.startswith("*.") and domain.endswith(pat[1:]):
                        return True, f"Matched wildcard pattern: {pat} ({reason})"

                # Dot prefix check (e.g. '.gov')
                if pat.startswith(".") and domain.endswith(pat):
                    return True, f"Matched domain suffix: {pat} ({reason})"

        return False, None


_global_blacklist_manager = None

def get_blacklist_manager() -> BlacklistManager:
    global _global_blacklist_manager
    if _global_blacklist_manager is None:
        _global_blacklist_manager = BlacklistManager()
    return _global_blacklist_manager
