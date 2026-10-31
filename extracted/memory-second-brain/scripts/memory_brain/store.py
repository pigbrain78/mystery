"""Derived projection — rebuildable, never patched.

The ledger is the source of truth. These tables are a projection: any disagreement means
the projection is wrong and gets rebuilt from the ledger. Nothing here may be edited
directly to "fix" a discrepancy — that would hide a determinism bug.

Rebuilding at an arbitrary `end` must reproduce the state as of that sequence, inclusive.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .canonical import canonical_json
from .ledger import Ledger

__all__ = ["Projection", "PROJECTION_SCHEMA"]

PROJECTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    memory_id           TEXT PRIMARY KEY,
    created_seq         INTEGER NOT NULL,
    last_seq            INTEGER NOT NULL,
    status              TEXT NOT NULL,
    claim               TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    provenance_class    TEXT NOT NULL,
    source_id           TEXT NOT NULL,
    importance          INTEGER NOT NULL DEFAULT 0,
    source_confidence   REAL NOT NULL DEFAULT 0.0,
    extraction_confidence REAL NOT NULL DEFAULT 0.0,
    inference_confidence  REAL NOT NULL DEFAULT 0.0,
    current_confidence    REAL NOT NULL DEFAULT 0.0,
    valid_from          TEXT,
    valid_to            TEXT,
    retention_class     TEXT NOT NULL DEFAULT 'STANDARD',
    tags_json           TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS memory_links (
    link_hash   TEXT PRIMARY KEY,
    from_id     TEXT NOT NULL,
    to_id       TEXT NOT NULL,
    kind        TEXT NOT NULL,
    created_seq INTEGER NOT NULL,
    weight      REAL
);

CREATE TABLE IF NOT EXISTS review_queue (
    item_id       TEXT PRIMARY KEY,
    kind          TEXT NOT NULL,
    memory_ids    TEXT NOT NULL,
    proposal_json TEXT NOT NULL,
    created_seq   INTEGER NOT NULL,
    state         TEXT NOT NULL DEFAULT 'OPEN',
    decided_seq   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_mem_status ON memories(status);
CREATE INDEX IF NOT EXISTS idx_links_from ON memory_links(from_id);
CREATE INDEX IF NOT EXISTS idx_links_to ON memory_links(to_id);
CREATE INDEX IF NOT EXISTS idx_review_state ON review_queue(state);
"""

#: Event types that move a memory's status.
_STATUS_EVENTS = {
    "MEMORY_STATUS_CHANGED": "status",
    "MEMORY_SUPERSEDED": "SUPERSEDED",
    "MEMORY_RETRACTED": "RETRACTED",
    "MEMORY_ARCHIVED": "ARCHIVED",
    "MEMORY_QUARANTINED": "QUARANTINED",
    "MEMORY_CORRECTED": "ACTIVE",
}


