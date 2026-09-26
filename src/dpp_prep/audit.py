"""The diary: a persistent, append-only record of every step (R09).

SQLite, with only two operations: add an event, read events. There is no
update or delete function. This makes the history durable and reproducible
for the thesis evaluation; it is NOT tamper-proof against someone editing
the database file directly, and the thesis should not claim that it is.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any, Optional

from .models import now

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    time         TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    element_id   TEXT,
    actor_role   TEXT NOT NULL,
    actor_id     TEXT,
    action       TEXT NOT NULL,
    record_version TEXT,
    detail       TEXT
)"""


class AuditStore:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        # The review screen handles each click in a different thread, so the
        # connection is shared across threads and guarded by a lock.
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._db.execute(_SCHEMA)
        self._db.commit()

    def add(self, run_id: str, actor_role: str, action: str, element_id: Optional[str] = None,
            actor_id: Optional[str] = None, record_version: Optional[str] = None,
            detail: Any = None) -> None:
        with self._lock:
            self._insert(run_id, actor_role, action, element_id, actor_id, record_version, detail)

    def _insert(self, run_id, actor_role, action, element_id, actor_id, record_version, detail) -> None:
        self._db.execute(
            "INSERT INTO events (time, run_id, element_id, actor_role, actor_id, action, record_version, detail)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), run_id, element_id, actor_role, actor_id, action, record_version,
             json.dumps(detail, default=str) if detail is not None else None))
        self._db.commit()

    def events(self, run_id: Optional[str] = None, element_id: Optional[str] = None) -> list[dict]:
        q, args = "SELECT * FROM events WHERE 1=1", []
        if run_id:
            q, args = q + " AND run_id = ?", args + [run_id]
        if element_id:
            q, args = q + " AND element_id = ?", args + [element_id]
        with self._lock:
            cur = self._db.execute(q + " ORDER BY seq", args)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
