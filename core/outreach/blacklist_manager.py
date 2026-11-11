"""
Nexus-Pulse Enterprise Build
Outreach Engine: Global Domain Blacklist Manager
Defines and enforces exclusion rules (*.gov, *.edu, competitor domains, etc.)
Auto-filters blacklisted targets during the Hunt & Verify phase and scraper parsing.
"""

import fnmatch
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from database.db_engine import get_db_engine


class BlacklistManager:
    """
    Manages global domain and email exclusion patterns.
    Enforces automatic exclusion across all operators during discovery and outreach.
    """

    def __init__(self):
        self.db = get_db_engine()

    def get_rules(self) -> List[Dict[str, Any]]:
        """Returns all registered blacklist patterns."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, pattern, entity_type, reason, created_by, created_at
                FROM blacklist_rules
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def add_rule(self, pattern: str, reason: str = "Excluded Domain", created_by: str = "admin") -> Dict[str, Any]:
        """Registers a new blacklist rule pattern."""
        clean_pat = pattern.strip().lower()
        if not clean_pat:
            raise ValueError("Pattern is required.")

        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id FROM blacklist_rules WHERE lower(pattern) = ?", (clean_pat,)).fetchone()
            if existing:
                raise ValueError(f"Blacklist pattern '{clean_pat}' already exists.")

            conn.execute("""
                INSERT INTO blacklist_rules (pattern, entity_type, reason, created_by)
                VALUES (?, 'domain', ?, ?)
            """, (clean_pat, reason.strip() or "Excluded Pattern", created_by))
            conn.commit()
            last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        return {
            "id": last_id,
            "pattern": clean_pat,
            "reason": reason,
            "created_by": created_by
        }

    def remove_rule(self, rule_id: int) -> bool:
        """Removes a blacklist rule."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT id FROM blacklist_rules WHERE id = ?", (rule_id,)).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM blacklist_rules WHERE id = ?", (rule_id,))
            conn.commit()
            return True

    def is_domain_blacklisted(self, domain_or_email: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether a domain or email matches any registered blacklist rule.
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

        with self.db.get_connection() as conn:
            rules = conn.execute("SELECT pattern, reason FROM blacklist_rules").fetchall()

            for rule in rules:
                pat = rule["pattern"].lower()
                reason = rule["reason"]

                # Exact match
                if pat == domain:
                    return True, f"Matched blacklist rule: {pat} ({reason})"

                # Subdomain match (e.g. pat='competitor.com' matches 'sub.competitor.com')
                if domain.endswith(f".{pat}"):
                    return True, f"Subdomain of blacklisted entity: {pat} ({reason})"

                # Wildcard matching (e.g. '*.gov', '*.mil', '*bank*')
                if "*" in pat:
                    if fnmatch.fnmatch(domain, pat):
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
