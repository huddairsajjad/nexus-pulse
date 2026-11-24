"""
Nexus-Pulse Enterprise Build
Outreach Engine: Multi-Service Template Pool & Dynamic Industry Matching
Allows users/operators to compose, store, and manage custom service proposals with
variable interpolation ({{company_name}}, {{niche}}, {{country}}, {{city}}, {{unsubscribe_link}}).
Auto-matches target category to the corresponding user-defined template.
"""

import os
import urllib.parse
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.db_engine import get_db_engine


class TemplateManager:
    """
    Manages custom user service proposals and dynamic niche-based template matching.
    Guarantees no hardcoded message text is forced upon operators.
    """

    def __init__(self):
        self.db = get_db_engine()

    def get_templates(
        self,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists custom templates for an operator/user or global templates."""
        owner = (owner_username or "").strip().lower()
        if not owner and operator_id:
            try:
                with self.db.get_connection() as u_conn:
                    u_row = u_conn.execute("SELECT username FROM users WHERE id = ?", (operator_id,)).fetchone()
                    if u_row and u_row[0]:
                        owner = u_row[0].strip().lower()
            except Exception:
                pass
        op_id = (operator_id or "").strip()
        with self.db.get_connection() as conn:
            if owner and op_id:
                rows = conn.execute("""
                    SELECT id, operator_id, owner_username, title, niche, subject_template, body_template,
                           is_default, created_at, updated_at
                    FROM service_templates
                    WHERE (lower(owner_username) = ? OR operator_id = ? OR operator_id = 'global')
                    ORDER BY is_default DESC, title ASC
                """, (owner, op_id)).fetchall()
            elif owner:
                rows = conn.execute("""
                    SELECT id, operator_id, owner_username, title, niche, subject_template, body_template,
                           is_default, created_at, updated_at
                    FROM service_templates
                    WHERE (lower(owner_username) = ? OR operator_id = 'global')
                    ORDER BY is_default DESC, title ASC
                """, (owner,)).fetchall()
            elif op_id:
                rows = conn.execute("""
                    SELECT id, operator_id, owner_username, title, niche, subject_template, body_template,
                           is_default, created_at, updated_at
                    FROM service_templates
                    WHERE (operator_id = ? OR operator_id = 'global')
                    ORDER BY is_default DESC, title ASC
                """, (op_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, operator_id, owner_username, title, niche, subject_template, body_template,
                           is_default, created_at, updated_at
                    FROM service_templates
                    ORDER BY operator_id ASC, is_default DESC, title ASC
                """).fetchall()
            return [dict(r) for r in rows]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single template by ID."""
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT id, operator_id, owner_username, title, niche, subject_template, body_template,
                       is_default, created_at, updated_at
                FROM service_templates
                WHERE id = ?
            """, (template_id,)).fetchone()
            return dict(row) if row else None

    def create_template(
        self,
        operator_id: str,
        title: str,
        niche: str,
        subject_template: str,
        body_template: str,
        is_default: bool = False,
        owner_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a custom service proposal template."""
        clean_title = title.strip()
        clean_niche = niche.strip()
        clean_subj = subject_template.strip()
        clean_body = body_template.strip()
        owner = (owner_username or "").strip().lower()
        if not owner and operator_id:
            try:
                with self.db.get_connection() as u_conn:
                    u_row = u_conn.execute("SELECT username FROM users WHERE id = ?", (operator_id,)).fetchone()
                    if u_row and u_row[0]:
                        owner = u_row[0].strip().lower()
            except Exception:
                pass

        if not clean_title or not clean_subj or not clean_body:
            raise ValueError("Title, subject template, and body template are required.")

        t_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            if is_default:
                if owner:
                    conn.execute("""
                        UPDATE service_templates
                        SET is_default = 0
                        WHERE lower(owner_username) = ? OR operator_id = ?
                    """, (owner, operator_id))
                else:
                    conn.execute("""
                        UPDATE service_templates
                        SET is_default = 0
                        WHERE operator_id = ?
                    """, (operator_id,))

            conn.execute("""
                INSERT INTO service_templates (
                    id, operator_id, owner_username, title, niche, subject_template, body_template,
                    is_default, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t_id, operator_id, owner, clean_title, clean_niche, clean_subj, clean_body,
                1 if is_default else 0, now_str, now_str
            ))
            conn.commit()

        return {
            "id": t_id,
            "operator_id": operator_id,
            "owner_username": owner,
            "title": clean_title,
            "niche": clean_niche,
            "subject_template": clean_subj,
            "body_template": clean_body,
            "is_default": is_default,
            "created_at": now_str
        }

    def update_template(
        self,
        template_id: str,
        operator_id: Optional[str] = None,
        title: Optional[str] = None,
        niche: Optional[str] = None,
        subject_template: Optional[str] = None,
        body_template: Optional[str] = None,
        is_default: Optional[bool] = None,
        owner_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates an existing proposal template."""
        owner = (owner_username or "").strip().lower()
        if not owner and operator_id:
            try:
                with self.db.get_connection() as u_conn:
                    u_row = u_conn.execute("SELECT username FROM users WHERE id = ?", (operator_id,)).fetchone()
                    if u_row and u_row[0]:
                        owner = u_row[0].strip().lower()
            except Exception:
                pass
        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id, operator_id, owner_username FROM service_templates WHERE id = ?", (template_id,)).fetchone()
            if not existing:
                raise ValueError("Template not found.")

            ex_owner = (existing["owner_username"] or "").strip().lower()
            ex_op = (existing["operator_id"] or "").strip()
            if operator_id != "admin":
                if owner and ex_owner and ex_owner != owner:
                    raise PermissionError("Unauthorized to modify this template.")
                elif operator_id and ex_op and ex_op != operator_id:
                    raise PermissionError("Unauthorized to modify this template.")

            fields = []
            values = []
            if title is not None:
                fields.append("title = ?"); values.append(title.strip())
            if niche is not None:
                fields.append("niche = ?"); values.append(niche.strip())
            if subject_template is not None:
                fields.append("subject_template = ?"); values.append(subject_template.strip())
            if body_template is not None:
                fields.append("body_template = ?"); values.append(body_template.strip())
            if is_default is not None:
                if is_default:
                    if owner:
                        conn.execute("UPDATE service_templates SET is_default = 0 WHERE lower(owner_username) = ? OR operator_id = ?", (owner, existing["operator_id"]))
                    else:
                        conn.execute("UPDATE service_templates SET is_default = 0 WHERE operator_id = ?", (existing["operator_id"],))
                fields.append("is_default = ?"); values.append(1 if is_default else 0)

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            fields.append("updated_at = ?"); values.append(now_str)

            values.append(template_id)
            conn.execute(f"UPDATE service_templates SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()

        return {"id": template_id, "updated": True}

    def delete_template(
        self,
        template_id: str,
        operator_id: Optional[str] = None,
        owner_username: Optional[str] = None
    ) -> bool:
        """Deletes a custom template."""
        owner = (owner_username or "").strip().lower()
        if not owner and operator_id:
            try:
                with self.db.get_connection() as u_conn:
                    u_row = u_conn.execute("SELECT username FROM users WHERE id = ?", (operator_id,)).fetchone()
                    if u_row and u_row[0]:
                        owner = u_row[0].strip().lower()
            except Exception:
                pass
        with self.db.get_connection() as conn:
            existing = conn.execute("SELECT id, operator_id, owner_username FROM service_templates WHERE id = ?", (template_id,)).fetchone()
            if not existing:
                return False
            ex_owner = (existing["owner_username"] or "").strip().lower()
            ex_op = (existing["operator_id"] or "").strip()
            if operator_id != "admin":
                if owner and ex_owner and ex_owner != owner:
                    raise PermissionError("Unauthorized to delete this template.")
                elif operator_id and ex_op and ex_op != operator_id:
                    raise PermissionError("Unauthorized to delete this template.")
            conn.execute("DELETE FROM service_templates WHERE id = ?", (template_id,))
            conn.commit()
            return True

    def match_and_render_template(
        self,
        operator_id: Optional[str],
        niche: str,
        company_name: str,
        recipient_email: str,
        country: str,
        city: str = "",
        tech_stack: Optional[List[str]] = None,
        unsubscribe_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Dynamic Industry/Niche Matching:
        Matches target lead category to the corresponding user-defined template.
        Interpolates template variables:
          {{company_name}}, {{recipient_email}}, {{niche}}, {{country}}, {{city}}, {{tech_stack}}, {{unsubscribe_link}}
        """
        clean_niche = (niche or "").strip()
        stack_str = ", ".join(tech_stack) if tech_stack else ""
        _app_base = os.getenv("APP_BASE_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN", os.getenv("RAILWAY_STATIC_URL", "nexus-pulse-production.up.railway.app"))).strip()
        if _app_base and not _app_base.startswith("http"):
            _app_base = f"https://{_app_base}"
        _recip_enc = urllib.parse.quote(recipient_email, safe="@")
        unsub_link = unsubscribe_url or f"{_app_base}/api/unsubscribe?email={_recip_enc}"

        with self.db.get_connection() as conn:
            # 1. Look for exact or fuzzy niche match for this operator
            query = """
                SELECT subject_template, body_template
                FROM service_templates
                WHERE (operator_id = ? OR operator_id = 'global' OR ? IS NULL)
            """
            params: List[Any] = [operator_id, operator_id]

            # Try exact niche match first
            row = conn.execute(query + " AND lower(niche) = lower(?) LIMIT 1", params + [clean_niche]).fetchone()

            # Try substring match
            if not row and clean_niche:
                row = conn.execute(query + " AND (instr(lower(?), lower(niche)) > 0 OR instr(lower(niche), lower(?)) > 0) LIMIT 1", params + [clean_niche, clean_niche]).fetchone()

            # Try default template
            if not row:
                row = conn.execute(query + " AND is_default = 1 LIMIT 1", params).fetchone()

            # Try any template for this operator
            if not row:
                row = conn.execute(query + " ORDER BY created_at DESC LIMIT 1", params).fetchone()

        if row:
            subject_tpl = row["subject_template"]
            body_tpl = row["body_template"]
        else:
            # Fallback dynamic copy without hardcoded names
            subject_tpl = "Commercial Collaboration // {{company_name}} [{{country}}]"
            body_tpl = (
                "Dear Estimating & Project Management Team at {{company_name}},\n\n"
                "We are reaching out to submit our credentials and commercial capacity for upcoming {{niche}} packages in {{country}}.\n\n"
                "Our team delivers high-precision takeoffs, competitive subcontractor pricing, and rapid estimating turnaround.\n\n"
                "Please confirm the right contact or portal to submit our credentials.\n\n"
                "Best regards,\n"
                "Commercial Estimating Department\n\n"
                "---\n"
                "To opt-out from future communications: {{unsubscribe_link}}"
            )

        # Interpolate variables
        replacements = {
            "{{company_name}}": company_name,
            "{{recipient_email}}": recipient_email,
            "{{niche}}": clean_niche or "Commercial Projects",
            "{{country}}": country or "Europe",
            "{{city}}": city or "Local",
            "{{tech_stack}}": stack_str,
            "{{unsubscribe_link}}": unsub_link
        }

        subj = subject_tpl
        body = body_tpl
        for var, val in replacements.items():
            subj = subj.replace(var, val)
            body = body.replace(var, val)

        # Append unsubscribe link at bottom if not already in template
        if "{{unsubscribe_link}}" not in body_tpl and unsub_link not in body:
            body += f"\n\n---\nOpt-out: {unsub_link}"

        return {"subject": subj, "body": body}


_global_template_manager = None

def get_template_manager() -> TemplateManager:
    global _global_template_manager
    if _global_template_manager is None:
        _global_template_manager = TemplateManager()
    return _global_template_manager
