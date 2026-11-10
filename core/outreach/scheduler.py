"""
H.Huddair's Nexus-Pulse - Level 2
Outreach Engine: Time-Zone Smart Scheduler
Enforces strict dispatching windows during target country office hours (9:00 AM - 11:00 AM local time).
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple


# Target Country -> UTC Offset & Timezone Code
TIMEZONE_OFFSETS: Dict[str, Tuple[int, str]] = {
    "germany": (1, "CET"),
    "france": (1, "CET"),
    "spain": (1, "CET"),
    "italy": (1, "CET"),
    "netherlands": (1, "CET"),
    "poland": (1, "CET"),
    "united kingdom": (0, "GMT"),
    "ireland": (0, "GMT"),
    "russia": (3, "MSK"),
    "united states": (-5, "EST"),  # Defaulting to Eastern; regional adjustments available
    "canada": (-5, "EST"),
    "united arab emirates": (4, "GST"),
    "saudi arabia": (3, "AST"),
    "default": (1, "CET")
}


class TimezoneScheduler:
    """
    Computes local business hours for target countries and ensures
    outreach is dispatched strictly between 9:00 AM and 11:00 AM local time.
    """

    @staticmethod
    def get_country_timezone_info(country: str) -> Tuple[int, str]:
        """Returns (utc_offset_hours, timezone_code) for target country."""
        clean = country.strip().lower()
        for k, v in TIMEZONE_OFFSETS.items():
            if k in clean or clean in k:
                return v
        return TIMEZONE_OFFSETS["default"]

    @classmethod
    def get_target_local_time(cls, country: str) -> Dict[str, Any]:
        """Calculates current wall-clock time in the target country."""
        offset_hours, tz_code = cls.get_country_timezone_info(country)
        now_utc = datetime.now(timezone.utc)
        target_local = now_utc + timedelta(hours=offset_hours)

        hour = target_local.hour
        minute = target_local.minute
        is_office_hours = (9 <= hour < 11)  # Strictly 9:00 AM - 11:00 AM window
        is_weekday = target_local.weekday() < 5  # Mon-Fri (0-4)

        return {
            "country": country,
            "timezone_code": tz_code,
            "utc_offset_hours": offset_hours,
            "current_local_time": target_local.strftime("%Y-%m-%d %H:%M:%S"),
            "current_local_hour": hour,
            "is_in_send_window": is_office_hours and is_weekday,
            "is_weekday": is_weekday,
            "window_description": "Active Office Window (09:00 - 11:00 local)" if is_office_hours else "Outside Office Window (Queued for next 09:00 AM)"
        }

    @classmethod
    def calculate_next_send_slot(cls, country: str) -> datetime:
        """
        Calculates the exact UTC timestamp for the next 9:00 AM local time slot.
        If current local time is before 9 AM on a weekday, schedules for today at 9 AM.
        If past 11 AM or on a weekend, advances to the next weekday at 9 AM.
        """
        offset_hours, _ = cls.get_country_timezone_info(country)
        now_utc = datetime.now(timezone.utc)
        target_local = now_utc + timedelta(hours=offset_hours)

        # Candidate: today at 9:00 AM
        next_local = target_local.replace(hour=9, minute=0, second=0, microsecond=0)

        # If already past 11:00 AM today, or past 9:00 AM when window missed, advance day
        if target_local.hour >= 11 or (target_local.hour >= 9 and target_local.minute > 59):
            next_local += timedelta(days=1)
        elif target_local.hour < 9:
            pass  # today at 9:00 AM is good

        # If landed on weekend (Saturday=5, Sunday=6), roll to Monday
        while next_local.weekday() >= 5:
            next_local += timedelta(days=1)

        # Convert target_local back to UTC
        scheduled_utc = next_local - timedelta(hours=offset_hours)
        return scheduled_utc


_global_scheduler = None

def get_scheduler() -> TimezoneScheduler:
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TimezoneScheduler()
    return _global_scheduler
