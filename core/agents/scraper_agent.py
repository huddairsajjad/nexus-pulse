"""
H.Huddair's Nexus-Pulse - Level 1
Agent Module: Deep Scraper & Tech-Stack Detector
Extracts contact emails, phones, addresses, and full tech-stack footprints from target domains.
Prioritizes high-value estimating & tender contacts over generic mailboxes.
Supports autonomous multi-engine search discovery and deep subpage contact extraction.
"""

import html
import logging
import re
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import httpx

from ..models import Lead, TechStack, EmailTier, ScrapedEmail
from .priority_finder import PriorityEmailFinder

logger = logging.getLogger("nexus.scraper")

# Regex for email detection including mailto: and obfuscation
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9_.+-]+(?:\s*\[at\]\s*|\s*\(at\)\s*|@)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
)

# Regex for phone numbers
PHONE_REGEX = re.compile(
    r'(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}'
)

# Realistic modern browser headers preventing cloud bot blocks
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8,fr;q=0.7,es;q=0.6",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}

# Subpage anchor keywords to crawl when landing page has no emails
CONTACT_SUBPAGE_KEYWORDS = [
    "kontakt", "contact", "impressum", "about", "ueber-uns", "uber-uns",
    "ansprechpartner", "team", "mentions", "mentions-legales", "legal",
    "contacto", "contatti", "contacts", "direction", "firmensitz", "standort"
]

COMMON_SUBPATHS = [
    "/kontakt", "/kontakt/", "/impressum", "/impressum/",
    "/contact", "/contact/", "/about", "/about-us", "/ueber-uns"
]


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

        # Check server header directly
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


