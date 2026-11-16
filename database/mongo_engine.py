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

    def _ensure_unique_indexes(self):
        """Enforces MongoDB unique indexes on domain and primary_email."""
        if self.db is None:
            return

        try:
            # 1. Unique index on domain
            self.db.leads.create_index(
                [("domain", pymongo.ASCENDING)],
                unique=True,
                name="idx_leads_domain_unique"
            )
            # 2. Unique index on primary_email
            self.db.leads.create_index(
                [("primary_email", pymongo.ASCENDING)],
                unique=True,
                name="idx_leads_email_unique"
            )
            # Index on operator_id for fast tenant queries
            self.db.leads.create_index([("operator_id", pymongo.ASCENDING)])
            self.db.leads.create_index([("unsubscribed", pymongo.ASCENDING)])

            # Users collection unique index on email & username
            self.db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            self.db.users.create_index([("email", pymongo.ASCENDING)], unique=True, sparse=True)

            logger.info("[MONGO] Enforced unique indexes on leads(domain, primary_email).")
        except Exception as ex:
            logger.warning(f"[MONGO] Index creation notice: {ex}")

    def insert_lead(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts lead into MongoDB collection.
        Raises DuplicateKeyError or ValueError if domain or primary_email already exists.
        """
        if self.db is None:
            return {"success": False, "reason": "NO_MONGO_CONNECTION"}

        clean_doc = dict(lead_dict)
        clean_doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        clean_doc.setdefault("unsubscribed", False)
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

    def is_duplicate(self, domain: Optional[str] = None, email: Optional[str] = None) -> bool:
        """Checks if a domain or email already exists in MongoDB leads collection."""
        if self.db is None:
            return False

        query = []
        if domain:
            query.append({"domain": domain.strip().lower()})
        if email:
            query.append({"primary_email": email.strip().lower()})

        if not query:
            return False

        found = self.db.leads.find_one({"$or": query})
        return found is not None

    def find_lead(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds single lead matching query."""
        if self.db is None:
            return None
        return self.db.leads.find_one(query)

    def set_unsubscribed(self, email_or_domain: str) -> int:
        """Marks lead as unsubscribed: true across MongoDB."""
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
        if self.db is None:
            return False
        target = email_or_domain.strip().lower()
        found = self.db.leads.find_one({
            "$or": [{"primary_email": target}, {"domain": target}],
            "unsubscribed": True
        })
        return found is not None

    def purge_all(self) -> Dict[str, int]:
        """
        Permanently purges all documents across all collections in MongoDB.
        Used for Step 8 strict database cleanup.
        """
        counts = {}
        if self.db is None:
            return counts

        for coll_name in ["leads", "users", "outreach", "logs"]:
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
