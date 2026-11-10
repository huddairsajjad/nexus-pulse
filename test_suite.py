"""
H.Huddair's Nexus-Pulse - Level 1
Comprehensive Verification Test Suite
Validates all 7 Technical Requirements for Level 1.
"""

import os
import sys
import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import (
    generate_license_key,
    verify_license_key,
    load_or_initialize_license,
    UnauthorizedDeviceError,
    InvalidSignatureError
)
from security.crypto_vault import get_crypto_vault
from config.config_manager import get_config
from core.agents.localization_engine import LocalizationEngine
from core.agents.priority_finder import PriorityEmailFinder
from core.agents.scraper_agent import DeepScraperAgent, TechStackDetector
from database.deduplication_shield import get_dedup_shield
from database.db_engine import get_db_engine
from vault.vault_manager import get_vault_manager
from core.hygiene.zero_bounce_shield import get_hygiene_shield
from core.models import EmailTier, HygieneStatus, Lead, TechStack


class TestNexusPulseLevel1(unittest.TestCase):

    def setUp(self):
        self.root_dir = PROJECT_ROOT
        self.config = get_config()
        self.hygiene = get_hygiene_shield()
        self.dedup = get_dedup_shield()
        self.vault = get_vault_manager()
        self.crypto = get_crypto_vault()

    # -------------------------------------------------------------
    # REQUIREMENT 1: Dedicated Workspace Folder Structure
    # -------------------------------------------------------------
    def test_01_workspace_folder_setup(self):
        """Verifies root directory 'rabbi' and all required subdirectories exist."""
        self.assertTrue(self.root_dir.exists(), "Root folder Desktop/rabbi must exist")
        self.assertEqual(self.root_dir.name, "rabbi", "Root directory must be named 'rabbi'")

        expected_dirs = ["config", "database", "security", "core", "vault", "api"]
        for d in expected_dirs:
            sub = self.root_dir / d
            self.assertTrue(sub.exists() and sub.is_dir(), f"Subdirectory '{d}' must exist in Desktop/rabbi")

    # -------------------------------------------------------------
    # REQUIREMENT 2: Anti-Theft & Licensing Middleware
    # -------------------------------------------------------------
    def test_02_anti_theft_and_licensing(self):
        """Tests machine fingerprinting, cryptographic validation, and device locking."""
        fp = generate_machine_fingerprint()
        self.assertIn("machine_id", fp)
        self.assertTrue(fp["machine_id"].startswith("NEXUS-"), "Machine ID format must be NEXUS-XXXX-...")
        self.assertTrue(len(fp["machine_guid"]) > 0, "MachineGuid must be populated")

        # Test valid license generation and verification
        host_id = fp["machine_id"]
        valid_key = generate_license_key(machine_id=host_id, client_name="H.Huddair Enterprise")
        payload = verify_license_key(valid_key, host_id)
        self.assertEqual(payload["machine_id"], host_id)
        self.assertEqual(payload["tier"], "Level-1-Enterprise")

        # Test ANTI-THEFT: Execution must be blocked on unauthorized device
        rogue_host_id = "NEXUS-9999-8888-7777-6666"
        with self.assertRaises(UnauthorizedDeviceError):
            verify_license_key(valid_key, rogue_host_id)

        # Test Tampered Signature
        tampered_key = valid_key[:-6] + "dead00"
        with self.assertRaises(InvalidSignatureError):
            verify_license_key(tampered_key, host_id)

        # Test Encrypted Storage Standards
        test_payload = {"secret_lead": "estimating@enterprise.com", "valuation": 500000}
        encrypted = self.crypto.encrypt_json(test_payload)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, json.dumps(test_payload))
        decrypted = self.crypto.decrypt_json(encrypted)
        self.assertEqual(decrypted["secret_lead"], test_payload["secret_lead"])

    # -------------------------------------------------------------
    # REQUIREMENT 3: Dynamic Config Engine & Localization
    # -------------------------------------------------------------
    def test_03_dynamic_config_and_localization(self):
        """Tests JSON/YAML dynamic config and native search query localization."""
        # Config test
        self.config.set("target_country", "Germany")
        self.config.set("target_city", "Berlin")
        self.assertEqual(self.config.target_country, "Germany")
        self.assertEqual(self.config.target_city, "Berlin")

        # Verify files exist and match
        yaml_path = self.root_dir / "config" / "settings.yaml"
        json_path = self.root_dir / "config" / "settings.json"
        self.assertTrue(yaml_path.exists())
        self.assertTrue(json_path.exists())

        # Test Localization Engine for Non-English target regions
        loc = LocalizationEngine()
        # German
        de_queries = loc.generate_localized_queries("Germany", "Berlin", "Commercial Construction")
        self.assertTrue(any("Ausschreibungen" in q["query"] or "Kalkulation" in q["query"] for q in de_queries))
        self.assertTrue(any(".de" in q["query"] for q in de_queries))

        # Russian
        ru_queries = loc.generate_localized_queries("Russia", "Moscow", "General Contractors")
        self.assertTrue(any("Тендерный отдел" in q["query"] or "Сметный отдел" in q["query"] for q in ru_queries))
        self.assertTrue(any(".ru" in q["query"] for q in ru_queries))

        # French
        fr_queries = loc.generate_localized_queries("France", "Paris", "Commercial Construction")
        self.assertTrue(any("Appels d'offres" in q["query"] or "chiffrage" in q["query"] for q in fr_queries))
        self.assertTrue(any(".fr" in q["query"] for q in fr_queries))

    # -------------------------------------------------------------
    # REQUIREMENT 4: Deep Scraper & Priority Finder
    # -------------------------------------------------------------
    def test_04_scraper_and_priority_finder(self):
        """Tests prioritization of high-value direct emails over generic info@ and tech stack."""
        raw_emails = [
            "info@contractor.com",
            "estimating@contractor.com",
            "hello@contractor.com",
            "director@contractor.com",
            "qs@contractor.com"
        ]

        ranked = PriorityEmailFinder.rank_emails(raw_emails)
        primary = PriorityEmailFinder.pick_primary_email(ranked)

        # Primary MUST be estimating@ or qs@ (Tier 1), NEVER info@
        self.assertIn(primary.prefix, ["estimating", "qs"])
        self.assertEqual(primary.tier, EmailTier.TIER_1_ESTIMATING)
        self.assertEqual(primary.priority_score, 100)

        # info@ must be lowest priority
        info_email = next(e for e in ranked if e.prefix == "info")
        self.assertEqual(info_email.tier, EmailTier.TIER_GENERIC)
        self.assertEqual(info_email.priority_score, 20)

        # Test Tech-Stack Detection
        sample_html = """
        <html><head>
        <meta name="generator" content="WordPress 6.4" />
        <script src="/_next/static/test.js"></script>
        <script src="https://js.hs-scripts.com/123.js"></script>
        </head><body><div class="border-t-transparent">Hello</div></body></html>
        """
        stack = TechStackDetector.detect(sample_html)
        self.assertIn("WordPress", stack.cms)
        self.assertIn("Next.js", stack.frontend_frameworks)
        self.assertIn("HubSpot", stack.crm_and_marketing)
        self.assertIn("Tailwind CSS", stack.frontend_frameworks)

    # -------------------------------------------------------------
    # REQUIREMENT 5: Deduplication Shield
    # -------------------------------------------------------------
    def test_05_deduplication_shield(self):
        """Tests persistent global SQLite deduplication check."""
        import uuid
        unique_token = uuid.uuid4().hex[:8]
        test_domain = f"unique-test-{unique_token}.com"
        test_email = f"bids@unique-test-{unique_token}.com"
        test_company = f"Unique Corp {unique_token}"

        # Initially should not be duplicate
        is_dup, _ = self.dedup.is_entity_duplicate(test_domain, test_email, test_company)
        self.assertFalse(is_dup)

        # Register lead
        mock_lead = Lead(
            company_name=test_company,
            domain=test_domain,
            website_url=f"https://{test_domain}",
            target_country="Germany",
            target_city="Berlin",
            industry_niche="Commercial Construction",
            primary_email=test_email,
            primary_email_tier=EmailTier.TIER_1_ESTIMATING,
            priority_score=100
        )
        self.dedup.register_lead(mock_lead, status="VERIFIED")

        # Second check MUST be flagged as duplicate
        is_dup_again, reason = self.dedup.is_entity_duplicate(test_domain, test_email, test_company)
        self.assertTrue(is_dup_again)
        self.assertIn("already processed", reason)

    # -------------------------------------------------------------
    # REQUIREMENT 6: Category Vault & Local Backup
    # -------------------------------------------------------------
    def test_06_category_vault_and_backups(self):
        """Tests partitioned storage (Country -> Niche -> Quality Tag) and JSON/CSV/Excel exports."""
        mock_lead = Lead(
            company_name="Vault Test Hochbau GmbH",
            domain="vault-test-hochbau.de",
            website_url="https://vault-test-hochbau.de",
            target_country="Germany",
            target_city="Berlin",
            industry_niche="Hochbau",
            primary_email="kalkulation@vault-test-hochbau.de",
            primary_email_tier=EmailTier.TIER_1_ESTIMATING,
            priority_score=100,
            quality_tag="TIER-1-ESTIMATING",
            tech_stack=TechStack(cms=["WordPress"], frontend_frameworks=["Tailwind CSS"])
        )

        store_res = self.vault.store_lead(mock_lead)
        self.assertTrue(Path(store_res["json_path"]).exists())
        self.assertTrue(Path(store_res["csv_path"]).exists())
        self.assertTrue(Path(store_res["xlsx_path"]).exists())

        # Test Global Multi-Format Snapshot Export
        backup_res = self.vault.export_global_snapshot_backups()
        self.assertTrue(Path(backup_res["json_backup"]).exists())
        self.assertTrue(Path(backup_res["csv_backup"]).exists())
        self.assertTrue(Path(backup_res["xlsx_backup"]).exists())

    # -------------------------------------------------------------
    # REQUIREMENT 7: Zero-Bounce 3-Stage Hygiene Shield
    # -------------------------------------------------------------
    def test_07_zero_bounce_hygiene_shield(self):
        """Tests Syntax check, Disposable email rejection, and DNS MX resolution."""
        # Stage 1: Syntax & Disposable provider filtering
        s1_ok, disp, _ = self.hygiene.verify_stage_1_syntax("invalid-no-at-symbol")
        self.assertFalse(s1_ok)

        s1_ok, is_disposable, _ = self.hygiene.verify_stage_1_syntax("user@mailinator.com")
        self.assertTrue(s1_ok)
        self.assertTrue(is_disposable, "mailinator.com must be caught as disposable")

        # Stage 2: DNS MX Resolution on valid domain
        mx_ok, mx_hosts, _ = self.hygiene.verify_stage_2_mx("gmail.com")
        self.assertTrue(mx_ok)
        self.assertTrue(len(mx_hosts) > 0)

        # Stage 2: Non-existent domain (NXDOMAIN)
        mx_fail, _, _ = self.hygiene.verify_stage_2_mx("nxdomain-nonexistent-dead-domain-999.xyz")
        self.assertFalse(mx_fail)

        # Full Lead Validation on disposable email
        report = self.hygiene.validate_lead_email("spammer@10minutemail.com")
        self.assertEqual(report.status, HygieneStatus.SYNTAX_INVALID)
        self.assertTrue(report.is_disposable_domain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