class SearchDiscoveryAgent:
    """
    Autonomous B2B Search Discovery Engine.
    Discovers candidate target domains and URLs across search engines
    (DuckDuckGo Lite, DuckDuckGo HTML, and Bing fallback) using localized native queries.
    """

    DISCARD_DOMAINS = {
        "google.", "duckduckgo.", "bing.", "yahoo.", "microsoft.",
        "facebook.", "instagram.", "twitter.", "x.com", "linkedin.",
        "youtube.", "wikipedia.", "reddit.", "amazon.", "apple.",
        "github.", "pinterest.", "tiktok.", "medium.", "quora.",
        "tripadvisor.", "yelp.", "w3schools.", "stackoverflow.", "t.me"
    }

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds

    @classmethod
    def clean_candidate_url(cls, raw_url: str) -> Optional[str]:
        """Validates and unpacks wrapped search result links."""
        if not raw_url:
            return None

        # Handle DDG redirect /uddg=
        if "uddg=" in raw_url:
            raw_url = urllib.parse.unquote(raw_url.split("uddg=")[1].split("&")[0])

        # Handle Bing redirect /ck/a?!...&u=a1<base64>
        if "bing.com/ck/a" in raw_url and "u=a1" in raw_url:
            try:
                import base64
                u_param = raw_url.split("u=a1")[1].split("&")[0]
                raw_url = base64.urlsafe_b64decode(u_param + "==").decode("utf-8", errors="ignore")
            except Exception:
                pass

        if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            return None

        parsed = urlparse(raw_url)
        domain = parsed.netloc.lower().replace("www.", "")
        if not domain or any(d in domain for d in cls.DISCARD_DOMAINS):
            return None

        # Return root domain website URL
        return f"{parsed.scheme}://{parsed.netloc}"

    @classmethod
    def sanitize_search_query(cls, query: str) -> str:
        """Strips nested quotes, boolean OR, and site: operators that cause search engines to return 0 results."""
        cleaned = re.sub(r'[\(\)"]', '', query)
        cleaned = re.sub(r'\bOR\b', '', cleaned)
        cleaned = re.sub(r'site:\S+', '', cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned

    async def discover_candidate_urls(
        self,
        queries: List[Dict[str, str]],
        limit: int = 20,
        country: str = "Germany",
        city: str = "Berlin",
        niche: str = "Commercial Construction"
    ) -> List[str]:
        """
        Queries search engines using localized query matrices and returns unique candidate website URLs.
        """
        discovered_urls: List[str] = []
        seen_domains: Set[str] = set()

        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False
        ) as client:
            for q_item in queries:
                raw_q = q_item.get("query", "")
                q_type = q_item.get("type", "GENERAL")
                clean_q = self.sanitize_search_query(raw_q)
                if not clean_q:
                    continue

                logger.info(f"[DISCOVERY] Executing search query [{q_type}]: '{clean_q}'")
                found_links: List[str] = []

                # Strategy 1: DuckDuckGo Lite (POST)
                try:
                    resp = await client.post("https://lite.duckduckgo.com/lite/", data={"q": clean_q})
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for a_tag in soup.select(".result-link"):
                            href = a_tag.get("href", "")
                            u = self.clean_candidate_url(href)
                            if u:
                                found_links.append(u)
                        logger.info(f"[DISCOVERY] DDG Lite returned {len(found_links)} candidate links for '{clean_q}'")
                    else:
                        logger.warning(f"[DISCOVERY] DDG Lite returned status {resp.status_code} for '{clean_q}'")
                except Exception as ex:
                    logger.warning(f"[DISCOVERY] DDG Lite request error for '{clean_q}': {ex}")

                # Strategy 2: DuckDuckGo HTML Fallback (GET/POST)
                if not found_links:
                    try:
                        resp = await client.get("https://html.duckduckgo.com/html/", params={"q": clean_q})
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "html.parser")
                            for a_tag in soup.select("h2.result__title a, a.result__url"):
                                href = a_tag.get("href", "")
                                u = self.clean_candidate_url(href)
                                if u:
                                    found_links.append(u)
                            logger.info(f"[DISCOVERY] DDG HTML returned {len(found_links)} candidate links for '{clean_q}'")
                        else:
                            logger.warning(f"[DISCOVERY] DDG HTML returned status {resp.status_code} for '{clean_q}'")
                    except Exception as ex:
                        logger.warning(f"[DISCOVERY] DDG HTML request error for '{clean_q}': {ex}")

                # Strategy 3: Bing Search Fallback
                if not found_links:
                    try:
                        resp = await client.get("https://www.bing.com/search", params={"q": clean_q})
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "html.parser")
                            for a_tag in soup.select("li.b_algo h2 a"):
                                href = a_tag.get("href", "")
                                u = self.clean_candidate_url(href)
                                if u:
                                    found_links.append(u)
                            logger.info(f"[DISCOVERY] Bing fallback returned {len(found_links)} candidate links for '{clean_q}'")
                    except Exception as ex:
                        logger.warning(f"[DISCOVERY] Bing fallback request error for '{clean_q}': {ex}")

                # Deduplicate and register found domains
                for u in found_links:
                    domain = urlparse(u).netloc.replace("www.", "").lower()
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        discovered_urls.append(u)

                if len(discovered_urls) >= limit:
                    break

        logger.info(f"[DISCOVERY] Finished discovery run: {len(discovered_urls)} unique candidate domains found.")
        return discovered_urls[:limit]


