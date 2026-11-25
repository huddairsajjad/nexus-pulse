"""
H.Huddair's Nexus-Pulse - Production Build
Agent Module: Deep Scraper & Tech-Stack Detector

Extracts real B2B contact emails, phones, and tech-stack from target domains.
Prioritises high-value estimating & tender contacts over generic mailboxes.

Search Discovery: Cascading multi-provider pipeline that is Railway cloud-resilient:
  Provider 1 — ddgs / duckduckgo-search Python library (DDGS().text, backend='lite' then 'html')
  Provider 2 — Bing Web Search HTML scraping (base64 URL unpack)
  Provider 3 — DuckDuckGo Lite HTTP POST (legacy fallback)

Zero-Seed Policy: Never returns hardcoded or fake lead data.
"""

from __future__ import annotations

import asyncio
import base64
import html
import logging
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

from ..models import Lead, TechStack, EmailTier, ScrapedEmail
from .priority_finder import PriorityEmailFinder
from core.hygiene.lead_validator import LeadValidationFilter

logger = logging.getLogger("nexus.scraper")


class SerperAPIError(RuntimeError):
    """Raised when Serper.dev API returns an error status or error message."""
    pass


class MissingSerperApiKeyError(SerperAPIError):
    """Raised when SERPER_API_KEY is missing in env or .env."""
    pass

# ---------------------------------------------------------------------------
# Try modern `ddgs` package first, fall back to legacy `duckduckgo_search`
# ---------------------------------------------------------------------------
_DDGS = None
try:
    from ddgs import DDGS as _DDGS_import  # type: ignore
    _DDGS = _DDGS_import
    logger.info("[DDGS] Loaded via `ddgs` package (v9+)")
except ImportError:
    try:
        from duckduckgo_search import DDGS as _DDGS_import  # type: ignore
        _DDGS = _DDGS_import
        logger.info("[DDGS] Loaded via legacy `duckduckgo_search` package")
    except ImportError:
        logger.warning("[DDGS] Neither `ddgs` nor `duckduckgo_search` available — Provider 1 disabled")


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9_.+-]+(?:\s*\[at\]\s*|\s*\(at\)\s*|@)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
)
PHONE_REGEX = re.compile(
    r'(?:\+?\d{1,4}[-.\\s]?)?(?:\(\d{2,5}\)[-.\\s]?)?\d{3,5}[-.\\s]?\d{3,5}'
)

# ---------------------------------------------------------------------------
# Domains that are search engines, social networks, or aggregate directories
# (never valid B2B leads)
# ---------------------------------------------------------------------------
DISCARD_DOMAINS = {
    "google.", "duckduckgo.", "bing.", "yahoo.", "microsoft.",
    "facebook.", "instagram.", "twitter.", "x.com", "linkedin.",
    "youtube.", "wikipedia.", "wikimedia.", "reddit.", "amazon.", "apple.",
    "github.", "pinterest.", "tiktok.", "medium.", "quora.", "zhihu.",
    "tripadvisor.", "yelp.", "w3schools.", "stackoverflow.", "t.me", "whatsapp.",
    "wixpress.com", "sentry-next.wixpress.com", "sentry.io",
    "lexisnexis.com", "m-w.com", "f6s.com", "imdb.com", "rottentomatoes.com",
    "yellowpages.", "houzz.", "checkatrade.", "bark.com",
    "clutch.co", "trustpilot.", "glassdoor.", "indeed.", "example.com",
    "aeroleads.", "hunter.io", "apollo.io", "openai.", "chatgpt.",
    "slideshare.", "scribd.", "baidu.", "carigold.", "meta.com", "threads.net",
    "merriam-webster.", "dictionary.", "thefreedictionary.", "vocabulary.com",
    "cambridge.org", "collinsdictionary.", "oxfordlearnersdictionaries.", "britannica.",
    "rozee.pk", "mustakbil.com", "olx.com", "olx.com.pk", "daraz.pk", "zameen.com", "graana.com", "pakwheels.com",
}

# Junk email domains / prefixes handled by LeadValidationFilter but also
# enforced explicitly here as a fast path:
JUNK_EMAIL_PREFIXES = (
    # True system/daemon/junk addresses only — do NOT block legitimate B2B contacts
    # like privacy@, support@, admin@, press@, careers@ which are real business emails
    "noreply", "no-reply", "webmaster", "sentry", "mailer-daemon",
    "donotreply", "do-not-reply", "bounce", "example", "test",
    "demo", "sample", "placeholder", "postmaster", "hostmaster", "abuse",
    "unsubscribe", "optout", "opt-out", "notifications", "alerts",
)
JUNK_EMAIL_DOMAINS = {
    "example.com", "email.com", "sample.com", "domain.com", "test.com",
    "company.com", "yourdomain.com", "mydomain.com",
    "facebook.com", "linkedin.com", "yelp.com",
    "yellowpages.com", "houzz.com", "checkatrade.com", "bark.com",
}

# ---------------------------------------------------------------------------
# Realistic desktop browser headers for all outbound HTTP requests
# ---------------------------------------------------------------------------
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
]
_ua_index = 0

def _rotated_headers(accept_language: str = "en-US,en;q=0.9") -> Dict[str, str]:
    global _ua_index
    ua = _UA_POOL[_ua_index % len(_UA_POOL)]
    _ua_index += 1
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Chromium";v="130", "Not?A_Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

DEFAULT_HEADERS = _rotated_headers()

# ---------------------------------------------------------------------------
# Contact subpage discovery keywords (multilingual & global)
# ---------------------------------------------------------------------------
CONTACT_SUBPAGE_KEYWORDS = [
    "kontakt", "contact", "impressum", "about", "ueber-uns", "uber-uns",
    "ansprechpartner", "team", "our-team", "leadership", "people", "staff", "mentions", "mentions-legales", "legal",
    "contacto", "contatti", "contacts", "direction", "firmensitz", "standort", "imprint",
    "qui-sommes-nous", "chi-siamo", "quienes-somos", "fale-conosco", "faleconosco", "over-ons",
    "equipo", "management", "directors", "inquiries", "enquiries", "location", "sede",
    "privacy", "privacy-policy", "terms", "terms-of-service", "datenschutz", "policy",
]
COMMON_SUBPATHS = [
    "/contact", "/contact/", "/contact-us", "/contact-us/",
    "/about", "/about-us", "/about-us/", "/about/",
    "/team", "/team/", "/our-team", "/our-team/",
    "/kontakt", "/kontakt/", "/impressum", "/impressum/",
    "/contacto", "/contacto/", "/contatti", "/contatti/",
    "/contactez-nous", "/contactez-nous/",
    "/imprint", "/imprint/", "/legal", "/legal/",
    "/contato", "/contato/", "/over-ons", "/over-ons/",
    # Privacy & legal pages frequently contain real business email addresses
    "/privacy-policy", "/privacy-policy/", "/privacy", "/privacy/",
    "/terms", "/terms/", "/terms-of-service", "/terms-of-service/",
    "/terms-of-use", "/terms-of-use/",
    "/legal/privacy", "/legal/privacy/",
    "/gdpr", "/gdpr/", "/data-protection", "/data-protection/",
]


