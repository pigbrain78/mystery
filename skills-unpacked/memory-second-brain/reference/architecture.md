# Architecture

## The one rule

`memory_brain` is the ecosystem's **shared memory layer**. Every other system — agents,
control rooms, mobile cockpits, retrieval front-ends — is a **thin projection layer** over
it. Nothing else owns memory state. Nothing else hashes memory content.

## Module layout

```
memory_brain/
  __init__.py          # public surface: the 12 verbs, the enums, the errors
  canonical.py         # ADAPTER over the ONE authority. Sole hashing path.
  ledger.py            # append-only hash-chained event store (SQLite)
  models.py            # frozen enums + dataclasses (status, provenance, confidence)
  store.py             # derived projection tables; rebuilt from the ledger, never patched
  extract.py           # raw input -> candidate claims (+ extraction provenance)
  classify.py          # candidate -> memory class, provenance, importance, retention
  dedup.py             # 7-signal duplicate detection
  contradiction.py     # detection + relationship + ledger event + non-resolution
  consolidation.py     # versioned, reproducible merge with full input linkage
  retrieval.py         # hybrid candidate generation + rerank
  context.py           # Context Package assembly (the shared contract)
  governance.py        # review queue, approval gates, authority checks
  service.py           # the 12-verb interface
  selfcheck.py         # runnable acceptance probe
```

## Data flow

```
raw input
  -> extract        candidate claims + EXTRACTION provenance
  -> classify       memory class, provenance class, importance, retention
  -> dedup          7 signals -> EXACT (auto) | PROBABLE/POSSIBLE (review) | DISTINCT
  -> contradiction  relationship + event, never a resolution
  -> ledger.append  the authoritative fact
  -> store.project  derived projection, rebuildable
  -> [ governance ] human gate for every state-changing resolution
  -> retrieval      hybrid candidate generation
  -> context        Context Package, fully cited
```

Two flows are **separate by design**: ingest writes facts; governance changes state. A
retrieval path must never mutate anything.

## Storage split

- **Ledger (authoritative)** — append-only `events` table. The only source of truth.
- **Projection (derived)** — `memories`, `memory_links`, `review_queue`, `context_index`.
  May be dropped and rebuilt from the ledger at any time.

Keeping these separate is what makes SQLite → Postgres a backend swap rather than a
redesign: the ledger contract is narrow and portable; indexes, isolation and policy live
ledger-side and application-side.

## Invariants (assert these in code, not in comments)

| # | Invariant | Enforced by |
|---|---|---|
| 1 | No event is ever updated or deleted | `RAISE(ABORT)` triggers on `events` |
| 2 | `event_hash` recomputes to the stored value | `ledger.verify_chain()` |
| 3 | `prev_hash` of seq *n* equals `event_hash` of seq *n-1* | `ledger.verify_chain()` |
| 4 | Sequence numbers are contiguous from 1 | `ledger.verify_chain()` |
| 5 | Replay is deterministic and end-inclusive | `ledger.rebuild()` golden test |
| 6 | Derived state equals replayed state | rebuild comparison |
| 7 | No unresolved contradiction is hidden | review queue is exhaustive |
| 8 | Every memory traces to a provenance class | `models.Memory` construction |
| 9 | Every state-changing resolution has an approval event | `governance.py` |
| 10 | All hashing goes through `canonical.py` | import discipline + review |

## Integration contract

Downstream systems consume memory **only** through `service.py`. The surface is frozen at
12 verbs (see `reference/retrieval.md`). A new need is expressed as a composition of
existing verbs before a 13th is considered — convergence over fragmentation.

Two rules for consumers:

- **Cite or don't claim.** Anything derived from memory carries `memory_id` + `event_seq`.
- **Advisory is not authoritative.** An inference layer (shadow, twin, planner) may
  propose; only a human-gated ledger event disposes.

## Failure semantics

| Condition | Behavior |
|---|---|
| Canonical authority missing | `CanonicalAuthorityUnavailable`, hard fail, no fallback |
| Chain verification fails | `LedgerIntegrityError`, refuse all reads and writes |
| Non-finite float at ingest | deterministic failure id, reject record |
| Projection/ledger divergence | log divergence, rebuild projection, keep ledger |
| Contradiction detected | record + queue, never resolve |
| Approval missing on a state change | refuse, surface in review queue |

## Evolution rules

- Schema changes bump `SCHEMA_VERSION` and are additive only.
- New status / provenance / relationship members are versioned changes, not patches.
- A new memory subsystem is not built if an existing one can be extended — the ecosystem
  consolidates rather than fragmenting.
- Algorithm changes (dedup weights, consolidation merge) bump their own version stamp so
  old outputs stay explainable.
