from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from .models import Event


class EventStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def append(self, event: Event) -> None:
        payload_json = json.dumps(event.payload)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO events (ts, type, payload) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat(), event.type, payload_json),
            )
            conn.commit()

    def list_events(self) -> List[Event]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("SELECT type, payload FROM events ORDER BY id ASC").fetchall()
        events: List[Event] = []
        for row in rows:
            events.append(Event(type=row[0], payload=json.loads(row[1])))
        return events

    def clear(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM events")
            conn.commit()
