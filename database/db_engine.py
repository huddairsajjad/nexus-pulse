"""
H.Huddair's Nexus-Pulse - Level 1
Database Engine: Persistent Encrypted SQLite Storage
Location: Desktop/rabbi/database/nexus_vault.db
Provides schema creation, encrypted payload persistence, and fast indexed deduplication lookups.
"""

import os
import sqlite3
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "database"

def _resolve_default_db_path() -> Path:
    env_path = os.environ.get("NEXUS_DB_PATH") or os.environ.get("DATABASE_URL")
    if env_path and not env_path.startswith(("postgres://", "postgresql://", "mysql://", "redis://")):
        # Strip sqlite:/// prefix if present
        clean_path = env_path.replace("sqlite:///", "").replace("sqlite://", "").strip()
        if clean_path:
            return Path(clean_path).resolve()
    return DB_DIR / "nexus_vault.db"

DB_FILE_PATH = _resolve_default_db_path()


def compute_sha256(text: str) -> str:
    """Computes SHA-256 hex digest for fast hash lookups."""
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


class DatabaseEngine:
    """
    Manages SQLite database operations with support for field encryption
    and persistent deduplication indices. Supports sync and async connections.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _resolve_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def get_connection(self, max_retries: int = 3, retry_delay: float = 0.2):
        """Context-managed SQLite connection ensuring transaction commit, retry resilience, and clean closing."""
        import time
        conn = None
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=30.0)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("PRAGMA busy_timeout = 30000;")
                break
            except sqlite3.OperationalError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (2 ** attempt))
        try:
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    async def get_async_connection(self):
        """Asynchronous SQLite connection helper for high-concurrency cloud workloads."""
        try:
            import aiosqlite
            conn = await aiosqlite.connect(str(self.db_path), timeout=20.0)
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode = WAL;")
            await conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except ImportError:
            # Fallback wrapper if aiosqlite is not yet installed
            return None
            conn.close()

    def _init_schema(self) -> None:
        """Initializes database tables and performance indices."""
        with self.get_connection() as conn:
            # 1. Per-User Scoped Deduplication Registry
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dedup_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,           -- 'domain', 'email', 'company'
                    normalized_key TEXT NOT NULL,        -- clean lowercase string
                    hash_fingerprint TEXT NOT NULL,      -- sha256 hex
                    status TEXT NOT NULL DEFAULT 'SCRAPED', -- 'SCRAPED', 'VERIFIED', 'CONTACTED', 'BLACKLISTED'
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lead_id TEXT,
                    alias_group TEXT,
                    domain TEXT,
                    owner_username TEXT DEFAULT ''
                );
            """)
            # Migration check: ensure owner_username exists and composite unique index is enforced
            existing_dd_cols = {col["name"] for col in conn.execute("PRAGMA table_info(dedup_registry)").fetchall()}
            if "owner_username" not in existing_dd_cols:
                try:
                    conn.execute("ALTER TABLE dedup_registry ADD COLUMN owner_username TEXT DEFAULT '';")
                except Exception:
                    pass
            if "tenant_id" not in existing_dd_cols:
                try:
                    conn.execute("ALTER TABLE dedup_registry ADD COLUMN tenant_id TEXT DEFAULT '';")
                except Exception:
                    pass
            if "alias_group" not in existing_dd_cols:
                try:
                    conn.execute("ALTER TABLE dedup_registry ADD COLUMN alias_group TEXT;")
                except Exception:
                    pass
            if "domain" not in existing_dd_cols:
                try:
                    conn.execute("ALTER TABLE dedup_registry ADD COLUMN domain TEXT;")
                except Exception:
                    pass

            # Check if dedup_registry has single-column unique constraint on normalized_key (autoindex)
            # If so, migrate to table with composite uniqueness (normalized_key, owner_username)
            needs_recreate = False
            for idx_info in conn.execute("PRAGMA index_list(dedup_registry)").fetchall():
                if idx_info["unique"]:
                    cols = [r[2] for r in conn.execute(f"PRAGMA index_info({idx_info['name']})").fetchall()]
                    if cols == ["normalized_key"]:
                        needs_recreate = True
                        break

            if needs_recreate:
                conn.execute("""
                    CREATE TABLE dedup_registry_mig (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT NOT NULL,
                        normalized_key TEXT NOT NULL,
                        hash_fingerprint TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'SCRAPED',
                        first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        lead_id TEXT,
                        alias_group TEXT,
                        domain TEXT,
                        owner_username TEXT DEFAULT ''
                    );
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO dedup_registry_mig
                    (id, entity_type, normalized_key, hash_fingerprint, status, first_seen_at, last_processed_at, lead_id, alias_group, domain, owner_username)
                    SELECT id, entity_type, normalized_key, hash_fingerprint, status, first_seen_at, last_processed_at, lead_id, alias_group, domain, COALESCE(owner_username, '')
                    FROM dedup_registry;
                """)
                conn.execute("DROP TABLE dedup_registry;")
                conn.execute("ALTER TABLE dedup_registry_mig RENAME TO dedup_registry;")

            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dedup_key_owner ON dedup_registry(normalized_key, owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_hash ON dedup_registry(hash_fingerprint);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_owner ON dedup_registry(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_status ON dedup_registry(status);")

            # 2. Vault Leads (Encrypted Record Storage)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_leads (
                    id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    primary_email TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    quality_tag TEXT NOT NULL,
                    priority_score INTEGER DEFAULT 0,
                    encrypted_payload TEXT NOT NULL,     -- AES-256 encrypted JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_domain ON vault_leads(domain);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_email ON vault_leads(primary_email);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_country_niche ON vault_leads(country, niche);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_quality ON vault_leads(quality_tag);")

            # 3. Hygiene Verification Audit Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hygiene_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage_1_syntax INTEGER NOT NULL,
                    is_disposable INTEGER NOT NULL,
                    stage_2_mx INTEGER NOT NULL,
                    stage_3_smtp INTEGER,
                    smtp_code INTEGER,
                    smtp_message TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hygiene_email ON hygiene_audit_log(email);")

            # -------------------------------------------------------------
            # LEVEL 2 ENTERPRISE EXTENSIONS
            # -------------------------------------------------------------
            # 4. Users & Role-Based Access Control
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'operator', -- 'admin', 'operator'
                    full_name TEXT NOT NULL,
                    email TEXT DEFAULT 'huddair@nexus-pulse.io',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    device_lock_id TEXT,
                    device_lock_enabled INTEGER NOT NULL DEFAULT 1,
                    expiry_date TEXT,
                    daily_scrape_quota INTEGER NOT NULL DEFAULT 200,
                    daily_send_quota INTEGER NOT NULL DEFAULT 50,
                    license_key TEXT,
                    last_login_device TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")

            # Dynamic migration for existing users table
            existing_user_cols = {col["name"] for col in conn.execute("PRAGMA table_info(users)").fetchall()}
            migrations = [
                ("email", "TEXT DEFAULT 'huddair@nexus-pulse.io'"),
                ("tenant_id", "TEXT DEFAULT ''"),
                ("is_active", "INTEGER NOT NULL DEFAULT 1"),
                ("device_lock_id", "TEXT"),
                ("device_lock_enabled", "INTEGER NOT NULL DEFAULT 1"),
                ("expiry_date", "TEXT"),
                ("daily_scrape_quota", "INTEGER NOT NULL DEFAULT 200"),
                ("daily_send_quota", "INTEGER NOT NULL DEFAULT 50"),
                ("license_key", "TEXT"),
                ("last_login_device", "TEXT"),
                ("auth_provider", "TEXT DEFAULT 'local'"),
                ("google_id", "TEXT"),
                ("google_refresh_token", "TEXT"),
                ("google_access_token", "TEXT"),
                ("google_token_expiry", "TEXT"),
                ("trial_status", "TEXT DEFAULT 'active'"),
                ("trial_started_at", "TEXT"),
                ("trial_active", "INTEGER NOT NULL DEFAULT 0"),
                ("trial_expires_at", "TEXT"),
                ("subscription_status", "TEXT DEFAULT 'none'"),
                ("subscription_plan", "TEXT DEFAULT ''"),
                ("subscription_expires_at", "TEXT")
            ]
            for col_name, col_def in migrations:
                if col_name not in existing_user_cols:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);")
            try:
                conn.execute("UPDATE users SET tenant_id = id WHERE (tenant_id IS NULL OR tenant_id = '') AND id IS NOT NULL;")
            except Exception:
                pass

            # Dynamic migration for vault_leads
            existing_vl_cols = {col["name"] for col in conn.execute("PRAGMA table_info(vault_leads)").fetchall()}
            if "operator_id" not in existing_vl_cols:
                conn.execute("ALTER TABLE vault_leads ADD COLUMN operator_id TEXT;")
            if "tenant_id" not in existing_vl_cols:
                conn.execute("ALTER TABLE vault_leads ADD COLUMN tenant_id TEXT DEFAULT '';")
            if "unsubscribed" not in existing_vl_cols:
                conn.execute("ALTER TABLE vault_leads ADD COLUMN unsubscribed INTEGER NOT NULL DEFAULT 0;")
            if "owner_username" not in existing_vl_cols:
                conn.execute("ALTER TABLE vault_leads ADD COLUMN owner_username TEXT DEFAULT '';")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_operator ON vault_leads(operator_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_owner ON vault_leads(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_tenant ON vault_leads(tenant_id);")
            try:
                conn.execute("UPDATE vault_leads SET owner_username = (SELECT username FROM users WHERE users.id = vault_leads.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE vault_leads SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass

            # 5. Outreach Queue (Human Approval Gate & Scheduled Dispatch)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outreach_queue (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT,
                    channel TEXT NOT NULL DEFAULT 'EMAIL',  -- 'EMAIL', 'WEB_FORM'
                    recipient TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    message_body TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL', -- 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'SCHEDULED', 'SENT', 'REPLIED', 'HOT_LEAD', 'CLOSED', 'BOUNCED', 'SUPPRESSED'
                    target_country TEXT NOT NULL DEFAULT 'Germany',
                    target_timezone TEXT NOT NULL DEFAULT 'CET',
                    scheduled_for TIMESTAMP,
                    approved_by TEXT,
                    approved_at TIMESTAMP,
                    sent_at TIMESTAMP,
                    mailbox_used TEXT,
                    operator_id TEXT,
                    tracking_id TEXT,
                    opened_at TIMESTAMP,
                    bounced_at TIMESTAMP,
                    bounce_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Dynamic migration for outreach_queue columns (must run before indices)
            existing_oq_cols = {col["name"] for col in conn.execute("PRAGMA table_info(outreach_queue)").fetchall()}
            oq_migrations = [
                ("operator_id", "TEXT"),
                ("tenant_id", "TEXT DEFAULT ''"),
                ("owner_username", "TEXT DEFAULT ''"),
                ("tracking_id", "TEXT"),
                ("opened_at", "TIMESTAMP"),
                ("bounced_at", "TIMESTAMP"),
                ("bounce_reason", "TEXT"),
                ("message_id", "TEXT"),
                ("unsubscribed", "INTEGER NOT NULL DEFAULT 0"),
                ("replied_at", "TIMESTAMP"),
                ("reply_snippet", "TEXT"),
                ("dispatched_at", "TIMESTAMP"),
                ("industry_niche", "TEXT DEFAULT 'Commercial Construction'")
            ]
            for col_name, col_def in oq_migrations:
                if col_name not in existing_oq_cols:
                    conn.execute(f"ALTER TABLE outreach_queue ADD COLUMN {col_name} {col_def};")

            try:
                conn.execute("UPDATE outreach_queue SET owner_username = (SELECT username FROM users WHERE users.id = outreach_queue.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE outreach_queue SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass

            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON outreach_queue(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_lead ON outreach_queue(lead_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_operator ON outreach_queue(operator_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_owner ON outreach_queue(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_tenant ON outreach_queue(tenant_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_msgid ON outreach_queue(message_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_tracking ON outreach_queue(tracking_id);")

            # 6. Mailbox Rotator (Domain & Daily Limits)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mailbox_rotator (
                    id TEXT PRIMARY KEY,
                    email_address TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    daily_limit INTEGER NOT NULL DEFAULT 45,
                    sent_today INTEGER NOT NULL DEFAULT 0,
                    last_reset_date TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    smtp_host TEXT DEFAULT '',
                    smtp_port INTEGER DEFAULT 587,
                    smtp_username TEXT DEFAULT '',
                    smtp_password TEXT DEFAULT '',
                    operator_id TEXT,
                    imap_host TEXT DEFAULT '',
                    imap_port INTEGER DEFAULT 993,
                    imap_username TEXT DEFAULT '',
                    imap_password TEXT DEFAULT '',
                    webhook_url TEXT DEFAULT ''
                );
            """)

            # Dynamic migration for mailbox_rotator columns (must run before indices)
            existing_mb_cols = {col["name"] for col in conn.execute("PRAGMA table_info(mailbox_rotator)").fetchall()}
            mb_migrations = [
                ("smtp_host", "TEXT DEFAULT ''"),
                ("smtp_port", "INTEGER DEFAULT 587"),
                ("smtp_username", "TEXT DEFAULT ''"),
                ("smtp_password", "TEXT DEFAULT ''"),
                ("operator_id", "TEXT"),
                ("tenant_id", "TEXT DEFAULT ''"),
                ("owner_username", "TEXT DEFAULT ''"),
                ("imap_host", "TEXT DEFAULT ''"),
                ("imap_port", "INTEGER DEFAULT 993"),
                ("imap_username", "TEXT DEFAULT ''"),
                ("imap_password", "TEXT DEFAULT ''"),
                ("webhook_url", "TEXT DEFAULT ''")
            ]
            for col_name, col_def in mb_migrations:
                if col_name not in existing_mb_cols:
                    conn.execute(f"ALTER TABLE mailbox_rotator ADD COLUMN {col_name} {col_def};")

            try:
                conn.execute("UPDATE mailbox_rotator SET owner_username = (SELECT username FROM users WHERE users.id = mailbox_rotator.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE mailbox_rotator SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass

            conn.execute("CREATE INDEX IF NOT EXISTS idx_mailbox_operator ON mailbox_rotator(operator_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mailbox_owner ON mailbox_rotator(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mailbox_tenant ON mailbox_rotator(tenant_id);")

            # 7. Inbox Replies, AI Classification & Hot Lead Alerts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inbox_replies (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT,
                    sender_email TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    message_body TEXT NOT NULL,
                    classification TEXT NOT NULL, -- 'INTERESTED', 'UNSUBSCRIBE', 'BOUNCE', 'NEUTRAL'
                    is_hot_lead INTEGER NOT NULL DEFAULT 0,
                    ai_suggested_reply TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'UNREAD', -- 'UNREAD', 'RESOLVED', 'REPLIED'
                    operator_id TEXT,
                    owner_username TEXT DEFAULT ''
                );
            """)
            # Dynamic migration for inbox_replies columns
            existing_rep_cols = {col["name"] for col in conn.execute("PRAGMA table_info(inbox_replies)").fetchall()}
            if "operator_id" not in existing_rep_cols:
                conn.execute("ALTER TABLE inbox_replies ADD COLUMN operator_id TEXT;")
            if "tenant_id" not in existing_rep_cols:
                conn.execute("ALTER TABLE inbox_replies ADD COLUMN tenant_id TEXT DEFAULT '';")
            if "owner_username" not in existing_rep_cols:
                conn.execute("ALTER TABLE inbox_replies ADD COLUMN owner_username TEXT DEFAULT '';")
            if "message_id" not in existing_rep_cols:
                conn.execute("ALTER TABLE inbox_replies ADD COLUMN message_id TEXT;")

            try:
                conn.execute("UPDATE inbox_replies SET owner_username = (SELECT username FROM users WHERE users.id = inbox_replies.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE inbox_replies SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass

            conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_hot ON inbox_replies(is_hot_lead);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_class ON inbox_replies(classification);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_operator ON inbox_replies(operator_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_owner ON inbox_replies(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_replies_tenant ON inbox_replies(tenant_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inbox_msgid ON inbox_replies(message_id);")

            # 8. Autonomous 7-Day Follow-Up Sequences
            conn.execute("""
                CREATE TABLE IF NOT EXISTS followup_sequences (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    initial_outreach_id TEXT,
                    recipient_email TEXT NOT NULL,
                    initial_sent_at TIMESTAMP NOT NULL,
                    followup_due_at TIMESTAMP NOT NULL,
                    followup_sent_at TIMESTAMP,
                    step_number INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'PENDING' -- 'PENDING', 'QUEUED_FOR_APPROVAL', 'SENT', 'TERMINATED'
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_followup_due ON followup_sequences(followup_due_at, status);")

            # 9. Permanent DNC / GDPR Blacklist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dnc_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT NOT NULL UNIQUE, -- clean domain or email
                    entity_type TEXT NOT NULL,   -- 'email', 'domain'
                    reason TEXT NOT NULL,
                    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dnc_entity ON dnc_blacklist(entity);")

            # 10. Operator Session / Activity Audit Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operator_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,         -- 'LOGIN', 'LOGOUT', 'SCRAPE', 'APPROVE', 'REJECT', 'BACKUP', 'SETTINGS_CHANGE'
                    detail TEXT,
                    ip_address TEXT,
                    device_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON operator_sessions(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON operator_sessions(created_at);")

            existing_sess_cols = {col["name"] for col in conn.execute("PRAGMA table_info(operator_sessions)").fetchall()}
            if "tenant_id" not in existing_sess_cols:
                conn.execute("ALTER TABLE operator_sessions ADD COLUMN tenant_id TEXT DEFAULT '';")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON operator_sessions(tenant_id);")
            try:
                conn.execute("UPDATE operator_sessions SET tenant_id = user_id WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass

            # -------------------------------------------------------------
            # SAAS MULTI-TENANCY & COMPLIANCE EXTENSIONS
            # -------------------------------------------------------------
            # 11. Multi-Service Template Pool
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_templates (
                    id TEXT PRIMARY KEY,
                    operator_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    subject_template TEXT NOT NULL,
                    body_template TEXT NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    owner_username TEXT DEFAULT ''
                );
            """)
            existing_tpl_cols = {col["name"] for col in conn.execute("PRAGMA table_info(service_templates)").fetchall()}
            if "owner_username" not in existing_tpl_cols:
                conn.execute("ALTER TABLE service_templates ADD COLUMN owner_username TEXT DEFAULT '';")
            if "tenant_id" not in existing_tpl_cols:
                conn.execute("ALTER TABLE service_templates ADD COLUMN tenant_id TEXT DEFAULT '';")
            try:
                conn.execute("UPDATE service_templates SET owner_username = (SELECT username FROM users WHERE users.id = service_templates.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE service_templates SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_operator ON service_templates(operator_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_owner ON service_templates(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_tenant ON service_templates(tenant_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_niche ON service_templates(niche);")

            # 12. Global & Per-User Suppressed Domains / Emails (Unsubscribes & Bounces)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suppressed_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT NOT NULL UNIQUE, -- clean lowercase domain or email
                    entity_type TEXT NOT NULL,   -- 'email', 'domain'
                    reason TEXT NOT NULL,        -- 'UNSUBSCRIBE', 'BOUNCE', 'SPAM_COMPLAINT', 'MANUAL_OPT_OUT'
                    operator_id TEXT,
                    owner_username TEXT DEFAULT '',
                    suppressed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            existing_sup_cols = {col["name"] for col in conn.execute("PRAGMA table_info(suppressed_entities)").fetchall()}
            if "owner_username" not in existing_sup_cols:
                conn.execute("ALTER TABLE suppressed_entities ADD COLUMN owner_username TEXT DEFAULT '';")
            if "tenant_id" not in existing_sup_cols:
                conn.execute("ALTER TABLE suppressed_entities ADD COLUMN tenant_id TEXT DEFAULT '';")
            try:
                conn.execute("UPDATE suppressed_entities SET owner_username = (SELECT username FROM users WHERE users.id = suppressed_entities.operator_id) WHERE (owner_username IS NULL OR owner_username = '') AND operator_id IS NOT NULL;")
                conn.execute("UPDATE suppressed_entities SET tenant_id = COALESCE(NULLIF(operator_id, ''), NULLIF(owner_username, '')) WHERE (tenant_id IS NULL OR tenant_id = '');")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_suppressed_entity ON suppressed_entities(entity);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_suppressed_owner ON suppressed_entities(owner_username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_suppressed_tenant ON suppressed_entities(tenant_id);")

            # 9. Permanent DNC / GDPR Blacklist
            existing_dnc_cols = {col["name"] for col in conn.execute("PRAGMA table_info(dnc_blacklist)").fetchall()}
            if "owner_username" not in existing_dnc_cols:
                conn.execute("ALTER TABLE dnc_blacklist ADD COLUMN owner_username TEXT DEFAULT '';")
            if "is_global" not in existing_dnc_cols:
                conn.execute("ALTER TABLE dnc_blacklist ADD COLUMN is_global INTEGER DEFAULT 0;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dnc_owner ON dnc_blacklist(owner_username);")

            # 13. Global Domain Blacklist Rules
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklist_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL UNIQUE, -- e.g. '*.gov', '*.edu', 'competitor.com'
                    entity_type TEXT NOT NULL DEFAULT 'domain',
                    reason TEXT NOT NULL DEFAULT 'Excluded Domain Pattern',
                    created_by TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_blacklist_pattern ON blacklist_rules(pattern);")

            # 14. Manual Operator Billing & License Subscriptions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operator_billing (
                    id TEXT PRIMARY KEY,
                    operator_id TEXT NOT NULL,
                    base_price REAL NOT NULL,
                    duration_days INTEGER NOT NULL,
                    discount_percent REAL DEFAULT 0.0,
                    discount_amount REAL DEFAULT 0.0,
                    final_price REAL NOT NULL,
                    extended_until TEXT NOT NULL,
                    notes TEXT,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_operator ON operator_billing(operator_id);")

            # 15. User Subscription Plan Requests (Post-Trial Paywall)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscription_requests (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    plan_name TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    price REAL NOT NULL,
                    payment_method TEXT DEFAULT 'MANUAL_INVOICE',
                    notes TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_req_user ON subscription_requests(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_req_status ON subscription_requests(status);")

            # 16. System & Billing Configuration
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()

        # Run startup/migration cleanup for public email provider domain wildcards
        self.purge_public_domain_suppressions()

    def purge_public_domain_suppressions(self) -> Dict[str, int]:
        """
        Startup & migration cleanup routine:
        Purges any domain-level suppression, blacklist, or wildcard entries
        for public webmail providers (gmail.com, yahoo.com, outlook.com, etc.).
        Ensures exact recipient emails are preserved while unblocking root domains.
        """
        public_domains = [
            "gmail.com", "googlemail.com", "yahoo.com", "ymail.com",
            "outlook.com", "hotmail.com", "live.com", "msn.com",
            "icloud.com", "me.com", "mac.com", "aol.com", "protonmail.com",
            "proton.me", "zoho.com", "yandex.com", "mail.com", "gmx.com", "gmx.de"
        ]
        counts = {
            "suppressed_entities_purged": 0,
            "blacklist_rules_purged": 0,
            "vault_leads_restored": 0,
            "outreach_queue_restored": 0
        }

        try:
            with self.get_connection() as conn:
                for pub in public_domains:
                    # 1. Purge root public domains from suppressed_entities
                    r1 = conn.execute(
                        "DELETE FROM suppressed_entities WHERE lower(entity) = ?", (pub,)
                    ).rowcount
                    counts["suppressed_entities_purged"] += r1

                    # 2. Purge root public domain blacklist rules (preserve specific email rules)
                    r2 = conn.execute(
                        "DELETE FROM blacklist_rules WHERE lower(pattern) = ? AND (entity_type = 'domain' OR pattern NOT LIKE '%@%')",
                        (pub,)
                    ).rowcount
                    counts["blacklist_rules_purged"] += r2

                    # 3. Restore vault leads mistakenly marked unsubscribed purely because domain was a public webmail domain
                    r3 = conn.execute("""
                        UPDATE vault_leads
                        SET unsubscribed = 0
                        WHERE lower(domain) = ? AND unsubscribed = 1
                          AND lower(primary_email) NOT IN (
                              SELECT lower(entity) FROM suppressed_entities
                          )
                          AND lower(primary_email) NOT IN (
                              SELECT lower(pattern) FROM blacklist_rules
                          )
                    """, (pub,)).rowcount
                    counts["vault_leads_restored"] += r3

                    # 4. Restore outreach queue leads that were erroneously marked SUPPRESSED due to domain wildcard
                    r4 = conn.execute("""
                        UPDATE outreach_queue
                        SET status = 'PENDING_APPROVAL', unsubscribed = 0, bounce_reason = NULL
                        WHERE (lower(recipient) LIKE ? OR lower(bounce_reason) LIKE ?)
                          AND status = 'SUPPRESSED'
                          AND lower(recipient) NOT IN (
                              SELECT lower(entity) FROM suppressed_entities
                          )
                          AND lower(recipient) NOT IN (
                              SELECT lower(pattern) FROM blacklist_rules
                          )
                    """, (f"%@{pub}", f"%@{pub}%")).rowcount
                    counts["outreach_queue_restored"] += r4

                conn.commit()
        except Exception as e:
            logger.warning(f"Error during public domain suppression purge: {e}")

        return counts


_global_db_engine = None

def get_db_engine() -> DatabaseEngine:
    global _global_db_engine
    if _global_db_engine is None:
        _global_db_engine = DatabaseEngine()
    return _global_db_engine
