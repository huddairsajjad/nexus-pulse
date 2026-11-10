"""
H.Huddair's Nexus-Pulse - Level 1
Pipeline Orchestrator: Autonomous Multi-Agent B2B Lead Engine Core
Chains Anti-Theft Licensing -> Dynamic Config -> Native Localization
-> Deep Scraper & Priority Finder -> Deduplication Shield
-> Zero-Bounce Hygiene Shield -> Category Vault & Local Backup
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import enforce_security_boundary
from config.config_manager import get_config
from core.agents.localization_engine import LocalizationEngine
from core.agents.scraper_agent import DeepScraperAgent
from core.agents.priority_finder import PriorityEmailFinder
from core.hygiene.zero_bounce_shield import get_hygiene_shield
from database.deduplication_shield import get_dedup_shield
from vault.vault_manager import get_vault_manager
from core.models import Lead, HygieneStatus, EmailTier


class NexusPulseOrchestrator:
    """
    Central Coordinator for Level 1 Autonomous Lead Operations.
    """

    def __init__(self, bypass_license_check: bool = False):
        self.config = get_config()
        self.mf = generate_machine_fingerprint()
        self.machine_id = self.mf["machine_id"]

        # 1. Anti-Theft Licensing Enforcement
        if not bypass_license_check:
            self.license_info = enforce_security_boundary(self.machine_id)
        else:
            self.license_info = {"status": "BYPASS_TEST"}

        # Initialize Subsystems
        self.localization = LocalizationEngine()
        self.scraper = DeepScraperAgent(timeout_seconds=float(self.config.get("crawler.request_timeout_seconds", 12.0)))
        self.hygiene = get_hygiene_shield()
        self.dedup = get_dedup_shield()
        self.vault = get_vault_manager()

    def get_system_status(self) -> Dict[str, Any]:
        """Provides holistic telemetry on system state, security, and storage."""
        vault_stats = self.vault.get_vault_statistics()
        dedup_stats = self.dedup.get_shield_stats()
        cfg = self.config.as_dict()

        return {
            "status": "OPERATIONAL",
            "tier": "Level-1-Enterprise",
            "machine_id": self.machine_id,
            "license": {
                "active": True,
                "client": self.license_info.get("client_name", "Authorized"),
                "tier": self.license_info.get("tier", "Enterprise")
            },
            "active_target": {
                "country": self.config.target_country,
                "city": self.config.target_city,
                "niche": self.config.industry_niche,
                "ready_to_send": self.config.ready_to_send
            },
            "vault_metrics": vault_stats,
            "dedup_metrics": dedup_stats
        }

    def process_and_preserve_lead(self, raw_lead: Lead) -> Dict[str, Any]:
        """
        Takes a raw scraped Lead, applies Deduplication Shield,
        runs Zero-Bounce Hygiene Shield, and archives to Category Vault.
        """
        # 1. Deduplication Shield Check
        is_dup, dup_reason = self.dedup.is_entity_duplicate(
            domain=raw_lead.domain,
            email=raw_lead.primary_email,
            company_name=raw_lead.company_name
        )

        if is_dup:
            return {
                "success": False,
                "reason": "DEDUPLICATION_BLOCKED",
                "details": dup_reason,
                "lead_domain": raw_lead.domain,
                "primary_email": raw_lead.primary_email
            }

        # 2. Zero-Bounce 3-Stage Hygiene Shield
        hygiene_report = self.hygiene.validate_lead_email(raw_lead.primary_email)
        raw_lead.hygiene_report = hygiene_report

        # If primary email fails syntax or has no MX, try secondary emails from scrapelist
        if hygiene_report.status in (HygieneStatus.SYNTAX_INVALID, HygieneStatus.DOMAIN_NO_MX, HygieneStatus.SMTP_REJECTED):
            fallback_found = False
            for sec_candidate in raw_lead.all_emails[1:]:
                alt_report = self.hygiene.validate_lead_email(sec_candidate.email)
                if alt_report.status in (HygieneStatus.VERIFIED, HygieneStatus.SMTP_INDETERMINATE):
                    raw_lead.primary_email = sec_candidate.email
                    raw_lead.primary_email_tier = sec_candidate.tier
                    raw_lead.priority_score = sec_candidate.priority_score
                    raw_lead.hygiene_report = alt_report
                    fallback_found = True
                    break

            if not fallback_found:
                return {
                    "success": False,
                    "reason": "HYGIENE_FAILED",
                    "status": hygiene_report.status.value,
                    "diagnostic": hygiene_report.smtp_diagnostic_message,
                    "lead_domain": raw_lead.domain
                }

        # 3. Register in Deduplication Shield
        self.dedup.register_lead(raw_lead, status="VERIFIED")

        # 4. Store in Category Vault & Synchronize Partitions (JSON, CSV, Excel)
        store_res = self.vault.store_lead(raw_lead)

        return {
            "success": True,
            "lead_id": raw_lead.id,
            "company_name": raw_lead.company_name,
            "primary_email": raw_lead.primary_email,
            "email_tier": raw_lead.primary_email_tier.value,
            "priority_score": raw_lead.priority_score,
            "quality_tag": raw_lead.quality_tag,
            "hygiene_status": raw_lead.hygiene_report.status.value if raw_lead.hygiene_report else "UNRATED",
            "tech_stack": raw_lead.tech_stack.raw_technologies,
            "partition_dir": store_res["partition_dir"],
            "json_path": store_res["json_path"],
            "csv_path": store_res["csv_path"],
            "xlsx_path": store_res["xlsx_path"]
        }

    def execute_targeted_pipeline(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        niche: Optional[str] = None,
        sample_targets: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Executes a targeted search and processing run using localized queries.
        """
        c_country = country or self.config.target_country
        c_city = city or self.config.target_city
        c_niche = niche or self.config.industry_niche

        # Generate localized native queries
        queries = self.localization.generate_localized_queries(c_country, c_city, c_niche)

        processed_leads: List[Dict[str, Any]] = []
        rejected_leads: List[Dict[str, Any]] = []

        # If sample target HTML/domains provided, process them
        if sample_targets:
            for item in sample_targets:
                if "html" in item:
                    lead = self.scraper.parse_html_content(
                        html_content=item["html"],
                        source_url=item.get("url", f"https://{item.get('domain', 'target.de')}"),
                        country=c_country,
                        city=c_city,
                        niche=c_niche
                    )
                else:
                    lead = None

                if lead:
                    result = self.process_and_preserve_lead(lead)
                    if result["success"]:
                        processed_leads.append(result)
                    else:
                        rejected_leads.append(result)

        # Trigger consolidated multi-format backup export
        backup_res = self.vault.export_global_snapshot_backups()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": {"country": c_country, "city": c_city, "niche": c_niche},
            "localized_queries": queries,
            "leads_preserved_count": len(processed_leads),
            "leads_rejected_count": len(rejected_leads),
            "processed_leads": processed_leads,
            "rejected_leads": rejected_leads,
            "backup_exports": backup_res
        }