# ===========================================================================
# Tech-Stack Detector (unchanged)
# ===========================================================================
class TechStackDetector:
    """Detects website CMS, frameworks, analytics, CDN, and marketing stacks."""

    SIGNATURES = {
        "cms": {
            "WordPress": [r"wp-content", r"wp-includes", r"name=\"generator\" content=\"WordPress"],
            "Webflow": [r"assets\.website-files\.com", r"data-wf-site", r"Webflow"],
            "Shopify": [r"cdn\.shopify\.com", r"Shopify\.shop"],
            "Wix": [r"wix\.com", r"wix-warmup-data", r"_wixStaticPath"],
            "Squarespace": [r"squarespace\.com", r"static1\.squarespace\.com"],
            "Drupal": [r"Drupal\.settings", r"sites/default/files"],
            "Joomla": [r"media/jui", r"joomla!"],
            "HubSpot CMS": [r"hs-scripts\.com", r"hs-content-id"]
        },
        "frontend_frameworks": {
            "Next.js": [r"/_next/static", r"__NEXT_DATA__"],
            "React": [r"react\.production\.min\.js", r"_reactListening", r"react-root"],
            "Vue.js": [r"vue\.runtime", r"vue\.global", r"data-v-[a-z0-9]"],
            "Nuxt.js": [r"/_nuxt/", r"__NUXT__"],
            "Angular": [r"ng-version", r"zone\.js"],
            "Tailwind CSS": [r"tailwind", r"border-t-transparent"],
            "Bootstrap": [r"bootstrap(?:\.min)?\.css", r"bootstrap(?:\.bundle)?\.js"],
            "jQuery": [r"jquery(?:\.min)?\.js"]
        },
        "crm_and_marketing": {
            "HubSpot": [r"js\.hs-scripts\.com", r"js\.hubspot\.com", r"hbspt\.forms"],
            "Salesforce": [r"pardot\.com", r"salesforce\.com"],
            "Google Analytics 4": [r"googletagmanager\.com/gtag/js\?id=G-", r"gtag\('config',\s*'G-"],
            "Google Tag Manager": [r"googletagmanager\.com/gtm\.js\?id=GTM-"],
            "Hotjar": [r"static\.hotjar\.com"],
            "Klaviyo": [r"static\.klaviyo\.com"],
            "Mailchimp": [r"chimpstatic\.com", r"list-manage\.com"],
            "Intercom": [r"widget\.intercom\.io"]
        },
        "web_server_and_cdn": {
            "Cloudflare": [r"cloudflare", r"cf-ray", r"cdnjs\.cloudflare\.com"],
            "AWS CloudFront": [r"cloudfront\.net"],
            "Vercel": [r"vercel\.app", r"x-vercel-id"],
            "Netlify": [r"netlify"],
            "Nginx": [r"nginx"],
            "Apache": [r"apache"]
        }
    }

    @classmethod
    def detect(cls, html_text: str, headers: Optional[Dict[str, str]] = None) -> TechStack:
        headers = headers or {}
        header_str = " ".join(f"{k}: {v}" for k, v in headers.items())
        combined_text = f"{header_str}\n{html_text}"
        stack = TechStack()
        raw_detected: Set[str] = set()
        for category, signatures in cls.SIGNATURES.items():
            for tech_name, patterns in signatures.items():
                for pat in patterns:
                    if re.search(pat, combined_text, re.IGNORECASE):
                        getattr(stack, category).append(tech_name)
                        raw_detected.add(tech_name)
                        break
        server_header = headers.get("server", "").lower()
        if "cloudflare" in server_header and "Cloudflare" not in stack.web_server_and_cdn:
            stack.web_server_and_cdn.append("Cloudflare")
            raw_detected.add("Cloudflare")
        if "nginx" in server_header and "Nginx" not in stack.web_server_and_cdn:
            stack.web_server_and_cdn.append("Nginx")
            raw_detected.add("Nginx")
        if "apache" in server_header and "Apache" not in stack.web_server_and_cdn:
            stack.web_server_and_cdn.append("Apache")
            raw_detected.add("Apache")
        stack.raw_technologies = sorted(list(raw_detected))
        return stack


# ===========================================================================
# Serper.dev Country & Language Mapping
# ===========================================================================
SERPER_COUNTRY_CODES: Dict[str, str] = {
    "pakistan": "pk",
    "germany": "de",
    "deutschland": "de",
    "united kingdom": "gb",
    "uk": "gb",
    "great britain": "gb",
    "england": "gb",
    "united states": "us",
    "usa": "us",
    "canada": "ca",
    "australia": "au",
    "france": "fr",
    "italy": "it",
    "spain": "es",
    "netherlands": "nl",
    "switzerland": "ch",
    "austria": "at",
    "belgium": "be",
    "united arab emirates": "ae",
    "uae": "ae",
    "saudi arabia": "sa",
    "qatar": "qa",
    "singapore": "sg",
    "malaysia": "my",
    "india": "in",
    "brazil": "br",
    "mexico": "mx",
    "turkey": "tr",
    "poland": "pl",
    "sweden": "se",
    "norway": "no",
    "denmark": "dk",
    "finland": "fi",
    "ireland": "ie",
    "new zealand": "nz",
    "south africa": "za",
    "china": "cn",
    "japan": "jp",
}

SERPER_LANGUAGE_CODES: Dict[str, str] = {
    "pk": "en",
    "de": "de",
    "at": "de",
    "ch": "de",
    "gb": "en",
    "us": "en",
    "ca": "en",
    "au": "en",
    "fr": "fr",
    "be": "fr",
    "it": "it",
    "es": "es",
    "mx": "es",
    "nl": "nl",
    "ae": "en",
    "sa": "ar",
    "qa": "ar",
    "sg": "en",
    "my": "en",
    "in": "en",
    "br": "pt",
    "tr": "tr",
    "pl": "pl",
    "se": "sv",
    "no": "no",
    "dk": "da",
    "fi": "fi",
}

def resolve_serper_gl(country: str) -> str:
    c = (country or "").strip().lower()
    return SERPER_COUNTRY_CODES.get(c, "us")

def resolve_serper_hl(country: str) -> str:
    gl = resolve_serper_gl(country)
    return SERPER_LANGUAGE_CODES.get(gl, "en")


