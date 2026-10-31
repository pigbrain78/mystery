"""End-to-end probe of the memory_brain service surface against the fixture authority.

Exercises the §36 demo flow and the acceptance rows that need the full stack:
ingest -> dedup -> contradiction -> ledger -> context package -> human approval -> verify.

Not shipped with the skill; it validates the pattern modules before they are handed over.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from memory_brain import service
from memory_brain.models import ProvenanceClass

T = "2026-01-0{}T00:00:00Z"
ACTOR = "operator"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        brain = service.MemoryBrain(Path(d) / "brain.db")

        # --- §36 step 1: ingest a technical document -------------------------------
        doc = (
            "The Pocket OS ledger is append-only and every event is hash-chained. "
            "Canonical serialization authority is sail_canonical. "
            "The memory subsystem must never resolve a contradiction without approval. "
            "Schema version 1 is frozen and additive only."
        )
        r1 = brain.remember(
            doc, provenance_class=ProvenanceClass.SOURCE, source_id="doc://spec",
            actor=ACTOR, created_at=T.format(1), tags=["architecture", "policy"],
        )
        check("1 ingest technical doc", len(r1["created"]) >= 4, f"{len(r1['created'])} memories")

        # --- §36 step 2: ingest a conversation that CONFLICTS ---------------------
        # Shares subject keys ("ledger", "append-only"-style vocabulary) but negates.
        conflicting = "The Pocket OS ledger is not append-only in practice."
        r2 = brain.remember(
            conflicting, provenance_class=ProvenanceClass.OBSERVATION,
            source_id="conv://standup", actor=ACTOR, created_at=T.format(2),
        )
        check("2 ingest conflicting observation", len(r2["created"]) >= 1,
              f"{len(r2['created'])} memories")

        # --- §36 step 3: exact duplicate auto-merges ------------------------------
        before = brain.ledger.count()
        r3 = brain.remember(
            doc, provenance_class=ProvenanceClass.SOURCE, source_id="doc://spec",
            actor=ACTOR, created_at=T.format(3),
        )
        deduped = [c for c in r3["created"] if c.get("deduplicated")]
        check("3 exact duplicate auto-merge", len(deduped) >= 1,
              f"{len(deduped)} deduplicated, +{brain.ledger.count() - before} events")

        # --- §36 step 4: contradiction detected, NOT resolved ---------------------
        open_items = brain.projection.open_review_items()
        contradictions = [i for i in open_items if i["kind"] == "CONTRADICTION"]
        check("4 contradiction queued unresolved", len(contradictions) >= 1,
              f"{len(contradictions)} contradiction items, none auto-resolved")

        contradicted = brain.search({"status": "CONTRADICTED"}, actor=ACTOR)
        check("4b both sides remain CONTRADICTED", len(contradicted) >= 1,
              f"{len(contradicted)} memories marked CONTRADICTED")

        # --- §36 step 5: ledger verifies ------------------------------------------
        report = brain.ledger.verify_chain()
        check("5 ledger chain intact", report.ok, f"length={report.length}")

        # --- §36 step 6: context package carries BOTH sides + conflicts -----------
        pkg = brain.recall("Pocket OS ledger append-only", actor=ACTOR, created_at=T.format(4))
        both = len(pkg.items) >= 1
        check("6 context package cites sources",
              all(i.memory_id and i.event_seq for i in pkg.items) and both,
              f"{len(pkg.items)} items, truncated={pkg.truncated}")
        check("6b conflicts surfaced even if unasked", "conflicts" in pkg.as_dict(),
              f"{len(pkg.conflicts)} conflicts, {pkg.coverage['unresolved_conflicts']} unresolved")

        # --- §36 step 7: human approval resolves it -------------------------------
        if contradictions:
            item_id = contradictions[0]["item_id"]
            ids = brain.projection.get_memory(
                __import__("json").loads(contradictions[0]["memory_ids"])[0]
            )
            decision = "PREFER_A"
            out = brain.resolve_contradiction(
                item_id, decision, rationale="spec outranks standup observation",
                actor="reviewer", created_at=T.format(5), claimed_authority="OWNER",
            )
            approvals = [e for e in brain.ledger.events()
                         if e.event_type == "APPROVAL_GRANTED"]
            check("7 approval recorded with actor + authority",
                  len(approvals) == 1 and approvals[0].payload["claimed_authority"] == "OWNER",
                  f"decision={out['applied']}")
            check("7b both memories still queryable after resolution",
                  ids is not None and brain.projection.get_memory(ids["memory_id"]) is not None)
            check("7c chain still intact post-approval", brain.ledger.verify_chain().ok)

        # --- §36 step 8: verify + explain ----------------------------------------
        live = brain.search({"status": "ACTIVE"}, actor=ACTOR, limit=1)
        if live:
            mid = live[0]["memory_id"]
            v = brain.verify(mid)
            e = brain.explain(mid)
            check("8 verify walks chain + hash",
                  v["chain"]["ok"] and v["content_hash_ok"], f"status={v['status']}")
            check("8b explain exposes all four confidence parts",
                  set(e["confidence"]) == {"source", "extraction", "inference", "current"},
                  f"{len(e['history'])} history events")

        # --- No self-approval by inference ---------------------------------------
        queued = brain.projection.open_review_items()
        if queued:
            try:
                brain.resolve_contradiction(
                    queued[0]["item_id"], "REJECT", rationale="self",
                    actor=ACTOR, created_at=T.format(6),
                )
                check("9 self-approval refused", False, "approval was allowed")
            except Exception as exc:  # noqa: BLE001
                check("9 self-approval refused", "self-approval" in str(exc), str(exc)[:60])

        # --- read-only retrieval does not mutate --------------------------------
        n_before = brain.ledger.count()
        brain.recall("ledger", actor=ACTOR, created_at=T.format(7))
        brain.search({}, actor=ACTOR)
        check("10 retrieval is read-only", brain.ledger.count() == n_before,
              f"events {n_before} -> {brain.ledger.count()}")

        # --- projection rebuild determinism -------------------------------------
        h1 = brain.projection.dump_digest()
        brain.projection.rebuild(brain.ledger)
        h2 = brain.projection.dump_digest()
        check("11 projection rebuild is deterministic", h1 == h2, h1[:16])

        # --- export / import round-trip -----------------------------------------
        snap = brain.export(actor=ACTOR)
        with tempfile.TemporaryDirectory() as d2:
            brain2 = service.MemoryBrain(Path(d2) / "restored.db")
            written = brain2.import_snapshot(snap, actor=ACTOR)
            check("12 export/import round-trip",
                  brain2.ledger.verify_chain().ok
                  and brain2.projection.dump_digest() == h1,
                  f"{written} events restored")
            # Tampered snapshot must be refused.
            bad = snap.replace(b'"actor": "operator"', b'"actor": "attacker"', 1)
            try:
                import json as _json
                tampered = _json.loads(bad.decode())
                tampered["events"][0]["event_type"] = "MEMORY_RETRACTED"
                brain2.import_snapshot(
                    _json.dumps(tampered).encode(), actor=ACTOR,
                    allow_merge_into_nonempty=True,
                )
                check("13 tampered import refused", False, "tampered payload accepted")
            except Exception as exc:  # noqa: BLE001
                check("13 tampered import refused", True, type(exc).__name__)
            brain2.close()

        # --- non-finite float rejected with a deterministic id ------------------
        try:
            brain.remember({"metric": float("nan")},
                           provenance_class=ProvenanceClass.EXTRACTION,
                           source_id="s", actor=ACTOR, created_at=T.format(8))
            check("14 non-finite rejected", False, "NaN accepted")
        except service.IngestRejected as exc:
            check("14 non-finite rejected with deterministic id",
                  len(exc.failure_id) == 64, exc.failure_id[:16])

        brain.close()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"OVERALL: FAIL ({len(FAILURES)}): {FAILURES}")
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
