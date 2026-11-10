"""
H.Huddair's Nexus-Pulse - Level 1
Deduplication Shield: Persistent Global Deduplication & Filtering Engine
Guarantees that previously scraped, verified, or contacted domains, emails,
and companies are never re-processed.
"""

import time
import re
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

from .db_engine import get_db_engine, compute_sha256
from core.models import Lead


def _normalize_domain(domain: str) -> str:
    clean = domain.strip().lower()
    clean = re.sub(r'^https?://', '', clean)
    clean = re.sub(r'^www\.', '', clean)
    return clean.split('/')[0].strip()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_company(name: str) -> str:
    clean = name.strip().lower()
    # Remove common corporate suffixes for matching
    clean = re.sub(r'\b(gmbh|ag|llc|inc|ltd|corp|sa|sarl|plc|co)\b\.?', '', clean)
    clean = re.sub(r'[^a-z0-9]', '', clean)
    return clean


class DeduplicationShield:
    """
    Enforces persistent global deduplication across domains, emails, and company entities.
    """

    def __init__(self):
        self.db = get_db_engine()

    def is_entity_duplicate(
        self,
        domain: str,
        email: str,
        company_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Checks if domain, email, or company has already been processed.
        Returns: (is_duplicate: bool, reason: str)
        """
        clean_domain = _normalize_domain(domain)
        clean_email = _normalize_email(email)

        with self.db.get_connection() as conn:
            # 1. Check Domain
            row = conn.execute(
                "SELECT status, last_processed_at FROM dedup_registry WHERE entity_type = 'domain' AND normalized_key = ?",
                (clean_domain,)
            ).fetchone()
            if row:
                return True, f"Domain '{clean_domain}' already processed (Status: {row['status']}, Date: {row['last_processed_at']})"

            # 2. Check Email
            row = conn.execute(
                "SELECT status, last_processed_at FROM dedup_registry WHERE entity_type = 'email' AND normalized_key = ?",
                (clean_email,)
            ).fetchone()
            if row:
                return True, f"Email '{clean_email}' already processed (Status: {row['status']}, Date: {row['last_processed_at']})"

            # 3. Check Company Name if provided
            if company_name and len(company_name.strip()) >= 3:
                clean_comp = _normalize_company(company_name)
                if len(clean_comp) >= 3:
                    row = conn.execute(
                        "SELECT status FROM dedup_registry WHERE entity_type = 'company' AND normalized_key = ?",
                        (clean_comp,)
                    ).fetchone()
                    if row:
                        return True, f"Company '{company_name}' already registered (Status: {row['status']})"

        return False, "NEW_ENTITY"

    def register_lead(self, lead: Lead, status: str = "VERIFIED") -> None:
        """
        Registers lead entities (domain, all emails, company) into dedup registry.
        """
        clean_domain = _normalize_domain(lead.domain or lead.website_url)
        clean_email = _normalize_email(lead.primary_email)
        clean_comp = _normalize_company(lead.company_name)
        lead_id = lead.id or compute_sha256(f"{clean_domain}:{clean_email}")

        entities = [
            ("domain", clean_domain, compute_sha256(clean_domain)),
            ("email", clean_email, compute_sha256(clean_email))
        ]

        # Register secondary emails as well to prevent cross-contact duplicates
        for sec_email in lead.all_emails:
            clean_sec = _normalize_email(sec_email.email)
            if clean_sec != clean_email:
                entities.append(("email", clean_sec, compute_sha256(clean_sec)))

        if len(clean_comp) >= 3:
            entities.append(("company", clean_comp, compute_sha256(clean_comp)))

        with self.db.get_connection() as conn:
            for entity_type, key, sha in entities:
                conn.execute("""
                    INSERT INTO dedup_registry (entity_type, normalized_key, hash_fingerprint, status, lead_id)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(normalized_key) DO UPDATE SET
                        last_processed_at = CURRENT_TIMESTAMP,
                        status = excluded.status,
                        lead_id = excluded.lead_id;
                """, (entity_type, key, sha, status, lead_id))
            conn.commit()

    def filter_new_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Filters a list of leads, returning only truly new, uncontacted entities.
        """
        fresh_leads: List[Lead] = []
        for lead in leads:
            is_dup, _ = self.is_entity_duplicate(
                domain=lead.domain,
                email=lead.primary_email,
                company_name=lead.company_name
            )
            if not is_dup:
                fresh_leads.append(lead)
        return fresh_leads

    def mark_as_contacted(self, email_or_domain: str) -> bool:
        """Flags an entity as CONTACTED in the global registry."""
        clean = email_or_domain.strip().lower()
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                UPDATE dedup_registry
                SET status = 'CONTACTED', last_processed_at = CURRENT_TIMESTAMP
                WHERE normalized_key = ? OR normalized_key = ?
            """, (clean, _normalize_domain(clean)))
            conn.commit()
            return cur.rowcount > 0

    def get_shield_stats(self) -> Dict[str, Any]:
        """Returns statistics on deduplication registry size and tracked entities."""
        with self.db.get_connection() as conn:
            total_domains = conn.execute("SELECT COUNT(*) FROM dedup_registry WHERE entity_type = 'domain'").fetchone()[0]
            total_emails = conn.execute("SELECT COUNT(*) FROM dedup_registry WHERE entity_type = 'email'").fetchone()[0]
            total_companies = conn.execute("SELECT COUNT(*) FROM dedup_registry WHERE entity_type = 'company'").fetchone()[0]
            contacted = conn.execute("SELECT COUNT(*) FROM dedup_registry WHERE status = 'CONTACTED'").fetchone()[0]

            return {
                "total_tracked_domains": total_domains,
                "total_tracked_emails": total_emails,
                "total_tracked_companies": total_companies,
                "entities_contacted": contacted,
                "total_dedup_records": total_domains + total_emails + total_companies
            }


_global_dedup_shield = None

def get_dedup_shield() -> DeduplicationShield:
    global _global_dedup_shield
    if _global_dedup_shield is None:
        _global_dedup_shield = DeduplicationShield()
    return _global_dedup_shield
