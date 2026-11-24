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
import re
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import httpx

from ..models import Lead, TechStack, EmailTier, ScrapedEmail
from .priority_finder import PriorityEmailFinder
from core.hygiene.lead_validator import LeadValidationFilter

logger = logging.getLogger("nexus.scraper")

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
# SearchDiscoveryAgent — Multi-Provider, Cloud-Resilient
# ===========================================================================
class SearchDiscoveryAgent:
    """
    Autonomous B2B Search Discovery Engine with cascading 3-provider fallback.

    Provider 1 (Primary):   ddgs / duckduckgo-search Python library
                            Uses DDGS().text() with backend='lite', then 'html'.
                            Works well from Railway datacenters — library handles
                            cookies and anti-bot measures internally.
    Provider 2 (Secondary): Bing HTML scraper with base64 redirect unpack.
    Provider 3 (Tertiary):  DuckDuckGo Lite HTTP POST (legacy, unchanged).

    Each provider is tried per query; we stop once we have enough unique URLs.
    All providers share the same sanitization and discard logic.
    Full logging is emitted at every step for Railway Deploy Log visibility.
    """

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds

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
        """
        Sanitises query for direct HTTP search engines.
        Strips nested quotes, boolean OR, and site: operators that
        cause many search engines to return 0 results.
        DDGS library handles these operators natively, so we only sanitise
        for Bing/DDG-Lite HTTP paths.
        """
        cleaned = re.sub(r'["()]', '', query)
        cleaned = re.sub(r'\bOR\b', '', cleaned)
        cleaned = re.sub(r'site:\S+', '', cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned

    # ------------------------------------------------------------------
    # Provider 1: DDGS library (ddgs / duckduckgo-search)
    # ------------------------------------------------------------------
    def _ddgs_search(self, query: str, max_results: int = 15) -> List[str]:
        """
        Runs a synchronous DDGS text search with lite→html backend fallback.
        Returns list of raw result URLs (before clean_candidate_url).
        """
        if _DDGS is None:
            logger.warning("[PROVIDER-1 DDGS] Library not installed — skipping")
            return []

        urls: List[str] = []
        for backend in ("api", "html", "lite"):
            try:
                logger.info(f"[PROVIDER-1 DDGS] backend='{backend}' query='{query}'")
                with _DDGS(timeout=int(self.timeout)) as ddgs_client:
                    results = list(ddgs_client.text(query, max_results=max_results, backend=backend, safesearch="on"))
                logger.info(f"[PROVIDER-1 DDGS] backend='{backend}' returned {len(results)} raw results")
                for r in results:
                    href = r.get("href") or r.get("link") or ""
                    if href:
                        urls.append(href)
                if urls:
                    logger.info(f"[PROVIDER-1 DDGS] backend='{backend}' succeeded: {len(urls)} candidate URLs")
                    return urls
            except Exception as ex:
                logger.debug(f"[PROVIDER-1 DDGS] backend='{backend}' exception: {ex}")

        return []

    # ------------------------------------------------------------------
    # Provider 2: Bing HTML Scraper (multi-page async pagination)
    # ------------------------------------------------------------------
    async def _bing_search(self, query: str, client: httpx.AsyncClient, max_results: int = 30) -> List[str]:
        """
        Performs a Bing web search and extracts organic result URLs across multiple pages.
        Handles Bing's base64-encoded redirect links (/ck/a?!).
        """
        clean_q = self.sanitize_search_query(query)
        urls: List[str] = []
        page_offsets = [1, 11, 21, 31][:max(1, min((max_results + 9) // 10, 4))]

        for first_offset in page_offsets:
            try:
                resp = await client.get(
                    "https://www.bing.com/search",
                    params={"q": clean_q, "first": str(first_offset), "setlang": "en", "adlt": "strict"},
                )
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                selectors = [
                    "li.b_algo h2 a",
                    "li.b_algo .b_title a",
                    "li.b_algo .b_algoheader a",
                    "li.b_algo h3 a",
                ]
                page_found = 0
                for sel in selectors:
                    anchors = soup.select(sel)
                    for a in anchors:
                        href = a.get("href", "").strip()
                        if href and href not in urls:
                            urls.append(href)
                            page_found += 1
                    if page_found >= 10:
                        break

                if page_found == 0:
                    break
            except Exception as ex:
                logger.debug(f"[PROVIDER-2 BING] offset={first_offset} exception: {ex}")
                break

        logger.info(f"[PROVIDER-2 BING] Extracted {len(urls)} raw anchors for '{clean_q}'")
        return urls

    # ------------------------------------------------------------------
    # Provider 3: Yahoo Search HTML (async)
    # ------------------------------------------------------------------
    async def _yahoo_search(self, query: str, client: httpx.AsyncClient, max_results: int = 20) -> List[str]:
        """Performs a Yahoo search and extracts organic result URLs."""
        clean_q = self.sanitize_search_query(query)
        urls: List[str] = []
        try:
            resp = await client.get(
                "https://search.yahoo.com/search",
                params={"p": clean_q, "n": str(max_results)},
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                selectors = [
                    "div.compTitle h3 a",
                    "ol.searchCenterMiddle li h3 a",
                    "div.algo h3 a",
                    "h3.title a",
                ]
                for sel in selectors:
                    anchors = soup.select(sel)
                    for a in anchors:
                        href = a.get("href", "").strip()
                        if href and href not in urls:
                            urls.append(href)
                logger.info(f"[PROVIDER-3 YAHOO] Extracted {len(urls)} raw anchors for '{clean_q}'")
        except Exception as ex:
            logger.debug(f"[PROVIDER-3 YAHOO] Exception: {ex}")
        return urls

    # ------------------------------------------------------------------
    # Provider 4: Brave Search HTML (async)
    # ------------------------------------------------------------------
    async def _brave_search(self, query: str, client: httpx.AsyncClient, max_results: int = 20) -> List[str]:
        """Performs a Brave web search and extracts organic result URLs."""
        clean_q = self.sanitize_search_query(query)
        urls: List[str] = []
        try:
            resp = await client.get(
                "https://search.brave.com/search",
                params={"q": clean_q, "source": "web"},
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                selectors = [
                    "a.heading-link",
                    "a.snippet",
                    "div.snippet a[href^='http']",
                    "a[data-test-id='result-link']",
                ]
                for sel in selectors:
                    anchors = soup.select(sel)
                    for a in anchors:
                        href = a.get("href", "").strip()
                        if href and href not in urls:
                            urls.append(href)
                logger.info(f"[PROVIDER-4 BRAVE] Extracted {len(urls)} raw anchors for '{clean_q}'")
        except Exception as ex:
            logger.debug(f"[PROVIDER-4 BRAVE] Exception: {ex}")
        return urls

    # ------------------------------------------------------------------
    # Provider 5: DuckDuckGo Lite HTTP POST (legacy, async)
    # ------------------------------------------------------------------
    async def _ddg_lite_post(self, query: str, client: httpx.AsyncClient) -> List[str]:
        """Legacy DDG Lite POST fallback (useful backup)."""
        clean_q = self.sanitize_search_query(query)
        urls: List[str] = []
        try:
            resp = await client.post("https://lite.duckduckgo.com/lite/", data={"q": clean_q})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a_tag in soup.select(".result-link"):
                    href = a_tag.get("href", "")
                    if href and href not in urls:
                        urls.append(href)
                logger.info(f"[PROVIDER-5 DDG-LITE] Returned {len(urls)} raw links for '{clean_q}'")
        except Exception as ex:
            logger.debug(f"[PROVIDER-5 DDG-LITE] Exception: {ex}")
        return urls

    # ------------------------------------------------------------------
    # Query variation generator for a niche+city pair
    # ------------------------------------------------------------------
    @staticmethod
    def build_query_variations(niche: str, city: str, country: str) -> List[str]:
        """
        Generates diverse query variations designed to surface real B2B company
        contact pages rather than directories, blogs, or social networks.
        Dynamically adapts between construction-specific and universal multi-niche commercial queries.

        CLOUD-DATACENTER STRATEGY: Broad, unquoted queries are listed FIRST because
        heavily-quoted queries consistently fail on Railway/cloud IPs (Bing/DDGS filter them).
        Quoted/precise variations are added afterward as supplementary depth queries.
        """
        n = niche.strip()
        c = city.strip()
        n_lower = n.lower()
        construction_keywords = (
            "construction", "contractor", "hochbau", "tiefbau", "bâtiment",
            "building", "roofing", "mep", "tga", "civil", "infrastructure",
            "architecture", "architect", "engineering", "plumbing", "electrical",
            "bauunternehmen", "travaux", "edificación", "general contractors"
        )
        is_construction = any(ck in n_lower for ck in construction_keywords)

        if is_construction:
            return [
                # Cloud-friendly broad queries FIRST (no heavy quoting)
                f"{n} companies {c} contact email",
                f"{n} contractors {c} email",
                f"{n} {c} company website contact",
                f"{n} general contractors {c} contact email",
                f'{n} {c} "contact us" email',
                # Deeper quoted variations
                f'"{n}" "{c}" "estimating" OR "tenders" contact email',
                f'"{n}" contractors "{c}" contact email',
                f'"{n}" firms "{c}" contact phone email',
                f'{n} company "{c}" "{country}" contact',
                f'"{n}" suppliers "{c}" "{country}" email',
            ]
        else:
            return [
                # Cloud-friendly broad queries FIRST (no heavy quoting — works on cloud IPs)
                f"{n} companies {c} contact email",
                f"{n} {c} company email",
                f"{n} {c} contact us",
                f"{n} agency {c} email contact",
                f"{n} software {c} company contact",
                f"{n} {c} {country} company website",
                f"{n} {c} business email info",
                # Quoted variations for deeper recall
                f'"{n}" "{c}" contact email',
                f'"{n}" "{c}" "contact us" email',
                f'"{n}" agency OR company OR firm "{c}" email',
                f'"{n}" "{c}" inurl:contact',
                f'"{n}" "{c}" ("inquiries" OR "office") email',
                f'"{n}" "{c}" official website contact',
                f'"{n}" "{c}" "info@" OR "contact@"',
                f'"{n}" specialists "{c}" contact phone',
            ]

    # ------------------------------------------------------------------
    # GitHub Org Discovery — works from cloud datacenter IPs (60 req/hr)
    # ------------------------------------------------------------------
    async def _github_org_search(self, city: str, niche: str, max_results: int = 20) -> List[str]:
        """
        Queries the GitHub public search API for organisations located in the target city.
        GitHub does NOT block cloud/datacenter IPs and requires no auth (60 req/hr limit).
        Returns a list of company website URLs harvested from GitHub org profiles.
        """
        urls: List[str] = []
        queries = [
            f'location:"{city}" type:org {niche}',
            f'location:"{city}" type:org',
        ]
        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": "NexusPulse/2.0", "Accept": "application/vnd.github+json"},
                timeout=10.0,
                verify=False,
                follow_redirects=True,
            ) as gh_client:
                for q in queries:
                    if len(urls) >= max_results:
                        break
                    try:
                        r = await gh_client.get(
                            "https://api.github.com/search/users",
                            params={"q": q, "per_page": min(max_results, 30), "type": "org"},
                        )
                        logger.info(f"[GITHUB-DISCOVERY] query='{q}' status={r.status_code}")
                        if r.status_code != 200:
                            continue
                        items = r.json().get("items", [])
                        for item in items:
                            if len(urls) >= max_results:
                                break
                            login = item.get("login", "")
                            if not login:
                                continue
                            try:
                                r2 = await gh_client.get(f"https://api.github.com/users/{login}", timeout=5.0)
                                if r2.status_code == 200:
                                    profile = r2.json()
                                    blog = (profile.get("blog") or "").strip()
                                    if blog and not blog.startswith("http"):
                                        blog = f"https://{blog}"
                                    if blog and blog.startswith("http"):
                                        urls.append(blog)
                                        logger.info(f"[GITHUB-DISCOVERY] ✓ {login} → {blog}")
                            except Exception as _gh_user_ex:
                                logger.debug(f"[GITHUB-DISCOVERY] User fetch error for {login}: {_gh_user_ex}")
                    except Exception as _gh_q_ex:
                        logger.debug(f"[GITHUB-DISCOVERY] Query error '{q}': {_gh_q_ex}")
        except Exception as _gh_ex:
            logger.debug(f"[GITHUB-DISCOVERY] Session error: {_gh_ex}")
        logger.info(f"[GITHUB-DISCOVERY] Harvested {len(urls)} org website URLs for city='{city}' niche='{niche}'")
        return urls

    # ------------------------------------------------------------------
    # Main discovery entry point (Parallel Multi-Source)
    # ------------------------------------------------------------------
    async def discover_candidate_urls(
        self,
        queries: List[Dict[str, str]],
        limit: int = 20,
        country: str = "United Kingdom",
        city: str = "London",
        niche: str = "Commercial Construction",
        excluded_domains: Optional[Set[str]] = None,
        is_cancelled: Optional[Any] = None,
    ) -> List[str]:
        """
        Runs the parallel multi-source search pipeline across Bing, DDGS, Yahoo, Brave, and DDG-Lite,
        returning up to `limit` unique company root-domain URLs, automatically excluding already
        captured/seen domains.
        """
        discovered_urls: List[str] = []
        seen_domains: Set[str] = set()
        excluded: Set[str] = {d.strip().lower() for d in (excluded_domains or set()) if d}

        if is_cancelled and is_cancelled():
            logger.info("[DISCOVERY] Cancellation signal observed before start — aborting discovery.")
            return []

        # Build the full query list: existing localised queries first, then
        # add our own commercial intent variations as extra fallback queries.
        all_queries: List[str] = []
        for q_item in queries:
            if isinstance(q_item, dict):
                raw_q = q_item.get("query", "")
            elif isinstance(q_item, str):
                raw_q = q_item.strip()
            else:
                raw_q = str(q_item).strip()
            if raw_q and raw_q not in all_queries:
                all_queries.append(raw_q)

        variation_queries = self.build_query_variations(niche, city, country)
        for vq in variation_queries:
            if vq not in all_queries:
                all_queries.append(vq)

        logger.info(
            f"[DISCOVERY] Starting multi-source parallel search | niche='{niche}' | city='{city}' "
            f"| country='{country}' | queries={len(all_queries)} | limit={limit} | excluded={len(excluded)}"
        )

        def _register_urls(raw_list: List[str], provider_name: str) -> int:
            """Cleans and deduplicates raw URLs; returns count of new additions."""
            added = 0
            for raw_url in raw_list:
                if not raw_url:
                    continue
                u = self.clean_candidate_url(raw_url)
                if not u:
                    continue
                domain = urlparse(u).netloc.replace("www.", "").lower()
                if not domain:
                    continue
                if domain in excluded:
                    continue
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    discovered_urls.append(u)
                    added += 1
                    logger.info(f"[DISCOVERY] ✓ Accepted [{provider_name}] {u}")
                    if len(discovered_urls) >= limit:
                        break
            return added

        async with httpx.AsyncClient(
            headers=_rotated_headers(),
            timeout=self.timeout,
            follow_redirects=True,
            verify=False,
        ) as client:

            # Run GitHub org search concurrently with the first search query batch
            # GitHub is unblocked on Railway cloud IPs and reliably returns real company websites
            _github_task_done = False

            for query_str in all_queries:
                if is_cancelled and is_cancelled():
                    logger.info("[DISCOVERY] Cancellation signal observed — stopping discovery.")
                    break
                if len(discovered_urls) >= limit:
                    break

                logger.info(f"[DISCOVERY] ━━ Processing query: '{query_str[:80]}...' ━━")

                # Launch search providers in parallel for maximum recall
                # On first query, also fire GitHub org search as a bonus provider
                if not _github_task_done:
                    _github_task_done = True
                    tasks = [
                        asyncio.get_event_loop().run_in_executor(
                            None, self._ddgs_search, query_str, max(limit * 2, 20)
                        ),
                        self._bing_search(query_str, client, max_results=max(limit * 2, 25)),
                        self._yahoo_search(query_str, client, max_results=max(limit, 15)),
                        self._brave_search(query_str, client, max_results=max(limit, 15)),
                        self._github_org_search(city, niche, max_results=min(limit, 25)),
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    p_names = ["DDGS", "BING", "YAHOO", "BRAVE", "GITHUB"]
                else:
                    tasks = [
                        asyncio.get_event_loop().run_in_executor(
                            None, self._ddgs_search, query_str, max(limit * 2, 20)
                        ),
                        self._bing_search(query_str, client, max_results=max(limit * 2, 25)),
                        self._yahoo_search(query_str, client, max_results=max(limit, 15)),
                        self._brave_search(query_str, client, max_results=max(limit, 15)),
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    p_names = ["DDGS", "BING", "YAHOO", "BRAVE"]

                # Process results from all successful providers
                for i, res in enumerate(results):
                    if isinstance(res, list) and res:
                        _register_urls(res, p_names[i])
                        if len(discovered_urls) >= limit:
                            break

                # If still under limit and all yielded few, query DDG Lite
                if len(discovered_urls) < limit:
                    lite_res = await self._ddg_lite_post(query_str, client)
                    if lite_res:
                        _register_urls(lite_res, "DDG-LITE")

                if is_cancelled and is_cancelled():
                    break
                if len(discovered_urls) >= limit:
                    break

        total = len(discovered_urls)
        logger.info(
            f"[DISCOVERY] ✅ Multi-source search complete — {total} unique candidate domains discovered "
            f"(limit={limit})"
        )
        return discovered_urls[:limit]


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

                if lead and lead.all_emails and len(lead.all_emails) >= 3:
                    logger.info(
                        f"[SCRAPER] ✅ Root page hit on {target_url} (3+ emails): "
                        f"{len(lead.all_emails)} email(s) | Primary: {lead.primary_email} | "
                        f"Company: {lead.company_name}"
                    )
                    lead.all_emails = lead.all_emails[:3]
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
                                if len(all_found_emails) >= 3:
                                    break
                            else:
                                logger.debug(f"[SCRAPER] No valid emails on subpage {sub_url}")
                        except Exception as parse_err:
                            logger.debug(f"[SCRAPER] Subpage parsing error for {sub_url}: {parse_err}")

                if all_found_emails and lead:
                    # Sort by priority score descending
                    ranked_list = sorted(all_found_emails.values(), key=lambda e: e.priority_score, reverse=True)
                    # Keep up to 3 distinct valid emails
                    lead.all_emails = ranked_list[:3]
                    lead.primary_email = lead.all_emails[0].email
                    lead.primary_email_tier = lead.all_emails[0].tier
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
