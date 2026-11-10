"""
H.Huddair's Nexus-Pulse - Level 1
Agent Module: Deep Scraper & Tech-Stack Detector
Extracts contact emails, phones, addresses, and full tech-stack footprints from target domains.
Prioritizes high-value estimating & tender contacts over generic mailboxes.
"""

import html
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import httpx

from ..models import Lead, TechStack, EmailTier, ScrapedEmail
from .priority_finder import PriorityEmailFinder

# Regex for email detection including mailto: and obfuscation
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9_.+-]+(?:\s*\[at\]\s*|\s*\(at\)\s*|@)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
)

# Regex for phone numbers
PHONE_REGEX = re.compile(
    r'(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}'
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8,fr;q=0.7",
    "DNT": "1",
    "Connection": "keep-alive"
}


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


class DeepScraperAgent:
    """
    Scraper Agent equipped with Tech-Stack Detection and Priority Contact Extraction.
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
                if not any(clean_match.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]):
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
            # Remove tagline after delimiters (|, -, –, :)
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
        """Asynchronously scrapes target live URL with browser emulation."""
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                resp = await client.get(url)
                if resp.status_code < 400:
                    headers_dict = dict(resp.headers)
                    return self.parse_html_content(
                        html_content=resp.text,
                        source_url=str(resp.url),
                        country=country,
                        city=city,
                        niche=niche,
                        headers=headers_dict
                    )
        except Exception:
            pass

        return None
