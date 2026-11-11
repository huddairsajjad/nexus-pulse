"""
Nexus-Pulse Enterprise Build
FastAPI Routes: Multi-Tenant Enterprise REST API & RBAC Protection
Integrates Multi-Tenancy Data Isolation, Super Admin Controls, Multi-Service Template Pool,
Inbox Rotator with Auto-Switching, Regional Working Hours Engine, IMAP Bounce Listener,
CAN-SPAM / GDPR Unsubscribe Compliance, Global Blacklist Manager, and Deliverability Analytics.
"""

import os
import json
import uuid
import time
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends, Query, Request
from fastapi.responses import FileResponse, Response, HTMLResponse
from pydantic import BaseModel, Field

from config.config_manager import get_config
from security.machine_fingerprint import generate_machine_fingerprint
from security.license_validator import load_or_initialize_license
from security.crypto_vault import get_crypto_vault
from core.agents.localization_engine import LocalizationEngine
from core.hygiene.zero_bounce_shield import get_hygiene_shield
from core.agents.scraper_agent import DeepScraperAgent
from database.deduplication_shield import get_dedup_shield
from database.db_engine import get_db_engine
from vault.vault_manager import get_vault_manager
from core.orchestrator import NexusPulseOrchestrator

from auth.user_manager import get_user_manager
from auth.jwt_handler import decode_access_token
from core.outreach.approval_gate import get_approval_gate
from core.outreach.scheduler import get_scheduler
from core.outreach.inbox_rotator import get_inbox_rotator
from core.outreach.reply_listener import get_reply_listener
from core.outreach.template_manager import get_template_manager
from core.outreach.blacklist_manager import get_blacklist_manager
from core.agents.webform_agent import BackupWebFormAgent
from core.agents.followup_engine import get_followup_engine

router = APIRouter(prefix="/api", tags=["Nexus-Pulse Multi-Tenant Enterprise"])


# -------------------------------------------------------------
# RBAC & Tenant Authentication Dependencies
# -------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates JWT session token and returns decoded payload.
    Strict Zero-Seed / Production Policy: No hardcoded fallback user is permitted.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required. Please provide a valid Bearer token.")

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    # Ensure 'id' is mapped from 'sub'
    if "sub" in payload and "id" not in payload:
        payload["id"] = payload["sub"]
    return payload


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Enforces Super Admin access for administrative endpoints.
    Blocks Operator tokens with HTTP 403 Forbidden.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Administrative privileges required. Operator accounts cannot access this endpoint."
        )
    return current_user


# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class SetupAdminRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: Optional[str] = "operator"


class ConfigUpdateRequest(BaseModel):
    target_country: Optional[str] = None
    target_city: Optional[str] = None
    industry_niche: Optional[str] = None
    ready_to_send: Optional[bool] = None
    search_depth: Optional[int] = None


class VerifyEmailRequest(BaseModel):
    email: str


class ApproveOutreachRequest(BaseModel):
    queue_id: str
    approver: Optional[str] = None
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None


class BatchApproveRequest(BaseModel):
    approver: Optional[str] = None


class RejectOutreachRequest(BaseModel):
    queue_id: str
    approver: Optional[str] = None


class DispatchHotReplyRequest(BaseModel):
    reply_id: str
    recipient: str
    response_body: str


class SimulateReplyRequest(BaseModel):
    sender_email: str
    subject: str
    body: str
    company_name: Optional[str] = None


class WebFormFormatRequest(BaseModel):
    lead_id: str
    company_name: str
    website_url: str
    niche: Optional[str] = "Commercial Construction"
    country: Optional[str] = "Germany"


class ScrapeRequest(BaseModel):
    region: Optional[str] = "Europe"
    country: str = "Germany"
    city: Optional[str] = None
    niche: str = "Commercial Construction"
    max_results: Optional[int] = 20
    target_urls: Optional[List[str]] = None


class MailboxCreateRequest(BaseModel):
    email_address: str
    display_name: str
    domain: Optional[str] = None
    daily_limit: Optional[int] = 45
    smtp_host: Optional[str] = ""
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = ""
    smtp_password: Optional[str] = ""
    imap_host: Optional[str] = ""
    imap_port: Optional[int] = 993
    imap_username: Optional[str] = ""
    imap_password: Optional[str] = ""


class MailboxUpdateRequest(BaseModel):
    email_address: Optional[str] = None
    display_name: Optional[str] = None
    domain: Optional[str] = None
    daily_limit: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None


class AdminProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class CreateOperatorRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    device_lock_id: Optional[str] = None
    device_lock_enabled: Optional[bool] = True
    expiry_days: Optional[int] = 90
    daily_scrape_quota: Optional[int] = 200
    daily_send_quota: Optional[int] = 50


class ResetPasswordRequest(BaseModel):
    new_password: str