class Projection:
    """Writes and reads the derived tables. All writes come from replaying events."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(PROJECTION_SCHEMA)

    # -- rebuild -----------------------------------------------------------------------
    def rebuild(self, ledger: Ledger, *, end: int | None = None) -> int:
        """Drop and replay. Deterministic: same ledger + same end -> same projection."""
        self._conn.execute("DELETE FROM memories")
        self._conn.execute("DELETE FROM memory_links")
        self._conn.execute("DELETE FROM review_queue")

        applied = 0
        for event in ledger.events(end=end):
            self._apply(event)
            applied += 1
        return applied

    def _apply(self, event: Any) -> None:
        payload = event.payload
        etype = event.event_type

        if etype in ("MEMORY_CREATED", "MEMORY_ENRICHED"):
            m = payload.get("memory") or payload
            row = self._conn.execute(
                "SELECT memory_id FROM memories WHERE memory_id = ?", (m["memory_id"],)
            ).fetchone()
            if row is None:
                conf = m.get("confidence", {})
                self._conn.execute(
                    "INSERT INTO memories (memory_id, created_seq, last_seq, status, claim,"
                    " content_hash, provenance_class, source_id, importance,"
                    " source_confidence, extraction_confidence, inference_confidence,"
                    " current_confidence, valid_from, valid_to, retention_class, tags_json)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        m["memory_id"], event.seq, event.seq,
                        m.get("status", "ACTIVE"), m["claim"], m["content_hash"],
                        m["provenance_class"], m.get("source_id", ""),
                        int(m.get("importance", 0)),
                        float(conf.get("source", 0.0)),
                        float(conf.get("extraction", 0.0)),
                        float(conf.get("inference", 0.0)),
                        float(conf.get("current", 0.0)),
                        m.get("valid_from"), m.get("valid_to"),
                        m.get("retention_class", "STANDARD"),
                        canonical_json(list(m.get("tags", []))),
                    ),
                )
            else:
                self._conn.execute(
                    "UPDATE memories SET last_seq = ? WHERE memory_id = ?",
                    (event.seq, m["memory_id"]),
                )

        elif etype in _STATUS_EVENTS:
            memory_id = payload.get("memory_id")
            target = payload.get("status") or _STATUS_EVENTS[etype]
            # `_STATUS_EVENTS` maps MEMORY_STATUS_CHANGED to the sentinel "status" meaning
            # "read the target from the payload". Anything else is a literal target status.
            if memory_id and target and target != "status":
                self._conn.execute(
                    "UPDATE memories SET status = ?, last_seq = ? WHERE memory_id = ?",
                    (target, event.seq, memory_id),
                )

        elif etype == "LINK_CREATED":
            link = payload.get("link") or payload
            self._conn.execute(
                "INSERT OR IGNORE INTO memory_links (link_hash, from_id, to_id, kind,"
                " created_seq, weight) VALUES (?,?,?,?,?,?)",
                (
                    link["link_hash"], link["from_id"], link["to_id"], link["kind"],
                    event.seq, link.get("weight"),
                ),
            )

        elif etype in ("CONTRADICTION_DETECTED", "DUPLICATE_DETECTED"):
            # Participants live inside the queued review item; some callers also set a
            # top-level `memory_ids`. Accept either, and fall back to the item.
            ids = payload.get("memory_ids") or (
                payload.get("review_item", {}).get("memory_ids", [])
            )
            if etype == "CONTRADICTION_DETECTED":
                for mid in ids:
                    self._conn.execute(
                        "UPDATE memories SET status = 'CONTRADICTED', last_seq = ?"
                        " WHERE memory_id = ? AND status NOT IN ('RETRACTED','SUPERSEDED')",
                        (event.seq, mid),
                    )

        elif etype in ("CONTRADICTION_RESOLVED",):
            winner = payload.get("preferred")
            loser = payload.get("superseded")
            if winner:
                self._conn.execute(
                    "UPDATE memories SET status = 'ACTIVE', last_seq = ? WHERE memory_id = ?",
                    (event.seq, winner),
                )
            if loser:
                self._conn.execute(
                    "UPDATE memories SET status = 'SUPERSEDED', last_seq = ? WHERE memory_id = ?",
                    (event.seq, loser),
                )
            for mid in payload.get("keep_unresolved", []):
                self._conn.execute(
                    "UPDATE memories SET status = 'CONTRADICTED', last_seq = ?"
                    " WHERE memory_id = ?",
                    (event.seq, mid),
                )

        elif etype in ("CONSOLIDATION_CREATED", "MERGE_APPLIED"):
            canonical_id = payload.get("canonical_id") or payload.get("target_id")
            for src in payload.get("inputs", payload.get("memory_ids", [])):
                if src == canonical_id:
                    continue
                self._conn.execute(
                    "UPDATE memories SET status = 'SUPERSEDED', last_seq = ?"
                    " WHERE memory_id = ? AND status != 'RETRACTED'",
                    (event.seq, src),
                )

        # Review queue items are inserted by the governance layer, which owns the
        # decision lifecycle; replaying their events re-marks state.
        if etype in ("CONTRADICTION_DETECTED", "DUPLICATE_DETECTED"):
            item = payload.get("review_item")
            if item:
                self._conn.execute(
                    "INSERT OR IGNORE INTO review_queue (item_id, kind, memory_ids,"
                    " proposal_json, created_seq, state, decided_seq)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (
                        item["item_id"], item["kind"],
                        canonical_json(item.get("memory_ids", [])),
                        canonical_json(item.get("proposal", {})),
                        event.seq, "OPEN", None,
                    ),
                )

        elif event.event_type in ("APPROVAL_GRANTED", "APPROVAL_DENIED"):
            item_id = payload.get("review_item_id")
            state = "APPROVED" if event.event_type == "APPROVAL_GRANTED" else "REJECTED"
            if item_id and payload.get("decision", state) in ("APPROVED", "REJECTED", "DEFERRED"):
                self._conn.execute(
                    "UPDATE review_queue SET state = ?, decided_seq = ? WHERE item_id = ?",
                    (payload.get("decision", state), event.seq, item_id),
                )

    # -- reads -------------------------------------------------------------------------
    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        return dict(row) if row else None

    def open_review_items(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM review_queue WHERE state = 'OPEN' ORDER BY created_seq"
        ).fetchall()
        return [dict(r) for r in rows]

    def links_of(self, memory_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM memory_links WHERE from_id = ? OR to_id = ? ORDER BY created_seq",
            (memory_id, memory_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def dump_digest(self) -> str:
        """Canonical dump for determinism tests (row 4 / 22 of the acceptance matrix)."""
        from .canonical import digest

        state = {
            "memories": [
                dict(r) for r in self._conn.execute(
                    "SELECT * FROM memories ORDER BY memory_id"
                ).fetchall()
            ],
            "links": [
                dict(r) for r in self._conn.execute(
                    "SELECT * FROM memory_links ORDER BY link_hash"
                ).fetchall()
            ],
            "review": [
                dict(r) for r in self._conn.execute(
                    "SELECT * FROM review_queue ORDER BY item_id"
                ).fetchall()
            ],
        }
        return digest("memory-branch:projection:v1", state)
