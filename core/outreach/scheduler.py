"""
Nexus-Pulse Enterprise Build
Outreach Engine: Regional Working Hours Engine & Timezone Scheduler
Enforces strict dispatching windows during target regional business hours:
Window 1: 9:00 AM - 11:00 AM local time
Window 2: 2:00 PM - 5:00 PM local time
Detects timezone from country metadata and domain TLDs.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional


# Target Country / TLD -> (UTC Offset Hours, Timezone Code, Primary Country)
REGIONAL_TIMEZONE_MAP: Dict[str, Tuple[float, str, str]] = {
    # Europe
    "germany": (1.0, "CET", "Germany"),
    "de": (1.0, "CET", "Germany"),
    "france": (1.0, "CET", "France"),
    "fr": (1.0, "CET", "France"),
    "spain": (1.0, "CET", "Spain"),
    "es": (1.0, "CET", "Spain"),
    "italy": (1.0, "CET", "Italy"),
    "it": (1.0, "CET", "Italy"),
    "netherlands": (1.0, "CET", "Netherlands"),
    "nl": (1.0, "CET", "Netherlands"),
    "poland": (1.0, "CET", "Poland"),
    "pl": (1.0, "CET", "Poland"),
    "switzerland": (1.0, "CET", "Switzerland"),
    "ch": (1.0, "CET", "Switzerland"),
    "austria": (1.0, "CET", "Austria"),
    "at": (1.0, "CET", "Austria"),
    "united kingdom": (0.0, "GMT", "United Kingdom"),
    "uk": (0.0, "GMT", "United Kingdom"),
    "co.uk": (0.0, "GMT", "United Kingdom"),
    "ireland": (0.0, "GMT", "Ireland"),
    "ie": (0.0, "GMT", "Ireland"),
    "russia": (3.0, "MSK", "Russia"),
    "ru": (3.0, "MSK", "Russia"),
    # North America
    "united states": (-5.0, "EST", "United States"),
    "usa": (-5.0, "EST", "United States"),
    "us": (-5.0, "EST", "United States"),
    "com": (-5.0, "EST", "United States"),
    "canada": (-5.0, "EST", "Canada"),
    "ca": (-5.0, "EST", "Canada"),
    # Middle East
    "united arab emirates": (4.0, "GST", "United Arab Emirates"),
    "uae": (4.0, "GST", "United Arab Emirates"),
    "ae": (4.0, "GST", "United Arab Emirates"),
    "saudi arabia": (3.0, "AST", "Saudi Arabia"),
    "saudi": (3.0, "AST", "Saudi Arabia"),
    "sa": (3.0, "AST", "Saudi Arabia"),
    "qatar": (3.0, "AST", "Qatar"),
    "qa": (3.0, "AST", "Qatar"),
    # Asia Pacific
    "australia": (10.0, "AEST", "Australia"),
    "au": (10.0, "AEST", "Australia"),
    "com.au": (10.0, "AEST", "Australia"),
    "singapore": (8.0, "SGT", "Singapore"),
    "sg": (8.0, "SGT", "Singapore"),
    # South Asia
    "india": (5.5, "IST", "India"),
    "in": (5.5, "IST", "India"),
    "pakistan": (5.0, "PKT", "Pakistan"),
    "pk": (5.0, "PKT", "Pakistan"),
    # Default
    "default": (1.0, "CET", "Germany")
}


class TimezoneScheduler:
    """
    Regional Working Hours Engine:
    Detects target country/timezone from domain TLD or country metadata.
    Enforces email dispatches strictly within local business hours:
      - Window 1: 9:00 AM - 11:00 AM local time
      - Window 2: 2:00 PM - 5:00 PM (14:00 - 17:00) local time
    Ensures weekends (Sat/Sun) roll over to Monday morning.
    """

    @classmethod
    def detect_timezone_info(cls, country: Optional[str] = None, domain: Optional[str] = None) -> Tuple[float, str, str]:
        """
        Resolves (utc_offset_hours, timezone_code, resolved_country) from country or domain TLD.
        """
        # 1. Check domain TLD first if available
        if domain:
            dom = domain.strip().lower()
            parts = dom.split(".")
            if len(parts) >= 2:
                # Check multi-part tld like co.uk or com.au
                if len(parts) >= 3:
                    sub_tld = f"{parts[-2]}.{parts[-1]}"
                    if sub_tld in REGIONAL_TIMEZONE_MAP:
                        return REGIONAL_TIMEZONE_MAP[sub_tld]
                tld = parts[-1]
                if tld in REGIONAL_TIMEZONE_MAP:
                    return REGIONAL_TIMEZONE_MAP[tld]

        # 2. Check country string
        if country:
            clean = country.strip().lower()
            # 2a. Exact match
            if clean in REGIONAL_TIMEZONE_MAP:
                return REGIONAL_TIMEZONE_MAP[clean]
            # 2b. Longer country names substring match (avoid 2-letter codes like "it" matching "united kingdom")
            for key, val in REGIONAL_TIMEZONE_MAP.items():
                if len(key) > 2 and (key in clean or clean in key):
                    return val
            # 2c. Token/word match for 2-letter codes (e.g. "UK", "US", "DE")
            for word in clean.split():
                if word in REGIONAL_TIMEZONE_MAP:
                    return REGIONAL_TIMEZONE_MAP[word]

        return REGIONAL_TIMEZONE_MAP["default"]

    @classmethod
    def get_target_local_time(cls, country: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        """Calculates current wall-clock time in the target country/timezone."""
        offset_hours, tz_code, resolved_country = cls.detect_timezone_info(country, domain)
        now_utc = datetime.now(timezone.utc)
        target_local = now_utc + timedelta(hours=offset_hours)

        hour = target_local.hour
        minute = target_local.minute
        is_weekday = target_local.weekday() < 5  # Mon-Fri (0-4)

        # Regional business hours: 9 AM - 11 AM AND 2 PM - 5 PM (14:00 - 17:00)
        is_morning_window = (9 <= hour < 11)
        is_afternoon_window = (14 <= hour < 17)
        is_in_send_window = (is_morning_window or is_afternoon_window) and is_weekday

        if is_morning_window and is_weekday:
            window_desc = "Active Morning Window (09:00 - 11:00 local)"
        elif is_afternoon_window and is_weekday:
            window_desc = "Active Afternoon Window (14:00 - 17:00 local)"
        elif not is_weekday:
            window_desc = "Weekend (Queued for Monday 09:00 AM local)"
        elif hour < 9:
            window_desc = "Pre-Morning (Queued for today 09:00 AM local)"
        elif 11 <= hour < 14:
            window_desc = "Midday Intermission (Queued for today 14:00 local)"
        else:
            window_desc = "After-Hours (Queued for next business day 09:00 AM local)"

        return {
            "country": country or resolved_country,
            "resolved_country": resolved_country,
            "timezone_code": tz_code,
            "utc_offset_hours": offset_hours,
            "current_local_time": target_local.strftime("%Y-%m-%d %H:%M:%S"),
            "current_local_hour": hour,
            "current_local_minute": minute,
            "is_in_send_window": is_in_send_window,
            "is_weekday": is_weekday,
            "window_description": window_desc
        }

    @classmethod
    def calculate_next_send_slot(cls, country: Optional[str] = None, domain: Optional[str] = None) -> datetime:
        """
        Calculates the exact UTC timestamp for the next dispatch window.
        Windows: 09:00 local OR 14:00 local on weekdays.
        """
        offset_hours, _, _ = cls.detect_timezone_info(country, domain)
        now_utc = datetime.now(timezone.utc)
        target_local = now_utc + timedelta(hours=offset_hours)

        # If currently on a weekend (Saturday=5, Sunday=6), advance to next Monday at 9:00 AM
        if target_local.weekday() >= 5:
            days_to_monday = 7 - target_local.weekday()
            next_local = (target_local + timedelta(days=days_to_monday)).replace(hour=9, minute=0, second=0, microsecond=0)
            return next_local - timedelta(hours=offset_hours)

        # On a weekday:
        hour = target_local.hour
        if hour < 9:
            # Schedule today at 09:00 AM
            next_local = target_local.replace(hour=9, minute=0, second=0, microsecond=0)
        elif 9 <= hour < 11:
            # Inside morning window: immediate dispatch slot
            return now_utc
        elif 11 <= hour < 14:
            # Schedule today at 14:00 (2:00 PM)
            next_local = target_local.replace(hour=14, minute=0, second=0, microsecond=0)
        elif 14 <= hour < 17:
            # Inside afternoon window: immediate dispatch slot
            return now_utc
        else:
            # Past 17:00, advance to next business day at 09:00 AM
            next_day = target_local + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            next_local = next_day.replace(hour=9, minute=0, second=0, microsecond=0)

        return next_local - timedelta(hours=offset_hours)


_global_scheduler = None

def get_scheduler() -> TimezoneScheduler:
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TimezoneScheduler()
    return _global_scheduler
