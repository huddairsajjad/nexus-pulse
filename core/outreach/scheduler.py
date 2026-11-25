"""
Nexus-Pulse Enterprise Build
Outreach Engine: Global Timezone-Aware Working Hours Engine & Smart Scheduler
Enforces dynamic dispatching windows during regional business hours:
Standard Window: 9:00 AM to 5:00 PM (09:00 - 17:00) local recipient time on weekdays (Mon-Fri).
Supports full manual override / bypass window toggle for immediate testing outside hours & weekends.
Robust fallback guarantees for unknown countries / generic .com TLDs to prevent queue lockups.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional


# Comprehensive Global Regional Timezone Map
# Key (lowercase country / TLD / alias) -> (UTC Offset Hours, Timezone Code, Canonical Country Name)
REGIONAL_TIMEZONE_MAP: Dict[str, Tuple[float, str, str]] = {
    # Europe (CET / CEST = +1.0)
    "germany": (1.0, "CET", "Germany"),
    "deutschland": (1.0, "CET", "Germany"),
    "de": (1.0, "CET", "Germany"),
    "france": (1.0, "CET", "France"),
    "fr": (1.0, "CET", "France"),
    "spain": (1.0, "CET", "Spain"),
    "espana": (1.0, "CET", "Spain"),
    "es": (1.0, "CET", "Spain"),
    "italy": (1.0, "CET", "Italy"),
    "italia": (1.0, "CET", "Italy"),
    "it": (1.0, "CET", "Italy"),
    "netherlands": (1.0, "CET", "Netherlands"),
    "holland": (1.0, "CET", "Netherlands"),
    "nl": (1.0, "CET", "Netherlands"),
    "belgium": (1.0, "CET", "Belgium"),
    "be": (1.0, "CET", "Belgium"),
    "switzerland": (1.0, "CET", "Switzerland"),
    "schweiz": (1.0, "CET", "Switzerland"),
    "ch": (1.0, "CET", "Switzerland"),
    "austria": (1.0, "CET", "Austria"),
    "osterreich": (1.0, "CET", "Austria"),
    "at": (1.0, "CET", "Austria"),
    "poland": (1.0, "CET", "Poland"),
    "pl": (1.0, "CET", "Poland"),
    "sweden": (1.0, "CET", "Sweden"),
    "se": (1.0, "CET", "Sweden"),
    "norway": (1.0, "CET", "Norway"),
    "no": (1.0, "CET", "Norway"),
    "denmark": (1.0, "CET", "Denmark"),
    "dk": (1.0, "CET", "Denmark"),
    "czech republic": (1.0, "CET", "Czech Republic"),
    "czechia": (1.0, "CET", "Czech Republic"),
    "cz": (1.0, "CET", "Czech Republic"),
    "hungary": (1.0, "CET", "Hungary"),
    "hu": (1.0, "CET", "Hungary"),
    "slovakia": (1.0, "CET", "Slovakia"),
    "sk": (1.0, "CET", "Slovakia"),
    "slovenia": (1.0, "CET", "Slovenia"),
    "si": (1.0, "CET", "Slovenia"),
    "croatia": (1.0, "CET", "Croatia"),
    "hr": (1.0, "CET", "Croatia"),
    "portugal": (0.0, "WET", "Portugal"),
    "pt": (0.0, "WET", "Portugal"),
    # Europe (GMT / UTC = +0.0)
    "united kingdom": (0.0, "GMT", "United Kingdom"),
    "uk": (0.0, "GMT", "United Kingdom"),
    "co.uk": (0.0, "GMT", "United Kingdom"),
    "great britain": (0.0, "GMT", "United Kingdom"),
    "england": (0.0, "GMT", "United Kingdom"),
    "scotland": (0.0, "GMT", "United Kingdom"),
    "wales": (0.0, "GMT", "United Kingdom"),
    "britain": (0.0, "GMT", "United Kingdom"),
    "gb": (0.0, "GMT", "United Kingdom"),
    "ireland": (0.0, "GMT", "Ireland"),
    "ie": (0.0, "GMT", "Ireland"),
    "iceland": (0.0, "GMT", "Iceland"),
    "is": (0.0, "GMT", "Iceland"),
    # Eastern Europe (EET = +2.0)
    "finland": (2.0, "EET", "Finland"),
    "fi": (2.0, "EET", "Finland"),
    "greece": (2.0, "EET", "Greece"),
    "gr": (2.0, "EET", "Greece"),
    "romania": (2.0, "EET", "Romania"),
    "ro": (2.0, "EET", "Romania"),
    "bulgaria": (2.0, "EET", "Bulgaria"),
    "bg": (2.0, "EET", "Bulgaria"),
    "ukraine": (2.0, "EET", "Ukraine"),
    "ua": (2.0, "EET", "Ukraine"),
    "estonia": (2.0, "EET", "Estonia"),
    "ee": (2.0, "EET", "Estonia"),
    "latvia": (2.0, "EET", "Latvia"),
    "lv": (2.0, "EET", "Latvia"),
    "lithuania": (2.0, "EET", "Lithuania"),
    "lt": (2.0, "EET", "Lithuania"),
    "russia": (3.0, "MSK", "Russia"),
    "ru": (3.0, "MSK", "Russia"),
    # North America
    "united states of america": (-5.0, "EST", "United States"),
    "united states": (-5.0, "EST", "United States"),
    "usa": (-5.0, "EST", "United States"),
    "us": (-5.0, "EST", "United States"),
    "america": (-5.0, "EST", "United States"),
    "canada": (-5.0, "EST", "Canada"),
    "ca": (-5.0, "EST", "Canada"),
    "mexico": (-6.0, "CST", "Mexico"),
    "mx": (-6.0, "CST", "Mexico"),
    # Latin America
    "brazil": (-3.0, "BRT", "Brazil"),
    "brasil": (-3.0, "BRT", "Brazil"),
    "br": (-3.0, "BRT", "Brazil"),
    "com.br": (-3.0, "BRT", "Brazil"),
    "argentina": (-3.0, "ART", "Argentina"),
    "ar": (-3.0, "ART", "Argentina"),
    "uruguay": (-3.0, "UYT", "Uruguay"),
    "uy": (-3.0, "UYT", "Uruguay"),
    "colombia": (-5.0, "COT", "Colombia"),
    "peru": (-5.0, "PET", "Peru"),
    "pe": (-5.0, "PET", "Peru"),
    "ecuador": (-5.0, "ECT", "Ecuador"),
    "ec": (-5.0, "ECT", "Ecuador"),
    "panama": (-5.0, "EST", "Panama"),
    "costa rica": (-6.0, "CST", "Costa Rica"),
    "chile": (-4.0, "CLT", "Chile"),
    "cl": (-4.0, "CLT", "Chile"),
    # Middle East
    "united arab emirates": (4.0, "GST", "United Arab Emirates"),
    "emirates": (4.0, "GST", "United Arab Emirates"),
    "uae": (4.0, "GST", "United Arab Emirates"),
    "ae": (4.0, "GST", "United Arab Emirates"),
    "dubai": (4.0, "GST", "United Arab Emirates"),
    "abu dhabi": (4.0, "GST", "United Arab Emirates"),
    "oman": (4.0, "GST", "Oman"),
    "om": (4.0, "GST", "Oman"),
    "saudi arabia": (3.0, "AST", "Saudi Arabia"),
    "saudi": (3.0, "AST", "Saudi Arabia"),
    "sa": (3.0, "AST", "Saudi Arabia"),
    "qatar": (3.0, "AST", "Qatar"),
    "qa": (3.0, "AST", "Qatar"),
    "kuwait": (3.0, "AST", "Kuwait"),
    "kw": (3.0, "AST", "Kuwait"),
    "bahrain": (3.0, "AST", "Bahrain"),
    "bh": (3.0, "AST", "Bahrain"),
    "jordan": (3.0, "EET_JO", "Jordan"),
    "jo": (3.0, "EET_JO", "Jordan"),
    "israel": (2.0, "IST_IL", "Israel"),
    "il": (2.0, "IST_IL", "Israel"),
    "turkey": (3.0, "TRT", "Turkey"),
    "turkiye": (3.0, "TRT", "Turkey"),
    "tr": (3.0, "TRT", "Turkey"),
    # Asia Pacific
    "australia": (10.0, "AEST", "Australia"),
    "au": (10.0, "AEST", "Australia"),
    "com.au": (10.0, "AEST", "Australia"),
    "new zealand": (12.0, "NZST", "New Zealand"),
    "nz": (12.0, "NZST", "New Zealand"),
    "co.nz": (12.0, "NZST", "New Zealand"),
    "singapore": (8.0, "SGT", "Singapore"),
    "sg": (8.0, "SGT", "Singapore"),
    "japan": (9.0, "JST", "Japan"),
    "jp": (9.0, "JST", "Japan"),
    "south korea": (9.0, "KST", "South Korea"),
    "korea": (9.0, "KST", "South Korea"),
    "kr": (9.0, "KST", "South Korea"),
    "hong kong": (8.0, "HKT", "Hong Kong"),
    "hk": (8.0, "HKT", "Hong Kong"),
    "taiwan": (8.0, "CST_TW", "Taiwan"),
    "tw": (8.0, "CST_TW", "Taiwan"),
    "china": (8.0, "CST", "China"),
    "cn": (8.0, "CST", "China"),
    "malaysia": (8.0, "MYT", "Malaysia"),
    "my": (8.0, "MYT", "Malaysia"),
    "philippines": (8.0, "PHT", "Philippines"),
    "ph": (8.0, "PHT", "Philippines"),
    "indonesia": (7.0, "WIB", "Indonesia"),
    "thailand": (7.0, "ICT", "Thailand"),
    "th": (7.0, "ICT", "Thailand"),
    "vietnam": (7.0, "ICT", "Vietnam"),
    "vn": (7.0, "ICT", "Vietnam"),
    # South Asia
    "india": (5.5, "IST", "India"),
    "in": (5.5, "IST", "India"),
    "pakistan": (5.0, "PKT", "Pakistan"),
    "pk": (5.0, "PKT", "Pakistan"),
    "bangladesh": (6.0, "BST", "Bangladesh"),
    "bd": (6.0, "BST", "Bangladesh"),
    # Africa
    "south africa": (2.0, "SAST", "South Africa"),
    "za": (2.0, "SAST", "South Africa"),
    "co.za": (2.0, "SAST", "South Africa"),
    "nigeria": (1.0, "WAT", "Nigeria"),
    "ng": (1.0, "WAT", "Nigeria"),
    "egypt": (2.0, "EET", "Egypt"),
    "eg": (2.0, "EET", "Egypt"),
    "kenya": (3.0, "EAT", "Kenya"),
    "ke": (3.0, "EAT", "Kenya"),
    "morocco": (1.0, "WAT", "Morocco"),
    "ma": (1.0, "WAT", "Morocco"),
    # Global Default Fallback
    "default": (1.0, "CET", "Germany/CET")
}

# Multi-timezone city/region overrides (used when city or region hint clarifies offset)
CITY_TIMEZONE_OVERRIDES: Dict[str, Tuple[float, str, str]] = {
    # US Central Time (-6.0)
    "austin": (-6.0, "CST_US", "United States"),
    "dallas": (-6.0, "CST_US", "United States"),
    "houston": (-6.0, "CST_US", "United States"),
    "san antonio": (-6.0, "CST_US", "United States"),
    "texas": (-6.0, "CST_US", "United States"),
    "chicago": (-6.0, "CST_US", "United States"),
    "minneapolis": (-6.0, "CST_US", "United States"),
    "nashville": (-6.0, "CST_US", "United States"),
    "winnipeg": (-6.0, "CST_CA", "Canada"),
    # US Mountain Time (-7.0)
    "denver": (-7.0, "MST", "United States"),
    "colorado": (-7.0, "MST", "United States"),
    "phoenix": (-7.0, "MST", "United States"),
    "arizona": (-7.0, "MST", "United States"),
    "salt lake city": (-7.0, "MST", "United States"),
    "calgary": (-7.0, "MST", "Canada"),
    "edmonton": (-7.0, "MST", "Canada"),
    # US/Canada Pacific Time (-8.0)
    "los angeles": (-8.0, "PST", "United States"),
    "san francisco": (-8.0, "PST", "United States"),
    "san diego": (-8.0, "PST", "United States"),
    "california": (-8.0, "PST", "United States"),
    "seattle": (-8.0, "PST", "United States"),
    "portland": (-8.0, "PST", "United States"),
    "las vegas": (-8.0, "PST", "United States"),
    "vancouver": (-8.0, "PST", "Canada"),
    # Australia Western / Central
    "perth": (8.0, "AWST", "Australia"),
    "adelaide": (9.5, "ACST", "Australia"),
}

# Generic TLDs that do NOT indicate country-specific location
GENERIC_TLDS = {
    "com", "org", "net", "io", "ai", "co", "app", "biz", "info", "xyz",
    "cloud", "dev", "tech", "online", "site", "global", "pro", "mobi"
}


class TimezoneScheduler:
    """
    Global Timezone-Aware Working Hours Engine:
    Detects target country/timezone dynamically from country metadata, domain TLD, or location.
    Enforces email dispatches strictly within local recipient business hours:
      - Continuous Active Window: 9:00 AM to 5:00 PM (09:00 - 17:00) local time on weekdays (Mon-Fri).
      - Immediate bypass mode when admin enables "Dispatch Now / Bypass Window".
      - Safe UTC/CET fallback for unknown locations or generic .com domains.
    """

    @staticmethod
    def _normalize_location_text(text: str) -> str:
        """Normalizes punctuation (e.g. 'U.S.A.' -> 'usa', 'Austin, TX' -> 'austin tx')."""
        s = text.strip().lower()
        # Collapse dotted abbreviations like U.S.A., U.K., U.A.E.
        s_nodots = re.sub(r"\b([a-z])\.", r"\1", s).replace(".", "")
        s_clean = re.sub(r"[^a-z0-9\s]", " ", s_nodots)
        return re.sub(r"\s+", " ", s_clean).strip()

    @classmethod
    def _match_region_map(
        cls,
        raw_text: str,
        mapping: Dict[str, Tuple[float, str, str]],
        exclude_default: bool = True,
    ) -> Optional[Tuple[float, str, str]]:
        """Matches exact text first, then longest word-boundary phrase without false substring hits."""
        clean_raw = raw_text.strip().lower()
        norm_text = cls._normalize_location_text(raw_text)
        if not norm_text:
            return None

        if clean_raw in mapping and (not exclude_default or clean_raw != "default"):
            return mapping[clean_raw]
        if norm_text in mapping and (not exclude_default or norm_text != "default"):
            return mapping[norm_text]

        # Word-boundary match ordered longest key first (prevents 'oman' matching 'romania')
        # Skip <=2-char ISO codes in multi-word phrase matching to avoid stopword hits ('in', 'at', 'no', 'is', 'it')
        for key in sorted(mapping.keys(), key=len, reverse=True):
            if exclude_default and key == "default":
                continue
            norm_key = cls._normalize_location_text(key)
            if not norm_key or (len(norm_key) <= 2 and norm_key != "uk"):
                continue
            if re.search(rf"(?<!\w){re.escape(norm_key)}(?!\w)", norm_text):
                return mapping[key]
        return None

    @classmethod
    def detect_timezone_info(
        cls,
        country: Optional[str] = None,
        domain: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Tuple[float, str, str]:
        """
        Resolves (utc_offset_hours, timezone_code, resolved_country).
        Checks city-level overrides for multi-timezone countries, then explicit country,
        then ccTLD from domain, falling back safely to CET (UTC+1).
        """
        try:
            # 0. Multi-timezone city/state clarification if city provided or embedded in country
            if city and isinstance(city, str) and city.strip():
                city_match = cls._match_region_map(city, CITY_TIMEZONE_OVERRIDES, exclude_default=False)
                if city_match:
                    return city_match

            if country and isinstance(country, str) and country.strip():
                city_in_country = cls._match_region_map(country, CITY_TIMEZONE_OVERRIDES, exclude_default=False)
                if city_in_country:
                    return city_in_country

            # 1. PRIORITY 1: Explicit Country Metadata if provided
            if country and isinstance(country, str) and country.strip():
                country_match = cls._match_region_map(country, REGIONAL_TIMEZONE_MAP, exclude_default=True)
                if country_match:
                    return country_match

            # 2. PRIORITY 2: Domain TLD if country wasn't resolved
            if domain and isinstance(domain, str):
                dom = domain.strip().lower().replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
                parts = dom.split(".")
                if len(parts) >= 2:
                    # Check multi-part ccTLD first (e.g., co.uk, com.au, com.br, co.za)
                    if len(parts) >= 3:
                        sub_tld = f"{parts[-2]}.{parts[-1]}"
                        if sub_tld in REGIONAL_TIMEZONE_MAP:
                            return REGIONAL_TIMEZONE_MAP[sub_tld]
                    tld = parts[-1]
                    # If TLD is a known regional country code (and not in generic list)
                    if tld in REGIONAL_TIMEZONE_MAP and tld not in GENERIC_TLDS:
                        return REGIONAL_TIMEZONE_MAP[tld]

            # 3. PRIORITY 3: Safe Default Fallback (CET / UTC+1)
            return REGIONAL_TIMEZONE_MAP["default"]
        except Exception:
            # Absolute safety net: never throw exception
            return REGIONAL_TIMEZONE_MAP["default"]

    @staticmethod
    def _coerce_utc(now_utc: Optional[datetime] = None) -> datetime:
        """Returns a timezone-aware UTC datetime."""
        if now_utc is None:
            return datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            return now_utc.replace(tzinfo=timezone.utc)
        return now_utc.astimezone(timezone.utc)

    @classmethod
    def get_target_local_time(
        cls,
        country: Optional[str] = None,
        domain: Optional[str] = None,
        bypass_window: bool = False,
        city: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculates wall-clock time in the target country/timezone and evaluates whether
        the lead is currently within the active 9:00 AM - 5:00 PM local business window.
        Supports manual bypass override for immediate testing / weekend dispatch.
        """
        try:
            offset_hours, tz_code, resolved_country = cls.detect_timezone_info(country, domain, city=city)
            utc_dt = cls._coerce_utc(now_utc)
            target_tz = timezone(timedelta(hours=offset_hours))
            target_local = utc_dt.astimezone(target_tz)

            hour = target_local.hour
            minute = target_local.minute
            is_weekday = target_local.weekday() < 5  # Mon-Fri (0-4)

            # Dynamic 9:00 AM - 5:00 PM (09:00 inclusive through 16:59 inclusive; 17:00 is off-hours)
            is_working_hours = (9 <= hour < 17) and is_weekday
            is_in_send_window = is_working_hours or bool(bypass_window)

            if bypass_window:
                window_desc = "Manual Override Active: Bypass Window (Immediate Dispatch)"
            elif is_working_hours:
                window_desc = f"Active Business Window (09:00 - 17:00 local {tz_code})"
            elif not is_weekday:
                window_desc = "Weekend: Queued for Monday 09:00 AM local"
            elif hour < 9:
                window_desc = f"Pre-Morning: Queued for today 09:00 AM local ({tz_code})"
            else:
                window_desc = f"After-Hours: Queued for next business day 09:00 AM local ({tz_code})"

            return {
                "country": country or resolved_country,
                "resolved_country": resolved_country,
                "timezone_code": tz_code,
                "utc_offset_hours": offset_hours,
                "current_local_time": target_local.strftime("%Y-%m-%d %H:%M:%S"),
                "current_local_hour": hour,
                "current_local_minute": minute,
                "is_in_send_window": is_in_send_window,
                "is_working_hours": is_working_hours,
                "is_weekday": is_weekday,
                "bypass_window": bool(bypass_window),
                "window_description": window_desc
            }
        except Exception:
            # Fallback defensively without falsely bypassing 9-5 window when bypass_window=False
            utc_dt = cls._coerce_utc(now_utc)
            cet_local = utc_dt.astimezone(timezone(timedelta(hours=1.0)))
            is_wh = (9 <= cet_local.hour < 17) and (cet_local.weekday() < 5)
            return {
                "country": country or "Global Default",
                "resolved_country": "Germany/CET",
                "timezone_code": "CET",
                "utc_offset_hours": 1.0,
                "current_local_time": cet_local.strftime("%Y-%m-%d %H:%M:%S"),
                "current_local_hour": cet_local.hour,
                "current_local_minute": cet_local.minute,
                "is_in_send_window": is_wh or bool(bypass_window),
                "is_working_hours": is_wh,
                "is_weekday": cet_local.weekday() < 5,
                "bypass_window": bool(bypass_window),
                "window_description": "Safe Fallback Window (09:00 - 17:00 local CET)"
            }

    @classmethod
    def calculate_next_send_slot(
        cls,
        country: Optional[str] = None,
        domain: Optional[str] = None,
        bypass_window: bool = False,
        city: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> datetime:
        """
        Calculates the exact UTC timestamp for the next valid dispatch slot.
        - If bypass_window is True: returns current UTC time immediately.
        - If currently within 9:00 AM - 5:00 PM local time on a weekday: returns current UTC time (immediate).
        - If before 9:00 AM on a weekday: schedules for 09:00 AM today local time.
        - If after 5:00 PM (17:00) on a weekday: advances to 09:00 AM on next business day.
        - If weekend: advances to 09:00 AM on coming Monday.
        """
        utc_dt = cls._coerce_utc(now_utc)
        if bypass_window:
            return utc_dt

        try:
            offset_hours, _, _ = cls.detect_timezone_info(country, domain, city=city)
            target_tz = timezone(timedelta(hours=offset_hours))
            target_local = utc_dt.astimezone(target_tz)

            # If weekend (Saturday=5, Sunday=6), advance to next Monday at 9:00 AM local
            if target_local.weekday() >= 5:
                days_to_monday = 7 - target_local.weekday()
                next_local = (target_local + timedelta(days=days_to_monday)).replace(hour=9, minute=0, second=0, microsecond=0)
                return next_local.astimezone(timezone.utc)

            hour = target_local.hour
            # If before 9:00 AM on a weekday: schedule for 09:00 AM today local
            if hour < 9:
                next_local = target_local.replace(hour=9, minute=0, second=0, microsecond=0)
                return next_local.astimezone(timezone.utc)

            # If inside active 9:00 AM - 5:00 PM (17:00) window: immediate dispatch slot
            if 9 <= hour < 17:
                return utc_dt

            # Past 17:00 (5:00 PM): advance to next business day at 09:00 AM local
            next_day = target_local + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            next_local = next_day.replace(hour=9, minute=0, second=0, microsecond=0)
            return next_local.astimezone(timezone.utc)

        except Exception:
            return utc_dt


_global_scheduler = None

def get_scheduler() -> TimezoneScheduler:
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TimezoneScheduler()
    return _global_scheduler
