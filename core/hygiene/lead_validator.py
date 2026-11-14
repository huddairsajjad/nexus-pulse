"""
H.Huddair's Nexus-Pulse Enterprise Build
Lead Validation & Sanitization Filter (4-Layer Scraper Pipeline Guard)

Layer 1: Regex & HTML Entity Sanitization & Truncated Local-Part Blocker
Layer 2: Role-Based, Gov/Edu/Mil & System Tracker Blocker
Layer 3: Junk Title, Bot-Shield & Generic Navigation Brand Extractor
Layer 4: Niche Relevance Scoring (0-100) & Auto-Template / Mailbox Mapper
Deduplication Guard: Database existence verification across Pipeline, Sent history & Blacklist
"""

import html
import logging
import re
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("nexus.lead_validator")

# Layer 1: Truncated or mangled local-parts from scraper regex clipping
TRUNCATED_LOCAL_PARTS = {
    "upport", "nfo", "ontact", "ales", "ello", "dmin", "stimate", "stimating",
    "kalkulation", "ress", "areers", "ervice", "eam", "ffice", "illing",
    "nquiries", "nquiry", "billing", "eneral", "ommercial", "rocurement"
}

# Layer 2: Role-based addresses to auto-reject
ROLE_BASED_PREFIXES = (
    "careers", "press", "investorrelations", "no-reply", "noreply",
    "admin", "encompassadmin", "bug-reporting", "sentry"
)

# Layer 2: Suffixes and system / tracker domains
RESTRICTED_GOV_EDU_TLDS = (".gov", ".edu", ".mil")
SYSTEM_TRACKER_DOMAINS = {"wixpress.com", "lexisnexis.com", "m-w.com", "f6s.com"}

# Layer 3: Junk and bot-shield page title phrases (case-insensitive)
BOT_SHIELD_TITLES = [
    "checking your browser",
    "attention required",
    "access denied",
    "security check",
    "cloudflare",
    "robot or human",
    "just a moment",
    "ddos protection",
    "ray id",
    "404",
    "not found",
    "page not found",
    "get help with",
    "new & used"
]

# Generic navigation titles that should trigger brand name extraction from domain
GENERIC_NAV_TITLES = {
    "contact us", "contact", "about us", "about", "home", "homepage",
    "impressum", "kontakt", "ueber uns", "uber uns", "main page", "welcome", "index"
}

# Common commercial compound keywords for domain brand extraction
KNOWN_DOMAIN_COMPOUNDS = [
    "construction", "contractor", "contracting", "building", "builders",
    "fitness", "equipment", "barbells", "weights", "strength",
    "software", "technologies", "technology", "solutions", "systems", "saas",
    "consulting", "services", "digital", "capital", "holdings", "partners",
    "global", "industries", "works", "studio", "health", "care", "supply",
    "direct", "dynamics", "energy", "logistics", "group", "labs", "tech"
]

# Layer 4: Niche keyword weight profiles
NICHE_KEYWORD_PROFILES = {
    "Enterprise SaaS": {
        "primary": [
            "saas", "software", "cloud platform", "b2b software", "api",
            "workflow automation", "crm", "erp", "devops", "ai platform",
            "multi-tenant", "soc2", "enterprise ready", "subscription",
            "cloud solutions", "developer platform", "automation platform"
        ],
        "secondary": [
            "enterprise", "platform", "cloud", "analytics", "integration",
            "dashboard", "security", "infrastructure", "developer", "automation",
            "scalable", "data", "solution", "solutions", "app", "application",
            "database", "ai", "machine learning", "b2b", "reporting", "integrations"
        ]
    },
    "Commercial Construction": {
        "primary": [
            "commercial construction", "general contractor", "commercial building",
            "estimating", "tenders", "subcontractor", "preconstruction", "takeoffs",
            "boq", "bill of quantities", "bauunternehmen", "hochbau", "gewerbebau",
            "procurement", "commercial contracting", "tender package", "bidding"
        ],
        "secondary": [
            "construction", "contractor", "commercial", "building", "renovation",
            "infrastructure", "architectural", "engineering", "concrete", "steel",
            "drywall", "hvac", "roofing", "electrical", "mechanical", "project management",
            "contractors", "buildings", "development", "facilities", "site work"
        ]
    },
    "Gym Equipment": {
        "primary": [
            "gym equipment", "fitness equipment", "commercial gym", "strength training",
            "barbell", "dumbbell", "treadmill", "power rack", "weight plates",
            "workout machines", "fitness center", "strength equipment", "free weights",
            "commercial fitness", "cardio equipment", "plate loaded"
        ],
        "secondary": [
            "gym", "fitness", "exercise", "workout", "strength", "cardio",
            "weights", "training", "athletic", "bench", "crossfit", "plates",
            "lifting", "rigs", "dumbbells", "barbells", "benches", "kettlebells",
            "selectorized", "facility", "gyms", "athletes", "gymnasium"
        ]
    }
}


