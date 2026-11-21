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

# Layer 2: Invalid / system / role-based prefixes to auto-reject
INVALID_SYSTEM_PREFIXES = (
    "nosub_", "nosub", "no-reply", "noreply", "bounce",
    "careers", "press", "investorrelations", "admin", "encompassadmin",
    "bug-reporting", "sentry", "donotreply", "do-not-reply", "mailer-daemon"
)
ROLE_BASED_PREFIXES = INVALID_SYSTEM_PREFIXES

# Strictly blocked dummy/placeholder emails — always rejected regardless of wildcard rules
DUMMY_PLACEHOLDER_EMAILS = {
    "you@company.com", "user@example.com", "email@example.com",
    "test@example.com", "hello@example.com", "info@example.com",
    "contact@example.com", "name@company.com", "yourname@domain.com",
    "example@email.com", "user@email.com", "test@email.com", "admin@email.com",
}
DUMMY_PLACEHOLDER_LOCAL_PARTS = {
    "you", "user", "yourname", "name", "email", "someone",
    "test", "demo", "sample", "placeholder", "example",
}
DUMMY_PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net", "company.com", "domain.com",
    "yourdomain.com", "mydomain.com", "acme.com", "test.com", "email.com", "sample.com",
}

# Off-niche domain keywords — media, magazine, directory, blog sources never valid B2B leads
OFF_NICHE_DOMAIN_PATTERNS = (
    "magazine", "mag.", ".magazine", "news", "journal", "press.",
    "blog", "blogs.", "media.", ".media", "directory", "listings",
    "review", "reviews.", "forum", "forums.", "classifieds",
    "advertise", "advertising", "ads.", "sqmagazine", "fashionmagazine",
)

# Layer 2: Suffixes and system / tracker / junk domains
RESTRICTED_GOV_EDU_TLDS = (".gov", ".edu", ".mil")
SYSTEM_TRACKER_DOMAINS = {
    "wixpress.com", "sentry-next.wixpress.com", "sentry.io",
    "lexisnexis.com", "m-w.com", "f6s.com"
}

# Layer 3: Junk, HTTP error, and bot-shield page title phrases (case-insensitive)
HTTP_ERROR_AND_BOT_SHIELD_PATTERNS = [
    r"\b404\b",
    r"\b403\b",
    r"\b500\b",
    r"\b502\b",
    r"\b503\b",
    r"not found",
    r"page not found",
    r"access denied",
    r"forbidden",
    r"internal server error",
    r"bad gateway",
    r"service unavailable",
    r"attention required",
    r"checking your browser",
    r"security check",
    r"cloudflare",
    r"robot or human",
    r"just a moment",
    r"ddos protection",
    r"ray id",
    r"get help with",
    r"new & used"
]
BOT_SHIELD_TITLES = HTTP_ERROR_AND_BOT_SHIELD_PATTERNS

# Generic raw abbreviation fragments that should never be displayed as company names
GENERIC_SHORT_FRAGMENTS = {
    "AI", "IT", "HR", "PR", "HQ", "CO", "IO", "APP", "DEV", "TECH",
    "THE", "AND", "OR", "COM", "NET", "ORG", "LLC", "INC", "LTD", "CORP"
}

# Regex for stripping generic words from company names/titles
GENERIC_WORDS_PATTERN = re.compile(
    r'\b(?:welcome\s+to|official\s+site|official\s+website|home\s*page|home|welcome|main\s+page)\b',
    re.IGNORECASE
)

