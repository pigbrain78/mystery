# Verification

Run this matrix before declaring any memory subsystem done. Every row is a test that must
**fail loudly** when the invariant is broken — a row that passes because it never ran is
worse than a missing test.

## Acceptance matrix

| # | Test | Setup | Expected |
|---|---|---|---|
| 1 | Chain integrity | append N events, `verify_chain()` | all N verify; contiguous seqs; `prev_hash` links correct |
| 2 | Tamper detection | mutate one `payload_json` row directly via SQL, then `verify_chain()` | `LedgerIntegrityError` raised; the corrupted seq is identified |
| 3 | Append-only enforcement | `UPDATE events SET ...` / `DELETE FROM events` | SQLite aborts the statement (trigger) |
| 4 | Deterministic replay | `rebuild()` twice from the same ledger | byte-identical derived state (compare a canonical dump hash) |
| 5 | End-inclusive replay | create 10 events, replay with `end=5` vs `end=10` | the `end=5` state matches the state as of seq 5, inclusive |
| 6 | History immutable | supersede memory M, then read M at the earlier seq | the earlier status is recoverable and unchanged |
| 7 | Exact dedup auto-merge | ingest the same canonical content twice | merged; a `MERGE_APPLIED` event names both; original preserved |
| 8 | Non-exact dedup queues | ingest near-duplicates | review item `PROBABLE_DUPLICATE` / `POSSIBLE_DUPLICATE`, `OPEN`; nothing merged |
| 9 | Contradiction visible | ingest two mutually exclusive claims | `CONTRADICTION_DETECTED` + `contradicts` link + review item; no silent resolution |
| 10 | Contradiction needs a human | attempt to auto-resolve | refused; both memories stay `CONTRADICTED` until an approval event exists |
| 11 | Approval is recorded | approve a queued item | `APPROVAL_GRANTED` event with `actor` and `claimed_authority` |
| 12 | Retraction terminal | retract a memory, then attempt any status change | refused; status stays `RETRACTED` |
| 13 | Provenance travels | `explain()` a memory | provenance class + all four confidence components present, none collapsed |
| 14 | Context Package cites | `recall()` | every item has `memory_id` + `event_seq`; `conflicts` key present even when empty |
| 15 | Truncation is honest | recall with a small `limit` over many matches | `truncated: true`, and `coverage.matched` > items returned |
| 16 | Read-only retrieval | run `recall`/`verify`/`explain` | ledger event count unchanged |
| 17 | Canonical authority binding | remove/rename the canonical module | `CanonicalAuthorityUnavailable`; **no fallback serializer used** |
| 18 | Non-finite float | ingest a record containing `NaN`/`Infinity` | rejected with a deterministic failure id; same input → same id |
| 19 | Export/import round-trip | `export()` then `import_snapshot()` into an empty store | chain verifies; replayed state matches the source |
| 20 | Corrupt import refused | tamper an exported payload, import | refused before any write |
| 21 | No wall-clock in hashing | grep the hashing path for `now()`/`utcnow()` | none inside the event-hash input |
| 22 | Projection rebuild | drop the projection tables, `rebuild()` | identical projection restored from the ledger |

## The §36 end-to-end demo

This is the whole system in one test, and it must pass as a single flow:

1. Ingest a **technical document** (long, structured) → several memories with `EXTRACTION`
   provenance.
2. Ingest a **conversation** transcript → memories with `OBSERVATION` provenance, at least
   one of which **conflicts** with the document.
3. Dedup fires on a repeated claim → `EXACT_DUPLICATE` auto-merge, originals preserved.
4. Contradiction detected → relationship + event + review item.
5. Ledger verified → chain intact, tamper test still detects a manual mutation.
6. `recall()` returns a **Context Package** containing both sides of the conflict, each
   fully cited, with `conflicts` populated and `state: UNRESOLVED`.
7. A simulated human approval resolves the contradiction → new events appended, both
   memories still queryable, the resolution traceable to an `actor`.
8. `verify()` on the resolved memory → walks provenance intact; `explain()` returns the
   full derivation.

If step 6 returns only one side, the system has silently resolved a contradiction and the
run fails regardless of every other test passing.

## Failure semantics

| Detection | Response |
|---|---|
| Chain verification fails | Refuse **all** reads and writes. Do not serve from a broken ledger. |
| Projection diverges from ledger | Rebuild the projection; never patch it. Log the divergence. |
| Canonical authority unavailable | Hard fail. No substitute serializer, no `json.dumps` fallback. |
| Open review item found during a state read | Surface it in the response. Never suppress. |
| Non-determinism in replay | Treat as a defect in the hashing or ordering path, not a flake. |

## Self-check

`python -m memory_brain.selfcheck` runs rows 1–6 and 17–18 against the configured
authority and prints a PASS/FAIL per row plus `OVERALL`. Rows 7–16 and 19–22 need the
full ingest/retrieval/governance stack and live in the test suite, not the self-check.