class LeadValidationFilter:
    """
    Production-grade 4-layer lead sanitization, validation, and relevance filter.
    Guarantees low-quality, malformed, system, or irrelevant leads never enter the Approval Gate.
    """

    # -------------------------------------------------------------------------
    # LAYER 1: Regex & Entity Sanitization + Truncated Local-Part Blocker
    # -------------------------------------------------------------------------
    @classmethod
    def sanitize_and_validate_email(
        cls,
        raw_email: str,
        domain_context: Optional[str] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Strips HTML entities (e.g. \u003e, >, %20, whitespace) from scraped emails before validation.
        Rejects malformed, clipped, or truncated local-parts (e.g. upport@ instead of support@).
        Returns: (is_valid: bool, sanitized_email: Optional[str], reason: str)
        """
        if not raw_email or not isinstance(raw_email, str):
            return False, None, "Empty or invalid email string"

        # 1. Unescape HTML entities & decode URL encodings
        cleaned = html.unescape(raw_email)
        cleaned = urllib.parse.unquote(cleaned)

        # 2. Strip Unicode entity fragments, HTML brackets, quotes, whitespace
        cleaned = cleaned.replace("\\u003e", "").replace("\\u003c", "")
        cleaned = re.sub(r'[\u003e\u003c<>&\'";,\(\)\{\}\[\]\t\r\n\s]', '', cleaned).strip()

        # 3. Match valid email format
        email_match = re.search(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', cleaned)
        if not email_match:
            return False, None, f"Failed regex email extraction on '{cleaned}'"

        local_part = email_match.group(1).lower().strip()
        domain_part = email_match.group(2).lower().strip()
        sanitized = f"{local_part}@{domain_part}"

        # 4. Check for truncated local-part (e.g. 'upport' instead of 'support')
        if local_part in TRUNCATED_LOCAL_PARTS:
            return False, None, f"Rejected truncated/clipped local-part: '{local_part}@'"

        # 5. Check syntax constraints on local-part
        if len(local_part) < 2:
            return False, None, f"Local-part too short: '{local_part}'"
        if local_part.startswith((".", "-", "_", "+")) or local_part.endswith((".", "-", "_", "+")):
            return False, None, f"Malformed local-part punctuation: '{local_part}'"
        if ".." in local_part or "--" in local_part:
            return False, None, f"Consecutive separator characters in local-part: '{local_part}'"

        # 6. Ensure domain has valid TLD
        tld = domain_part.split(".")[-1]
        if len(tld) < 2 or tld.isdigit():
            return False, None, f"Invalid top-level domain: .{tld}"

        return True, sanitized, "Passed Layer 1 validation"

    # -------------------------------------------------------------------------
    # LAYER 2: Role-Based, Gov/Edu/Mil & System Tracker Blocker
    # -------------------------------------------------------------------------
    @classmethod
    def check_role_and_domain_blocker(cls, email: str, domain: str) -> Tuple[bool, str]:
        """
        Auto-rejects emails starting with:
        careers@, press@, investorrelations@, no-reply@, noreply@, admin@, encompassadmin@, bug-reporting, sentry.
        Auto-rejects domains ending in .gov, .edu, .mil, or system/tracker domains.
        Returns: (is_allowed: bool, reason: str)
        """
        clean_email = email.strip().lower()
        clean_domain = domain.strip().lower()

        local_part = clean_email.split("@")[0] if "@" in clean_email else clean_email

        # 1. Role-based prefix rejection
        for role in ROLE_BASED_PREFIXES:
            if local_part == role or local_part.startswith(role + ".") or local_part.startswith(role + "-") or local_part.startswith(role + "_"):
                return False, f"Auto-rejected role-based email prefix: '{role}@'"
            # Check if local-part begins directly with role pattern
            if local_part.startswith(role):
                return False, f"Auto-rejected role-based prefix: '{local_part}@'"

        # 2. Governmental, Educational, and Military domains rejection
        if any(clean_domain.endswith(suffix) for suffix in RESTRICTED_GOV_EDU_TLDS):
            return False, f"Auto-rejected restricted governmental/educational/military domain: '{clean_domain}'"
        if re.search(r'\.(?:gov|edu|mil)(?:\.[a-z]{2})?$', clean_domain):
            return False, f"Auto-rejected governmental/educational TLD in '{clean_domain}'"

        # 3. System and Tracker domains rejection
        for tracker in SYSTEM_TRACKER_DOMAINS:
            if clean_domain == tracker or clean_domain.endswith("." + tracker):
                return False, f"Auto-rejected system/tracker domain: '{clean_domain}'"

        return True, "Passed Layer 2 blocker checks"

    # -------------------------------------------------------------------------
    # LAYER 3: Junk Title & Bot-Shield Filter + Clean Brand Name Extractor
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_page_title(cls, raw_title: str, domain: str) -> Tuple[bool, str, str]:
        """
        Checks if page title indicates bot-protection, 404 error, or generic navigation.
        If bot-shield or junk error: rejects page (is_valid=False).
        If generic navigation (e.g. 'Contact Us'): extracts clean brand name from domain.
        Returns: (is_valid: bool, company_name: str, reason: str)
        """
        title = (raw_title or "").strip()
        title_lower = title.lower()

        # 1. Bot-shield & Junk Page check
        for bot_term in BOT_SHIELD_TITLES:
            if bot_term in title_lower:
                return False, "", f"Bot-shield or junk page detected in title: '{bot_term}'"

        # 2. Check if title is purely generic navigation
        is_generic_nav = False
        if not title or len(title) < 3:
            is_generic_nav = True
        else:
            # Check exact match or title consisting only of generic words
            cleaned_title = re.sub(r'[^a-z\s]', '', title_lower).strip()
            if cleaned_title in GENERIC_NAV_TITLES:
                is_generic_nav = True
            elif any(cleaned_title == nav for nav in GENERIC_NAV_TITLES):
                is_generic_nav = True

        if is_generic_nav:
            extracted_brand = cls.extract_brand_name_from_domain(domain)
            return True, extracted_brand, f"Generic navigation title replaced with domain brand: '{extracted_brand}'"

        # 3. Clean extracted title by stripping separators
        split_parts = re.split(r'[\|\-\–\:\•]', title)
        candidate_name = split_parts[0].strip()
        if len(candidate_name) < 2 or candidate_name.lower() in GENERIC_NAV_TITLES:
            candidate_name = cls.extract_brand_name_from_domain(domain)

        return True, candidate_name, "Extracted valid company title"

    @classmethod
    def extract_brand_name_from_domain(cls, domain: str) -> str:
        """
        Extracts a clean, publication-ready company/brand name from a B2B domain.
        Example: 'zeusfitness.ca' -> 'Zeus Fitness'
                 'apex-construction.de' -> 'Apex Construction'
        """
        clean_dom = domain.strip().lower()
        clean_dom = re.sub(r'^https?://', '', clean_dom)
        clean_dom = re.sub(r'^www\.', '', clean_dom)
        clean_dom = clean_dom.split('/')[0].split(':')[0]

        # Strip multi-part TLDs and common TLD extensions
        stem = re.sub(r'\.(?:co\.[a-z]{2}|com\.[a-z]{2}|org\.[a-z]{2}|[a-z]{2,8})$', '', clean_dom)

        # Handle hyphen or dot separated stems
        if "-" in stem or "." in stem or "_" in stem:
            words = re.split(r'[-._]', stem)
            return " ".join(w.capitalize() for w in words if w)

        # Handle known compound words (e.g. 'zeusfitness' -> 'Zeus Fitness')
        for compound in KNOWN_DOMAIN_COMPOUNDS:
            if stem.endswith(compound) and len(stem) > len(compound):
                prefix = stem[:-len(compound)]
                # Handle special abbreviations like 'saas' -> 'SaaS'
                compound_display = "SaaS" if compound == "saas" else compound.capitalize()
                return f"{prefix.capitalize()} {compound_display}"

        return stem.capitalize()

    # -------------------------------------------------------------------------
    # LAYER 4: Niche Relevance & Auto-Template Scoring (0–100)
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_niche_score(
        cls,
        niche: str,
        page_title: str,
        page_content: str,
        meta_description: str = "",
        domain: str = ""
    ) -> Tuple[int, str]:
        """
        Scores scraped lead (0–100) against active campaign niche.
        Only leads scoring >= 70 pass into the Approval Gate.
        Returns: (score: int, evaluation_summary: str)
        """
        target_niche = (niche or "Commercial Construction").strip()
        profile = None

        # Resolve niche profile by exact or fuzzy match
        for key, p in NICHE_KEYWORD_PROFILES.items():
            if key.lower() == target_niche.lower() or key.lower() in target_niche.lower() or target_niche.lower() in key.lower():
                profile = p
                target_niche = key
                break

        # Fallback profile for custom unlisted niches
        if not profile:
            words = [w.lower() for w in re.findall(r'[a-zA-Z]{3,}', target_niche)]
            profile = {
                "primary": [target_niche.lower()],
                "secondary": words
            }

        title_lower = (page_title or "").lower()
        desc_lower = (meta_description or "").lower()
        domain_lower = (domain or "").lower()
        content_lower = (page_content or "").lower()[:15000]

        score = 0
        matched_indicators: List[str] = []

        # 1. Domain match check (+25 points)
        for prim in profile["primary"]:
            clean_token = prim.replace(" ", "")
            if clean_token in domain_lower:
                score += 25
                matched_indicators.append(f"domain:'{clean_token}'")
                break
        if score == 0:
            for sec in profile["secondary"]:
                if sec in domain_lower and len(sec) >= 4:
                    score += 15
                    matched_indicators.append(f"domain:'{sec}'")
                    break

        # 2. Page Title match check (+25 points primary, +15 secondary)
        for prim in profile["primary"]:
            if prim in title_lower:
                score += 25
                matched_indicators.append(f"title:'{prim}'")
                break
        else:
            for sec in profile["secondary"]:
                if re.search(rf'\b{re.escape(sec)}\b', title_lower):
                    score += 15
                    matched_indicators.append(f"title:'{sec}'")
                    break

        # 3. Meta Description match check (+20 points primary, +10 secondary)
        for prim in profile["primary"]:
            if prim in desc_lower:
                score += 20
                matched_indicators.append(f"meta:'{prim}'")
                break
        else:
            for sec in profile["secondary"]:
                if re.search(rf'\b{re.escape(sec)}\b', desc_lower):
                    score += 10
                    matched_indicators.append(f"meta:'{sec}'")
                    break

        # 4. Content Body keyword density check (up to 40 points)
        content_primary_hits = sum(1 for p in profile["primary"] if p in content_lower)
        content_sec_hits = sum(1 for s in profile["secondary"] if re.search(rf'\b{re.escape(s)}\b', content_lower))

        content_points = min(40, (content_primary_hits * 15) + (content_sec_hits * 5))
        if content_points > 0:
            score += content_points
            matched_indicators.append(f"content_hits:p{content_primary_hits}_s{content_sec_hits}")

        final_score = min(100, max(0, score))
        summary = f"Score: {final_score}/100 [{', '.join(matched_indicators) if matched_indicators else 'no niche signals'}]"
        return final_score, summary

    # -------------------------------------------------------------------------
    # DEDUPLICATION GUARD: Pipeline, Sent History & Blacklist Pre-Check
    # -------------------------------------------------------------------------
    @classmethod
    def is_lead_duplicate_or_blacklisted(
        cls,
        email: str,
        db_conn: Any,
        domain: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verifies that newly scraped email does not already exist in:
        1. Outreach Pipeline / History (outreach_queue - PENDING, APPROVED, SCHEDULED, SENT, REPLIED, etc.)
        2. Global Deduplication Registry (dedup_registry)
        3. Global Blacklist Rules (blacklist_rules)
        4. Global Suppression List (suppressed_entities / dnc_blacklist)
        Returns: (is_blocked: bool, reason: str)
        """
        clean_email = email.strip().lower()
        clean_domain = (domain or clean_email.split("@")[-1]).strip().lower()

        # 1. Check outreach_queue for any record of this email
        row = db_conn.execute("""
            SELECT id, status, company_name, created_at
            FROM outreach_queue
            WHERE lower(recipient) = ?
            LIMIT 1
        """, (clean_email,)).fetchone()
        if row:
            return True, f"Lead already exists in outreach queue/history (Status: {row['status']})"

        # 2. Check dedup_registry
        row_dedup = db_conn.execute("""
            SELECT status, last_processed_at
            FROM dedup_registry
            WHERE normalized_key = ?
            LIMIT 1
        """, (clean_email,)).fetchone()
        if row_dedup and row_dedup["status"] in ("CONTACTED", "SENT", "BLACKLISTED"):
            return True, f"Email registered as {row_dedup['status']} in deduplication shield"

        # 3. Check blacklist_rules
        rules = db_conn.execute("SELECT pattern, reason FROM blacklist_rules").fetchall()
        for r in rules:
            pat = r["pattern"].lower().strip()
            if pat == clean_email or pat == clean_domain:
                return True, f"Blocked by Blacklist rule: {pat} ({r['reason']})"
            if clean_domain.endswith(f".{pat}"):
                return True, f"Blocked by Blacklist subdomain rule: {pat} ({r['reason']})"
            if pat.startswith("*.") and clean_domain.endswith(pat[1:]):
                return True, f"Blocked by Blacklist wildcard rule: {pat} ({r['reason']})"

        # 4. Check suppressed_entities
        suppressed = db_conn.execute("""
            SELECT reason FROM suppressed_entities
            WHERE lower(entity) = ? OR lower(entity) = ?
            LIMIT 1
        """, (clean_email, clean_domain)).fetchone()
        if suppressed:
            return True, f"Entity suppressed due to opt-out or bounce: ({suppressed['reason']})"

        return False, "Lead is fresh and unique"
