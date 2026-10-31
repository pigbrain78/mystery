"""Append-only, hash-chained event ledger. The authoritative store.

Design rules enforced here, not merely documented:

  * No event is ever updated or deleted — enforced by SQLite triggers, so even a bulk
    "migration" script that tries to rewrite history is aborted by the database.
  * Every event is hash-chained to its predecessor; `prev_hash` of seq n is `event_hash`
    of seq n-1 (GENESIS_HASH for seq 1).
  * Sequence numbers are contiguous from 1.
  * Timestamps are INJECTED by the caller. Nothing in the hashing path reads the clock —
    a `datetime.now()` inside the event path makes replay non-deterministic and the chain
    unverifiable.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .canonical import (
    DOMAIN_CONTENT,
    DOMAIN_EVENT,
    GENESIS_HASH,
    canonical_json,
    digest,
)
from .models import SCHEMA_VERSION

__all__ = ["Ledger", "Event", "LedgerIntegrityError", "ChainReport"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq            INTEGER PRIMARY KEY,
    event_id       TEXT NOT NULL UNIQUE,
    event_type     TEXT NOT NULL,
    prev_hash      TEXT NOT NULL,
    content_hash   TEXT NOT NULL,
    payload_json   TEXT NOT NULL,
    actor          TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    event_hash     TEXT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events is append-only: UPDATE is forbidden');
END;

CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events is append-only: DELETE is forbidden');
END;
"""


class LedgerIntegrityError(RuntimeError):
    """The chain does not verify. Refuse all reads and writes until resolved."""


@dataclass(frozen=True)
class Event:
    seq: int
    event_id: str
    event_type: str
    prev_hash: str
    content_hash: str
    payload: dict[str, Any]
    actor: str
    created_at: str
    schema_version: int
    event_hash: str

    @property
    def header(self) -> dict[str, Any]:
        """The exact dict that was hashed. `payload_json` is deliberately excluded."""
        return {
            "v": self.schema_version,
            "seq": self.seq,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "prev_hash": self.prev_hash,
            "content_hash": self.content_hash,
            "actor": self.actor,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ChainReport:
    ok: bool
    length: int
    head_hash: str | None
    broken_at: int | None = None
    reason: str | None = None

    def raise_if_broken(self) -> None:
        if not self.ok:
            raise LedgerIntegrityError(
                f"ledger chain broken at seq {self.broken_at}: {self.reason}"
            )


class Ledger:
    """SQLite-backed append-only chain.

    The connection is per-instance and not thread-safe; give each thread its own Ledger
    or wrap access in the service layer. Reads never mutate.
    """

    def __init__(self, db_path: str | Path = "memory_brain.db") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    # -- lifecycle ---------------------------------------------------------------------
    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Ledger":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- writes ------------------------------------------------------------------------
    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        actor: str,
        created_at: str,
        event_id: str | None = None,
    ) -> Event:
        """Append one event and return it.

        ``created_at`` is required and injected — the ledger never reads the clock.
        """
        if not created_at:
            raise ValueError("created_at must be injected by the caller (RFC3339 UTC)")

        payload_json = canonical_json(payload)
        content_hash = digest(DOMAIN_CONTENT, payload)

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            head = self.head()
            seq = 1 if head is None else head.seq + 1
            prev_hash = GENESIS_HASH if head is None else head.event_hash

            event = Event(
                seq=seq,
                event_id=event_id or str(uuid.uuid4()),
                event_type=event_type,
                prev_hash=prev_hash,
                content_hash=content_hash,
                payload=payload,
                actor=actor,
                created_at=created_at,
                schema_version=SCHEMA_VERSION,
                event_hash="",  # computed below from the header
            )
            event_hash = digest(DOMAIN_EVENT, event.header)
            event = Event(**{**event.__dict__, "event_hash": event_hash})

            self._conn.execute(
                "INSERT INTO events (seq, event_id, event_type, prev_hash, content_hash,"
                " payload_json, actor, created_at, schema_version, event_hash)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    event.seq,
                    event.event_id,
                    event.event_type,
                    event.prev_hash,
                    event.content_hash,
                    payload_json,
                    event.actor,
                    event.created_at,
                    event.schema_version,
                    event.event_hash,
                ),
            )
            self._conn.execute("COMMIT")
            return event
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # -- reads -------------------------------------------------------------------------
    def head(self) -> Event | None:
        row = self._conn.execute("SELECT * FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return self._row_to_event(row) if row else None

    def get(self, seq: int) -> Event | None:
        row = self._conn.execute("SELECT * FROM events WHERE seq = ?", (int(seq),)).fetchone()
        return self._row_to_event(row) if row else None

    def events(self, *, start: int = 1, end: int | None = None) -> Iterator[Event]:
        """Inclusive [start, end]. `end=None` means "to the head"."""
        sql = "SELECT * FROM events WHERE seq >= ?"
        params: list[Any] = [int(start)]
        if end is not None:
            sql += " AND seq <= ?"
            params.append(int(end))
        sql += " ORDER BY seq ASC"
        for row in self._conn.execute(sql, params):
            yield self._row_to_event(row)

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    # -- verification ------------------------------------------------------------------
    def verify_chain(self, *, end: int | None = None) -> ChainReport:
        """Recompute every hash and every link. Does not trust stored hashes."""
        expected_prev = GENESIS_HASH
        expected_seq = 1
        last_hash: str | None = None
        length = 0

        for event in self.events(end=end):
            length += 1
            if event.seq != expected_seq:
                return ChainReport(
                    ok=False, length=length, head_hash=last_hash,
                    broken_at=event.seq,
                    reason=f"sequence gap: expected {expected_seq}, found {event.seq}",
                )
            if event.prev_hash != expected_prev:
                return ChainReport(
                    ok=False, length=length, head_hash=last_hash,
                    broken_at=event.seq,
                    reason="prev_hash does not match predecessor event_hash",
                )
            recomputed_content = digest(DOMAIN_CONTENT, event.payload)
            if recomputed_content != event.content_hash:
                return ChainReport(
                    ok=False, length=length, head_hash=last_hash,
                    broken_at=event.seq,
                    reason="content_hash does not recompute from payload",
                )
            recomputed_event = digest(DOMAIN_EVENT, event.header)
            if recomputed_event != event.event_hash:
                return ChainReport(
                    ok=False, length=length, head_hash=last_hash,
                    broken_at=event.seq,
                    reason="event_hash does not recompute from header",
                )
            expected_prev = event.event_hash
            expected_seq += 1
            last_hash = event.event_hash

        return ChainReport(ok=True, length=length, head_hash=last_hash)

    def require_intact(self) -> ChainReport:
        """Verify and raise on failure — call before serving any read."""
        report = self.verify_chain()
        report.raise_if_broken()
        return report

    # -- helpers -----------------------------------------------------------------------
    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> Event:
        import json

        return Event(
            seq=row["seq"],
            event_id=row["event_id"],
            event_type=row["event_type"],
            prev_hash=row["prev_hash"],
            content_hash=row["content_hash"],
            payload=json.loads(row["payload_json"]),
            actor=row["actor"],
            created_at=row["created_at"],
            schema_version=row["schema_version"],
            event_hash=row["event_hash"],
        )
