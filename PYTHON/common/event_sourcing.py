"""
common/event_sourcing.py — Distributed Event Sourcing (Phase 2)
Module 7 from anatoliax_prompt_v6.txt

Features:
  - All state S(t) derived from immutable event log E = [e_1, e_2, ..., e_n].
  - State reconstruction: S(t) = reduce(apply, E[0:t], S_0).
  - Event schema: {event_id, event_type, timestamp, payload, causation_id, correlation_id}.
  - Event types: MarketDataEvent, SignalEvent, RiskCheckEvent, OrderEvent, FillEvent, PositionEvent, PnLEvent, RegimeEvent.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class EventType(Enum):
    MARKET_DATA = "MarketDataEvent"
    SIGNAL = "SignalEvent"
    RISK_CHECK = "RiskCheckEvent"
    ORDER = "OrderEvent"
    FILL = "FillEvent"
    POSITION = "PositionEvent"
    PNL = "PnLEvent"
    REGIME = "RegimeEvent"


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.MARKET_DATA
    timestamp: int = field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1e9))
    payload: Dict[str, Any] = field(default_factory=dict)
    causation_id: str = ""
    correlation_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "payload": json.dumps(self.payload, sort_keys=True),
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        return cls(
            event_id=d["event_id"],
            event_type=EventType(d["event_type"]),
            timestamp=d["timestamp"],
            payload=json.loads(d["payload"]),
            causation_id=d["causation_id"],
            correlation_id=d["correlation_id"],
        )


class EventStore:
    """
    Immutable event log backed by SQLite WAL.
    All state S(t) derived from event log E.
    """

    def __init__(self, db_path: str = "event_store.db"):
        self.db_path = db_path
        self._conn = None
        if db_path == ":memory:" or db_path.startswith("file::memory:"):
            self._conn = sqlite3.connect(db_path, uri=db_path.startswith("file"))
            self._init_db(self._conn)
        else:
            self._init_db()

    def _init_db(self, conn=None):
        target = conn or sqlite3.connect(self.db_path)
        try:
            target.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    timestamp INTEGER,
                    payload TEXT,
                    causation_id TEXT,
                    correlation_id TEXT
                )
            """)
            target.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp)")
            target.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            target.commit()
        finally:
            if conn is None:
                target.close()

    def append(self, event: Event):
        """Append immutable event to log E."""
        if self._conn:
            self._conn.execute(
                "INSERT INTO events (event_id, event_type, timestamp, payload, causation_id, correlation_id) VALUES (?, ?, ?, ?, ?, ?)",
                (event.event_id, event.event_type.value, event.timestamp,
                 json.dumps(event.payload, sort_keys=True), event.causation_id, event.correlation_id)
            )
            self._conn.commit()
        else:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO events (event_id, event_type, timestamp, payload, causation_id, correlation_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (event.event_id, event.event_type.value, event.timestamp,
                     json.dumps(event.payload, sort_keys=True), event.causation_id, event.correlation_id)
                )
                conn.commit()

    def get_events(self, after_ts: int = 0, event_type: Optional[EventType] = None, limit: int = 10000) -> List[Event]:
        if self._conn:
            if event_type:
                cursor = self._conn.execute(
                    "SELECT event_id, event_type, timestamp, payload, causation_id, correlation_id FROM events WHERE timestamp > ? AND event_type = ? ORDER BY timestamp LIMIT ?",
                    (after_ts, event_type.value, limit)
                )
            else:
                cursor = self._conn.execute(
                    "SELECT event_id, event_type, timestamp, payload, causation_id, correlation_id FROM events WHERE timestamp > ? ORDER BY timestamp LIMIT ?",
                    (after_ts, limit)
                )
            rows = cursor.fetchall()
        else:
            with sqlite3.connect(self.db_path) as conn:
                if event_type:
                    cursor = conn.execute(
                        "SELECT event_id, event_type, timestamp, payload, causation_id, correlation_id FROM events WHERE timestamp > ? AND event_type = ? ORDER BY timestamp LIMIT ?",
                        (after_ts, event_type.value, limit)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT event_id, event_type, timestamp, payload, causation_id, correlation_id FROM events WHERE timestamp > ? ORDER BY timestamp LIMIT ?",
                        (after_ts, limit)
                    )
                rows = cursor.fetchall()
        return [Event.from_dict({
            "event_id": r[0], "event_type": r[1], "timestamp": r[2],
            "payload": r[3], "causation_id": r[4], "correlation_id": r[5]
        }) for r in rows]

    def replay(self, apply_fn: Callable[[Any, Event], Any], initial_state: Any) -> Any:
        """
        State reconstruction: S(t) = reduce(apply, E[0:t], S_0).
        """
        state = initial_state
        events = self.get_events(limit=1000000)
        for event in events:
            state = apply_fn(state, event)
        return state

    def checkpoint(self, state: Any, timestamp: int):
        """Periodic checkpoint for fast replay."""
        if self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO checkpoints (timestamp, state) VALUES (?, ?)",
                (timestamp, json.dumps(state, sort_keys=True, default=str))
            )
            self._conn.commit()
        else:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO checkpoints (timestamp, state) VALUES (?, ?)",
                    (timestamp, json.dumps(state, sort_keys=True, default=str))
                )
                conn.commit()


class EventBus:
    """
    In-memory event bus for pub/sub between agents.
    Mirrors common/message_bus.py with event sourcing support.
    """

    def __init__(self, event_store: Optional[EventStore] = None):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._store = event_store

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        self._subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event: Event):
        if self._store:
            self._store.append(event)
        for cb in self._subscribers.get(event.event_type, []):
            cb(event)