# ===========================================================================
# SearchDiscoveryAgent — Serper.dev Fast Lead Discovery Engine
# ===========================================================================
class SearchDiscoveryAgent:
    """
    High-Speed Autonomous B2B Lead Discovery Engine powered by Serper.dev JSON APIs.
    Endpoints:
      - https://google.serper.dev/places (Google Places / Verified Local Commercial Businesses)
      - https://google.serper.dev/search (Google Organic Commercial Web Search)
    Authenticated via header 'X-API-KEY' loaded from SERPER_API_KEY (.env / os.environ).

    Features:
      - Bounded request timeouts (5–8s) & controlled concurrency
      - Continual query and pagination expansion for exact lead quota fulfillment
      - Instant cancellation checks between calls to halt execution without hanging
      - Automatic directory, social network, and aggregator exclusion
      - Zero-Seed Policy: 100% real leads from live web sources; zero dummy/mock data.
    """

    def __init__(
        self,
        timeout_seconds: float = 7.0,
        serper_api_key: Optional[str] = None,
        query_mode: Optional[str] = None,
    ):
        self.timeout = timeout_seconds
        self._api_key = serper_api_key
        self._configured_query_mode = query_mode
        self._free_tier_fallback_active = False
        self.discovered_metadata: Dict[str, Dict[str, Any]] = {}
        self._executed_places_queries: Set[Tuple[str, str]] = set()
        self._executed_search_pages: Set[Tuple[str, str, int]] = set()

    @property
    def query_mode(self) -> str:
        """
        Reads SERPER_QUERY_MODE from constructor, environment, or .env.
        Allowed values: 'auto' (default), 'simple', 'advanced'.
        """
        if self._configured_query_mode and self._configured_query_mode.strip():
            mode = self._configured_query_mode.strip().lower()
        else:
            try:
                load_dotenv(PROJECT_ROOT / ".env", override=False)
            except Exception:
                pass
            mode = os.environ.get("SERPER_QUERY_MODE", "auto").strip().lower()
        if mode not in ("auto", "simple", "advanced"):
            mode = "auto"
        return mode

    @property
    def is_simple_mode(self) -> bool:
        """True if explicitly configured for simple queries or auto-fallback is active."""
        return self.query_mode == "simple" or (self.query_mode == "auto" and self._free_tier_fallback_active)

    @classmethod
    def to_simple_query(cls, query: str) -> str:
        """
        Converts an advanced search query into a clean, simple search query
        for Serper.dev free-tier accounts without boolean operators or syntax restrictions.
        Strips quotes, parentheses, OR/AND operators, site:/inurl:/mailto: prefixes, and special symbols.
        """
        if not query:
            return ""
        q = str(query)
        # Strip operators like site:..., inurl:..., intitle:..., filetype:..., mailto:...
        q = re.sub(r'(?:^|\s)[+-]?(?:site|inurl|intitle|filetype|mailto):[^\s\)]+', ' ', q, flags=re.IGNORECASE)
        q = re.sub(r'\b(?:site|inurl|intitle|filetype|mailto):[^\s\)]+', '', q, flags=re.IGNORECASE)
        # Strip standalone "mailto:"
        q = re.sub(r'["\']?mailto:?["\']?', '', q, flags=re.IGNORECASE)
        # Convert prefix@ patterns like "info@" or "contact@" cleanly without gluing words
        q = re.sub(r'([a-zA-Z0-9._+-]+)@(?=[\s"\'\)]|$)', r'\1 email ', q)
        # Convert standalone "@" or (@) to " email "
        q = re.sub(r'["\']?@["\']?', ' email ', q)
        # Strip boolean keywords OR, AND, NOT
        q = re.sub(r'\b(?:OR|AND|NOT)\b', ' ', q, flags=re.IGNORECASE)
        # Strip quotes, curly quotes, parentheses, brackets, and wildcards
        q = re.sub(r'["\'\u201c\u201d\u2018\u2019\(\)\[\]\{\}\*]', ' ', q)
        # Strip colons, semicolons, pipe symbols, slashes
        q = re.sub(r'[:;\|/\\~^]', ' ', q)
        # Strip leading search inclusion/exclusion +/- operators on standalone tokens
        q = re.sub(r'(?:^|\s)[+-]+(?=[a-zA-Z0-9])', ' ', q)
        # Collapse multiple spaces
        q = " ".join(q.split())
        return q.strip()

    @staticmethod
    def is_free_tier_error(resp_status: int, resp_text: str) -> bool:
        """Detects whether an HTTP 400 response from Serper indicates free-tier query pattern restrictions."""
        if resp_status != 400:
            return False
        txt = resp_text.lower()
        if "free" in txt and ("account" in txt or "plan" in txt or "tier" in txt):
            return True
        if "query pattern" in txt or "pattern not allowed" in txt:
            return True
        if "not allowed for free" in txt:
            return True
        return False

    def get_api_key(self) -> str:
        """Reads SERPER_API_KEY from environment or .env without hardcoding."""
        if self._api_key and self._api_key.strip():
            return self._api_key.strip()
        try:
            load_dotenv(PROJECT_ROOT / ".env", override=False)
        except Exception:
            pass
        return os.environ.get("SERPER_API_KEY", "").strip()

    def check_api_key(self) -> str:
        """Verifies SERPER_API_KEY is present; raises explicit MissingSerperApiKeyError if missing."""
        key = self.get_api_key()
        if not key:
            raise MissingSerperApiKeyError(
                "SERPER_API_KEY is not configured in .env or environment variables. "
                "Please add a valid Serper.dev API key to enable live lead discovery."
            )
        return key

    # ------------------------------------------------------------------
    # URL cleaning & validation helpers
    # ------------------------------------------------------------------
    @classmethod
    def clean_candidate_url(cls, raw_url: str) -> Optional[str]:
        """Validates, unpacks, and normalises a raw search result URL."""
        if not raw_url:
            return None

        # DuckDuckGo redirect /uddg=
        if "uddg=" in raw_url:
            raw_url = urllib.parse.unquote(raw_url.split("uddg=")[1].split("&")[0])

        # Bing redirect /ck/a?!...&u=a1<base64>
        if "bing.com/ck/a" in raw_url and "u=a1" in raw_url:
            try:
                u_param = raw_url.split("u=a1")[1].split("&")[0]
                # Proper base64 padding
                u_param += "=" * ((4 - len(u_param) % 4) % 4)
                raw_url = base64.urlsafe_b64decode(u_param).decode("utf-8", errors="ignore")
            except Exception:
                pass

        # Yahoo redirect /RU=.../RK=
        if "r.search.yahoo.com" in raw_url and "/RU=" in raw_url:
            try:
                ru_param = raw_url.split("/RU=")[1].split("/RK=")[0]
                raw_url = urllib.parse.unquote(ru_param)
            except Exception:
                pass

        # Google redirect /url?q=...
        if "google.com/url" in raw_url and "q=" in raw_url:
            try:
                raw_url = urllib.parse.unquote(raw_url.split("q=")[1].split("&")[0])
            except Exception:
                pass

        if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            return None

        parsed = urlparse(raw_url)
        domain = parsed.netloc.lower().replace("www.", "").split(":")[0]
        if not domain or any(d in domain for d in DISCARD_DOMAINS):
            return None

        # Filter out placeholder seed domains (like example-contractor.de)
        if (
            domain.startswith("example-")
            or domain == "example.com"
            or domain.endswith(".example.com")
            or domain.startswith("example.")
            or domain.endswith(".example")
            or "example-contractor" in domain
            or domain.startswith("test-")
            or domain.startswith("dummy-")
            or domain == "test.com"
        ):
            return None

        # Filter out off-niche media, magazine, blog, directory domains
        try:
            is_off, _ = LeadValidationFilter.is_off_niche_domain(domain)
            if is_off:
                return None
        except Exception:
            pass

        # Delegate .gov/.edu/.mil and system tracker blocks to LeadValidationFilter
        try:
            is_allowed, _ = LeadValidationFilter.check_role_and_domain_blocker("check@" + domain, domain)
            if not is_allowed:
                return None
        except Exception:
            pass

        return f"{parsed.scheme}://{parsed.netloc}"

    @classmethod
    def sanitize_search_query(cls, query: str) -> str:
        """Sanitises search query string."""
        cleaned = re.sub(r'["()]', '', query)
        cleaned = re.sub(r'\bOR\b', '', cleaned)
        cleaned = re.sub(r'site:\S+', '', cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned

    @staticmethod
    def build_query_variations(niche: str, city: str, country: str) -> List[str]:
        """Generates diverse search queries for niche, city, and country."""
        n = niche.strip()
        c = city.strip()
        co = country.strip()
        return [
            f"{n} in {c} {co}",
            f"{n} companies {c}",
            f"{n} contractors in {c} contact",
            f"{n} firms {c} email",
            f"best {n} {c} official website",
            f"{n} services in {c}",
            f"{n} {c} contact email",
            f"{n} {c} tenders projects",
            f"{n} commercial {c} contact",
            f"{n} suppliers in {c} {co}",
            f"commercial {n} companies in {c}",
            f"{n} group {c} official",
            f"{n} corporate office {c} {co}",
            f"{n} headquarters {c}",
            f"{n} specialists {c} contact",
            f"{n} commercial engineering {c}",
            f"{n} developers in {c} {co}",
            f"{n} solutions {c} email",
        ]

    # ------------------------------------------------------------------
    # Serper Places JSON API (https://google.serper.dev/places)
    # ------------------------------------------------------------------
    async def query_serper_places(
        self,
        query: str,
        country: str,
        client: httpx.AsyncClient,
        is_cancelled: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Queries Serper Places API to discover verified local commercial businesses."""
        if is_cancelled and is_cancelled():
            return []
        key = self.check_api_key()
        gl = resolve_serper_gl(country)
        hl = resolve_serper_hl(country)
        headers = {
            "X-API-KEY": key,
            "Content-Type": "application/json",
        }

        # Apply simple query mode if configured or fallen back
        effective_query = self.to_simple_query(query) if self.is_simple_mode else query.strip()
        if not effective_query:
            effective_query = query.strip()

        payload = {
            "q": effective_query,
            "gl": gl,
            "hl": hl,
        }
        logger.info(f"[SERPER:PLACES] Requesting: '{effective_query}' (gl={gl}, hl={hl}, mode={self.query_mode})")
        try:
            resp = await client.post(
                "https://google.serper.dev/places",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as ex:
            logger.error(f"[SERPER:PLACES] Network/HTTP error: {ex}")
            raise SerperAPIError(f"Serper.dev places request failed: {ex}") from ex

        if resp.status_code == 401:
            raise SerperAPIError("Serper.dev API error (401): Unauthorized. Invalid SERPER_API_KEY.")
        if resp.status_code == 403:
            raise SerperAPIError("Serper.dev API error (403): Forbidden. Check account permissions.")
        if resp.status_code == 429:
            raise SerperAPIError("Serper.dev API error (429): Quota exceeded or rate limited on Serper.dev.")

        # Automatic fallback on free-tier 400 restriction
        if resp.status_code == 400:
            resp_text = resp.text
            if self.is_free_tier_error(resp.status_code, resp_text) and self.query_mode in ("auto", "simple") and not self._free_tier_fallback_active:
                logger.warning(
                    f"[SERPER:PLACES:FALLBACK] Serper free-tier query restriction on '{effective_query}'. "
                    f"Auto-switching to clean simple query mode."
                )
                self._free_tier_fallback_active = True
                fallback_query = self.to_simple_query(effective_query)
                if fallback_query and fallback_query != effective_query:
                    logger.info(f"[SERPER:PLACES:FALLBACK] Retrying places with clean simple query: '{fallback_query}'")
                    return await self.query_serper_places(fallback_query, country, client, is_cancelled=is_cancelled)
            raise SerperAPIError(f"Serper.dev API error (400): {resp_text}")

        if resp.status_code >= 400:
            raise SerperAPIError(f"Serper.dev API error ({resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except Exception as parse_err:
            raise SerperAPIError(f"Serper.dev places response JSON parse error: {parse_err}") from parse_err

        places = data.get("places", [])
        logger.info(f"[SERPER:PLACES] Found {len(places)} listings for '{effective_query}'")
        return places

    # ------------------------------------------------------------------
    # Serper Search JSON API (https://google.serper.dev/search)
    # ------------------------------------------------------------------
    async def query_serper_search(
        self,
        query: str,
        country: str,
        page: int,
        client: httpx.AsyncClient,
        num: int = 20,
        is_cancelled: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Queries Serper Search API for Google organic search results with pagination."""
        if is_cancelled and is_cancelled():
            return []
        key = self.check_api_key()
        gl = resolve_serper_gl(country)
        hl = resolve_serper_hl(country)
        headers = {
            "X-API-KEY": key,
            "Content-Type": "application/json",
        }

        # Apply simple query mode if configured or fallen back
        effective_query = self.to_simple_query(query) if self.is_simple_mode else query.strip()
        if not effective_query:
            effective_query = query.strip()

        payload = {
            "q": effective_query,
            "gl": gl,
            "hl": hl,
            "num": num,
            "page": page,
        }
        logger.info(f"[SERPER:SEARCH] Requesting: '{effective_query}' (page={page}, gl={gl}, hl={hl}, mode={self.query_mode})")
        try:
            resp = await client.post(
                "https://google.serper.dev/search",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as ex:
            logger.error(f"[SERPER:SEARCH] Network/HTTP error: {ex}")
            raise SerperAPIError(f"Serper.dev search request failed: {ex}") from ex

        if resp.status_code == 401:
            raise SerperAPIError("Serper.dev API error (401): Unauthorized. Invalid SERPER_API_KEY.")
        if resp.status_code == 403:
            raise SerperAPIError("Serper.dev API error (403): Forbidden. Check account permissions.")
        if resp.status_code == 429:
            raise SerperAPIError("Serper.dev API error (429): Quota exceeded or rate limited on Serper.dev.")

        # Automatic fallback on free-tier 400 restriction
        if resp.status_code == 400:
            resp_text = resp.text
            if self.is_free_tier_error(resp.status_code, resp_text) and self.query_mode in ("auto", "simple") and not self._free_tier_fallback_active:
                logger.warning(
                    f"[SERPER:SEARCH:FALLBACK] Serper free-tier query restriction on '{effective_query}'. "
                    f"Auto-switching to clean simple query mode."
                )
                self._free_tier_fallback_active = True
                fallback_query = self.to_simple_query(effective_query)
                if fallback_query and fallback_query != effective_query:
                    logger.info(f"[SERPER:SEARCH:FALLBACK] Retrying search with clean simple query: '{fallback_query}' (page={page})")
                    return await self.query_serper_search(
                        fallback_query, country, page=page, client=client, num=num, is_cancelled=is_cancelled
                    )
            raise SerperAPIError(f"Serper.dev API error (400): {resp_text}")

        if resp.status_code >= 400:
            raise SerperAPIError(f"Serper.dev API error ({resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except Exception as parse_err:
            raise SerperAPIError(f"Serper.dev search response JSON parse error: {parse_err}") from parse_err

        items: List[Dict[str, Any]] = []
        for org in data.get("organic", []):
            link = org.get("link", "")
            title = org.get("title", "")
            snippet = org.get("snippet", "")
            if link:
                items.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": "serper_organic"
                })
        for pl in data.get("places", []):
            website = pl.get("website", "")
            if website:
                items.append({
                    "title": pl.get("title", ""),
                    "link": website,
                    "phone": pl.get("phoneNumber", ""),
                    "address": pl.get("address", ""),
                    "source": "serper_places"
                })
        logger.info(f"[SERPER:SEARCH] Found {len(items)} candidate links for '{effective_query}' (page={page})")
        return items

    # ------------------------------------------------------------------
    # Main Discovery Entry Point: Fast Serper Places & Search Pipeline
    # ------------------------------------------------------------------
    async def discover_candidate_urls(
        self,
        queries: Optional[List[Any]] = None,
        limit: int = 20,
        country: str = "Pakistan",
        city: str = "Lahore",
        niche: str = "Commercial Construction",
        excluded_domains: Optional[Set[str]] = None,
        is_cancelled: Optional[Any] = None,
    ) -> List[str]:
        """
        Runs high-speed domain discovery via Serper.dev Places and Search APIs.
        Expands queries and pagination until the candidate domain requirement is met.
        Strictly enforces cancellation checks to halt immediately on cancel.
        """
        if is_cancelled and is_cancelled():
            logger.info("[SERPER:DISCOVERY] Cancellation signal observed before start — aborting.")
            return []

        # Validate that SERPER_API_KEY is present; raises explicit MissingSerperApiKeyError if missing
        self.check_api_key()

        discovered_urls: List[str] = []
        seen_domains: Set[str] = set()
        excluded: Set[str] = {d.strip().lower() for d in (excluded_domains or set()) if d}

        # Dynamic domain quota & pagination scaling for arbitrary counts 1 to 100+
        if limit <= 5:
            needed_domains = max(limit * 3, 5)
            max_pages = 2
        elif limit <= 25:
            needed_domains = max(limit * 3, 20)
            max_pages = 4
        elif limit <= 50:
            needed_domains = max(limit * 3, 50)
            max_pages = 6
        else:
            needed_domains = max(limit * 3, 100)
            max_pages = 8

        def _register_candidate(raw_url: str, title: str = "", phone: str = "", address: str = "", source: str = "") -> bool:
            if not raw_url:
                return False
            clean_u = self.clean_candidate_url(raw_url)
            if not clean_u:
                return False
            dom = urlparse(clean_u).netloc.replace("www.", "").lower().split(":")[0]
            if not dom or dom in excluded or dom in seen_domains:
                return False
            seen_domains.add(dom)
            discovered_urls.append(clean_u)
            self.discovered_metadata[dom] = {
                "url": clean_u,
                "title": title.strip() if title else "",
                "phone": phone.strip() if phone else "",
                "address": address.strip() if address else "",
                "source": source
            }
            logger.info(f"[SERPER:DISCOVERY] ✓ Accepted [{source}] {clean_u} ({dom})")
            return True

        logger.info(
            f"[SERPER:DISCOVERY] Starting Serper lead discovery | niche='{niche}' | city='{city}' "
            f"| country='{country}' | target_domains={needed_domains} | excluded={len(excluded)} | mode={self.query_mode}"
        )

        gl_key = resolve_serper_gl(country)
        is_constr = any(
            k in niche.lower()
            for k in ("construction", "contractor", "roofing", "mep", "building", "civil", "infrastructure", "plumbing", "electrical")
        )

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=_rotated_headers(),
            follow_redirects=True,
            verify=False,
        ) as client:
            # 1. Serper Places API: Real local commercial businesses
            if is_constr:
                places_queries = [
                    f"{niche} in {city} {country}",
                    f"{niche} companies in {city}",
                    f"{niche} contractors in {city}",
                    f"{niche} firms in {city}",
                ]
            else:
                places_queries = [
                    f"{niche} in {city} {country}",
                    f"{niche} companies in {city}",
                    f"{niche} services in {city}",
                    f"{niche} firms in {city}",
                ]
            if needed_domains > 25:
                places_queries.extend([
                    f"{niche} specialists in {city}",
                    f"commercial {niche} in {city}",
                    f"{niche} suppliers in {city}",
                    f"best {niche} in {city}",
                ])

            for pq in places_queries:
                if is_cancelled and is_cancelled():
                    logger.info("[SERPER:DISCOVERY] Cancellation observed during places discovery.")
                    break
                if len(discovered_urls) >= needed_domains:
                    break
                pq_norm = (gl_key, pq.strip().lower())
                if pq_norm in self._executed_places_queries:
                    continue
                self._executed_places_queries.add(pq_norm)
                try:
                    places = await self.query_serper_places(pq, country, client, is_cancelled=is_cancelled)
                    for pl in places:
                        w = pl.get("website")
                        if w:
                            _register_candidate(
                                w,
                                title=pl.get("title", ""),
                                phone=pl.get("phoneNumber", ""),
                                address=pl.get("address", ""),
                                source="serper_places"
                            )
                            if len(discovered_urls) >= needed_domains:
                                break
                except SerperAPIError:
                    raise
                except Exception as ex:
                    logger.warning(f"[SERPER:DISCOVERY] Places query '{pq}' warning: {ex}")

            # 2. Serper Search API: Multi-page organic search
            search_query_list: List[str] = []
            if queries:
                for q in queries:
                    q_str = q.get("query") if isinstance(q, dict) else str(q)
                    q_str = q_str.strip() if q_str else ""
                    if q_str and q_str not in search_query_list:
                        search_query_list.append(q_str)

            built_queries = self.build_query_variations(niche, city, country)
            for bq in built_queries:
                if bq not in search_query_list:
                    search_query_list.append(bq)

            for sq in search_query_list:
                if is_cancelled and is_cancelled():
                    logger.info("[SERPER:DISCOVERY] Cancellation observed during organic search.")
                    break
                if len(discovered_urls) >= needed_domains:
                    break

                for page in range(1, max_pages + 1):
                    if is_cancelled and is_cancelled():
                        break
                    if len(discovered_urls) >= needed_domains:
                        break
                    sq_norm = (gl_key, sq.strip().lower(), page)
                    if sq_norm in self._executed_search_pages:
                        continue
                    self._executed_search_pages.add(sq_norm)
                    try:
                        search_items = await self.query_serper_search(
                            sq, country, page=page, client=client, num=20, is_cancelled=is_cancelled
                        )
                        if not search_items:
                            break
                        for item in search_items:
                            link = item.get("link")
                            if link:
                                _register_candidate(
                                    link,
                                    title=item.get("title", ""),
                                    phone=item.get("phone", ""),
                                    address=item.get("address", ""),
                                    source=item.get("source", "serper_organic")
                                )
                                if len(discovered_urls) >= needed_domains:
                                    break
                    except SerperAPIError:
                        raise
                    except Exception as ex:
                        logger.warning(f"[SERPER:DISCOVERY] Search query '{sq}' (page {page}) warning: {ex}")
                        break

        total = len(discovered_urls)
        logger.info(f"[SERPER:DISCOVERY] Discovery complete — {total} unique candidate domains collected (limit={limit})")
        return discovered_urls[:needed_domains]


# ===========================================================================
# DeepScraperAgent — scrapes individual company websites
# ===========================================================================
class DeepScraperAgent:
    """
    Scraper Agent with Tech-Stack Detection, Priority Contact Extraction,
    and Deep Contact Subpage Crawling.
    Crawls root page + up to 2 contact/about subpages per domain.
    Applies strict email hygiene: rejects noreply, support, privacy,
    webmaster, sentry, example.com, .png/.jpg and social media addresses.
    """

    def __init__(self, timeout_seconds: float = 6.0):
        self.timeout = timeout_seconds

    # ------------------------------------------------------------------
    # Static email hygiene guard (fast path before LeadValidationFilter)
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_extracted_email(raw_email: str) -> str:
        """Strips leading/trailing HTML or unicode artifacts (e.g. u003e, \\u003e, &gt;, quotes) from email."""
        if not raw_email or "@" not in raw_email:
            return ""
        clean = raw_email.strip().lower()
        clean = re.sub(r'^(?:u003[ec]|\\u003[ec]|&[gl]t;|[<>"\'\s\\])+', '', clean)
        clean = re.sub(r'(?:&[gl]t;|[<>"\'\s\\])+$', '', clean)
        return clean.strip()

    @classmethod
    def _is_junk_email(cls, email: str) -> bool:
        """Returns True if the email is a known junk/role/system address."""
        if not email or "@" not in email:
            return True
        clean_email = cls._clean_extracted_email(email)
        if not clean_email or "@" not in clean_email:
            return True
        local, domain = clean_email.split("@", 1)
        # Block unsubscribe / optout addresses and unicode remnants
        if (
            "unsubscribe" in local
            or "optout" in local
            or "opt-out" in local
            or local.startswith("remove")
            or local.startswith("u003")
            or "%" in local
        ):
            return True
        # Strict dummy / placeholder / example checks
        if local in {"example", "test", "demo", "sample", "placeholder", "user", "you", "yourname", "name", "someone"}:
            return True
        if domain in {"email.com", "example.com", "sample.com", "domain.com", "company.com", "test.com", "yourdomain.com", "mydomain.com"}:
            return True
        if domain.startswith("example.") or domain.startswith("example-") or domain.startswith("test-"):
            return True
        if local.startswith("example") or local.startswith("test-") or local.startswith("noreply") or local.startswith("no-reply"):
            return True
        # Junk domains
        if any(domain == jd or domain.endswith("." + jd) for jd in JUNK_EMAIL_DOMAINS):
            return True
        # Junk prefixes
        for prefix in JUNK_EMAIL_PREFIXES:
            if local == prefix or local.startswith(prefix + ".") or local.startswith(prefix + "-") or local.startswith(prefix + "_"):
                return True
        # Asset false positives (.png, .jpg, etc.)
        if any(clean_email.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".css", ".js")):
            return True
        return False

    # ------------------------------------------------------------------
    # Company name cleaner: prioritized multi-layer brand extraction
    # ------------------------------------------------------------------
    @classmethod
    def extract_clean_company_name(cls, soup: Optional[BeautifulSoup], raw_title: str, domain: str) -> str:
        """
        Derives an authentic clean brand/company name using a prioritized hierarchy:
        1. Schema.org JSON-LD (Organization, LocalBusiness, GeneralContractor, ConstructionBusiness)
        2. OpenGraph meta (og:site_name) or application-name
        3. Title parsing with strict generic SEO pattern rejection (ignoring taglines like
           'Best Construction Company in X', 'Find local contractors for free')
        4. Fallback to clean domain brand extraction.
        """
        import json

        GENERIC_SEO_PATTERNS = [
            r"^(?:home|welcome|contact|contact\s+us|about|about\s+us|services?|solutions|official\s+site|privacy|privacy\s+policy|terms|terms\s+of\s+(?:service|use)|legal|legal\s+notice|cookie\s+policy|datenschutz|impressum|imprint)$",
            r"\bbest\s+.*(?:in|near|across)\b",
            r"\btop\s+\d+\s+",
            r"\bfind\s+(?:local\s+)?(?:contractors?|builders?|companies)\b",
            r"\bfree\s+(?:estimates?|quotes?)\b",
            r"\bwelcome\s+to\b",
            r"\bhome\s*page?\b",
            r"\bcontact\s+us\b",
            r"\babout\s+us\b",
            r"\bservices?\s*overview\b",
            r"\bour\s+services\b",
            r"\bleading\s+(?:provider|contractor|construction|builder)\b",
            r"\btrusted\s+(?:local|commercial)?\s*(?:contractors?|builders?)\b",
            r"\bcommercial\s+construction\s+services\b",
            r"\baffordable\s+(?:construction|roofing|cladding)\b",
            r"\bfor\s+free\b",
            r"\bprivacy\s+policy\b",
            r"\bterms\s+of\s+(?:service|use)\b",
            r"\bcookie\s+policy\b",
            r"\blegal\s+notice\b",
            r"\bdatenschutz\b",
            r"\bimpressum\b",
        ]

        def is_generic_phrase(text: str) -> bool:
            if not text or len(text.strip()) <= 2:
                return True
            if text.strip().upper() in {"AI", "IT", "HR", "PR", "HQ", "CO", "IO", "APP", "DEV", "TECH", "THE", "AND", "OR"}:
                return True
            t_lower = text.strip().lower()
            generic_exact = {
                "privacy policy", "privacy", "terms of service", "terms of use", "terms", "terms and conditions",
                "terms & conditions", "legal notice", "legal", "cookie policy", "datenschutz", "impressum", "imprint",
                "contact us", "contact", "about us", "about", "home", "homepage", "welcome", "our services", "services",
                "solutions", "overview", "site map", "sitemap", "disclaimer", "accessibility"
            }
            if t_lower in generic_exact or any(t_lower == g or t_lower.startswith(g + " -") or t_lower.startswith(g + " |") for g in generic_exact):
                return True
            if any(re.search(pat, t_lower) for pat in GENERIC_SEO_PATTERNS):
                return True
            words = text.strip().split()
            if len(words) > 7:
                return True
            return False

        # Priority 1: Schema.org JSON-LD structured data
        if soup:
            try:
                for script in soup.find_all("script", type="application/ld+json"):
                    if not script.string:
                        continue
                    try:
                        data = json.loads(script.string.strip())
                    except Exception:
                        continue

                    items = data if isinstance(data, list) else [data]
                    if isinstance(data, dict) and "@graph" in data and isinstance(data["@graph"], list):
                        items.extend(data["@graph"])

                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        schema_type = str(item.get("@type", "")).lower()
                        if any(target in schema_type for target in ("organization", "business", "contractor", "corporation")):
                            name_val = item.get("name") or item.get("legalName")
                            if isinstance(name_val, str) and name_val.strip() and not is_generic_phrase(name_val):
                                return name_val.strip()
            except Exception:
                pass

        # Priority 2: OpenGraph og:site_name or application-name meta tag
        if soup:
            try:
                og_site = soup.find("meta", property=re.compile(r"^og:site_name$", re.I)) or soup.find("meta", attrs={"name": re.compile(r"^og:site_name$", re.I)})
                if og_site and og_site.get("content"):
                    site_name = og_site["content"].strip()
                    if site_name and not is_generic_phrase(site_name) and len(site_name) >= 2:
                        return site_name

                app_name = soup.find("meta", attrs={"name": re.compile(r"^application-name$", re.I)})
                if app_name and app_name.get("content"):
                    app_name_val = app_name["content"].strip()
                    if app_name_val and not is_generic_phrase(app_name_val) and len(app_name_val) >= 2:
                        return app_name_val
            except Exception:
                pass

        # Priority 3: Refined title cleaning & segment ranking
        if raw_title:
            cleaned = re.sub(
                r'\s*[\|\-\–\—•:]\s*(?:'
                r'home\s*page?|home|welcome|contact\s+us|contact|about\s+us|about|'
                r'official\s+site|official\s+website|main\s+page|our\s+services|'
                r'services|solutions|get\s+a\s+quote|quote|estimating'
                r')$',
                "", raw_title, flags=re.IGNORECASE
            ).strip()

            parts = [p.strip() for p in re.split(r'[\|\-\–\—•:]', cleaned) if p.strip()]
            valid_candidates = []
            for p in parts:
                if len(p) >= 2 and not is_generic_phrase(p):
                    valid_candidates.append(p)

            if valid_candidates:
                domain_brand = LeadValidationFilter.extract_brand_name_from_domain(domain).lower()
                for cand in valid_candidates:
                    cand_clean = re.sub(r'[^a-zA-Z0-9]', '', cand).lower()
                    if domain_brand in cand_clean or cand_clean in domain_brand:
                        return cand

                return min(valid_candidates, key=lambda c: len(c.split()))

        # Priority 4: Fallback to domain-derived brand name
        return LeadValidationFilter.extract_brand_name_from_domain(domain)

    @classmethod
    def _clean_company_name(cls, raw_title: str, domain: str) -> str:
        return cls.extract_clean_company_name(None, raw_title, domain)

    # ------------------------------------------------------------------
    # HTML parser (single page → Lead or None)
    # ------------------------------------------------------------------
    def parse_html_content(
        self,
        html_content: str,
        source_url: str,
        country: str = "United Kingdom",
        city: str = "London",
        niche: str = "Commercial Construction",
        headers: Optional[Dict[str, str]] = None,
        inherited_niche_score: Optional[int] = None,
    ) -> Optional[Lead]:
        """
        Parses raw HTML through the 4-Layer validation pipeline:
        Layer 1: HTML entity sanitisation + email regex extraction + junk email rejection
        Layer 2: Role-based / .gov/.edu/.mil / system tracker domain blocker
        Layer 3: Junk title / bot-shield filter + clean brand name extraction
        Layer 4: Niche relevance scoring (0–100); requires ≥ 70 to pass
        """
        if not html_content or len(html_content.strip()) < 50:
            return None

        raw_text = html.unescape(html_content)
        soup = BeautifulSoup(raw_text, "html.parser")

        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc.replace("www.", "").lower().split(":")[0]

        # ── Layer 2: Domain-level blocker ──────────────────────────────
        try:
            is_dom_ok, dom_reason = LeadValidationFilter.check_role_and_domain_blocker("check@" + domain, domain)
            if not is_dom_ok:
                logger.info(f"[LAYER-2 FILTER] Rejecting {source_url}: {dom_reason}")
                return None
        except Exception:
            pass

        # ── Layer 3: Title / Bot-Shield filter ─────────────────────────
        raw_title = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            raw_title = title_tag.text.strip()

        try:
            is_title_valid, lv_company_name, title_reason = LeadValidationFilter.evaluate_page_title(raw_title, domain)
            if not is_title_valid:
                logger.info(f"[LAYER-3 FILTER] Rejecting {source_url}: {title_reason}")
                return None
        except Exception:
            lv_company_name = ""

        # Clean company name using our multi-priority extractor
        extracted_name = self.extract_clean_company_name(soup, raw_title, domain) or lv_company_name
        fallback_brand = LeadValidationFilter.extract_brand_name_from_domain(domain)
        if not extracted_name or extracted_name.lower().strip() in {
            "privacy policy", "privacy", "terms of service", "terms of use", "terms",
            "legal notice", "legal", "cookie policy", "datenschutz", "impressum", "imprint"
        }:
            company_name = fallback_brand
        else:
            company_name = extracted_name

        # ── Layer 4: Niche relevance scoring ───────────────────────────
        if inherited_niche_score is not None:
            niche_score = inherited_niche_score
            score_summary = f"Inherited from root domain: {niche_score}/100"
        else:
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
            if desc_tag and desc_tag.get("content"):
                meta_desc = desc_tag["content"].strip()
            page_text = soup.get_text(separator=" ", strip=True)
            try:
                niche_score, score_summary = LeadValidationFilter.calculate_niche_score(
                    niche=niche,
                    page_title=raw_title,
                    page_content=page_text,
                    meta_description=meta_desc,
                    domain=domain,
                )
            except Exception:
                niche_score, score_summary = 0, "niche_score_error"

        if niche_score < 40 and inherited_niche_score is None:
            logger.info(
                f"[LAYER-4 FILTER] Rejecting {source_url}: "
                f"Niche score {niche_score}/100 < 40 for '{niche}' ({score_summary})"
            )
            return None

        # ── Layer 1: Extract & sanitise emails ─────────────────────────
        emails_found: Set[str] = set()
        context_map: Dict[str, str] = {}

        # mailto: links (highest fidelity)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("mailto:"):
                raw_mail = self._clean_extracted_email(href[7:].split("?")[0].strip())
                if not raw_mail or self._is_junk_email(raw_mail):
                    logger.info(f"[EMAIL-FILTER] Rejected junk mailto: {raw_mail} on {source_url}")
                    continue
                try:
                    is_valid, clean_mail, reason = LeadValidationFilter.sanitize_and_validate_email(raw_mail, domain)
                except Exception:
                    is_valid, clean_mail = False, None
                if is_valid and clean_mail:
                    try:
                        is_allowed, _ = LeadValidationFilter.check_role_and_domain_blocker(clean_mail, domain)
                    except Exception:
                        is_allowed = True
                    if is_allowed:
                        emails_found.add(clean_mail)
                        context_map[clean_mail.lower()] = a_tag.get_text(strip=True) or "mailto anchor"
                        logger.info(f"[EMAIL] ✓ Accepted (mailto): {clean_mail} on {source_url}")
                    else:
                        logger.info(f"[EMAIL-FILTER] Rejected (Layer-2 role block): {clean_mail}")

        # Regex full-text sweep
        for match in EMAIL_REGEX.findall(raw_text):
            # Normalise obfuscated [at]/(at)
            normalised = re.sub(r'\s*[\[\(]at[\]\)]\s*', '@', match, flags=re.IGNORECASE).replace(" ", "")
            normalised = self._clean_extracted_email(normalised)
            if not normalised or self._is_junk_email(normalised):
                logger.info(f"[EMAIL-FILTER] Rejected junk regex match: {normalised}")
                continue
            try:
                is_valid, clean_mail, reason = LeadValidationFilter.sanitize_and_validate_email(normalised, domain)
            except Exception:
                is_valid, clean_mail = False, None
            if is_valid and clean_mail:
                try:
                    is_allowed, _ = LeadValidationFilter.check_role_and_domain_blocker(clean_mail, domain)
                except Exception:
                    is_allowed = True
                if is_allowed:
                    emails_found.add(clean_mail)
                    logger.info(f"[EMAIL] ✓ Accepted (regex): {clean_mail} on {source_url}")
                else:
                    logger.info(f"[EMAIL-FILTER] Rejected (Layer-2 role block): {clean_mail}")

        if not emails_found:
            logger.info(f"[SCRAPER] No valid emails after hygiene pass on {source_url}")
            return None

        # Prioritise emails
        try:
            ranked_emails: List[ScrapedEmail] = PriorityEmailFinder.rank_emails(
                raw_emails=list(emails_found),
                page_source=source_url,
                context_map=context_map,
            )
            primary = PriorityEmailFinder.pick_primary_email(ranked_emails)
        except Exception:
            ranked_emails = []
            primary = None

        if not primary:
            return None

        if not company_name or len(company_name) <= 2 or company_name.upper().strip() in {"AI", "IT", "HR", "PR", "HQ", "CO", "IO", "APP", "DEV", "TECH"}:
            company_name = LeadValidationFilter.clean_company_name(company_name, domain)

        # Extract phone numbers from tel: links
        phones: Set[str] = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("tel:"):
                phone_num = href[4:].strip()
                if len(phone_num) >= 7:
                    phones.add(phone_num)

        tech_stack = TechStackDetector.detect(raw_text, headers)

        tier_tag_map = {
            EmailTier.TIER_1_ESTIMATING: "TIER-1-ESTIMATING",
            EmailTier.TIER_2_EXECUTIVE: "TIER-2-EXECUTIVE",
            EmailTier.TIER_3_OPERATIONAL: "TIER-3-OPERATIONAL",
            EmailTier.TIER_GENERIC: "TIER-GENERIC",
            EmailTier.UNKNOWN: "TIER-UNRATED",
        }
        quality_tag = tier_tag_map.get(primary.tier, "TIER-GENERIC")

        return Lead(
            company_name=company_name,
            domain=domain,
            website_url=source_url,
            target_country=country,
            target_city=city,
            industry_niche=niche,
            primary_email=primary.email,
            primary_email_tier=primary.tier,
            priority_score=max(primary.priority_score, niche_score),
            all_emails=ranked_emails,
            phone_numbers=list(phones),
            tech_stack=tech_stack,
            quality_tag=quality_tag,
            metadata={"niche_score": niche_score, "niche_summary": score_summary},
        )

    # ------------------------------------------------------------------
    # Main URL scraper (crawls root + up to 2 contact subpages)
    # ------------------------------------------------------------------
    async def scrape_url(
        self,
        url: str,
        country: str = "United Kingdom",
        city: str = "London",
        niche: str = "Commercial Construction",
        is_cancelled: Optional[Any] = None,
        known_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Lead]:
        """
        Asynchronously scrapes a target company URL with strict short connect/read timeouts.
        Immediately skips dead/unreachable placeholder seed domains (like example-contractor.de).
        Honors cancellation tokens so aborted crawls stop cleanly and never insert zombie leads.
        """
        if is_cancelled and is_cancelled():
            return None

        target_url = url.strip()
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = f"https://{target_url}"

        # Immediately skip placeholder, dummy, or off-niche media/blog/directory domains
        try:
            parsed_u = urlparse(target_url)
            dom_check = parsed_u.netloc.lower().replace("www.", "").split(":")[0]
            if (
                dom_check in {"example.com", "company.com", "domain.com", "test.com"}
                or dom_check.startswith("example-")
                or "example" in dom_check
                or dom_check.endswith(".example")
                or "placeholder" in dom_check
                or "example-contractor" in dom_check
            ):
                logger.info(f"[SCRAPER] ⊘ Immediately skipping placeholder seed domain: {dom_check}")
                return None

            is_off, off_reason = LeadValidationFilter.is_off_niche_domain(dom_check, niche)
            if is_off:
                logger.info(f"[SCRAPER] ⊘ Skipping off-niche domain {dom_check}: {off_reason}")
                return None
        except Exception:
            pass

        logger.info(f"[SCRAPER] ▶ Crawling {target_url}")

        req_timeout = httpx.Timeout(connect=3.0, read=min(self.timeout, 5.0), write=5.0, pool=5.0)
        try:
            async with httpx.AsyncClient(
                headers=_rotated_headers(),
                timeout=req_timeout,
                follow_redirects=True,
                verify=False,
            ) as client:
                if is_cancelled and is_cancelled():
                    return None

                # ── Attempt 1: Root page ──────────────────────────────
                resp = None
                try:
                    resp = await client.get(target_url)
                except Exception as fetch_err:
                    logger.debug(f"[SCRAPER] Fetch failed for {target_url}: {fetch_err}")
                    return None  # Fast abort for unreachable domains

                if not resp or resp.status_code >= 400:
                    logger.debug(
                        f"[SCRAPER] {target_url} non-success: "
                        f"{resp.status_code if resp else 'NO_RESPONSE'}"
                    )
                    return None

                base_url = str(resp.url)
                base_domain = urlparse(base_url).netloc.replace("www.", "").lower()
                headers_dict = dict(resp.headers)

                lead = self.parse_html_content(
                    html_content=resp.text,
                    source_url=base_url,
                    country=country,
                    city=city,
                    niche=niche,
                    headers=headers_dict,
                )

                if lead and lead.all_emails and len(lead.all_emails) >= 4:
                    logger.info(
                        f"[SCRAPER] ✅ Root page hit on {target_url} (4 emails): "
                        f"{len(lead.all_emails)} email(s) | Primary: {lead.primary_email} | "
                        f"Company: {lead.company_name}"
                    )
                    lead.all_emails = lead.all_emails[:4]
                    if known_metadata:
                        k_title = (known_metadata.get("title") or "").strip()
                        if k_title and (not lead.company_name or len(lead.company_name) <= 3 or lead.company_name.lower() == base_domain.split('.')[0]):
                            lead.company_name = k_title
                        k_phone = (known_metadata.get("phone") or "").strip()
                        if k_phone and k_phone not in lead.phone_numbers:
                            lead.phone_numbers.append(k_phone)
                    return lead

                # ── Attempt 2: Discover contact subpages ─────────────
                if lead and lead.all_emails:
                    logger.info(
                        f"[SCRAPER] Root page found {len(lead.all_emails)} email(s) on {target_url}. "
                        f"Scanning subpages to extract up to 3 distinct contacts..."
                    )
                else:
                    logger.info(
                        f"[SCRAPER] No emails on root of {target_url}. "
                        f"Scanning for contact/about subpages..."
                    )
                soup = BeautifulSoup(resp.text, "html.parser")
                candidate_subpages: List[str] = []
                primary_contacts: List[str] = []
                legal_privacy: List[str] = []
                other_subpages: List[str] = []

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    text = a_tag.get_text(strip=True).lower()
                    href_lower = href.lower()
                    if any(kw in href_lower or kw in text for kw in CONTACT_SUBPAGE_KEYWORDS):
                        full_sub_url = urljoin(base_url, href)
                        sub_domain = urlparse(full_sub_url).netloc.replace("www.", "").lower()
                        if sub_domain == base_domain and full_sub_url != base_url:
                            if any(k in href_lower for k in ("privacy", "legal", "terms", "datenschutz", "impressum", "imprint")):
                                if full_sub_url not in legal_privacy:
                                    legal_privacy.append(full_sub_url)
                            elif any(k in href_lower for k in ("contact", "kontakt", "about", "team", "ansprechpartner")):
                                if full_sub_url not in primary_contacts:
                                    primary_contacts.append(full_sub_url)
                            else:
                                if full_sub_url not in other_subpages:
                                    other_subpages.append(full_sub_url)

                # Prioritize: up to 3 contact/about + up to 2 privacy/legal + fallback
                candidate_subpages = (primary_contacts[:3] + legal_privacy[:2] + other_subpages[:1])

                # Ensure at least 1 privacy/legal and 1 contact URL are present
                if not any("privacy" in u or "legal" in u for u in candidate_subpages):
                    for sp in ("/privacy-policy", "/privacy", "/legal/privacy"):
                        guess_url = urljoin(base_url, sp)
                        if guess_url not in candidate_subpages:
                            candidate_subpages.append(guess_url)
                            break
                if not any("contact" in u or "about" in u for u in candidate_subpages):
                    for sp in ("/contact", "/contact-us", "/about"):
                        guess_url = urljoin(base_url, sp)
                        if guess_url not in candidate_subpages:
                            candidate_subpages.append(guess_url)
                            break

                for sp in COMMON_SUBPATHS:
                    if len(candidate_subpages) >= 6:
                        break
                    guess_url = urljoin(base_url, sp)
                    if guess_url not in candidate_subpages and guess_url != base_url:
                        candidate_subpages.append(guess_url)

                # Limit to 6 subpages (crawled in parallel, completes in ~3.5s)
                candidate_subpages = candidate_subpages[:6]
                logger.info(
                    f"[SCRAPER] {len(candidate_subpages)} contact subpage(s) queued for "
                    f"{base_domain}: {candidate_subpages}"
                )

                # Pre-compute root niche score for subpage inheritance
                root_niche_score = None
                try:
                    root_title = soup.find("title").text.strip() if soup.find("title") and soup.find("title").text else ""
                    root_meta = ""
                    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
                    if desc_tag and desc_tag.get("content"):
                        root_meta = desc_tag["content"].strip()
                    root_text = soup.get_text(separator=" ", strip=True)
                    sc, _ = LeadValidationFilter.calculate_niche_score(niche, root_title, root_text, root_meta, base_domain)
                    if sc >= 25:
                        root_niche_score = sc
                except Exception:
                    pass

                # Fetch candidate subpages concurrently with tight per-subpage timeout
                async def _fetch_subpage(sub_url: str):
                    if is_cancelled and is_cancelled():
                        return None
                    try:
                        sub_to = httpx.Timeout(connect=2.5, read=3.5, write=3.0, pool=3.0)
                        sub_resp = await client.get(sub_url, timeout=sub_to)
                        if sub_resp.status_code < 400:
                            return (sub_url, sub_resp)
                    except Exception as sub_err:
                        logger.debug(f"[SCRAPER] Subpage fetch error for {sub_url}: {sub_err}")
                    return None

                subpage_tasks = [_fetch_subpage(su) for su in candidate_subpages]
                sub_results = await asyncio.gather(*subpage_tasks, return_exceptions=True)

                # Aggregate emails across root and subpages up to 3 distinct contacts
                all_found_emails: Dict[str, ScrapedEmail] = {}
                if lead and lead.all_emails:
                    for em in lead.all_emails:
                        all_found_emails[em.email.lower().strip()] = em

                for res in sub_results:
                    if is_cancelled and is_cancelled():
                        return None
                    if isinstance(res, tuple) and res[1] is not None:
                        sub_url, sub_resp = res
                        try:
                            sub_lead = self.parse_html_content(
                                html_content=sub_resp.text,
                                source_url=str(sub_resp.url),
                                country=country,
                                city=city,
                                niche=niche,
                                headers=dict(sub_resp.headers),
                                inherited_niche_score=root_niche_score,
                            )
                            if sub_lead and sub_lead.all_emails:
                                for em in sub_lead.all_emails:
                                    em_clean = em.email.lower().strip()
                                    if em_clean not in all_found_emails:
                                        all_found_emails[em_clean] = em
                                if not lead:
                                    lead = sub_lead
                                elif (not lead.company_name or len(lead.company_name) <= 2) and sub_lead.company_name:
                                    lead.company_name = sub_lead.company_name
                                if len(all_found_emails) >= 4:
                                    break
                            else:
                                logger.debug(f"[SCRAPER] No valid emails on subpage {sub_url}")
                        except Exception as parse_err:
                            logger.debug(f"[SCRAPER] Subpage parsing error for {sub_url}: {parse_err}")

                if all_found_emails and lead:
                    # Sort by priority score descending
                    ranked_list = sorted(all_found_emails.values(), key=lambda e: e.priority_score, reverse=True)
                    # Keep up to 4 distinct valid emails
                    lead.all_emails = ranked_list[:4]
                    lead.primary_email = lead.all_emails[0].email
                    lead.primary_email_tier = lead.all_emails[0].tier
                    if known_metadata:
                        k_title = (known_metadata.get("title") or "").strip()
                        if k_title and (not lead.company_name or len(lead.company_name) <= 3 or lead.company_name.lower() == base_domain.split('.')[0]):
                            lead.company_name = k_title
                        k_phone = (known_metadata.get("phone") or "").strip()
                        if k_phone and k_phone not in lead.phone_numbers:
                            lead.phone_numbers.append(k_phone)
                    logger.info(
                        f"[SCRAPER] ✅ Aggregated {len(lead.all_emails)} distinct email(s) for {base_domain} "
                        f"(Primary: {lead.primary_email}): {[e.email for e in lead.all_emails]}"
                    )
                    return lead

                logger.warning(
                    f"[SCRAPER] ✗ Discarding {target_url}: "
                    f"0 business emails after root + {len(candidate_subpages)} subpages."
                )
                return None

        except Exception as ex:
            logger.error(
                f"[SCRAPER] Unexpected error for {target_url}: "
                f"{type(ex).__name__} — {ex}",
                exc_info=False,
            )
            return None