# Regex for HTML title separators: |, -, –, —, :, •
TITLE_SEPARATORS_PATTERN = re.compile(r'[\|\-\–\—\:\•]')

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

    @classmethod
    def is_off_niche_domain(cls, domain: str, niche: str = "") -> Tuple[bool, str]:
        """
        Detects and filters out off-niche media, magazine, directory, blog, and content farm domains
        (e.g., SQ Magazine, trade magazines, tech blogs, yellow pages) when targeting B2B/SaaS/commercial niches.
        """
        if not domain:
            return True, "Empty domain"
        clean = domain.strip().lower()
        clean = re.sub(r'^https?://', '', clean)
        clean = re.sub(r'^www\.', '', clean)
        clean = clean.split('/')[0].split(':')[0]

        for pat in OFF_NICHE_DOMAIN_PATTERNS:
            if pat in clean:
                return True, f"Filtered off-niche media/magazine/directory/blog domain pattern: '{pat}' in '{clean}'"
        return False, "Domain is valid niche target"

    @classmethod
    def is_junk_domain(cls, domain: str) -> bool:
        """Checks if domain is a known junk, tracker, or sentry domain."""
        if not domain:
            return True
        clean = domain.strip().lower()
        clean = re.sub(r'^https?://', '', clean)
        clean = re.sub(r'^www\.', '', clean)
        clean = clean.split('/')[0].split(':')[0]
        for tracker in SYSTEM_TRACKER_DOMAINS:
            if clean == tracker or clean.endswith("." + tracker) or tracker in clean:
                return True
        return False

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
        Rejects invalid/system prefixes (nosub_, no-reply@, noreply@, bounce@).
        Drops junk tracker domains (wixpress.com, sentry-next.wixpress.com, sentry.io).
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

        # 4. Check for invalid or system prefixes (nosub_, no-reply, noreply, bounce, etc.)
        for prefix in INVALID_SYSTEM_PREFIXES:
            if local_part == prefix or local_part.startswith(prefix):
                return False, None, f"Auto-rejected invalid/system email prefix: '{local_part}@'"

        # 4b. Block dummy/placeholder emails unconditionally
        full_email_check = f"{local_part}@{domain_part}"
        if (
            full_email_check in DUMMY_PLACEHOLDER_EMAILS
            or full_email_check.startswith("you@")
            or full_email_check.startswith("test@")
            or full_email_check.startswith("example@")
            or full_email_check.startswith("noreply@")
            or full_email_check.startswith("no-reply@")
        ):
            return False, None, f"Rejected dummy/placeholder email: '{full_email_check}'"
        if (
            domain_part in DUMMY_PLACEHOLDER_DOMAINS
            or domain_part == "example.com"
            or domain_part == "email.com"
            or domain_part.endswith(".example.com")
            or domain_part.startswith("example.")
            or domain_part.startswith("example-")
            or domain_part.endswith(".example")
        ):
            return False, None, f"Rejected dummy/placeholder domain: '{domain_part}'"
        if (
            local_part in DUMMY_PLACEHOLDER_LOCAL_PARTS
            or local_part == "example"
            or local_part.startswith("test")
            or local_part.startswith("noreply")
            or local_part.startswith("no-reply")
        ):
            return False, None, f"Rejected dummy/placeholder local-part: '{local_part}@'"

        # 5. Check for junk/tracker domains (wixpress.com, sentry-next.wixpress.com, sentry.io)
        if cls.is_junk_domain(domain_part):
            return False, None, f"Auto-rejected junk/tracker domain in email: '{domain_part}'"

        # 6. Check for truncated local-part (e.g. 'upport' instead of 'support')
        if local_part in TRUNCATED_LOCAL_PARTS:
            return False, None, f"Rejected truncated/clipped local-part: '{local_part}@'"

        # 7. Check syntax constraints on local-part
        if len(local_part) < 2:
            return False, None, f"Local-part too short: '{local_part}'"
        if local_part.startswith((".", "-", "_", "+")) or local_part.endswith((".", "-", "_", "+")):
            return False, None, f"Malformed local-part punctuation: '{local_part}'"
        if ".." in local_part or "--" in local_part:
            return False, None, f"Consecutive separator characters in local-part: '{local_part}'"

        # 8. Ensure domain has valid TLD
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
        Auto-rejects emails with invalid/system prefixes:
        nosub_, no-reply@, noreply@, bounce@, careers@, press@, admin@, etc.
        Auto-rejects domains ending in .gov, .edu, .mil, or junk tracker domains
        (wixpress.com, sentry-next.wixpress.com, sentry.io, etc.).
        Returns: (is_allowed: bool, reason: str)
        """
        clean_email = email.strip().lower()
        clean_domain = domain.strip().lower()

        local_part = clean_email.split("@")[0] if "@" in clean_email else clean_email
        email_dom = clean_email.split("@")[-1] if "@" in clean_email else ""

        # 1. Invalid / system prefix rejection (nosub_, no-reply@, noreply@, bounce@, etc.)
        for role in INVALID_SYSTEM_PREFIXES:
            if local_part == role or local_part.startswith(role + ".") or local_part.startswith(role + "-") or local_part.startswith(role + "_") or local_part.startswith(role):
                return False, f"Auto-rejected invalid/system email prefix: '{local_part}@'"

        # 1b. Dummy / placeholder email and domain rejection
        if (
            clean_email in DUMMY_PLACEHOLDER_EMAILS
            or clean_email.startswith("you@")
            or clean_email.startswith("test@")
            or clean_email.startswith("example@")
            or clean_email.startswith("noreply@")
            or clean_email.startswith("no-reply@")
            or email_dom in DUMMY_PLACEHOLDER_DOMAINS
            or email_dom == "example.com"
            or email_dom == "email.com"
            or email_dom.endswith(".example.com")
            or email_dom.startswith("example.")
            or email_dom.startswith("example-")
            or local_part in DUMMY_PLACEHOLDER_LOCAL_PARTS
            or local_part == "example"
            or local_part.startswith("test")
            or local_part.startswith("noreply")
            or local_part.startswith("no-reply")
        ):
            return False, f"Auto-rejected dummy/placeholder email: '{clean_email}'"

        # 1c. Off-niche media, magazine, blog, directory domain rejection
        is_off, off_reason = cls.is_off_niche_domain(clean_domain)
        if is_off:
            return False, off_reason
        if email_dom:
            is_off_em, off_reason_em = cls.is_off_niche_domain(email_dom)
            if is_off_em:
                return False, off_reason_em

        # 2. Governmental, Educational, and Military domains rejection
        if any(clean_domain.endswith(suffix) for suffix in RESTRICTED_GOV_EDU_TLDS):
            return False, f"Auto-rejected restricted governmental/educational/military domain: '{clean_domain}'"
        if re.search(r'\.(?:gov|edu|mil)(?:\.[a-z]{2})?$', clean_domain):
            return False, f"Auto-rejected governmental/educational TLD in '{clean_domain}'"

        # 3. System, tracker, and junk domains rejection (wixpress.com, sentry-next.wixpress.com, sentry.io)
        if cls.is_junk_domain(clean_domain):
            return False, f"Auto-rejected system/tracker junk domain: '{clean_domain}'"
        if email_dom and cls.is_junk_domain(email_dom):
            return False, f"Auto-rejected system/tracker email domain: '{email_dom}'"

        return True, "Passed Layer 2 blocker checks"

    # -------------------------------------------------------------------------
    # LAYER 3: Junk Title & Bot-Shield Filter + Clean Brand Name Extractor
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_page_title(cls, raw_title: str, domain: str) -> Tuple[bool, str, str]:
        """
        Evaluates page title:
        - Rejects HTTP error titles (404, Access Denied, 403, 500) and bot-shield pages.
        - Removes HTML title separators (|, -, –, —, :, •) and generic words ('Home', 'Welcome to', 'Official Site').
        - Extracts clean company name, with intelligent domain brand fallback for purely generic navigation.
        Returns: (is_valid: bool, company_name: str, reason: str)
        """
        title = (raw_title or "").strip()
        title_lower = title.lower()

        # 1. Reject HTTP error titles (404, Access Denied, etc.) and bot-shield/DDoS pages
        for pat in HTTP_ERROR_AND_BOT_SHIELD_PATTERNS:
            if re.search(pat, title_lower):
                return False, "", f"HTTP error or bot-shield detected in title: '{title}'"

        # 2. Check if title is purely generic navigation or short raw fragment
        cleaned_for_nav = re.sub(r'[^a-z\s]', '', title_lower).strip()
        if not title or len(title) <= 2 or title.upper() in GENERIC_SHORT_FRAGMENTS or cleaned_for_nav in GENERIC_NAV_TITLES:
            extracted_brand = cls.extract_brand_name_from_domain(domain)
            return True, extracted_brand, f"Generic navigation or short title replaced with domain brand: '{extracted_brand}'"

        # 3. Clean extracted company names using regex to remove HTML title separators
        # (|, -, –, —, :, •) and generic words ("Home", "Welcome to", "Official Site")
        segments = TITLE_SEPARATORS_PATTERN.split(title)
        valid_candidates = []
        for seg in segments:
            # Remove generic words using regex
            cleaned = GENERIC_WORDS_PATTERN.sub('', seg)
            # Remove leftover title separators and strip punctuation/whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -–—:|•.,\t\r\n"\'')
            if len(cleaned) > 2 and cleaned.upper() not in GENERIC_SHORT_FRAGMENTS and cleaned.lower() not in GENERIC_NAV_TITLES:
                valid_candidates.append(cleaned)

        if valid_candidates:
            candidate_name = valid_candidates[0]
            return True, candidate_name, "Extracted valid company title"

        # Fallback to domain-based brand name extraction
        candidate_name = cls.extract_brand_name_from_domain(domain)
        return True, candidate_name, f"Title contained only generic terms; brand extracted from domain: '{candidate_name}'"

    @classmethod
    def clean_company_name(cls, name: str, domain: str = "") -> str:
        """
        Cleans an extracted company name by removing HTML title separators (|, -, –, :)
        and generic words ('Home', 'Welcome to', 'Official Site').
        Normalizes short raw fragments like 'AI' into clean brand names from domain/title/metadata.
        """
        if not name or not isinstance(name, str):
            return cls.extract_brand_name_from_domain(domain) if domain else ""

        # Inspect all segments of title to find valid company brand (e.g. 'AI | Acme Platform' -> 'Acme Platform')
        segments = TITLE_SEPARATORS_PATTERN.split(name)
        valid_candidates = []
        for seg in segments:
            seg_clean = GENERIC_WORDS_PATTERN.sub('', seg)
            seg_clean = re.sub(r'\s+', ' ', seg_clean).strip(' -–—:|•.,\t\r\n"\'')
            if len(seg_clean) > 2 and seg_clean.upper() not in GENERIC_SHORT_FRAGMENTS and seg_clean.lower() not in GENERIC_NAV_TITLES:
                valid_candidates.append(seg_clean)

        if valid_candidates:
            if domain:
                dom_brand = cls.extract_brand_name_from_domain(domain).lower()
                for c in valid_candidates:
                    if dom_brand in c.lower() or c.lower() in dom_brand:
                        return c
            return valid_candidates[0]

        cleaned = TITLE_SEPARATORS_PATTERN.split(name)[0]
        cleaned = GENERIC_WORDS_PATTERN.sub('', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -–—:|•.,\t\r\n"\'')
        if (len(cleaned) <= 2 or cleaned.upper() in GENERIC_SHORT_FRAGMENTS) and domain:
            dom_brand = cls.extract_brand_name_from_domain(domain)
            if dom_brand and dom_brand.upper() not in GENERIC_SHORT_FRAGMENTS and len(dom_brand) > 2:
                return dom_brand
            stem = re.sub(r'\.(?:co\.[a-z]{2}|com\.[a-z]{2}|org\.[a-z]{2}|[a-z]{2,8})$', '', domain.strip().lower().replace("www.", ""))
            if stem and len(stem) > 2:
                return stem.replace("-", " ").replace(".", " ").title()
            return f"{cleaned.upper()} Platform" if cleaned.upper() == "AI" else dom_brand
        return cleaned or (cls.extract_brand_name_from_domain(domain) if domain else name)

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

        # 4. Content Body keyword density check (up to 55 points)
        content_primary_hits = sum(1 for p in profile["primary"] if p in content_lower)
        content_sec_hits = sum(1 for s in profile["secondary"] if re.search(rf'\b{re.escape(s)}\b', content_lower))

        content_points = min(55, (content_primary_hits * 20) + (content_sec_hits * 8))
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
