# Engines — dedup, contradiction, consolidation

## 1. Dedup

Seven signals, evaluated **independently** and returned **separately**. Never collapse them
into one score for a decision — the breakdown is the audit trail, and the collapse is what
lets a system quietly merge two distinct facts.

| Signal | What it compares | Notes |
|---|---|---|
| `EXACT_HASH` | `content_hash` | byte-identical canonical content |
| `NORMALIZED_HASH` | hash of normalized claim text | case, whitespace, unicode NFKC, punctuation folded |
| `SEMANTIC_SIMILARITY` | embedding cosine of claim | threshold in config, versioned |
| `ENTITY_OVERLAP` | extracted entities | Jaccard over entity sets |
| `CLAIM_SIMILARITY` | predicate/argument structure | normalized triple comparison |
| `SOURCE_RELATIONSHIP` | source lineage | same source, derived source, or unrelated |
| `TEMPORAL_RELATIONSHIP` | `valid_from` / `valid_to` | overlapping vs disjoint windows |

Classification:

| Class | Condition | Action |
|---|---|---|
| `EXACT_DUPLICATE` | `EXACT_HASH` matches | **auto-merge** (append a merge event; original preserved) |
| `PROBABLE_DUPLICATE` | strong multi-signal agreement, not exact | review queue |
| `POSSIBLE_DUPLICATE` | weak or conflicting signals | review queue |
| `DISTINCT` | all signals below threshold | ingest normally |

Rules:

- Auto-merge is available **only** on `EXACT_DUPLICATE`. Everything else is a human call.
- A merge never deletes the absorbed memory. It appends a `duplicate_of` link and a
  `MERGE_APPLIED` event naming every input.
- Dedup thresholds live in one config object with a `dedup_algorithm_version` stamp, so a
  threshold change is visible in the ledger's history.

## 2. Contradiction

A contradiction is a **relationship plus an event**, never a resolution.

Detection is deliberately conservative — prefer a false positive that a human dismisses
over a false negative that silently corrupts the store. Candidate pairs come from:
same entities + opposing or mutually exclusive predicates, same subject with disjoint
values, or explicit negation markers.

On detection:

1. Append `CONTRADICTION_DETECTED` with both memory ids.
2. Insert a `contradicts` link (directed, kept forever).
3. Set both memories' status to `CONTRADICTED` **if and only if** neither has a stronger
   resolved provenance — otherwise a proposal is recorded and neither status moves.
4. Evaluate the four factors below and store them as the **proposal evidence**.
5. Enqueue a `CONTRADICTION` review item with state `OPEN`.
6. **Stop.** Nothing is resolved.

### The four evaluated factors

| Factor | Direction |
|---|---|
| **Recency** | newer `valid_from` / `created_seq` usually wins — but "usually" is the whole point |
| **Provenance strength** | `SOURCE` > `VERIFICATION` > `OBSERVATION` > `EXTRACTION` > `INTERPRETATION` > `INFERENCE` |
| **Confidence** | compare all four components, not just `current_confidence` |
| **Source authority** | a configured per-source authority rank |

### Outcomes

- One side `ACTIVE`, other `SUPERSEDED` — **as a proposal**, applied only on approval.
- Both `UNRESOLVED` — the honest answer when the factors conflict or are close. This is a
  first-class outcome, not a failure to decide.

A `CONTRADICTION` item is never auto-expired into a resolution. Expiry may only move it to
`EXPIRED`, which leaves both memories `CONTRADICTED` and visible.

## 3. Consolidation

Consolidation produces a canonical memory from several inputs. It is **reproducible** and
**versioned**.

Requirements:

- `consolidation_algorithm_version` is stamped on the output memory and the event.
- The canonical memory carries `derived_from` links to **every** input memory.
- Inputs are preserved and remain queryable in their prior state.
- Re-running consolidation on the same inputs with the same version yields the same
  `content_hash`. If it does not, that is a determinism bug, not a tuning problem.
- Consolidation is subject to the same human gate as any other state change: the merge is
  *proposed* by the engine and *applied* by an approval event.

### Merge policy

- The claim is the union of non-conflicting assertions, ordered canonically.
- Conflicting assertions become an embedded contradiction — consolidated or not, they
  stay visible.
- Confidence: `source_confidence` takes the **minimum** of inputs (a chain is as strong as
  its weakest source); `extraction_confidence` takes the minimum; `inference_confidence` is
  recomputed for the merged claim; `current_confidence` is recomputed from all three plus
  corroboration count.
- Importance is recomputed and stored separately — never inherited as the max, which would
  let a single loud source dominate a quiet consensus.