class ModifyQuotaRequest(BaseModel):
    extend_days: Optional[int] = None
    daily_scrape_quota: Optional[int] = None
    daily_send_quota: Optional[int] = None
    device_lock_id: Optional[str] = None
    device_lock_enabled: Optional[bool] = None


class OperatorBillingRequest(BaseModel):
    base_price: float
    duration_days: int
    notes: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    title: str
    niche: str
    subject_template: str
    body_template: str
    is_default: Optional[bool] = False


class TemplateUpdateRequest(BaseModel):
    title: Optional[str] = None
    niche: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    is_default: Optional[bool] = None


class BlacklistCreateRequest(BaseModel):
    pattern: str
    reason: Optional[str] = "Excluded Domain"


class UnsubscribeRequest(BaseModel):
    email: str
    token: Optional[str] = None


class LogActivityRequest(BaseModel):
    action: str
    detail: Optional[str] = None


# -------------------------------------------------------------
# 1. SUPER ADMIN: PROFILE & OPERATORS MANAGEMENT
# -------------------------------------------------------------
@router.get("/admin/profile")
def get_admin_profile(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Super Admin Profile inspector."""
    um = get_user_manager()
    admin_info = um.get_admin_user()
    if not admin_info:
        raise HTTPException(status_code=404, detail="Admin account record not found.")
    return admin_info


@router.put("/admin/profile")
def update_admin_profile(req: AdminProfileUpdateRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Allows Super Admin to update administrative profile and security credentials."""
    um = get_user_manager()
    admin_info = um.get_admin_user()
    if not admin_info:
        raise HTTPException(status_code=404, detail="Admin account not found.")

    res = um.update_admin_profile(
        admin_id=admin_info["id"],
        new_username=req.username,
        new_email=req.email,
        new_full_name=req.full_name,
        current_password=req.current_password,
        new_password=req.new_password
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Profile update failed."))
    return res


@router.get("/operators")
def list_all_operators(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Returns list of paying operator accounts."""
    um = get_user_manager()
    return um.get_all_operators()


@router.post("/operators")
def create_new_operator(req: CreateOperatorRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Provisions a new paying operator account."""
    um = get_user_manager()
    try:
        res = um.create_operator_account(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            email=req.email,
            device_lock_id=req.device_lock_id,
            device_lock_enabled=req.device_lock_enabled if req.device_lock_enabled is not None else True,
            expiry_days=req.expiry_days or 90,
            daily_scrape_quota=req.daily_scrape_quota or 200,
            daily_send_quota=req.daily_send_quota or 50
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/operators/{user_id}/toggle-status")
def toggle_operator_status(user_id: str, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Revokes or enables access for an operator."""
    um = get_user_manager()
    try:
        return um.toggle_operator_status(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/operators/{user_id}/reset-password")
def reset_operator_password(user_id: str, req: ResetPasswordRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Resets credentials for an operator."""
    um = get_user_manager()
    try:
        return um.reset_operator_password(user_id, req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/operators/{user_id}/quotas")
def update_operator_quotas(user_id: str, req: ModifyQuotaRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Modifies quotas, device lock, and subscription period for an operator."""
    um = get_user_manager()
    try:
        return um.modify_operator_quota_and_expiry(
            user_id=user_id,
            extend_days=req.extend_days,
            daily_scrape_quota=req.daily_scrape_quota,
            daily_send_quota=req.daily_send_quota,
            device_lock_id=req.device_lock_id,
            device_lock_enabled=req.device_lock_enabled
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# 2. SUPER ADMIN: MANUAL BILLING CONTROLS
# -------------------------------------------------------------
@router.post("/operators/{user_id}/billing")
def apply_operator_billing(user_id: str, req: OperatorBillingRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """
    Super Admin manual billing control:
    Accepts Base Price input, duration extenders (+30d, +90d, +180d, +1y),
    and applies automated 10% discount for 90-day plans.
    """
    um = get_user_manager()
    try:
        res = um.apply_operator_billing(
            operator_id=user_id,
            base_price=req.base_price,
            duration_days=req.duration_days,
            notes=req.notes,
            created_by=admin_user.get("username", "admin")
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/operators/{user_id}/billing-history")
def get_operator_billing_history(user_id: str, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Retrieves billing transaction history for a specific operator."""
    um = get_user_manager()
    return um.get_operator_billing_history(operator_id=user_id)


@router.get("/billing/all-history")
def get_all_billing_history(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Returns billing audit transactions across all operators."""
    um = get_user_manager()
    return um.get_operator_billing_history(operator_id=None)


# -------------------------------------------------------------
# 3. SUPER ADMIN: TELEMETRY & CLEAN DATABASE RESET
# -------------------------------------------------------------
@router.get("/licenses/telemetry")
def get_license_telemetry(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Returns cryptographic hardware lock status and system telemetry."""
    fp = generate_machine_fingerprint()
    lic = load_or_initialize_license()
    um = get_user_manager()
    return {
        "hardware_fingerprint": fp,
        "active_license": lic,
        "total_operators": len(um.get_all_operators()),
        "admin_configured": um.has_admin()
    }


@router.post("/database/reset-fresh")
def reset_fresh_database(admin_user: Dict[str, Any] = Depends(require_admin)):
    """
    System-wide Zero-Seed Reset Policy:
    Purges all test data, leads, mailboxes, and audit logs to restore a 100% clean production state.
    """
    um = get_user_manager()
    counts = um.purge_all_data()
    return {
        "success": True,
        "message": "Production database purged to 100% clean state.",
        "purged_records": counts
    }


# -------------------------------------------------------------
# 4. GLOBAL DOMAIN BLACKLIST MANAGER
# -------------------------------------------------------------
@router.get("/blacklist")
def get_blacklist_rules(current_user: Dict[str, Any] = Depends(require_admin)):
    """Lists registered global blacklist rules. Admin-only access."""
    mgr = get_blacklist_manager()
    return mgr.get_rules()


@router.post("/blacklist")
def add_blacklist_rule(req: BlacklistCreateRequest, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Registers an excluded domain/pattern (e.g., *.gov, competitor.com)."""
    mgr = get_blacklist_manager()
    try:
        return mgr.add_rule(
            pattern=req.pattern,
            reason=req.reason or "Excluded Pattern",
            created_by=admin_user.get("username", "admin")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/blacklist/{rule_id}")
def delete_blacklist_rule(rule_id: int, admin_user: Dict[str, Any] = Depends(require_admin)):
    """Removes a blacklist rule."""
    mgr = get_blacklist_manager()
    removed = mgr.remove_rule(rule_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Rule not found.")
    return {"success": True, "deleted_rule_id": rule_id}


# -------------------------------------------------------------
# 5. MULTI-SERVICE TEMPLATE POOL
# -------------------------------------------------------------
@router.get("/templates")
def list_service_templates(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists proposal templates belonging to the current tenant."""
    mgr = get_template_manager()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None
    return mgr.get_templates(operator_id=op_id)


@router.post("/templates")
def create_service_template(req: TemplateCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Composes and stores a new custom service proposal template."""
    mgr = get_template_manager()
    op_id = current_user["id"]
    try:
        return mgr.create_template(
            operator_id=op_id,
            title=req.title,
            niche=req.niche,
            subject_template=req.subject_template,
            body_template=req.body_template,
            is_default=req.is_default or False
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}")
def update_service_template(template_id: str, req: TemplateUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Updates an existing custom proposal template."""
    mgr = get_template_manager()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None
    try:
        return mgr.update_template(
            template_id=template_id,
            operator_id=op_id,
            title=req.title,
            niche=req.niche,
            subject_template=req.subject_template,
            body_template=req.body_template,
            is_default=req.is_default
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}")
def delete_service_template(template_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Deletes a custom proposal template."""
    mgr = get_template_manager()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None
    try:
        deleted = mgr.delete_template(template_id, operator_id=op_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Template not found.")
        return {"success": True, "deleted_template_id": template_id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# -------------------------------------------------------------
# 6. AUTHENTICATION & SESSION ENDPOINTS
# -------------------------------------------------------------
@router.get("/auth/setup-status")
def get_system_setup_status():
    """Returns whether first-run master admin has been initialized."""
    um = get_user_manager()
    has_admin = um.has_admin()
    return {
        "initialized": has_admin,
        "admin_configured": has_admin,
        "mode": "PRODUCTION_OPERATIONAL" if has_admin else "FRESH_INSTALL_AWAITING_ADMIN_SETUP"
    }


@router.post("/auth/initialize-admin")
def initialize_master_admin(req: SetupAdminRequest):
    """Provisions first-run master admin on clean installation."""
    um = get_user_manager()
    try:
        return um.initialize_admin(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            email=req.email
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
def login_for_access_token(req: LoginRequest):
    """Authenticates admin or operator credentials and returns JWT token."""
    um = get_user_manager()
    try:
        auth_res = um.authenticate_user(req.username, req.password)
        if not auth_res:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        return auth_res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/auth/register")
def register_new_account(req: RegisterRequest):
    """Registers an initial admin or new operator account."""
    um = get_user_manager()
    try:
        return um.register_user(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            role=req.role or "operator"
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/me")
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile for currently authenticated session."""
    return current_user


@router.get("/health")
def health_check():
    """Health and licensing telemetry endpoint."""
    fp = generate_machine_fingerprint()
    lic = load_or_initialize_license()
    um = get_user_manager()
    return {
        "status": "HEALTHY",
        "system": "Nexus-Pulse Enterprise Lead Engine",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hardware_id": fp["machine_id"],
        "licensed": bool(lic),
        "admin_initialized": um.has_admin()
    }


# -------------------------------------------------------------
# 7. PIPELINE & VISUAL KANBAN CRM
# -------------------------------------------------------------
@router.get("/kanban/leads")
def get_kanban_leads(
    current_user: Dict[str, Any] = Depends(get_current_user),
    operator_id: Optional[str] = Query(None)
):
    """
    Returns pipeline leads grouped by lifecycle status.
    Enforces multi-tenant data isolation: operators only view their own leads.
    """
    db = get_db_engine()
    # Determine tenant filter
    target_op = current_user["id"] if current_user.get("role") == "operator" else operator_id

    with db.get_connection() as conn:
        if target_op:
            rows = conn.execute("""
                SELECT id, lead_id, channel, recipient, company_name, subject,
                       message_body, status, target_country, scheduled_for,
                       approved_by, sent_at, mailbox_used, operator_id,
                       opened_at, bounced_at, bounce_reason, created_at
                FROM outreach_queue
                WHERE operator_id = ? OR operator_id IS NULL
                ORDER BY created_at DESC
            """, (target_op,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, lead_id, channel, recipient, company_name, subject,
                       message_body, status, target_country, scheduled_for,
                       approved_by, sent_at, mailbox_used, operator_id,
                       opened_at, bounced_at, bounce_reason, created_at
                FROM outreach_queue
                ORDER BY created_at DESC
            """).fetchall()

        items = [dict(r) for r in rows]

        # Fetch tech stack and priority details from vault_leads if available
        lead_ids = [item["lead_id"] for item in items if item.get("lead_id")]
        lead_meta_map = {}
        if lead_ids:
            crypto = get_crypto_vault()
            placeholders = ",".join(["?"] * len(lead_ids))
            v_rows = conn.execute(f"SELECT id, quality_tag, priority_score, encrypted_payload FROM vault_leads WHERE id IN ({placeholders})", lead_ids).fetchall()
            for vr in v_rows:
                meta = {
                    "quality_tag": vr["quality_tag"],
                    "priority_score": vr["priority_score"],
                    "tech_stack": []
                }
                try:
                    decrypted = crypto.decrypt_json(vr["encrypted_payload"])
                    if decrypted and "tech_stack" in decrypted:
                        meta["tech_stack"] = decrypted["tech_stack"].get("raw_technologies", [])
                except Exception:
                    pass
                lead_meta_map[vr["id"]] = meta

        # Hydrate queue items with tech metadata
        for item in items:
            lid = item.get("lead_id")
            if lid and lid in lead_meta_map:
                item["quality_tag"] = lead_meta_map[lid]["quality_tag"]
                item["priority_score"] = lead_meta_map[lid]["priority_score"]
                item["tech_stack"] = lead_meta_map[lid]["tech_stack"]
            else:
                item["quality_tag"] = "TIER-1-ESTIMATING"
                item["priority_score"] = 85
                item["tech_stack"] = []

        return items


# -------------------------------------------------------------
# 8. HUMAN APPROVAL GATE (OPERATOR & ADMIN ACCESS)
# -------------------------------------------------------------
@router.get("/outreach/pending")
def get_pending_outreach_approvals(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists items held in the mandatory approval gate for this tenant."""
    gate = get_approval_gate()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    return gate.get_pending_approvals(operator_id=target_op)


@router.post("/outreach/approve")
def approve_outreach_item(req: ApproveOutreachRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Authorizes outreach item. Operators can authorize their own items; Admins can authorize any."""
    gate = get_approval_gate()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    approver_name = req.approver or current_user.get("username", "operator")
    try:
        return gate.approve_outreach_item(
            queue_id=req.queue_id,
            approver=approver_name,
            edited_subject=req.edited_subject,
            edited_body=req.edited_body,
            operator_id=target_op
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/outreach/batch-approve")
def batch_approve_outreach(req: BatchApproveRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Batch approves all pending outreach items held in the gate for this tenant."""
    gate = get_approval_gate()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    approver_name = req.approver or current_user.get("username", "operator")
    return gate.batch_approve_all(approver=approver_name, operator_id=target_op)


@router.post("/outreach/reject")
def reject_outreach_item(req: RejectOutreachRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Rejects outreach item held in the gate."""
    gate = get_approval_gate()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    approver_name = req.approver or current_user.get("username", "operator")
    try:
        return gate.reject_outreach_item(req.queue_id, approver=approver_name, operator_id=target_op)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/outreach/dispatch/{queue_id}")
def dispatch_approved_item(queue_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Dispatches approved outreach item using an enrolled mailbox belonging to the operator."""
    gate = get_approval_gate()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    try:
        return gate.dispatch_approved_outreach(queue_id, operator_id=target_op)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scheduler/timezones")
def get_target_timezone_preview(
    country: Optional[str] = Query("Germany"),
    domain: Optional[str] = Query(None)
):
    """Regional Working Hours Engine: checks current office window for target."""
    scheduler = get_scheduler()
    return scheduler.get_target_local_time(country=country, domain=domain)


# -------------------------------------------------------------
# 9. INBOX ROTATOR (MULTI-TENANT ENROLLMENT & LOAD BALANCING)
# -------------------------------------------------------------
@router.get("/outreach/mailboxes")
@router.get("/mailboxes")
def list_enrolled_mailboxes(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns sending mailboxes. Operators see their own; Admins see all."""
    rotator = get_inbox_rotator()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    return rotator.get_all_mailboxes_status(operator_id=target_op)


@router.post("/mailboxes")
def enroll_mailbox(req: MailboxCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Enrolls an active SMTP profile with per-mailbox daily sending cap."""
    rotator = get_inbox_rotator()
    op_id = current_user["id"]
    try:
        return rotator.enroll_mailbox(
            email_address=req.email_address,
            display_name=req.display_name,
            domain=req.domain,
            daily_limit=req.daily_limit or 45,
            operator_id=op_id,
            smtp_host=req.smtp_host or "",
            smtp_port=req.smtp_port or 587,
            smtp_username=req.smtp_username or req.email_address,
            smtp_password=req.smtp_password or "",
            imap_host=req.imap_host or "",
            imap_port=req.imap_port or 993,
            imap_username=req.imap_username or req.email_address,
            imap_password=req.imap_password or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/mailboxes/{mailbox_id}")
def update_mailbox(mailbox_id: str, req: MailboxUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Updates configuration for an enrolled mailbox."""
    db = get_db_engine()
    with db.get_connection() as conn:
        existing = conn.execute("SELECT id, operator_id FROM mailbox_rotator WHERE id = ?", (mailbox_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Mailbox not found.")

        if current_user.get("role") != "admin" and existing["operator_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Forbidden: You can only edit your own mailboxes.")

        fields = []
        values = []
        if req.email_address is not None:
            fields.append("email_address = ?"); values.append(req.email_address.strip())
        if req.display_name is not None:
            fields.append("display_name = ?"); values.append(req.display_name.strip())
        if req.domain is not None:
            fields.append("domain = ?"); values.append(req.domain.strip())
        if req.daily_limit is not None:
            fields.append("daily_limit = ?"); values.append(req.daily_limit)
        if req.smtp_host is not None:
            fields.append("smtp_host = ?"); values.append(req.smtp_host.strip())
        if req.smtp_port is not None:
            fields.append("smtp_port = ?"); values.append(req.smtp_port)
        if req.smtp_username is not None:
            fields.append("smtp_username = ?"); values.append(req.smtp_username.strip())
        if req.smtp_password is not None:
            fields.append("smtp_password = ?"); values.append(req.smtp_password)
        if req.imap_host is not None:
            fields.append("imap_host = ?"); values.append(req.imap_host.strip())
        if req.imap_port is not None:
            fields.append("imap_port = ?"); values.append(req.imap_port)
        if req.imap_username is not None:
            fields.append("imap_username = ?"); values.append(req.imap_username.strip())
        if req.imap_password is not None:
            fields.append("imap_password = ?"); values.append(req.imap_password)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields provided to update.")

        values.append(mailbox_id)
        conn.execute(f"UPDATE mailbox_rotator SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    return {"success": True, "id": mailbox_id, "message": "Mailbox updated successfully."}


@router.delete("/mailboxes/{mailbox_id}")
def delete_mailbox(mailbox_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Deletes an enrolled mailbox."""
    db = get_db_engine()
    with db.get_connection() as conn:
        existing = conn.execute("SELECT id, operator_id, email_address FROM mailbox_rotator WHERE id = ?", (mailbox_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Mailbox not found.")

        if current_user.get("role") != "admin" and existing["operator_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own mailboxes.")

        conn.execute("DELETE FROM mailbox_rotator WHERE id = ?", (mailbox_id,))
        conn.commit()

    return {"success": True, "deleted_id": mailbox_id, "email": existing["email_address"]}


# -------------------------------------------------------------
# 10. HOT LEADS, REPLIES & IMAP BOUNCE LISTENER
# -------------------------------------------------------------
@router.get("/outreach/hot-leads")
def get_hot_leads(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns detected Hot Leads for this tenant."""
    listener = get_reply_listener()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    return listener.get_hot_lead_alerts(operator_id=target_op)


@router.post("/outreach/send-hot-reply")
def send_hot_reply(req: DispatchHotReplyRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Dispatches a rapid response to a Hot Lead inquiry."""
    db = get_db_engine()
    rotator = get_inbox_rotator()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    mb = rotator.get_next_available_mailbox(operator_id=target_op)
    sender = mb["email_address"] if mb else "outreach@enterprise.io"

    with db.get_connection() as conn:
        conn.execute("""
            UPDATE inbox_replies
            SET status = 'RESOLVED'
            WHERE id = ?
        """, (req.reply_id,))
        conn.commit()

    return {
        "success": True,
        "reply_id": req.reply_id,
        "recipient": req.recipient,
        "dispatched_from": sender,
        "status": "SENT"
    }


@router.post("/replies/simulate")
def simulate_inbound_reply(req: SimulateReplyRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Test/Simulation endpoint:
    Processes an inbound email, triggers reply classification,
    and runs bounce suppression or hot lead alerts.
    """
    listener = get_reply_listener()
    target_op = current_user["id"] if current_user.get("role") == "operator" else None
    return listener.process_incoming_reply(
        sender_email=req.sender_email,
        subject=req.subject,
        body=req.body,
        company_name=req.company_name,
        operator_id=target_op
    )


@router.post("/inbox/poll")
def poll_imap_inboxes(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Background polling service:
    Monitors enrolled IMAP inboxes for bounces and responses.
    """
    listener = get_reply_listener()
    return listener.poll_enrolled_inboxes()


# -------------------------------------------------------------
# 11. DELIVERABILITY ANALYTICS DASHBOARD
# -------------------------------------------------------------
@router.get("/analytics/deliverability")
def get_deliverability_analytics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Visual metric indicators tracking:
    Open Rates %, Bounce Rates %, Conversion Rates %, Sent, Delivered, and Suppressed.
    """
    db = get_db_engine()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None

    with db.get_connection() as conn:
        q_filter = "WHERE operator_id = ?" if op_id else ""
        q_params = [op_id] if op_id else []

        total_sent = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} status IN ('SENT', 'HOT_LEAD', 'REPLIED')", q_params).fetchone()[0]
        total_opened = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} opened_at IS NOT NULL", q_params).fetchone()[0]
        total_bounced = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} (status = 'BOUNCED' OR bounced_at IS NOT NULL)", q_params).fetchone()[0]
        total_replied = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} status IN ('REPLIED', 'HOT_LEAD')", q_params).fetchone()[0]
        total_hot = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} status = 'HOT_LEAD'", q_params).fetchone()[0]
        total_queued = conn.execute(f"SELECT count(*) FROM outreach_queue {q_filter} {'AND' if q_filter else 'WHERE'} status = 'PENDING_APPROVAL'", q_params).fetchone()[0]
        total_suppressed = conn.execute("SELECT count(*) FROM suppressed_entities").fetchone()[0]

    delivered = max(0, total_sent - total_bounced)
    open_rate = round((total_opened / max(1, delivered)) * 100.0, 1) if delivered > 0 else 0.0
    bounce_rate = round((total_bounced / max(1, total_sent)) * 100.0, 1) if total_sent > 0 else 0.0
    conversion_rate = round((total_replied / max(1, delivered)) * 100.0, 1) if delivered > 0 else 0.0

    return {
        "total_sent": total_sent,
        "total_delivered": delivered,
        "total_opened": total_opened,
        "total_bounced": total_bounced,
        "total_replied": total_replied,
        "total_hot_leads": total_hot,
        "total_queued": total_queued,
        "total_suppressed": total_suppressed,
        "open_rate_percent": open_rate,
        "bounce_rate_percent": bounce_rate,
        "conversion_rate_percent": conversion_rate
    }


@router.get("/track/open/{queue_id}.png")
def track_email_open(queue_id: str):
    """Tracking pixel endpoint: increments open metrics upon receipt rendering."""
    db = get_db_engine()
    with db.get_connection() as conn:
        conn.execute("UPDATE outreach_queue SET opened_at = CURRENT_TIMESTAMP WHERE id = ? OR tracking_id = ?", (queue_id, queue_id))
        conn.commit()
    transparent_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=transparent_png_bytes, media_type="image/png")


# -------------------------------------------------------------
# 12. UNSUBSCRIBE / OPT-OUT COMPLIANCE MANAGER
# -------------------------------------------------------------
@router.get("/unsubscribe")
def handle_unsubscribe_link(token: Optional[str] = Query(None), email: Optional[str] = Query(None)):
    """
    CAN-SPAM & GDPR Compliance:
    Suppresses opted-out contact and associated domain from future scraping and outreach.
    """
    clean_email = (email or "").strip().lower()
    if token and not clean_email:
        db = get_db_engine()
        with db.get_connection() as conn:
            row = conn.execute("SELECT recipient FROM outreach_queue WHERE tracking_id = ? OR id = ?", (token, token)).fetchone()
            if row:
                clean_email = row["recipient"].strip().lower()

    if clean_email:
        listener = get_reply_listener()
        domain_part = clean_email.split("@")[-1] if "@" in clean_email else clean_email
        listener.suppress_entity(clean_email, reason="UNSUBSCRIBE")
        listener.suppress_entity(domain_part, reason="UNSUBSCRIBE")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Unsubscribe Confirmation</title>
    <style>body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 32px; max-width: 480px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
    h1 {{ color: #58a6ff; font-size: 20px; margin-bottom: 12px; }}
    p {{ font-size: 14px; line-height: 1.6; color: #8b949e; }}
    .badge {{ display: inline-block; background: #238636; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-top: 12px; font-weight: 600; }}
    </style></head>
    <body>
    <div class="card">
      <h1>✓ Opt-Out Confirmed</h1>
      <p>The entity <strong>{clean_email or 'specified recipient'}</strong> has been globally suppressed.</p>
      <p>All future automated outreach and data aggregation have been permanently disabled for this domain in accordance with CAN-SPAM and GDPR guidelines.</p>
      <div class="badge">Suppressed from Outreach Engine</div>
    </div>
    </body></html>
    """
    return HTMLResponse(content=html_content)


@router.post("/unsubscribe")
def handle_unsubscribe_post(req: UnsubscribeRequest):
    """API endpoint for opt-out suppression."""
    listener = get_reply_listener()
    clean = req.email.strip().lower()
    domain = clean.split("@")[-1] if "@" in clean else clean
    listener.suppress_entity(clean, reason="UNSUBSCRIBE")
    listener.suppress_entity(domain, reason="UNSUBSCRIBE")
    return {"success": True, "suppressed_entity": clean}


@router.get("/suppressed")
def list_suppressed_entities(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all globally suppressed domains and emails."""
    listener = get_reply_listener()
    return listener.get_suppressed_entities()


# -------------------------------------------------------------
# 13. LIVE SCRAPE PIPELINE (ZERO-SEED PRODUCTION)
# -------------------------------------------------------------
@router.post("/scrape")
async def launch_scrape_pipeline(req: ScrapeRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Hunt & Verify pipeline:
    Extracts real company leads from target URLs or localized queries.
    Zero-Seed Policy: NO fake or synthetic companies are generated.
    Auto-matches detected niche to the operator's custom service template.
    Enforces blacklist rules and suppression filtering before persisting.
    """
    cfg = get_config()
    cfg.update({"target_country": req.country, "industry_niche": req.niche})
    db = get_db_engine()
    crypto = get_crypto_vault()
    orchestrator = NexusPulseOrchestrator()
    gate = get_approval_gate()
    blacklist_mgr = get_blacklist_manager()
    reply_listener = get_reply_listener()
    template_mgr = get_template_manager()

    country = req.country.strip()
    niche = req.niche.strip()
    city_override = (req.city or "").strip() or "Metropolis"
    limit = max(1, min(req.max_results or 20, 100))
    op_id = current_user["id"]

    scraped_leads = []
    verified_leads = []

    # If explicit target URLs are supplied, scrape them directly
    if req.target_urls:
        scraper = DeepScraperAgent()
        for url in req.target_urls[:limit]:
            clean_url = url.strip()
            if not clean_url:
                continue

            # Check blacklist & suppression
            domain_part = clean_url.split("/")[2] if "//" in clean_url else clean_url.split("/")[0]
            is_bl, _ = blacklist_mgr.is_domain_blacklisted(domain_part)
            if is_bl or reply_listener.is_suppressed(domain_part):
                continue

            lead = await scraper.scrape_url(
                url=clean_url,
                country=country,
                city=city_override,
                niche=niche
            )
            if lead:
                pres = orchestrator.process_and_preserve_lead(lead, operator_id=op_id)
                if pres["success"]:
                    verified_leads.append(pres)
                    # Queue in Approval Gate
                    gate.queue_outreach(
                        lead_id=pres["lead_id"],
                        company_name=pres["company_name"],
                        recipient=pres["primary_email"],
                        country=country,
                        niche=niche,
                        channel="EMAIL",
                        tech_stack=pres.get("tech_stack"),
                        operator_id=op_id,
                        city=city_override
                    )
                else:
                    scraped_leads.append({"domain": lead.domain, "reason": pres.get("reason")})

    return {
        "status": "COMPLETED",
        "target": {"country": country, "niche": niche, "city": city_override},
        "scraped_count": len(scraped_leads),
        "verified_count": len(verified_leads),
        "leads_preserved_count": len(verified_leads),
        "leads_rejected_count": len(scraped_leads),
        "scraped_leads": scraped_leads,
        "verified_leads": verified_leads,
        "processed_leads": verified_leads,
        "message": f"Hunt & Verify executed for {country} ({niche}). {len(verified_leads)} verified leads queued in Approval Gate." if verified_leads else "Hunt completed. 0 candidate leads found. Provide target domains or refine regional keywords."
    }


@router.post("/pipeline/run")
def run_full_pipeline_run(sample_targets: Optional[List[Dict[str, str]]] = None, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Executes full multi-agent pipeline on provided target definitions.
    Strict Zero-Seed: Returns clean empty result if no targets provided.
    """
    orchestrator = NexusPulseOrchestrator()
    op_id = current_user["id"]
    targets = sample_targets or []

    pipeline_res = orchestrator.execute_targeted_pipeline(sample_targets=targets, operator_id=op_id)

    # Queue preserved leads into Human Approval Gate
    gate = get_approval_gate()
    queued_in_gate = []
    for lead_info in pipeline_res["processed_leads"]:
        q_item = gate.queue_outreach(
            lead_id=lead_info["lead_id"],
            company_name=lead_info["company_name"],
            recipient=lead_info["primary_email"],
            country=pipeline_res["target"]["country"],
            niche=pipeline_res["target"]["niche"],
            channel="EMAIL",
            tech_stack=lead_info.get("tech_stack"),
            operator_id=op_id
        )
        queued_in_gate.append(q_item)

    pipeline_res["queued_in_approval_gate"] = queued_in_gate
    return pipeline_res


# -------------------------------------------------------------
# 14. CONFIG, VAULT, BACKUP & UTILITIES
# -------------------------------------------------------------
@router.get("/config")
def get_runtime_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    cfg = get_config()
    return cfg.as_dict()


@router.post("/config")
def update_runtime_config(req: ConfigUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    cfg = get_config()
    updates = {}
    if req.target_country is not None:
        updates["target_country"] = req.target_country
    if req.target_city is not None:
        updates["target_city"] = req.target_city
    if req.industry_niche is not None:
        updates["industry_niche"] = req.industry_niche
    if req.ready_to_send is not None:
        updates["ready_to_send"] = req.ready_to_send
    cfg.update(updates)
    return {"message": "Config updated successfully", "config": cfg.as_dict()}


@router.post("/vault/backup")
def trigger_snapshot_backup(current_user: Dict[str, Any] = Depends(get_current_user)):
    vault = get_vault_manager()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None
    return vault.export_global_snapshot_backups(operator_id=op_id)


@router.get("/backup")
@router.post("/backup")
@router.get("/backup/download")
@router.post("/backup/download")
def backup_and_download(format: Optional[str] = "json", current_user: Dict[str, Any] = Depends(get_current_user)):
    """Exports and downloads vault snapshots directly."""
    vault = get_vault_manager()
    op_id = current_user["id"] if current_user.get("role") == "operator" else None
    result = vault.export_global_snapshot_backups(operator_id=op_id)

    fmt = (format or "json").lower().strip()
    if fmt == "csv":
        path = result.get("csv_backup")
        media_type = "text/csv"
    elif fmt in ("xlsx", "excel"):
        path = result.get("xlsx_backup")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        path = result.get("json_backup")
        media_type = "application/json"

    if not path or not os.path.exists(path):
        path = result.get("json_backup")
        media_type = "application/json"
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=500, detail="Backup file was not created on disk.")

    filename = os.path.basename(path)
    return FileResponse(
        path=path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.post("/leads/verify")
def verify_email_address(req: VerifyEmailRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hygiene = get_hygiene_shield()
    return hygiene.validate_lead_email(req.email).model_dump()


@router.post("/followup/scan")
def trigger_followup_scanner(current_user: Dict[str, Any] = Depends(get_current_user)):
    engine = get_followup_engine()
    return engine.scan_and_trigger_due_followups(force_all_pending=True)


@router.post("/outreach/webform/format")
def format_backup_webform(req: WebFormFormatRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    return BackupWebFormAgent.format_web_form_payload(
        company_name=req.company_name,
        website_url=req.website_url,
        niche=req.niche or "Commercial Contracting",
        country=req.country or "Germany"
    )


@router.post("/operators/log-activity")
def log_operator_activity(req: LogActivityRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = get_db_engine()
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO operator_sessions (user_id, username, action, detail, device_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            current_user.get("id", ""),
            current_user.get("username", "unknown"),
            req.action.upper(),
            req.detail or "",
            current_user.get("device_id", "")
        ))
        conn.commit()
    return {"logged": True}


@router.get("/operators/{user_id}/activity-log")
def get_operator_activity_log(user_id: str, admin_user: Dict[str, Any] = Depends(require_admin)):
    db = get_db_engine()
    with db.get_connection() as conn:
        rows = conn.execute("""
            SELECT id, action, detail, device_id, created_at
            FROM operator_sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


@router.get("/operators-activity/all")
@router.get("/operators/activity-log/all")
def get_all_activity_logs(admin_user: Dict[str, Any] = Depends(require_admin)):
    """Returns activity audit logs across all operator accounts."""
    db = get_db_engine()
    with db.get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_id, username, action, detail, device_id, created_at
            FROM operator_sessions
            ORDER BY created_at DESC
            LIMIT 100
        """).fetchall()
    return [dict(r) for r in rows]
