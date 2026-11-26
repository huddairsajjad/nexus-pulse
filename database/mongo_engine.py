"""
Nexus-Pulse Production Build
Database Module: MongoDB Engine & Unique Deduplication Guard
Enforces MongoDB unique indexes on domain and primary_email to prevent duplicate lead insertions.
Provides automatic cloud connection (via MONGO_URI) with transparent mongomock fallback
for offline, local, or containerized environments.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("nexus.mongo")

# Try importing pymongo and mongomock
try:
    import pymongo
    import pymongo.errors
except ImportError:
    pymongo = None

try:
    import mongomock
except ImportError:
    mongomock = None


class MongoDatabaseEngine:
    """
    Direct MongoDB persistence engine for Nexus-Pulse Lead persistence and multi-tenant isolation.
    Enforces strict unique indexes on (primary_email, tenant_id) and requires persistent MONGO_URI.
    Collections persist across container restarts. Zero ephemeral or SQLite fallback in production.
    """

    def __init__(self, uri: Optional[str] = None):
        raw_uri = uri or os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
        self.uri = raw_uri.strip() if raw_uri else None
        self.client = None
        self.db = None
        self.is_mock = False
        self._initialize_connection()
        self._ensure_unique_indexes()

    def _initialize_connection(self):
        """
        Connects directly to live MongoDB using MONGO_URI.
        If MONGO_URI is missing or empty, fails fast at startup with a clear error
        instead of silently falling back to local SQLite or ephemeral storage.
        Offline test mode (e.g. pytest) uses mongomock only when explicitly in testing.
        """
        is_test_env = bool(
            os.getenv("PYTEST_CURRENT_TEST") or
            os.getenv("NEXUS_TEST_MODE") or
            os.getenv("TESTING") or
            (self.uri == "mongomock")
        )

        # 1. If explicitly mongomock in test env or running tests without live MONGO_URI:
        if self.uri == "mongomock" or (not self.uri and is_test_env):
            if mongomock:
                self.client = mongomock.MongoClient()
                self.db = self.client["nexus_pulse"]
                self.is_mock = True
                logger.info("[MONGO] Running in isolated test mode with in-memory mongomock.")
                return
            else:
                raise RuntimeError("Test environment requested mock MongoDB but mongomock is not installed.")

        # 2. Production check: MONGO_URI is strictly required!
        if not self.uri:
            err_msg = (
                "FATAL STARTUP ERROR: 'MONGO_URI' environment variable is missing or empty. "
                "Nexus-Pulse requires a persistent MongoDB connection string (os.getenv('MONGO_URI')) to start. "
                "Local SQLite and ephemeral storage fallbacks are disabled in production."
            )
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        # 3. Direct connection to live MongoDB
        if not pymongo:
            err_msg = "FATAL: 'pymongo' library is not installed. Live MongoDB connection cannot be established."
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        try:
            self.client = pymongo.MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            # Test connection with ping
            self.client.admin.command("ping")

            # Determine database name
            try:
                default_db = self.client.get_default_database()
                self.db = default_db if default_db is not None else self.client["nexus_pulse"]
            except Exception:
                db_name = self.uri.split("/")[-1].split("?")[0].strip() or "nexus_pulse"
                self.db = self.client[db_name]

            self.is_mock = False
            safe_target = self.uri.split("@")[-1] if "@" in self.uri else "cluster"
            logger.info(f"[MONGO] Successfully connected directly to live persistent MongoDB ({safe_target}/{self.db.name})")
        except Exception as ex:
            if is_test_env and mongomock:
                logger.warning(f"[MONGO TEST] Live MongoDB unavailable in test suite ({ex}). Using mongomock.")
                self.client = mongomock.MongoClient()
                self.db = self.client["nexus_pulse"]
                self.is_mock = True
                return

            err_msg = (
                f"FATAL STARTUP ERROR: Failed to connect directly to MongoDB via MONGO_URI: {ex}. "
                "Please verify your connection string, credentials, network connectivity, and whitelist settings. "
                "Ephemeral storage fallback is strictly disabled."
            )
            logger.critical(err_msg)
            raise RuntimeError(err_msg) from ex

    def _ensure_connected(self):
        """Validates connection to MongoDB and auto-reconnects if disconnected."""
        if self.client and not self.is_mock and pymongo:
            try:
                self.client.admin.command("ping")
            except Exception:
                logger.warning("[MONGO] Transient connection drop detected; reconnecting...")
                self._initialize_connection()
        elif self.db is None:
            self._initialize_connection()

    def _ensure_unique_indexes(self):
        """
        Enforces indexes on collections including strict tenant_id indexing,
        multi-tenant unique lead index (primary_email, tenant_id),
        and user unique credentials.
        Never drops or wipes collections so data persists across restarts.
        """
        if self.db is None:
            return

        try:
            # 1. Leads collection indexes
            for legacy_idx in ("idx_leads_domain_unique", "idx_leads_email_unique"):
                try:
                    self.db.leads.drop_index(legacy_idx)
                except Exception:
                    pass

            # Multi-tenant unique index: email per tenant_id
            self.db.leads.create_index(
                [("primary_email", pymongo.ASCENDING), ("tenant_id", pymongo.ASCENDING)],
                unique=True,
                name="idx_leads_email_tenant_unique"
            )
            self.db.leads.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_leads_tenant_id")
            self.db.leads.create_index([("operator_id", pymongo.ASCENDING)], name="idx_leads_operator_id")
            self.db.leads.create_index([("owner_username", pymongo.ASCENDING)], name="idx_leads_owner_username")
            self.db.leads.create_index([("domain", pymongo.ASCENDING)], name="idx_leads_domain")
            self.db.leads.create_index([("status", pymongo.ASCENDING)], name="idx_leads_status")
            self.db.leads.create_index([("unsubscribed", pymongo.ASCENDING)], name="idx_leads_unsubscribed")

            # 2. Users collection indexes
            self.db.users.create_index([("username", pymongo.ASCENDING)], unique=True, name="idx_users_username_unique")
            self.db.users.create_index([("email", pymongo.ASCENDING)], unique=True, sparse=True, name="idx_users_email_unique")
            self.db.users.create_index([("id", pymongo.ASCENDING)], unique=True, sparse=True, name="idx_users_id_unique")
            self.db.users.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_users_tenant_id")
            self.db.users.create_index([("role", pymongo.ASCENDING)], name="idx_users_role")

            # 3. Outreach queue collection indexes
            self.db.outreach.create_index([("queue_id", pymongo.ASCENDING)], name="idx_outreach_queue_id")
            self.db.outreach.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_outreach_tenant_id")
            self.db.outreach.create_index([("operator_id", pymongo.ASCENDING)], name="idx_outreach_operator_id")
            self.db.outreach.create_index([("owner_username", pymongo.ASCENDING)], name="idx_outreach_owner_username")
            self.db.outreach.create_index([("status", pymongo.ASCENDING)], name="idx_outreach_status")

            # 4. Mailboxes collection indexes
            self.db.mailboxes.create_index([("mailbox_id", pymongo.ASCENDING)], name="idx_mailboxes_id")
            self.db.mailboxes.create_index([("email_address", pymongo.ASCENDING)], name="idx_mailboxes_email")
            self.db.mailboxes.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_mailboxes_tenant_id")
            self.db.mailboxes.create_index([("operator_id", pymongo.ASCENDING)], name="idx_mailboxes_operator_id")
            self.db.mailboxes.create_index([("owner_username", pymongo.ASCENDING)], name="idx_mailboxes_owner_username")

            # 5. Service Templates & Logs indexes
            self.db.service_templates.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_templates_tenant_id")
            self.db.service_templates.create_index([("id", pymongo.ASCENDING)], name="idx_templates_id")
            self.db.logs.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_logs_tenant_id")
            self.db.dedup_registry.create_index([("tenant_id", pymongo.ASCENDING)], name="idx_dedup_tenant_id")

            logger.info("[MONGO] Enforced per-tenant unique indexes and multi-tenant schema isolation.")
        except Exception as ex:
            logger.warning(f"[MONGO] Index setup notice: {ex}")

    def insert_lead(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts lead into MongoDB collection with strict tenant_id isolation.
        Raises DuplicateKeyError or ValueError if primary_email already exists for this tenant.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        clean_doc = dict(lead_dict)
        clean_doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        clean_doc.setdefault("unsubscribed", False)
        
        # Enforce tenant_id across leads collection
        raw_tenant = clean_doc.get("tenant_id") or clean_doc.get("operator_id") or clean_doc.get("owner_username") or ""
        clean_doc["tenant_id"] = str(raw_tenant).strip()
        clean_doc["owner_username"] = str(clean_doc.get("owner_username") or "").strip().lower()
        if "domain" in clean_doc and clean_doc["domain"]:
            clean_doc["domain"] = clean_doc["domain"].strip().lower()
        if "primary_email" in clean_doc and clean_doc["primary_email"]:
            clean_doc["primary_email"] = clean_doc["primary_email"].strip().lower()

        try:
            res = self.db.leads.insert_one(clean_doc)
            return {
                "success": True,
                "inserted_id": str(res.inserted_id),
                "tenant_id": clean_doc["tenant_id"],
                "domain": clean_doc.get("domain"),
                "primary_email": clean_doc.get("primary_email")
            }
        except pymongo.errors.DuplicateKeyError as dke:
            logger.warning(f"[MONGO DEDUP] Blocked duplicate lead insertion for tenant '{clean_doc['tenant_id']}': {dke}")
            raise ValueError(f"DUPLICATE_LEAD: Lead email already exists in MongoDB for this tenant ({clean_doc.get('primary_email')})")
        except Exception as ex:
            logger.error(f"[MONGO] Lead insert error: {ex}")
            raise

    def is_duplicate(
        self,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        check_domain: bool = True,
    ) -> bool:
        """Checks if a domain or email already exists in MongoDB leads collection for this tenant."""
        self._ensure_connected()
        if self.db is None:
            return False

        query = []
        if check_domain and domain:
            query.append({"domain": domain.strip().lower()})
        if email:
            query.append({"primary_email": email.strip().lower()})

        if not query:
            return False

        tenant_filter = self._build_tenant_filter(owner_username=owner_username, operator_id=operator_id, tenant_id=tenant_id)
        if tenant_filter:
            found = self.db.leads.find_one({"$and": [{"$or": query}, tenant_filter]})
        else:
            found = self.db.leads.find_one({"$or": query})
        return found is not None

    def find_lead(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds single lead matching query."""
        self._ensure_connected()
        if self.db is None:
            return None
        return self.db.leads.find_one(query)

    def set_unsubscribed(self, email_or_domain: str) -> int:
        """Marks lead as unsubscribed: true across MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return 0
        target = email_or_domain.strip().lower()
        res = self.db.leads.update_many(
            {"$or": [{"primary_email": target}, {"domain": target}]},
            {"$set": {"unsubscribed": True, "unsubscribed_at": datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count

    def is_unsubscribed(self, email_or_domain: str) -> bool:
        """Checks if lead has unsubscribed: true in MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return False
        target = email_or_domain.strip().lower()
        found = self.db.leads.find_one({
            "$or": [{"primary_email": target}, {"domain": target}],
            "unsubscribed": True
        })
        return found is not None

    @staticmethod
    def _build_tenant_filter(
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Builds a strict MongoDB tenant filter scoped to tenant_id, owner_username and/or operator_id."""
        t_id = (tenant_id or "").strip()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        clauses = []
        if t_id:
            clauses.append({"tenant_id": t_id})
        if op_id and op_id != t_id:
            clauses.append({"operator_id": op_id})
        elif not t_id and op_id:
            clauses.append({"operator_id": op_id})
        if owner and owner != t_id and owner != op_id:
            clauses.append({"owner_username": owner})
        elif not t_id and not op_id and owner:
            clauses.append({"owner_username": owner})

        if not clauses:
            resolved = t_id or op_id or owner
            if resolved:
                return {"$or": [{"tenant_id": resolved}, {"operator_id": resolved}, {"owner_username": resolved.lower()}]}
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$or": clauses}

    def update_outreach_lead_content(
        self,
        queue_id: str,
        lead_id: Optional[str],
        old_email: str,
        new_email: str,
        company_name: str,
        subject: str,
        body: str,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        approved_by: Optional[str] = None,
        status: str = "approved",
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Persists modified lead/outreach fields in MongoDB (leads & outreach collections),
        strictly scoped to the authenticated user/tenant.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_old = (old_email or "").strip().lower()
        clean_new = (new_email or "").strip().lower()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        t_id = (tenant_id or "").strip() or op_id or owner
        tenant_filter = self._build_tenant_filter(owner_username=owner, operator_id=op_id, tenant_id=t_id)

        identity_clauses: List[Dict[str, Any]] = []
        if lead_id:
            identity_clauses.append({"lead_id": lead_id})
        if clean_old:
            identity_clauses.append({"primary_email": clean_old})
        if clean_new and clean_new != clean_old:
            identity_clauses.append({"primary_email": clean_new})

        base_fields: Dict[str, Any] = {
            "company_name": company_name,
            "recipient_email": clean_new,
            "subject": subject,
            "body": body,
            "message_body": body,
            "status": status,
            "updated_at": now_iso,
        }
        if approved_by:
            base_fields["approved_by"] = approved_by
            base_fields["approved_at"] = now_iso
        if owner:
            base_fields["owner_username"] = owner
        if op_id:
            base_fields["operator_id"] = op_id
        if t_id:
            base_fields["tenant_id"] = t_id

        leads_modified = 0
        if identity_clauses:
            lead_filter: Dict[str, Any] = {"$or": identity_clauses}
            if tenant_filter:
                lead_filter = {"$and": [lead_filter, tenant_filter]}
            lead_update = dict(base_fields)
            if clean_new:
                lead_update["primary_email"] = clean_new
            try:
                res = self.db.leads.update_many(lead_filter, {"$set": lead_update})
                leads_modified = res.modified_count
            except Exception as ex:
                if pymongo and isinstance(ex, pymongo.errors.DuplicateKeyError):
                    lead_update.pop("primary_email", None)
                    res = self.db.leads.update_many(lead_filter, {"$set": lead_update})
                    leads_modified = res.modified_count
                else:
                    logger.warning(f"[MONGO] update_outreach_lead_content leads notice: {ex}")

        outreach_filter: Dict[str, Any] = {"queue_id": queue_id}
        if tenant_filter:
            outreach_filter = {"$and": [outreach_filter, tenant_filter]}
        outreach_doc = dict(base_fields)
        outreach_doc["queue_id"] = queue_id
        if lead_id:
            outreach_doc["lead_id"] = lead_id
        if clean_new:
            outreach_doc["primary_email"] = clean_new
        if t_id:
            outreach_doc["tenant_id"] = t_id
        try:
            self.db.outreach.update_one(outreach_filter, {"$set": outreach_doc}, upsert=True)
        except Exception as ex:
            logger.warning(f"[MONGO] update_outreach_lead_content outreach notice: {ex}")

        return {"success": True, "leads_modified": leads_modified}

    def mark_lead_dispatched(
        self,
        queue_id: str,
        lead_id: Optional[str],
        recipient_email: str,
        mailbox_used: str,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        delivery_method: str = "WEBHOOK",
        dispatched_at: Optional[str] = None,
        message_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates a specific user-owned lead's status to 'dispatched' in MongoDB
        upon verified webhook/SMTP dispatch success, strictly scoped to tenant.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        now_iso = dispatched_at or datetime.now(timezone.utc).isoformat()
        clean_email = (recipient_email or "").strip().lower()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        t_id = (tenant_id or "").strip() or op_id or owner
        tenant_filter = self._build_tenant_filter(owner_username=owner, operator_id=op_id, tenant_id=t_id)

        dispatch_fields: Dict[str, Any] = {
            "status": "dispatched",
            "dispatched_at": now_iso,
            "sent_at": now_iso,
            "mailbox_used": mailbox_used,
            "delivery_method": delivery_method,
            "updated_at": now_iso,
        }
        if message_id:
            dispatch_fields["message_id"] = message_id
        if t_id:
            dispatch_fields["tenant_id"] = t_id

        identity_clauses: List[Dict[str, Any]] = []
        if lead_id:
            identity_clauses.append({"lead_id": lead_id})
        if clean_email:
            identity_clauses.append({"primary_email": clean_email})

        if identity_clauses:
            lead_filter: Dict[str, Any] = {"$or": identity_clauses}
            if tenant_filter:
                lead_filter = {"$and": [lead_filter, tenant_filter]}
            try:
                self.db.leads.update_many(lead_filter, {"$set": dispatch_fields})
            except Exception as ex:
                logger.warning(f"[MONGO] mark_lead_dispatched leads notice: {ex}")

        outreach_filter: Dict[str, Any] = {"queue_id": queue_id}
        if tenant_filter:
            outreach_filter = {"$and": [outreach_filter, tenant_filter]}
        outreach_update = dict(dispatch_fields)
        outreach_update["queue_id"] = queue_id
        if lead_id:
            outreach_update["lead_id"] = lead_id
        if clean_email:
            outreach_update["recipient_email"] = clean_email
            outreach_update["primary_email"] = clean_email
        if owner:
            outreach_update["owner_username"] = owner
        if op_id:
            outreach_update["operator_id"] = op_id
        if t_id:
            outreach_update["tenant_id"] = t_id
        try:
            self.db.outreach.update_one(outreach_filter, {"$set": outreach_update}, upsert=True)
        except Exception as ex:
            logger.warning(f"[MONGO] mark_lead_dispatched outreach notice: {ex}")

        return {"success": True, "status": "dispatched"}

    def increment_mailbox_sent_today(
        self,
        mailbox_id: Optional[str],
        email_address: str,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        sent_today: Optional[int] = None,
        daily_limit: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Increments or syncs only the active user's mailbox daily sent counter (sent_today) in MongoDB.
        Strictly scoped to tenant_id.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_email = (email_address or "").strip().lower()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        t_id = (tenant_id or "").strip() or op_id or owner
        tenant_filter = self._build_tenant_filter(owner_username=owner, operator_id=op_id, tenant_id=t_id)

        mb_clauses: List[Dict[str, Any]] = []
        if mailbox_id:
            mb_clauses.append({"mailbox_id": mailbox_id})
        if clean_email:
            mb_clauses.append({"email_address": clean_email})
        if not mb_clauses:
            return {"success": False, "reason": "MISSING_MAILBOX_KEY"}

        mb_filter: Dict[str, Any] = {"$or": mb_clauses} if len(mb_clauses) > 1 else mb_clauses[0]
        if tenant_filter:
            mb_filter = {"$and": [mb_filter, tenant_filter]}

        set_fields: Dict[str, Any] = {
            "email_address": clean_email,
            "updated_at": now_iso,
        }
        if mailbox_id:
            set_fields["mailbox_id"] = mailbox_id
        if owner:
            set_fields["owner_username"] = owner
        if op_id:
            set_fields["operator_id"] = op_id
        if t_id:
            set_fields["tenant_id"] = t_id
        if daily_limit is not None:
            set_fields["daily_limit"] = int(daily_limit)

        update_op: Dict[str, Any] = {"$set": set_fields}
        if sent_today is not None:
            set_fields["sent_today"] = int(sent_today)
        else:
            update_op["$inc"] = {"sent_today": 1}

        try:
            self.db.mailboxes.update_one(mb_filter, update_op, upsert=True)
        except Exception as ex:
            logger.warning(f"[MONGO] increment_mailbox_sent_today notice: {ex}")
            return {"success": False, "error": str(ex)}

        return {"success": True, "sent_today": sent_today}

    def find_user(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds a single user document in MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return None
        doc = self.db.users.find_one(query)
        if doc:
            doc = dict(doc)
            doc.pop("_id", None)
            return doc
        return None

    def upsert_user(self, user_doc: Dict[str, Any]) -> bool:
        """Upserts a user document into MongoDB users collection."""
        self._ensure_connected()
        if self.db is None:
            return False
        clean = dict(user_doc)
        clean.pop("_id", None)
        username = clean.get("username", "").strip().lower()
        if not username:
            return False
        clean["username"] = username
        if not clean.get("tenant_id"):
            clean["tenant_id"] = clean.get("id") or username
        self.db.users.update_one({"username": username}, {"$set": clean}, upsert=True)
        return True

    def count_users(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Counts user documents in MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return 0
        return self.db.users.count_documents(query or {})

    def has_admin(self) -> bool:
        """Checks if an administrator exists in MongoDB users collection."""
        return self.count_users({"role": "admin"}) > 0

    def list_users(self, tenant_id: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists users with optional tenant_id and role filtering."""
        self._ensure_connected()
        if self.db is None:
            return []
        q: Dict[str, Any] = {}
        if tenant_id:
            q["tenant_id"] = str(tenant_id).strip()
        if role:
            q["role"] = role
        cursor = self.db.users.find(q)
        results = []
        for doc in cursor:
            d = dict(doc)
            d.pop("_id", None)
            results.append(d)
        return results

    def update_user(self, username_or_id: str, updates: Dict[str, Any]) -> bool:
        """Updates fields on an existing user in MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return False
        clean = dict(updates)
        clean.pop("_id", None)
        target = username_or_id.strip()
        res = self.db.users.update_many(
            {"$or": [{"username": target.lower()}, {"id": target}]},
            {"$set": clean}
        )
        return res.modified_count > 0

    def delete_user(self, user_id_or_username: str) -> bool:
        """Deletes a user from MongoDB."""
        self._ensure_connected()
        if self.db is None:
            return False
        target = user_id_or_username.strip()
        res = self.db.users.delete_many({"$or": [{"username": target.lower()}, {"id": target}]})
        return res.deleted_count > 0

    def find_leads(
        self,
        tenant_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Finds leads strictly scoped to the tenant."""
        self._ensure_connected()
        if self.db is None:
            return []
        tenant_filter = self._build_tenant_filter(owner_username=owner_username, operator_id=operator_id, tenant_id=tenant_id)
        final_query = dict(query or {})
        if tenant_filter:
            final_query = {"$and": [final_query, tenant_filter]} if final_query else tenant_filter
        cursor = self.db.leads.find(final_query).skip(skip).limit(limit)
        results = []
        for doc in cursor:
            d = dict(doc)
            d.pop("_id", None)
            results.append(d)
        return results

    def count_leads(
        self,
        tenant_id: Optional[str] = None,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None
    ) -> int:
        """Counts leads strictly scoped to the tenant."""
        self._ensure_connected()
        if self.db is None:
            return 0
        tenant_filter = self._build_tenant_filter(owner_username=owner_username, operator_id=operator_id, tenant_id=tenant_id)
        final_query = dict(query or {})
        if tenant_filter:
            final_query = {"$and": [final_query, tenant_filter]} if final_query else tenant_filter
        return self.db.leads.count_documents(final_query)

    def purge_all(self) -> Dict[str, int]:
        """
        Permanently purges all documents across all collections in MongoDB.
        Used for Step 8 strict database cleanup.
        """
        self._ensure_connected()
        counts = {}
        if self.db is None:
            return counts

        for coll_name in ["leads", "users", "outreach", "mailboxes", "logs"]:
            try:
                cnt = self.db[coll_name].count_documents({})
                self.db[coll_name].delete_many({})
                counts[coll_name] = cnt
            except Exception:
                pass

        logger.info(f"[MONGO] Cleaned up MongoDB collections: {counts}")
        return counts


_global_mongo_engine = None

def get_mongo_engine() -> MongoDatabaseEngine:
    global _global_mongo_engine
    if _global_mongo_engine is None:
        _global_mongo_engine = MongoDatabaseEngine()
    return _global_mongo_engine