class DeepScraperAgent:
    """
    Scraper Agent equipped with Tech-Stack Detection, Priority Contact Extraction,
    and Deep Contact Subpage Crawling.
    """

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds

    def parse_html_content(
        self,
        html_content: str,
        source_url: str,
        country: str = "Germany",
        city: str = "Berlin",
        niche: str = "Commercial Construction",
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Lead]:
        """
        Parses raw HTML string to extract company lead, tech stack, and prioritized emails.
        """
        if not html_content or len(html_content.strip()) < 50:
            return None

        # Clean HTML unescaping
        raw_text = html.unescape(html_content)
        soup = BeautifulSoup(raw_text, "html.parser")

        # 1. Extract Emails from mailto: links and page text
        emails_found: Set[str] = set()
        context_map: Dict[str, str] = {}

        # Look in mailto links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("mailto:"):
                clean_mail = href[7:].split("?")[0].strip()
                if "@" in clean_mail:
                    emails_found.add(clean_mail)
                    context_map[clean_mail.lower()] = a_tag.get_text(strip=True) or "mailto anchor"

        # Regex search through raw text
        for match in EMAIL_REGEX.findall(raw_text):
            clean_match = match.replace("[at]", "@").replace("(at)", "@").replace(" ", "").strip()
            # Basic hygiene
            if "@" in clean_match and "." in clean_match.split("@")[-1]:
                # Exclude image/asset false positives
                if not any(clean_match.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".css", ".js"]):
                    emails_found.add(clean_match)

        if not emails_found:
            return None

        # 2. Prioritize emails
        ranked_emails: List[ScrapedEmail] = PriorityEmailFinder.rank_emails(
            raw_emails=list(emails_found),
            page_source=source_url,
            context_map=context_map
        )

        primary = PriorityEmailFinder.pick_primary_email(ranked_emails)
        if not primary:
            return None

        # 3. Extract Company Name
        company_name = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            raw_title = title_tag.text.strip()
            split_parts = re.split(r'[\|\-\–\:\•]', raw_title)
            company_name = split_parts[0].strip()

        if not company_name or len(company_name) < 2:
            h1 = soup.find("h1")
            if h1 and h1.text:
                company_name = h1.text.strip()[:40]
            else:
                domain_part = urlparse(source_url).netloc.replace("www.", "")
                company_name = domain_part.split(".")[0].capitalize()

        # 4. Extract Phone Numbers
        phones: Set[str] = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("tel:"):
                phone_num = href[4:].strip()
                if len(phone_num) >= 7:
                    phones.add(phone_num)

        # 5. Extract Tech Stack
        tech_stack = TechStackDetector.detect(raw_text, headers)

        # 6. Build parsed Domain
        domain = urlparse(source_url).netloc.replace("www.", "")
        if not domain:
            domain = primary.domain

        # Determine quality tag based on primary email tier
        tier_tag_map = {
            EmailTier.TIER_1_ESTIMATING: "TIER-1-ESTIMATING",
            EmailTier.TIER_2_EXECUTIVE: "TIER-2-EXECUTIVE",
            EmailTier.TIER_3_OPERATIONAL: "TIER-3-OPERATIONAL",
            EmailTier.TIER_GENERIC: "TIER-GENERIC",
            EmailTier.UNKNOWN: "TIER-UNRATED"
        }
        quality_tag = tier_tag_map.get(primary.tier, "TIER-GENERIC")

        lead = Lead(
            company_name=company_name,
            domain=domain,
            website_url=source_url,
            target_country=country,
            target_city=city,
            industry_niche=niche,
            primary_email=primary.email,
            primary_email_tier=primary.tier,
            priority_score=primary.priority_score,
            all_emails=ranked_emails,
            phone_numbers=list(phones),
            tech_stack=tech_stack,
            quality_tag=quality_tag
        )

        return lead

    async def scrape_url(
        self,
        url: str,
        country: str = "Germany",
        city: str = "Berlin",
        niche: str = "Commercial Construction"
    ) -> Optional[Lead]:
        """
        Asynchronously scrapes target live URL with modern browser headers, SSL fallback,
        and automatic contact/impressum subpage crawling.
        """
        target_url = url.strip()
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = f"https://{target_url}"

        logger.info(f"[SCRAPER] Target URL initiated: {target_url}")

        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                resp = None
                try:
                    resp = await client.get(target_url)
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, Exception) as fetch_err:
                    logger.warning(f"[SCRAPER] Initial GET failed for {target_url} ({type(fetch_err).__name__}: {fetch_err})")
                    # Try http:// fallback if https:// failed
                    if target_url.startswith("https://"):
                        fallback_url = "http://" + target_url[8:]
                        logger.info(f"[SCRAPER] Attempting HTTP fallback for {fallback_url}")
                        try:
                            resp = await client.get(fallback_url)
                        except Exception as fb_err:
                            logger.warning(f"[SCRAPER] HTTP fallback failed for {fallback_url}: {fb_err}")

                if not resp or resp.status_code >= 400:
                    status_code = resp.status_code if resp else "NO_RESPONSE"
                    logger.warning(f"[SCRAPER] Target {target_url} returned non-success status: {status_code}")
                    return None

                base_url = str(resp.url)
                base_domain = urlparse(base_url).netloc.replace("www.", "").lower()
                headers_dict = dict(resp.headers)

                # Attempt 1: Parse root page HTML
                lead = self.parse_html_content(
                    html_content=resp.text,
                    source_url=base_url,
                    country=country,
                    city=city,
                    niche=niche,
                    headers=headers_dict
                )

                if lead and lead.all_emails:
                    logger.info(f"[SCRAPER] Root page hit on {target_url}: found {len(lead.all_emails)} email(s) (Primary: {lead.primary_email})")
                    return lead

                # Attempt 2: If root landing page has no emails, crawl contact & impressum subpages
                logger.info(f"[SCRAPER] No emails on root of {target_url}. Discovering contact & impressum subpages...")
                soup = BeautifulSoup(resp.text, "html.parser")
                candidate_subpages: List[str] = []

                # Scan anchor links on page
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    text = a_tag.get_text(strip=True).lower()
                    href_lower = href.lower()

                    if any(kw in href_lower or kw in text for kw in CONTACT_SUBPAGE_KEYWORDS):
                        full_sub_url = urljoin(base_url, href)
                        sub_domain = urlparse(full_sub_url).netloc.replace("www.", "").lower()
                        # Ensure subpage belongs to same company domain
                        if sub_domain == base_domain and full_sub_url not in candidate_subpages and full_sub_url != base_url:
                            candidate_subpages.append(full_sub_url)

                # If no matching links found in DOM, test standard regional subpaths
                if len(candidate_subpages) < 2:
                    for sp in COMMON_SUBPATHS:
                        guess_url = urljoin(base_url, sp)
                        if guess_url not in candidate_subpages and guess_url != base_url:
                            candidate_subpages.append(guess_url)

                logger.info(f"[SCRAPER] Discovered {len(candidate_subpages)} contact subpages for {base_domain}: {candidate_subpages[:3]}")

                # Crawl top 3 subpages for business contacts
                for sub_url in candidate_subpages[:3]:
                    try:
                        sub_resp = await client.get(sub_url)
                        if sub_resp.status_code < 400:
                            sub_lead = self.parse_html_content(
                                html_content=sub_resp.text,
                                source_url=str(sub_resp.url),
                                country=country,
                                city=city,
                                niche=niche,
                                headers=dict(sub_resp.headers)
                            )
                            if sub_lead and sub_lead.all_emails:
                                logger.info(f"[SCRAPER] Contact subpage {sub_url} resolved {len(sub_lead.all_emails)} email(s) for {base_domain} (Primary: {sub_lead.primary_email})")
                                # Retain root company name if subpage is generic (e.g. "Impressum")
                                if lead and lead.company_name and len(lead.company_name) > 3:
                                    sub_lead.company_name = lead.company_name
                                return sub_lead
                    except Exception as sub_err:
                        logger.debug(f"[SCRAPER] Subpage fetch error for {sub_url}: {sub_err}")

                logger.warning(f"[SCRAPER] Discarding {target_url}: 0 business emails found after scanning root and contact subpages.")
                return None

        except Exception as ex:
            logger.error(f"[SCRAPER] Unexpected scraping error for {target_url}: {type(ex).__name__} - {ex}", exc_info=False)
            return None
