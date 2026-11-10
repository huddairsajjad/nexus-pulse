"""
H.Huddair's Nexus-Pulse - Level 1
Agent Module: Priority Email Finder & Scoring Engine
Ranks business email addresses according to commercial value density,
prioritizing estimating, bids, tenders, and QS contacts over generic info@ addresses.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from ..models import EmailTier, ScrapedEmail


# High-value prefix catalogs across multiple languages
TIER_1_PREFIXES = {
    # English
    "estimating", "estimator", "bids", "bid", "tenders", "tender", "qs",
    "quantitysurveyor", "procurement", "rfp", "takeoffs", "pricing",
    "subcontractors", "preconstruction", "pre-con", "commercial-team",
    # German
    "kalkulation", "ausschreibung", "ausschreibungen", "angebot", "bauangebot",
    # French
    "chiffrage", "devis", "appelsdoffres", "etudes", "metre", "etude-de-prix",
    # Russian (translit/latin)
    "smeta", "tender", "zakupki", "snabzhenie", "raschet",
    # Spanish
    "estudios", "presupuestos", "licitaciones", "contratacion"
}

TIER_2_PREFIXES = {
    "director", "managing-director", "md", "ceo", "commercial",
    "contracts", "projects", "operations", "management", "partner",
    "executive", "head", "vp", "president", "sales", "businessdev", "bd",
    "geschaeftsfuehrung", "direction", "gerencia"
}

TIER_3_PREFIXES = {
    "admin", "accounts", "finance", "billing", "office", "contact",
    "team", "enquiries", "inquiries", "kontakt", "buero", "accueil"
}

TIER_GENERIC_PREFIXES = {
    "info", "hello", "hi", "support", "mail", "general", "help",
    "inbox", "webmaster", "postmaster"
}


class PriorityEmailFinder:
    """
    Evaluates scraped email addresses and prioritizes direct high-value contacts.
    """

    @classmethod
    def classify_email(cls, email: str, context: Optional[str] = None) -> Tuple[EmailTier, int]:
        """
        Determines the tier and numeric priority score (0-100) of an email.
        """
        clean_email = email.strip().lower()
        if "@" not in clean_email:
            return EmailTier.UNKNOWN, 0

        prefix = clean_email.split("@")[0].strip()
        # Remove dots, dashes, underscores for prefix matching
        normalized_prefix = re.sub(r'[\.\-_\d]', '', prefix)

        # Check Tier 1 (Estimating, Bids, Tenders, QS)
        for t1 in TIER_1_PREFIXES:
            if t1 in prefix or prefix.startswith(t1) or normalized_prefix == t1:
                return EmailTier.TIER_1_ESTIMATING, 100

        # Check Tier 2 (Decision Makers & Commercial)
        for t2 in TIER_2_PREFIXES:
            if t2 in prefix or prefix.startswith(t2) or normalized_prefix == t2:
                return EmailTier.TIER_2_EXECUTIVE, 80

        # Check named personal corporate email (e.g., john.smith@company.com)
        # Named emails have high value compared to generic info@
        if "." in prefix and len(prefix.split(".")) == 2:
            part1, part2 = prefix.split(".")
            if len(part1) >= 2 and len(part2) >= 2 and part1 not in TIER_GENERIC_PREFIXES:
                return EmailTier.TIER_2_EXECUTIVE, 75

        # Check Tier 3 (Operational & Office)
        for t3 in TIER_3_PREFIXES:
            if t3 in prefix or prefix.startswith(t3) or normalized_prefix == t3:
                return EmailTier.TIER_3_OPERATIONAL, 50

        # Check Generic (info@, hello@)
        for tg in TIER_GENERIC_PREFIXES:
            if tg in prefix or normalized_prefix == tg:
                return EmailTier.TIER_GENERIC, 20

        # Default fallback for unlisted corporate address
        return EmailTier.TIER_3_OPERATIONAL, 40

    @classmethod
    def rank_emails(
        cls,
        raw_emails: List[str],
        page_source: str = "homepage",
        context_map: Optional[Dict[str, str]] = None
    ) -> List[ScrapedEmail]:
        """
        Deduplicates, scores, and sorts emails in descending order of commercial priority.
        """
        seen = set()
        ranked: List[ScrapedEmail] = []
        contexts = context_map or {}

        for email in raw_emails:
            clean = email.strip().lower()
            if clean in seen or "@" not in clean:
                continue
            seen.add(clean)

            prefix, domain = clean.split("@", 1)
            tier, score = cls.classify_email(clean, contexts.get(clean))

            ranked.append(ScrapedEmail(
                email=email.strip(),
                normalized_email=clean,
                prefix=prefix,
                domain=domain,
                tier=tier,
                priority_score=score,
                found_on_page=page_source,
                context_snippet=contexts.get(clean)
            ))

        # Sort descending by priority_score
        ranked.sort(key=lambda x: x.priority_score, reverse=True)
        return ranked

    @classmethod
    def pick_primary_email(cls, ranked_emails: List[ScrapedEmail]) -> Optional[ScrapedEmail]:
        """
        Selects the single best outreach email from the ranked list.
        Never selects generic info@ if estimating@ or executive direct emails exist.
        """
        if not ranked_emails:
            return None
        return ranked_emails[0]
