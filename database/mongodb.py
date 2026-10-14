"""
D-RTOS: MongoDB Service
Persistent storage layer using MongoDB (pymongo).
Falls back to an in-memory store if MongoDB is unavailable.
"""

from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


# ============================================================
# In-Memory Fallback Store
# ============================================================

class _InMemoryCollection:
    """Mimics a MongoDB collection in memory when MongoDB is unavailable."""
    def __init__(self):
        self._docs: List[Dict] = []

    def insert_one(self, doc: Dict) -> Any:
        doc = dict(doc)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self._docs.append(doc)
        class _R:
            inserted_id = doc["_id"]
        return _R()

    def insert_many(self, docs: List[Dict]):
        for d in docs:
            self.insert_one(d)

    def find(self, query: Dict = None, **kwargs) -> List[Dict]:
        if not query:
            return list(self._docs)
        result = []
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                result.append(doc)
        return result

    def find_one(self, query: Dict = None) -> Optional[Dict]:
        results = self.find(query)
        return results[0] if results else None

    def update_one(self, query: Dict, update: Dict, upsert: bool = False):
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                return
        if upsert:
            new_doc = dict(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            self.insert_one(new_doc)

    def count_documents(self, query: Dict = None) -> int:
        return len(self.find(query))

    def drop(self):
        self._docs.clear()


class _InMemoryDB:
    def __init__(self):
        self._collections = {}

    def __getattr__(self, name: str) -> _InMemoryCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection()
        return self._collections[name]

    def __getitem__(self, name: str):
        return getattr(self, name)

    def list_collection_names(self):
        return list(self._collections.keys())



# ============================================================
# MongoDB Service
# ============================================================

class MongoDBService:
    """
    Service layer for all D-RTOS MongoDB operations.
    Connects to MongoDB (local or Atlas).
    Falls back to an in-memory store transparently on connection failure.
    """

    DB_NAME = "drtos_database"

    COLLECTIONS = [
        "radar_events",
        "processes",
        "scheduling_results",
        "memory_events",
        "resource_events",
        "deadlock_events",
        "synchronization_events",
        "system_metrics",
        "simulation_sessions",
    ]

    def __init__(self, connection_uri: str = "mongodb://localhost:27017/",
                 timeout_ms: int = 2000):
        self.connection_uri = connection_uri
        self.timeout_ms = timeout_ms
        self._client = None
        self._db = None
        self.connected: bool = False
        self.using_fallback: bool = False
        self._connect()

    def _connect(self):
        if not PYMONGO_AVAILABLE:
            self._use_fallback("pymongo not installed")
            return
        try:
            self._client = MongoClient(
                self.connection_uri,
                serverSelectionTimeoutMS=self.timeout_ms,
            )
            self._client.admin.command("ping")
            self._db = self._client[self.DB_NAME]
            self.connected = True
            self.using_fallback = False
        except Exception as e:
            self._use_fallback(str(e))

    def _use_fallback(self, reason: str):
        self._db = _InMemoryDB()
        self.connected = False
        self.using_fallback = True

    def reconnect(self, uri: Optional[str] = None):
        if uri:
            self.connection_uri = uri
        self._connect()

    @property
    def status(self) -> str:
        if self.connected:
            return "CONNECTED"
        return "IN-MEMORY (MongoDB offline)"

    def col(self, name: str):
        return self._db[name]

    # ------------------------------------------------------------------ #
    #  Session Management                                                   #
    # ------------------------------------------------------------------ #
    def create_session(self, session_id: Optional[str] = None) -> str:
        sid = session_id or f"DRTOS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        self.col("simulation_sessions").insert_one({
            "session_id": sid,
            "start_time": time.time(),
            "start_datetime": datetime.now().isoformat(),
            "status": "ACTIVE",
        })
        return sid

    def close_session(self, session_id: str, stats: Dict = None):
        self.col("simulation_sessions").update_one(
            {"session_id": session_id},
            {"$set": {
                "end_time": time.time(),
                "end_datetime": datetime.now().isoformat(),
                "status": "COMPLETED",
                "stats": stats or {},
            }},
        )

    def get_sessions(self) -> List[Dict]:
        return self.col("simulation_sessions").find({})

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.col("simulation_sessions").find_one({"session_id": session_id})

    # ------------------------------------------------------------------ #
    #  Radar Events                                                         #
    # ------------------------------------------------------------------ #
    def save_radar_event(self, event: Dict) -> str:
        event.setdefault("saved_at", time.time())
        result = self.col("radar_events").insert_one(event)
        return str(result.inserted_id)

    def get_radar_events(self, session_id: Optional[str] = None) -> List[Dict]:
        query = {"session_id": session_id} if session_id else {}
        return self.col("radar_events").find(query)

    # ------------------------------------------------------------------ #
    #  Processes                                                            #
    # ------------------------------------------------------------------ #
    def save_process(self, pcb_dict: Dict) -> str:
        pcb_dict.setdefault("saved_at", time.time())
        result = self.col("processes").insert_one(pcb_dict)
        return str(result.inserted_id)

    def save_processes(self, pcb_list: List[Dict]):
        for p in pcb_list:
            self.save_process(p)

    def get_processes(self, session_id: Optional[str] = None) -> List[Dict]:
        query = {"session_id": session_id} if session_id else {}
        return self.col("processes").find(query)

    # ------------------------------------------------------------------ #
    #  Scheduling Results                                                   #
    # ------------------------------------------------------------------ #
    def save_scheduling_result(self, result_dict: Dict) -> str:
        result_dict.setdefault("saved_at", time.time())
        r = self.col("scheduling_results").insert_one(result_dict)
        return str(r.inserted_id)

    def get_scheduling_results(self, session_id: Optional[str] = None) -> List[Dict]:
        query = {"session_id": session_id} if session_id else {}
        return self.col("scheduling_results").find(query)

    # ------------------------------------------------------------------ #
    #  Memory Events                                                        #
    # ------------------------------------------------------------------ #
    def save_memory_event(self, event: Dict) -> str:
        event.setdefault("saved_at", time.time())
        r = self.col("memory_events").insert_one(event)
        return str(r.inserted_id)

    # ------------------------------------------------------------------ #
    #  Resource Events                                                      #
    # ------------------------------------------------------------------ #
    def save_resource_event(self, event: Dict) -> str:
        event.setdefault("saved_at", time.time())
        r = self.col("resource_events").insert_one(event)
        return str(r.inserted_id)

    # ------------------------------------------------------------------ #
    #  Deadlock Events                                                      #
    # ------------------------------------------------------------------ #
    def save_deadlock_event(self, event: Dict) -> str:
        event.setdefault("saved_at", time.time())
        r = self.col("deadlock_events").insert_one(event)
        return str(r.inserted_id)

    # ------------------------------------------------------------------ #
    #  Synchronization Events                                               #
    # ------------------------------------------------------------------ #
    def save_sync_event(self, event: Dict) -> str:
        event.setdefault("saved_at", time.time())
        r = self.col("synchronization_events").insert_one(event)
        return str(r.inserted_id)

    # ------------------------------------------------------------------ #
    #  System Metrics                                                        #
    # ------------------------------------------------------------------ #
    def save_system_metrics(self, metrics: Dict) -> str:
        metrics.setdefault("saved_at", time.time())
        r = self.col("system_metrics").insert_one(metrics)
        return str(r.inserted_id)

    def get_system_metrics(self, session_id: Optional[str] = None) -> List[Dict]:
        query = {"session_id": session_id} if session_id else {}
        return self.col("system_metrics").find(query)

    # ------------------------------------------------------------------ #
    #  History / Analytics                                                  #
    # ------------------------------------------------------------------ #
    def get_session_history(self) -> List[Dict]:
        sessions = self.get_sessions()
        history = []
        for s in sessions:
            sid = s.get("session_id", "?")
            radar_count    = self.col("radar_events").count_documents({"session_id": sid})
            process_count  = self.col("processes").count_documents({"session_id": sid})
            sched_count    = self.col("scheduling_results").count_documents({"session_id": sid})
            history.append({
                **s,
                "radar_events": radar_count,
                "processes": process_count,
                "scheduling_results": sched_count,
            })
        return history
