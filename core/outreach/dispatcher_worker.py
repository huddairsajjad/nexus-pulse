"""
Nexus-Pulse Enterprise Build
Outreach Engine: Background Dispatcher Worker & Queue Orchestrator
Continuously monitors approved and scheduled outreach leads.
Enforces dynamic timezone working hours (9:00 AM to 5:00 PM local recipient time).
Provides instant manual bypass window override and telemetry reporting.
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .approval_gate import get_approval_gate
from .scheduler import get_scheduler
from database.db_engine import get_db_engine

logger = logging.getLogger("nexus.dispatcher_worker")


class DispatcherWorker:
    """
    Background worker that orchestrates automated queue dispatch according to
    local business hours and per-tenant bypass toggles.
    All status transitions (DISPATCHING -> RUNNING), bypass flags, and telemetry
    counts are strictly isolated per authenticated user/tenant.
    """

    def __init__(self):
        self.status = "RUNNING"  # Fallback default when no tenant specified
        self.bypass_window = False
        self.last_run_at: Optional[str] = None
        self.total_dispatched = 0
        self.last_result: Dict[str, Any] = {}
        self._is_processing = False
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        self._tenant_states: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _tenant_key(operator_id: Optional[str] = None, owner_username: Optional[str] = None) -> str:
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        if owner:
            return f"owner:{owner}"
        if op_id:
            return f"op:{op_id}"
        return "__global__"

    def _get_or_create_tenant_state(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = self._tenant_key(operator_id=operator_id, owner_username=owner_username)
        if key not in self._tenant_states:
            self._tenant_states[key] = {
                "status": "RUNNING",
                "bypass_window": self.bypass_window,
                "last_run_at": None,
                "total_dispatched": 0,
                "last_result": {},
                "active_dispatches": 0,
            }
        return self._tenant_states[key]

    def set_bypass_window(
        self,
        bypass: bool,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
    ) -> bool:
        """Enables or disables immediate dispatch bypass mode strictly for the given tenant."""
        val = bool(bypass)
        with self._lock:
            key = self._tenant_key(operator_id=operator_id, owner_username=owner_username)
            if key == "__global__":
                self.bypass_window = val
            state = self._get_or_create_tenant_state(operator_id=operator_id, owner_username=owner_username)
            state["bypass_window"] = val
        logger.info(f"[DISPATCHER] Bypass window override for {key} set to: {val}")
        return val

    def get_bypass_window(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
    ) -> bool:
        with self._lock:
            key = self._tenant_key(operator_id=operator_id, owner_username=owner_username)
            if key in self._tenant_states:
                return bool(self._tenant_states[key]["bypass_window"])
            return bool(self.bypass_window)

    def begin_tenant_dispatch(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
    ) -> bool:
        """
        Marks the current tenant's engine status as DISPATCHING.
        Always pair with end_tenant_dispatch in a try/finally block.
        """
        with self._lock:
            state = self._get_or_create_tenant_state(operator_id=operator_id, owner_username=owner_username)
            state["active_dispatches"] += 1
            state["status"] = "DISPATCHING"
            if self._tenant_key(operator_id, owner_username) == "__global__":
                self._is_processing = True
                self.status = "DISPATCHING"
            return True

    def end_tenant_dispatch(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        dispatched_count: int = 0,
        last_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Cleanly resets the tenant's engine status from DISPATCHING back to RUNNING,
        even when an error or timeout occurred.
        """
        with self._lock:
            state = self._get_or_create_tenant_state(operator_id=operator_id, owner_username=owner_username)
            state["active_dispatches"] = max(0, state["active_dispatches"] - 1)
            if state["active_dispatches"] == 0:
                state["status"] = "RUNNING"
            if dispatched_count:
                state["total_dispatched"] += int(dispatched_count)
            if last_result is not None:
                state["last_result"] = last_result
                state["last_run_at"] = datetime.now(timezone.utc).isoformat()
            if self._tenant_key(operator_id, owner_username) == "__global__":
                self._is_processing = state["active_dispatches"] > 0
                if not self._is_processing:
                    self.status = "RUNNING"
                self.total_dispatched = state["total_dispatched"]
                if last_result is not None:
                    self.last_result = last_result
                    self.last_run_at = state["last_run_at"]

    def get_telemetry(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        """Provides real-time telemetry on the dispatch engine state strictly scoped to the tenant."""
        db = get_db_engine()
        op_id = (operator_id or "").strip()
        owner = (owner_username or "").strip().lower()
        counts = {"pending": 0, "approved": 0, "scheduled": 0, "sent": 0}
        try:
            with db.get_connection() as conn:
                if owner or op_id:
                    if is_admin:
                        rows = conn.execute("""
                            SELECT status, count(*) as cnt
                            FROM outreach_queue
                            WHERE (lower(owner_username) = ? OR operator_id = ? OR owner_username = '' OR owner_username IS NULL)
                            GROUP BY status
                        """, (owner, op_id)).fetchall()
                    else:
                        rows = conn.execute("""
                            SELECT status, count(*) as cnt
                            FROM outreach_queue
                            WHERE (lower(owner_username) = ? OR operator_id = ?)
                            GROUP BY status
                        """, (owner, op_id)).fetchall()
                else:
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
                    elif st in ("sent", "dispatched"):
                        counts["sent"] += r["cnt"]
        except Exception as e:
            logger.warning(f"[DISPATCHER] Telemetry count error: {e}")

        with self._lock:
            state = dict(self._get_or_create_tenant_state(operator_id=op_id or None, owner_username=owner or None))

        active_status = "DISPATCHING" if state["active_dispatches"] > 0 else "RUNNING"

        return {
            "status": active_status,
            "bypass_window": bool(state["bypass_window"]),
            "last_run_at": state["last_run_at"],
            "total_dispatched": state["total_dispatched"],
            "pending_count": counts["pending"],
            "approved_count": counts["approved"],
            "scheduled_count": counts["scheduled"],
            "sent_count": counts["sent"],
            "last_result": state["last_result"]
        }

    async def execute_cycle(
        self,
        bypass_window: Optional[bool] = None,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single dispatch pass scoped per tenant.
        Always resets tenant engine status from DISPATCHING back to RUNNING in try/finally.
        """
        op_id = (operator_id or "").strip() or None
        owner = (owner_username or "").strip().lower() or None

        if op_id or owner:
            with self._lock:
                state = self._get_or_create_tenant_state(operator_id=op_id, owner_username=owner)
                if state["active_dispatches"] > 0:
                    return {"success": False, "message": "Dispatcher is already executing a cycle for this workspace."}
            effective_bypass = self.get_bypass_window(op_id, owner) if bypass_window is None else bool(bypass_window)
            self.begin_tenant_dispatch(operator_id=op_id, owner_username=owner)
            res: Dict[str, Any] = {}
            try:
                gate = get_approval_gate()
                res = gate.dispatch_ready_queue(
                    bypass_window=effective_bypass,
                    operator_id=op_id,
                    owner_username=owner,
                )
                if res.get("dispatched_count", 0) > 0:
                    logger.info(f"[DISPATCHER] Cycle completed for {owner or op_id}: Dispatched {res['dispatched_count']} leads (Bypass: {effective_bypass})")
                return res
            except Exception as e:
                logger.error(f"[DISPATCHER] Cycle error for {owner or op_id}: {e}", exc_info=True)
                res = {"success": False, "error": str(e)}
                return res
            finally:
                self.end_tenant_dispatch(
                    operator_id=op_id,
                    owner_username=owner,
                    dispatched_count=res.get("dispatched_count", 0),
                    last_result=res,
                )

        # Background worker pass: run each tenant with queued items independently
        if self._is_processing:
            return {"success": False, "message": "Dispatcher is already executing a cycle."}

        self._is_processing = True
        self.status = "DISPATCHING"
        total_dispatched = 0
        total_scheduled = 0
        total_errors = 0
        try:
            db = get_db_engine()
            tenants = []
            with db.get_connection() as conn:
                t_rows = conn.execute("""
                    SELECT DISTINCT COALESCE(lower(owner_username), '') as owner_u, COALESCE(operator_id, '') as op_id
                    FROM outreach_queue
                    WHERE status IN ('APPROVED', 'SCHEDULED', 'FAILED')
                """).fetchall()
                tenants = [(r["op_id"] or None, r["owner_u"] or None) for r in t_rows]

            gate = get_approval_gate()
            for t_op, t_owner in tenants:
                t_bypass = self.get_bypass_window(t_op, t_owner) if bypass_window is None else bool(bypass_window)
                self.begin_tenant_dispatch(operator_id=t_op, owner_username=t_owner)
                t_res: Dict[str, Any] = {}
                try:
                    t_res = gate.dispatch_ready_queue(
                        bypass_window=t_bypass,
                        operator_id=t_op,
                        owner_username=t_owner,
                    )
                    total_dispatched += t_res.get("dispatched_count", 0)
                    total_scheduled += t_res.get("scheduled_count", 0)
                    total_errors += t_res.get("error_count", 0)
                except Exception as te:
                    logger.error(f"[DISPATCHER] Background tenant cycle error ({t_owner or t_op}): {te}")
                    t_res = {"success": False, "error": str(te)}
                finally:
                    self.end_tenant_dispatch(
                        operator_id=t_op,
                        owner_username=t_owner,
                        dispatched_count=t_res.get("dispatched_count", 0),
                        last_result=t_res,
                    )

            self.last_run_at = datetime.now(timezone.utc).isoformat()
            self.total_dispatched += total_dispatched
            self.last_result = {
                "success": True,
                "dispatched_count": total_dispatched,
                "scheduled_count": total_scheduled,
                "error_count": total_errors,
            }
            return self.last_result
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
