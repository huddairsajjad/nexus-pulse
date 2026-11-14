"""
Nexus-Pulse Enterprise Build
Outreach Engine: Background Dispatcher Worker & Queue Orchestrator
Continuously monitors approved and scheduled outreach leads.
Enforces dynamic timezone working hours (9:00 AM to 5:00 PM local recipient time).
Provides instant manual bypass window override and telemetry reporting.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .approval_gate import get_approval_gate
from .scheduler import get_scheduler
from database.db_engine import get_db_engine

logger = logging.getLogger("nexus.dispatcher_worker")


class DispatcherWorker:
    """
    Background worker that orchestrates automated queue dispatch according to
    local business hours and admin bypass toggles.
    """

    def __init__(self):
        self.status = "RUNNING"  # "IDLE", "RUNNING", "DISPATCHING"
        self.bypass_window = False
        self.last_run_at: Optional[str] = None
        self.total_dispatched = 0
        self.last_result: Dict[str, Any] = {}
        self._is_processing = False
        self._loop_task: Optional[asyncio.Task] = None

    def set_bypass_window(self, bypass: bool) -> bool:
        """Enables or disables immediate dispatch bypass mode."""
        self.bypass_window = bool(bypass)
        logger.info(f"[DISPATCHER] Manual bypass window override set to: {self.bypass_window}")
        return self.bypass_window

    def get_telemetry(self) -> Dict[str, Any]:
        """Provides real-time telemetry on the dispatch engine state."""
        db = get_db_engine()
        counts = {"pending": 0, "approved": 0, "scheduled": 0, "sent": 0}
        try:
            with db.get_connection() as conn:
                rows = conn.execute("""
                    SELECT status, count(*) as cnt
                    FROM outreach_queue
                    GROUP BY status
                """).fetchall()
                for r in rows:
                    st = (r["status"] or "").lower()
                    if "pending" in st:
                        counts["pending"] += r["cnt"]
                    elif "approved" in st:
                        counts["approved"] += r["cnt"]
                    elif "scheduled" in st:
                        counts["scheduled"] += r["cnt"]
                    elif "sent" in st:
                        counts["sent"] += r["cnt"]
        except Exception as e:
            logger.warning(f"[DISPATCHER] Telemetry count error: {e}")

        # Engine status: if processing -> DISPATCHING; if active items -> RUNNING; else RUNNING/IDLE
        active_status = self.status
        if self._is_processing:
            active_status = "DISPATCHING"
        elif counts["approved"] > 0 or counts["scheduled"] > 0:
            active_status = "RUNNING"
        elif active_status == "DISPATCHING":
            active_status = "RUNNING"

        return {
            "status": active_status,
            "bypass_window": self.bypass_window,
            "last_run_at": self.last_run_at,
            "total_dispatched": self.total_dispatched,
            "pending_count": counts["pending"],
            "approved_count": counts["approved"],
            "scheduled_count": counts["scheduled"],
            "sent_count": counts["sent"],
            "last_result": self.last_result
        }

    async def execute_cycle(self, bypass_window: Optional[bool] = None, operator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a single dispatch pass.
        If bypass_window is True (or engine default is True), dispatches all approved leads immediately.
        Otherwise, only dispatches leads currently within their 9:00 AM - 5:00 PM local business window.
        """
        if self._is_processing:
            return {"success": False, "message": "Dispatcher is already executing a cycle."}

        self._is_processing = True
        self.status = "DISPATCHING"
        effective_bypass = self.bypass_window if bypass_window is None else bool(bypass_window)

        try:
            gate = get_approval_gate()
            res = gate.dispatch_ready_queue(bypass_window=effective_bypass, operator_id=operator_id)
            self.last_run_at = datetime.now(timezone.utc).isoformat()
            self.total_dispatched += res.get("dispatched_count", 0)
            self.last_result = res
            if res.get("dispatched_count", 0) > 0:
                logger.info(f"[DISPATCHER] Cycle completed: Dispatched {res['dispatched_count']} leads (Bypass: {effective_bypass})")
            return res
        except Exception as e:
            logger.error(f"[DISPATCHER] Cycle error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            self._is_processing = False
            self.status = "RUNNING"

    async def start_background_loop(self, interval_seconds: int = 30):
        """Asynchronous background loop running periodically during server lifespan."""
        logger.info(f"[DISPATCHER] Background worker loop started (interval: {interval_seconds}s, bypass: {self.bypass_window})")
        self.status = "RUNNING"
        while True:
            try:
                await self.execute_cycle()
            except asyncio.CancelledError:
                logger.info("[DISPATCHER] Background loop received cancel signal.")
                break
            except Exception as e:
                logger.error(f"[DISPATCHER] Background loop unhandled exception: {e}")

            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break


_global_dispatcher_worker: Optional[DispatcherWorker] = None


def get_dispatcher_worker() -> DispatcherWorker:
    global _global_dispatcher_worker
    if _global_dispatcher_worker is None:
        _global_dispatcher_worker = DispatcherWorker()
    return _global_dispatcher_worker
