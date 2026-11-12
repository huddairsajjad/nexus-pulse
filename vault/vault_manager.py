"""
H.Huddair's Nexus-Pulse - Level 1
Category Vault & Asset Preservation Engine
Organizes verified leads into a partitioned folder hierarchy:
    Country -> Niche -> Quality Tag
Generates automatic synchronized multi-format exports:
    - Partition-level JSON, CSV, and Excel (.xlsx)
    - Global snapshot backups in vault/backups/
"""

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from core.models import Lead, HygieneReport
from security.crypto_vault import get_crypto_vault
from database.db_engine import get_db_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
VAULT_DIR = ROOT_DIR / "vault"
PARTITIONS_DIR = VAULT_DIR / "partitions"
BACKUPS_DIR = VAULT_DIR / "backups"


def _sanitize_path_segment(name: str) -> str:
    """Replaces spaces and illegal filesystem characters for path consistency."""
    clean = re.sub(r'[\\/*?:"<>|]', '_', name.strip())
    clean = re.sub(r'\s+', '_', clean)
    return clean or "UNKNOWN"


class CategoryVaultManager:
    """
    Enterprise Category Vault:
    Enforces hierarchical folder partitioning and multi-format asset preservation.
    """

    def __init__(self):
        PARTITIONS_DIR.mkdir(parents=True, exist_ok=True)
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        self.crypto = get_crypto_vault()
        self.db = get_db_engine()

    def get_partition_path(self, country: str, niche: str, quality_tag: str) -> Path:
        """
        Calculates and creates directory path for partition:
        vault/partitions/{Country}/{Niche}/{Quality_Tag}/
        """
        c_seg = _sanitize_path_segment(country)
        n_seg = _sanitize_path_segment(niche)
        q_seg = _sanitize_path_segment(quality_tag)

        partition_path = PARTITIONS_DIR / c_seg / n_seg / q_seg
        partition_path.mkdir(parents=True, exist_ok=True)
        return partition_path

    def _lead_to_flat_dict(self, lead: Lead) -> Dict[str, Any]:
        """Flattens a Lead object for CSV/Excel spreadsheet export."""
        hygiene_status = lead.hygiene_report.status.value if lead.hygiene_report else "UNCHECKED"
        smtp_diag = lead.hygiene_report.smtp_diagnostic_message if lead.hygiene_report else ""
        mx_records = ", ".join(lead.hygiene_report.mx_records) if lead.hygiene_report else ""

        all_emails_str = ", ".join(e.email for e in lead.all_emails)
        phones_str = ", ".join(lead.phone_numbers)

        cms_str = ", ".join(lead.tech_stack.cms)
        ui_str = ", ".join(lead.tech_stack.frontend_frameworks)
        crm_str = ", ".join(lead.tech_stack.crm_and_marketing)
        cdn_str = ", ".join(lead.tech_stack.web_server_and_cdn)

        return {
            "ID": lead.id or "",
            "Company Name": lead.company_name,
            "Primary Email": lead.primary_email,
            "Email Tier": lead.primary_email_tier.value,
            "Priority Score": lead.priority_score,
            "Quality Tag": lead.quality_tag,
            "Hygiene Status": hygiene_status,
            "Phone Numbers": phones_str,
            "Domain": lead.domain,
            "Website URL": lead.website_url,
            "Country": lead.target_country,
            "City": lead.target_city,
            "Industry Niche": lead.industry_niche,
            "All Emails Found": all_emails_str,
            "Tech CMS": cms_str,
            "Tech UI": ui_str,
            "Tech CRM": crm_str,
            "Tech Infra": cdn_str,
            "DNS MX Records": mx_records,
            "SMTP Diagnostic": smtp_diag,
            "Scraped At": lead.scraped_at
        }

    def store_lead(self, lead: Lead, operator_id: Optional[str] = None) -> Dict[str, str]:
        """
        Stores lead into encrypted SQLite vault and appends to partitioned files.
        Maintains tenant operator_id isolation.
        """
        lead_dict = lead.model_dump()
        lead_id = lead.id or f"{_sanitize_path_segment(lead.domain)}_{_sanitize_path_segment(lead.primary_email)}"
        lead.id = lead_id

        # 1. Encrypt and store in database
        encrypted_blob = self.crypto.encrypt_json(lead_dict)
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO vault_leads (
                    id, domain, primary_email, company_name, country,
                    city, niche, quality_tag, priority_score, encrypted_payload, operator_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    primary_email = excluded.primary_email,
                    quality_tag = excluded.quality_tag,
                    priority_score = excluded.priority_score,
                    encrypted_payload = excluded.encrypted_payload,
                    operator_id = COALESCE(excluded.operator_id, vault_leads.operator_id);
            """, (
                lead.id, lead.domain, lead.primary_email, lead.company_name,
                lead.target_country, lead.target_city, lead.industry_niche,
                lead.quality_tag, lead.priority_score, encrypted_blob, operator_id
            ))
            conn.commit()

        # 2. Append to Partition Folder
        part_dir = self.get_partition_path(
            country=lead.target_country,
            niche=lead.industry_niche,
            quality_tag=lead.quality_tag
        )

        json_file = part_dir / "leads.json"
        csv_file = part_dir / "leads.csv"
        xlsx_file = part_dir / "leads.xlsx"

        # Update partition JSON
        existing_leads: List[Dict[str, Any]] = []
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    existing_leads = json.load(f)
            except Exception:
                existing_leads = []

        # Deduplicate in partition json
        existing_leads = [l for l in existing_leads if l.get("primary_email") != lead.primary_email]
        existing_leads.append(lead_dict)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(existing_leads, f, indent=2, ensure_ascii=False)

        # Update partition CSV & Excel via DataFrame
        flat_records = [self._lead_to_flat_dict(Lead(**l)) for l in existing_leads]
        df = pd.DataFrame(flat_records)
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")

        try:
            df.to_excel(xlsx_file, index=False, engine="openpyxl")
        except Exception:
            pass

        return {
            "partition_dir": str(part_dir),
            "json_path": str(json_file),
            "csv_path": str(csv_file),
            "xlsx_path": str(xlsx_file)
        }

    def export_global_snapshot_backups(self, operator_id: Optional[str] = None) -> Dict[str, str]:
        """
        Creates timestamped consolidated snapshot backups of all verified leads
        across all categories inside vault/backups/ in JSON, CSV, and Excel formats.
        Supports filtering by operator_id.
        """
        # Fetch all leads from database and decrypt
        leads: List[Lead] = []
        with self.db.get_connection() as conn:
            if operator_id:
                rows = conn.execute("SELECT encrypted_payload FROM vault_leads WHERE operator_id = ? OR operator_id IS NULL ORDER BY priority_score DESC", (operator_id,)).fetchall()
            else:
                rows = conn.execute("SELECT encrypted_payload FROM vault_leads ORDER BY priority_score DESC").fetchall()
            for row in rows:
                try:
                    decrypted = self.crypto.decrypt_json(row["encrypted_payload"])
                    if decrypted:
                        leads.append(Lead(**decrypted))
                except Exception:
                    pass

        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_backup = BACKUPS_DIR / f"nexus_leads_backup_{timestamp}.json"
        csv_backup = BACKUPS_DIR / f"nexus_leads_backup_{timestamp}.csv"
        xlsx_backup = BACKUPS_DIR / f"nexus_leads_backup_{timestamp}.xlsx"

        # 1. JSON Backup
        leads_raw = [l.model_dump() for l in leads]
        with open(json_backup, "w", encoding="utf-8") as f:
            json.dump(leads_raw, f, indent=2, ensure_ascii=False)

        # 2. CSV & Excel Backups
        flat_list = [self._lead_to_flat_dict(l) for l in leads]
        if flat_list:
            df = pd.DataFrame(flat_list)
        else:
            df = pd.DataFrame(columns=[
                "ID", "Company Name", "Primary Email", "Email Tier", "Priority Score",
                "Quality Tag", "Hygiene Status", "Phone Numbers", "Domain", "Website URL",
                "Country", "City", "Industry Niche", "All Emails Found", "Tech CMS",
                "Tech UI", "Tech CRM", "Tech Infra", "DNS MX Records", "SMTP Diagnostic", "Scraped At"
            ])

        df.to_csv(csv_backup, index=False, encoding="utf-8-sig")

        try:
            df.to_excel(xlsx_backup, index=False, engine="openpyxl")
        except Exception:
            pass

        return {
            "total_leads_exported": str(len(leads)),
            "json_backup": str(json_backup),
            "csv_backup": str(csv_backup),
            "xlsx_backup": str(xlsx_backup),
            "timestamp": timestamp
        }

    def get_vault_statistics(self) -> Dict[str, Any]:
        """Computes partitioned lead counts, quality tag distribution, and backup status."""
        with self.db.get_connection() as conn:
            total_vault_leads = conn.execute("SELECT COUNT(*) FROM vault_leads").fetchone()[0]
            
            # Group by Country
            country_counts = {}
            for row in conn.execute("SELECT country, COUNT(*) as c FROM vault_leads GROUP BY country"):
                country_counts[row["country"]] = row["c"]

            # Group by Quality Tag
            tag_counts = {}
            for row in conn.execute("SELECT quality_tag, COUNT(*) as c FROM vault_leads GROUP BY quality_tag"):
                tag_counts[row["quality_tag"]] = row["c"]

            # Top Niche
            niche_counts = {}
            for row in conn.execute("SELECT niche, COUNT(*) as c FROM vault_leads GROUP BY niche"):
                niche_counts[row["niche"]] = row["c"]

        # Count backup files
        backups = list(BACKUPS_DIR.glob("nexus_leads_backup_*.*"))

        return {
            "total_verified_leads": total_vault_leads,
            "country_distribution": country_counts,
            "quality_tag_distribution": tag_counts,
            "niche_distribution": niche_counts,
            "backup_files_count": len(backups),
            "vault_root": str(VAULT_DIR)
        }

    def purge_partitions_and_backups(self) -> Dict[str, int]:
        """Scans and purges all partition folders and backups to ensure a zero-seed clean state."""
        import shutil
        cleaned_partitions = 0
        cleaned_backups = 0
        if PARTITIONS_DIR.exists():
            for item in PARTITIONS_DIR.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    cleaned_partitions += 1
        if BACKUPS_DIR.exists():
            for item in BACKUPS_DIR.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                        cleaned_backups += 1
                    except Exception:
                        pass
        return {"partitions_wiped": cleaned_partitions, "backups_wiped": cleaned_backups}


_global_vault_manager = None

def get_vault_manager() -> CategoryVaultManager:
    global _global_vault_manager
    if _global_vault_manager is None:
        _global_vault_manager = CategoryVaultManager()
    return _global_vault_manager
