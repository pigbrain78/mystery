"""The frozen service surface — the 12 verbs. Clients call these and NOTHING else.

Frozen at 12. A new need is expressed as a composition of existing verbs before a 13th
is considered; convergence over fragmentation.

Rules:
  * `remember` is the only ingest path. No back doors.
  * `consolidate` / `supersede` / `retract` / `resolve_contradiction` are the only
    state-changing paths, and all four require an approval event.
  * read verbs (`recall`, `search`, `verify`, `explain`, `export`) never mutate.
  * every verb takes `actor` and an INJECTED `created_at`. No verb reads the clock.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from . import classify as classify_mod
from . import contradiction as contradiction_mod
from . import dedup as dedup_mod
from . import extract as extract_mod
from . import governance as gov
from . import retrieval as retrieval_mod
from .canonical import (
    DOMAIN_CONTENT,
    CanonicalAuthorityUnavailable,
    canonical_json,
    digest,
)
from .consolidation import consolidate as consolidate_engine
from .context import build_package
from .ledger import Ledger, LedgerIntegrityError
from .models import (
    DuplicateClass,
    EventType,
    LinkKind,
    Memory,
    MemoryStatus,
    ProvenanceClass,
    RetentionClass,
    ReviewKind,
    SCHEMA_VERSION,
    Confirmation,
)
from .store import Projection

__all__ = ["MemoryBrain", "IngestRejected"]

#: Rejected inputs carry a deterministic id, never a wall-clock-tagged exception.
FAILURE_NON_FINITE = "NON_FINITE_FLOAT"
FAILURE_SCHEMA = "SCHEMA_VIOLATION"


class IngestRejected(ValueError):
    """Input refused at the boundary. Carries a deterministic failure id."""

    def __init__(self, kind: str, reason: str, failure_id: str) -> None:
        super().__init__(f"{kind}: {reason}")
        self.kind = kind
        self.reason = reason
        self.failure_id = failure_id


def _failure_id(kind: str, reason: str, safe_projection: Any) -> str:
    return digest(
        "memory-branch:failure:v1",
        {"kind": kind, "reason": reason, "input_digest": digest(DOMAIN_CONTENT, safe_projection)},
    )


def _reject_non_finite(obj: Any) -> None:
    """NaN / Infinity destroy canonicalization. Reject at the boundary, deterministically."""
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise IngestRejected(
                FAILURE_NON_FINITE,
                "non-finite float in input",
                _failure_id(FAILURE_NON_FINITE, "non-finite float", str(obj)),
            )
    elif isinstance(obj, dict):
        for v in obj.values():
            _reject_non_finite(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _reject_non_finite(v)


class MemoryBrain:
    """The shared memory layer. One instance per store."""

    def __init__(self, db_path: str | Path = "memory_brain.db") -> None:
        self.ledger = Ledger(db_path)
        self.projection = Projection(self.ledger._conn)
        self._conn: sqlite3.Connection = self.ledger._conn

    # -- lifecycle ---------------------------------------------------------------------
    def close(self) -> None:
        self.ledger.close()

    def __enter__(self) -> "MemoryBrain":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- 1. remember -------------------------------------------------------------------
    def remember(
        self,
        content: str | dict[str, Any],
        *,
        provenance_class: ProvenanceClass | str,
        source_id: str,
        actor: str,
        created_at: str,
        confidence: dict[str, float] | None = None,
        importance: int | None = None,
        valid_from: str | None = None,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Ingest -> extract -> classify -> dedup -> contradiction -> ledger append.

        Returns the created memory ids and any review items raised as a side effect.
        """
        _reject_non_finite(content)
        prov = (
            provenance_class
            if isinstance(provenance_class, ProvenanceClass)
            else ProvenanceClass(provenance_class)
        )

        if isinstance(content, str):
            candidates = extract_mod.extract(
                content, source_id=source_id, provenance_class=prov, tags=tags or ()
            )
        else:
            payload = {**content}
            payload.setdefault("title", title or "")
            claim = canonical_json(payload)
            candidates = [
                extract_mod.Candidate(
                    claim=claim,
                    provenance_class=prov,
                    source_id=source_id,
                    confidence=confidence or {
                        "source": 0.9, "extraction": 1.0, "inference": 0.0, "current": 0.9,
                    },
                    tags=tuple(tags or ()),
                    ordinal=0,
                )
            ]

        created: list[dict[str, Any]] = []
        reviews: list[str] = []

        for cand in candidates:
            cls = classify_mod.classify(cand)
            if confidence:
                merged = {**cand.confidence, **confidence}
                cand = extract_mod.Candidate(
                    claim=cand.claim, provenance_class=cand.provenance_class,
                    source_id=cand.source_id, confidence=merged,
                    entities=cand.entities, tags=cand.tags, ordinal=cand.ordinal,
                )

            content_hash = digest(
                DOMAIN_CONTENT,
                {"claim": cand.claim, "provenance": cand.provenance_class.value},
            )

            duplicate_of = self._find_exact_duplicate(content_hash)
            if duplicate_of:
                gov.auto_merge_exact(
                    self.ledger, target_id=duplicate_of, memory_ids=[duplicate_of],
                    actor=actor, created_at=created_at,
                )
                created.append({"memory_id": duplicate_of, "deduplicated": True})
                continue

            status = MemoryStatus.QUARANTINED if cls.quarantine else (
                MemoryStatus.UNVERIFIED
                if cand.confidence["current"] < classify_mod.Policy().min_active_confidence
                else MemoryStatus.ACTIVE
            )

            memory_id = "mem_" + uuid.uuid4().hex[:16]
            memory = {
                "memory_id": memory_id,
                "status": status.value,
                "claim": cand.claim,
                "content_hash": content_hash,
                "provenance_class": cand.provenance_class.value,
                "source_id": cand.source_id,
                "importance": importance if importance is not None else cls.importance,
                "confidence": cand.confidence,
                "valid_from": valid_from,
                "valid_to": None,
                "retention_class": cls.retention_class.value,
                "tags": list(cand.tags),
                "classification": cls.rationale,
                "schema_version": SCHEMA_VERSION,
            }

            event = self.ledger.append(
                EventType.MEMORY_CREATED.value,
                {"memory": memory},
                actor=actor,
                created_at=created_at,
            )

            created.append({"memory_id": memory_id, "seq": event.seq, "status": status.value})

        # The projection must know about the new memories BEFORE contradiction detection,
        # which reads both participants from it. Rebuilding first is what makes the check
        # see the memory it was just asked to reason about.
        self.projection.rebuild(self.ledger)

        newly_created = [
            c["memory_id"] for c in created if not c.get("deduplicated") and "memory_id" in c
        ]
        for memory_id in newly_created:
            # Dedup runs at ingest, as the architecture's data flow states. Without this
            # call a non-exact duplicate is silently ingested as a new memory and no
            # human ever sees the decision.
            reviews.extend(
                self._check_near_duplicates_for(memory_id, actor=actor, created_at=created_at)
            )
            reviews.extend(
                self._check_contradictions_for(memory_id, actor=actor, created_at=created_at)
            )

        self.projection.rebuild(self.ledger)
        return {"created": created, "review_items": reviews}

    # -- 2. recall ---------------------------------------------------------------------
    def recall(
        self,
        query: str,
        *,
        actor: str,
        created_at: str,
        limit: int = 12,
        include_contradicted: bool = True,
        min_confidence: float = 0.0,
    ):
        """Hybrid retrieval + Context Package assembly. Read-only."""
        self.ledger.require_intact()
        candidates = retrieval_mod.retrieve(self._conn, query)
        ranked = retrieval_mod.rerank(candidates, terms=retrieval_mod._terms(query))
        return build_package(
            self._conn, query, ranked, generated_at=created_at,
            limit=limit, min_confidence=min_confidence,
            include_contradicted=include_contradicted,
        )

    # -- 3. search ---------------------------------------------------------------------
    def search(
        self,
        filters: dict[str, Any] | None = None,
        *,
        actor: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Structured filter (status, tag, provenance, source, time window). No package."""
        filters = filters or {}
        clauses, params = [], []
        if filters.get("status"):
            clauses.append("status = ?")
            params.append(filters["status"])
        if filters.get("provenance_class"):
            clauses.append("provenance_class = ?")
            params.append(filters["provenance_class"])
        if filters.get("source_id"):
            clauses.append("source_id = ?")
            params.append(filters["source_id"])
        if filters.get("tag"):
            clauses.append("tags_json LIKE ?")
            params.append(f"%{filters['tag']}%")
        if filters.get("since_seq"):
            clauses.append("created_seq >= ?")
            params.append(int(filters["since_seq"]))
        sql = "SELECT * FROM memories"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_seq DESC LIMIT ?"
        params.append(int(limit))
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    # -- 4. verify ---------------------------------------------------------------------
    def verify(self, memory_id: str) -> dict[str, Any]:
        """Re-derive the hash, walk the chain, report status/links/conflicts. No mutation."""
        report = self.ledger.verify_chain()
        row = self.projection.get_memory(memory_id)
        if row is None:
            return {"memory_id": memory_id, "found": False, "chain": report.__dict__}

        recomputed = digest(
            DOMAIN_CONTENT,
            {"claim": row["claim"], "provenance": row["provenance_class"]},
        )
        return {
            "memory_id": memory_id,
            "found": True,
            "chain": {"ok": report.ok, "length": report.length, "head": report.head_hash},
            "content_hash_ok": recomputed == row["content_hash"],
            "status": row["status"],
            "provenance_class": row["provenance_class"],
            "confidence": {
                "source": row["source_confidence"],
                "extraction": row["extraction_confidence"],
                "inference": row["inference_confidence"],
                "current": row["current_confidence"],
            },
            "links": self.projection.links_of(memory_id),
            "conflicts": self._conflicts(memory_id),
        }

    # -- 5. explain --------------------------------------------------------------------
    def explain(self, memory_id: str) -> dict[str, Any]:
        """The full derivation: source, every supersession, every conflict, all four
        confidence components."""
        row = self.projection.get_memory(memory_id)
        if row is None:
            return {"memory_id": memory_id, "found": False}

        history = [
            {
                "seq": e.seq,
                "type": e.event_type,
                "actor": e.actor,
                "created_at": e.created_at,
                "payload": e.payload,
            }
            for e in self.ledger.events()
            if (e.payload.get("memory_id") == memory_id
                or (e.payload.get("memory") or {}).get("memory_id") == memory_id
                or memory_id in (e.payload.get("inputs") or [])
                or memory_id in (e.payload.get("memory_ids") or []))
        ]
        approvals = [
            h for h in history
            if h["type"] in (EventType.APPROVAL_GRANTED.value, EventType.APPROVAL_DENIED.value)
        ]
        return {
            "memory_id": memory_id,
            "found": True,
            "claim": row["claim"],
            "status": row["status"],
            "provenance_class": row["provenance_class"],
            "source_id": row["source_id"],
            "confidence": {
                "source": row["source_confidence"],
                "extraction": row["extraction_confidence"],
                "inference": row["inference_confidence"],
                "current": row["current_confidence"],
            },
            "history": history,
            "approvals": approvals,
            "links": self.projection.links_of(memory_id),
            "conflicts": self._conflicts(memory_id),
        }

    # -- 6. link -----------------------------------------------------------------------
    def link(
        self,
        from_id: str,
        to_id: str,
        kind: LinkKind | str,
        *,
        actor: str,
        created_at: str,
        weight: float | None = None,
    ) -> str:
        """Append a link event. An existing link is never rewritten."""
        kind_value = kind.value if isinstance(kind, LinkKind) else str(kind)
        link = {
            "link_hash": digest(
                DOMAIN_CONTENT,
                {"from": from_id, "to": to_id, "kind": kind_value, "weight": weight},
            ),
            "from_id": from_id,
            "to_id": to_id,
            "kind": kind_value,
            "weight": weight,
        }
        event = self.ledger.append(
            EventType.LINK_CREATED.value, {"link": link}, actor=actor, created_at=created_at
        )
        self.projection.rebuild(self.ledger)
        return link["link_hash"]

    # -- 7. consolidate ----------------------------------------------------------------
    def consolidate(
        self,
        memory_ids: list[str],
        *,
        actor: str,
        created_at: str,
    ) -> dict[str, Any]:
        """Build the proposal and queue it. DOES NOT APPLY."""
        memories = [self._as_memory(m) for m in memory_ids]
        result = consolidate_engine(memories)
        ref = gov.queue_item(
            self.ledger,
            kind=ReviewKind.LOW_CONFIDENCE,
            memory_ids=memory_ids,
            proposal={**result.proposal, "kind": "consolidation", "proposed_by": actor},
            actor=actor,
            created_at=created_at,
        )
        self.projection.rebuild(self.ledger)
        return {
            "proposal_id": ref.item_id,
            "canonical_id": result.canonical_id,
            "claim": result.claim,
            "confidence": result.confidence,
            "requires_approval": True,
        }

    # -- 8. supersede ------------------------------------------------------------------
    def supersede(
        self,
        old_id: str,
        new_id: str,
        *,
        rationale: str,
        actor: str,
        created_at: str,
    ) -> str:
        """Queue a supersession. Applies on approval."""
        ref = gov.queue_item(
            self.ledger,
            kind=ReviewKind.CONTRADICTION,
            memory_ids=[old_id, new_id],
            proposal={
                "kind": "supersede", "old_id": old_id, "new_id": new_id,
                "rationale": rationale, "proposed_by": actor,
            },
            actor=actor,
            created_at=created_at,
        )
        self.projection.rebuild(self.ledger)
        return ref.item_id

    # -- 9. retract --------------------------------------------------------------------
    def retract(
        self,
        memory_id: str,
        *,
        rationale: str,
        actor: str,
        created_at: str,
    ) -> str:
        """Queue an irreversible retraction. Applies on approval."""
        ref = gov.queue_item(
            self.ledger,
            kind=ReviewKind.QUARANTINE_RELEASE,
            memory_ids=[memory_id],
            proposal={
                "kind": "retract", "memory_id": memory_id,
                "rationale": rationale, "proposed_by": actor,
            },
            actor=actor,
            created_at=created_at,
        )
        self.projection.rebuild(self.ledger)
        return ref.item_id

    # -- 10. resolve_contradiction -----------------------------------------------------
    def resolve_contradiction(
        self,
        review_item_id: str,
        decision: str,
        *,
        rationale: str,
        actor: str,
        created_at: str,
        claimed_authority: str = "NONE",
    ) -> dict[str, Any]:
        """The human gate. decision in PREFER_A | PREFER_B | KEEP_BOTH_UNRESOLVED | REJECT."""
        item = gov._authority_block(self.ledger, review_item_id)
        ids = item.get("memory_ids", [])
        a = ids[0] if ids else None
        b = ids[1] if len(ids) > 1 else None

        if decision == "REJECT":
            gov.reject(
                self.ledger, review_item_id=review_item_id, actor=actor,
                created_at=created_at, rationale=rationale,
            )
            self.projection.rebuild(self.ledger)
            return {"review_item_id": review_item_id, "applied": "REJECT"}

        if decision == "KEEP_BOTH_UNRESOLVED":
            gov.approve(
                self.ledger, review_item_id=review_item_id, actor=actor,
                created_at=created_at, claimed_authority=claimed_authority, rationale=rationale,
                resulting_events=[{
                    "kind": "contradiction_resolution", "keep_unresolved": [a, b],
                    "rationale": rationale,
                }],
            )
            self.projection.rebuild(self.ledger)
            return {"review_item_id": review_item_id, "applied": "KEEP_BOTH_UNRESOLVED"}

        if decision not in ("PREFER_A", "PREFER_B"):
            raise ValueError(f"unknown decision: {decision!r}")

        preferred, superseded = (a, b) if decision == "PREFER_A" else (b, a)
        gov.approve(
            self.ledger, review_item_id=review_item_id, actor=actor,
            created_at=created_at, claimed_authority=claimed_authority, rationale=rationale,
            resulting_events=[{
                "kind": "contradiction_resolution",
                "preferred": preferred, "superseded": superseded,
                "rationale": rationale,
            }],
        )
        self.projection.rebuild(self.ledger)
        return {"review_item_id": review_item_id, "applied": decision, "preferred": preferred}

    # -- 11. export --------------------------------------------------------------------
    def export(self, *, since_seq: int | None = None, actor: str) -> bytes:
        """A verifiable snapshot: events + chain hashes + a manifest."""
        events = [
            {
                "seq": e.seq, "event_id": e.event_id, "event_type": e.event_type,
                "prev_hash": e.prev_hash, "content_hash": e.content_hash,
                "payload": e.payload, "actor": e.actor, "created_at": e.created_at,
                "schema_version": e.schema_version, "event_hash": e.event_hash,
            }
            for e in self.ledger.events(start=since_seq or 1)
        ]
        head = self.ledger.head()
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "count": len(events),
            "head_hash": head.event_hash if head else None,
            "exported_by": actor,
            "genesis_expected": events[0]["prev_hash"] if events else None,
        }
        payload = {"manifest": manifest, "events": events}
        return canonical_json(payload).encode("utf-8")

    # -- 12. import_snapshot ------------------------------------------------------------
    def import_snapshot(
        self,
        payload: bytes,
        *,
        verify_chain: bool = True,
        actor: str,
        allow_merge_into_nonempty: bool = False,
    ) -> int:
        """Restore from an export. Refuses a bad chain BEFORE any write, and refuses to
        merge into a non-empty store unless the caller explicitly asks."""
        data = json.loads(payload.decode("utf-8"))
        events = data.get("events", [])

        if self.ledger.count() and not allow_merge_into_nonempty:
            raise LedgerIntegrityError(
                "refusing to import into a non-empty store without allow_merge_into_nonempty"
            )

        if verify_chain:
            from .canonical import DOMAIN_EVENT as _DE
            expected_prev = events[0]["prev_hash"] if events else "0" * 64
            for i, e in enumerate(events):
                if e["prev_hash"] != expected_prev:
                    raise LedgerIntegrityError(f"import chain broken at position {i}")
                header = {
                    "v": e["schema_version"], "seq": e["seq"], "event_id": e["event_id"],
                    "event_type": e["event_type"], "prev_hash": e["prev_hash"],
                    "content_hash": e["content_hash"], "actor": e["actor"],
                    "created_at": e["created_at"],
                }
                if digest(_DE, header) != e["event_hash"]:
                    raise LedgerIntegrityError(f"event_hash mismatch at position {i}")
                if digest(DOMAIN_CONTENT, e["payload"]) != e["content_hash"]:
                    raise LedgerIntegrityError(f"content_hash mismatch at position {i}")
                expected_prev = e["event_hash"]

        written = 0
        for e in events:
            self.ledger.append(
                e["event_type"], e["payload"], actor=e["actor"],
                created_at=e["created_at"], event_id=e["event_id"],
            )
            written += 1

        self.projection.rebuild(self.ledger)
        return written

    # -- internals ---------------------------------------------------------------------
    def _find_exact_duplicate(self, content_hash: str) -> str | None:
        row = self._conn.execute(
            "SELECT memory_id FROM memories WHERE content_hash = ? LIMIT 1", (content_hash,)
        ).fetchone()
        return row["memory_id"] if row else None

    def _check_near_duplicates_for(
        self, memory_id: str, *, actor: str, created_at: str, window: int = 200
    ) -> list[str]:
        """Queue probable/possible duplicates for human review. Never auto-merges.

        Exact duplicates are auto-merged upstream (information-preserving, because the
        content is byte-identical). Everything below exact is a judgement call and routes
        here. The new memory is NOT dropped or altered — suppressing it would be data loss
        without an approval event, which governance forbids. The record stays; the
        decision is surfaced.

        Comparison is bounded to the most recent `window` live memories. A full pairwise
        scan is O(n) per ingest and belongs behind an index (or an embedding store) at
        scale — see reference/engines.md.
        """
        new = self._as_memory(memory_id)
        if new is None:
            return []

        cfg = dedup_mod.DedupConfig()
        rows = self._conn.execute(
            "SELECT memory_id, claim, content_hash, source_id, valid_from FROM memories"
            " WHERE memory_id != ? AND status != 'RETRACTED'"
            " ORDER BY created_seq DESC LIMIT ?",
            (memory_id, int(window)),
        ).fetchall()

        raised: list[str] = []
        for row in rows:
            if row["content_hash"] == new.content_hash:
                continue  # exact duplicates are handled before this point
            signals = dedup_mod.evaluate(
                claim_a=new.claim,
                claim_b=row["claim"],
                content_hash_a=new.content_hash,
                content_hash_b=row["content_hash"],
                source_id_a=new.source_id,
                source_id_b=row["source_id"],
                valid_from_a=new.valid_from,
                valid_from_b=row["valid_from"],
            )
            klass = dedup_mod.classify(signals, cfg)
            if klass not in (
                DuplicateClass.PROBABLE_DUPLICATE,
                DuplicateClass.POSSIBLE_DUPLICATE,
            ):
                continue

            kind = (
                ReviewKind.PROBABLE_DUPLICATE
                if klass == DuplicateClass.PROBABLE_DUPLICATE
                else ReviewKind.POSSIBLE_DUPLICATE
            )
            ref = gov.queue_item(
                self.ledger,
                kind=kind,
                memory_ids=[new.memory_id, row["memory_id"]],
                proposal={
                    "kind": "duplicate",
                    "classification": klass.value,
                    "signals": signals.as_dict(),
                    "requires_approval": True,
                    "proposed_by": actor,
                },
                actor=actor,
                created_at=created_at,
            )
            raised.append(ref.item_id)
        return raised

    def _check_contradictions_for(
        self, memory_id: str, *, actor: str, created_at: str
    ) -> list[str]:
        """Detect contradictions for one memory, record them, queue them, and STOP.

        Both participants are read from the projection, so this must run AFTER the
        projection has been rebuilt with the new memory. It never resolves anything.
        """
        new = self._as_memory(memory_id)
        if new is None:
            return []

        rows = self._conn.execute(
            "SELECT memory_id FROM memories WHERE memory_id != ?"
            " AND status NOT IN ('RETRACTED','SUPERSEDED')"
            " ORDER BY created_seq",
            (new.memory_id,),
        ).fetchall()

        raised: list[str] = []
        for row in rows:
            other = self._as_memory(row["memory_id"])
            if other is None:
                continue
            found = contradiction_mod.detect(new, other)
            if not found:
                continue

            factors = contradiction_mod.evaluate_factors(new, other)
            proposal = contradiction_mod.propose(new, other, factors)

            ref = gov.queue_item(
                self.ledger,
                kind=ReviewKind.CONTRADICTION,
                memory_ids=[found.a_id, found.b_id],
                proposal={**proposal, **found.as_dict(), "proposed_by": actor},
                actor=actor,
                created_at=created_at,
            )

            # The relationship is recorded, not just the queue entry: a directed
            # `contradicts` link is appended and kept forever. That link is what makes the
            # conflict retrievable later, and what a reader follows to see the two sides.
            link = {
                "link_hash": digest(
                    DOMAIN_CONTENT,
                    {"from": found.a_id, "to": found.b_id,
                     "kind": LinkKind.CONTRADICTS.value},
                ),
                "from_id": found.a_id,
                "to_id": found.b_id,
                "kind": LinkKind.CONTRADICTS.value,
                "weight": None,
            }
            self.ledger.append(
                EventType.LINK_CREATED.value, {"link": link},
                actor=actor, created_at=created_at,
            )

            raised.append(ref.item_id)
        return raised

    def _as_memory(self, memory_id: str) -> Memory | None:
        row = self.projection.get_memory(memory_id)
        if row is None:
            return None
        return Memory(
            memory_id=row["memory_id"],
            created_seq=row["created_seq"],
            status=MemoryStatus(row["status"]),
            claim=row["claim"],
            content_hash=row["content_hash"],
            provenance_class=ProvenanceClass(row["provenance_class"]),
            source_id=row["source_id"],
            confidence=Confirmation(
                source=row["source_confidence"],
                extraction=row["extraction_confidence"],
                inference=row["inference_confidence"],
                current=row["current_confidence"],
            ),
            importance=row["importance"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            retention_class=RetentionClass(row["retention_class"]),
            tags=tuple(json.loads(row["tags_json"])),
        )

    def _conflicts(self, memory_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT from_id, to_id FROM memory_links WHERE kind = 'contradicts'"
            " AND (from_id = ? OR to_id = ?)",
            (memory_id, memory_id),
        ).fetchall()
        return [{"a": r["from_id"], "b": r["to_id"]} for r in rows]
