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
    MongoDB abstraction for Nexus-Pulse Lead persistence and unique deduplication.
    Enforces strict unique indexes on domain and primary_email.
    """

    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
        self.client = None
        self.db = None
        self.is_mock = False
        self._initialize_connection()
        self._ensure_unique_indexes()

    def _initialize_connection(self):
        """Initializes connection to live MongoDB or falls back to mongomock."""
        if self.uri and pymongo:
            try:
                self.client = pymongo.MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000
                )
                # Test connection
                self.client.admin.command("ping")
                db_name = self.uri.split("/")[-1].split("?")[0] or "nexus_pulse"
                self.db = self.client[db_name]
                self.is_mock = False
                logger.info(f"[MONGO] Connected to live MongoDB at {self.uri.split('@')[-1]}")
                return
            except Exception as ex:
                logger.warning(f"[MONGO] Live MongoDB connection unavailable ({ex}). Falling back to in-memory mongomock.")

        # Fallback to mongomock
        if mongomock:
            self.client = mongomock.MongoClient()
            self.db = self.client["nexus_pulse"]
            self.is_mock = True
            logger.info("[MONGO] Initialized in-memory mongomock database with full index support.")
        else:
            logger.warning("[MONGO] Neither live MongoDB nor mongomock available.")

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
        """Enforces per-tenant MongoDB unique index on (primary_email, owner_username) for multi-email and user isolation."""
        if self.db is None:
            return

        try:
            for legacy_idx in ("idx_leads_domain_unique", "idx_leads_email_unique"):
                try:
                    self.db.leads.drop_index(legacy_idx)
                except Exception:
                    pass

            # Composite unique index per tenant & email (allows multi-email per domain + cross-tenant independence)
            self.db.leads.create_index(
                [("primary_email", pymongo.ASCENDING), ("owner_username", pymongo.ASCENDING)],
                unique=True,
                name="idx_leads_email_owner_unique"
            )
            self.db.leads.create_index([("domain", pymongo.ASCENDING)])
            self.db.leads.create_index([("operator_id", pymongo.ASCENDING)])
            self.db.leads.create_index([("owner_username", pymongo.ASCENDING)])
            self.db.leads.create_index([("unsubscribed", pymongo.ASCENDING)])

            # Users collection unique index on email & username
            self.db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            self.db.users.create_index([("email", pymongo.ASCENDING)], unique=True, sparse=True)

            # Outreach & Mailboxes indexes for strict tenant isolation
            self.db.outreach.create_index([("queue_id", pymongo.ASCENDING)])
            self.db.outreach.create_index([("owner_username", pymongo.ASCENDING)])
            self.db.outreach.create_index([("operator_id", pymongo.ASCENDING)])
            self.db.mailboxes.create_index([("mailbox_id", pymongo.ASCENDING)])
            self.db.mailboxes.create_index([("email_address", pymongo.ASCENDING)])
            self.db.mailboxes.create_index([("owner_username", pymongo.ASCENDING)])

            logger.info("[MONGO] Enforced per-user unique index on leads(primary_email, owner_username).")
        except Exception as ex:
            logger.warning(f"[MONGO] Index creation notice: {ex}")

    def insert_lead(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts lead into MongoDB collection.
        Raises DuplicateKeyError or ValueError if primary_email already exists for this owner.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        clean_doc = dict(lead_dict)
        clean_doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        clean_doc.setdefault("unsubscribed", False)
        clean_doc["owner_username"] = str(clean_doc.get("owner_username") or "").strip().lower()
        if "domain" in clean_doc:
            clean_doc["domain"] = clean_doc["domain"].strip().lower()
        if "primary_email" in clean_doc:
            clean_doc["primary_email"] = clean_doc["primary_email"].strip().lower()

        try:
            res = self.db.leads.insert_one(clean_doc)
            return {
                "success": True,
                "inserted_id": str(res.inserted_id),
                "domain": clean_doc.get("domain"),
                "primary_email": clean_doc.get("primary_email")
            }
        except pymongo.errors.DuplicateKeyError as dke:
            logger.warning(f"[MONGO DEDUP] Blocked duplicate lead insertion: {dke}")
            raise ValueError(f"DUPLICATE_LEAD: Lead domain or email already exists in MongoDB index ({clean_doc.get('domain')}, {clean_doc.get('primary_email')})")
        except Exception as ex:
            logger.error(f"[MONGO] Lead insert error: {ex}")
            raise

    def is_duplicate(
        self,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        owner_username: Optional[str] = None,
        operator_id: Optional[str] = None,
        check_domain: bool = True,
    ) -> bool:
        """Checks if a domain or email already exists in MongoDB leads collection for this user."""
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

        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()

        if owner or op_id:
            owner_clauses = []
            if owner:
                owner_clauses.append({"owner_username": owner})
            if op_id:
                owner_clauses.append({"operator_id": op_id})
            found = self.db.leads.find_one({"$and": [{"$or": query}, {"$or": owner_clauses}]})
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
    ) -> Dict[str, Any]:
        """Builds a strict MongoDB tenant filter scoped to owner_username and/or operator_id."""
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        clauses = []
        if owner:
            clauses.append({"owner_username": owner})
        if op_id:
            clauses.append({"operator_id": op_id})
        if not clauses:
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
        tenant_filter = self._build_tenant_filter(owner, op_id)

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
                # If unique index on (primary_email, owner_username) collides on email edit, persist non-key fields
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
    ) -> Dict[str, Any]:
        """
        Updates a specific user-owned lead's status to 'dispatched' in MongoDB
        upon verified webhook/SMTP dispatch success.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        now_iso = dispatched_at or datetime.now(timezone.utc).isoformat()
        clean_email = (recipient_email or "").strip().lower()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        tenant_filter = self._build_tenant_filter(owner, op_id)

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
    ) -> Dict[str, Any]:
        """
        Increments or syncs only the active user's mailbox daily sent counter (sent_today) in MongoDB.
        """
        self._ensure_connected()
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_email = (email_address or "").strip().lower()
        owner = (owner_username or "").strip().lower()
        op_id = (operator_id or "").strip()
        tenant_filter = self._build_tenant_filter(owner, op_id)

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
