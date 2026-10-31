# Retrieval, Context Packages, and the service surface

## Hybrid retrieval

Three generators, unioned then reranked. No single generator is trusted alone.

| Generator | Source | Strength |
|---|---|---|
| Lexical | FTS over normalized claim + tags | exact terms, names, ids |
| Vector | embedding similarity | paraphrase, conceptual match |
| Graph expansion | 1–2 hops over `memory_links` | corrects, supersedes, supports |

Rerank inputs, in order:

1. Query-term coverage.
2. Provenance class strength.
3. `current_confidence`.
4. Recency of `valid_from`, weighted by retention class.
5. Graph proximity to a directly-matched seed.

Reranking **never** drops a memory whose status is `CONTRADICTED` when the query touches
the contradicted assertion. Surfacing the conflict is the point.

## Context Package

The Context Package is the shared contract between memory and every consuming agent. It is
what makes "grounded context" checkable rather than aspirational.

```json
{
  "package_id": "ctx_...",
  "query": "the original query, verbatim",
  "generated_at": "RFC3339 UTC",
  "policy": { "max_items": 12, "min_confidence": 0.0, "include_contradicted": true },
  "items": [
    {
      "memory_id": "...",
      "event_seq": 42,
      "claim": "...",
      "status": "ACTIVE",
      "provenance_class": "SOURCE",
      "confidence": {
        "source": 0.9, "extraction": 0.8,
        "inference": 0.4, "current": 0.82
      },
      "valid_from": "RFC3339 UTC",
      "source_id": "...",
      "why_included": "lexical+vector match; graph hop from seed mem_7"
    }
  ],
  "conflicts": [
    { "a": "mem_...", "b": "mem_...", "state": "UNRESOLVED",
      "proposal": { "preferred": "a", "rationale": "recency + provenance" } }
  ],
  "coverage": { "matched": 7, "unresolved_conflicts": 1 },
  "truncated": false
}
```

Rules:

- **Every item cites `memory_id` and `event_seq`.** An item without both is a bug.
- **The confidence breakdown travels whole.** A consumer may not see a single collapsed
  number.
- **`conflicts` is non-optional.** If a relevant assertion is contested, the package says so
  even when the caller did not ask.
- `truncated: true` must be visible — a silently truncated package reads as "this is all
  there is", which is the most dangerous failure mode in retrieval.

## The 12 service verbs

Frozen interface. Clients call these and nothing else.

| Verb | Signature | Semantics |
|---|---|---|
| `remember` | `(content, *, provenance_class, source_id, confidence, importance=None, valid_from=None, tags=None, actor, created_at) -> memory_id` | ingest → extract → classify → dedup → contradiction → ledger append. Returns the memory id; queues review items as a side effect. |
| `recall` | `(query, *, limit=12, include_contradicted=True, actor, created_at) -> ContextPackage` | hybrid retrieval + Context Package assembly. |
| `search` | `(filters, *, limit=50, actor) -> list[Memory]` | structured filter (status, tag, provenance, source, time window). No package. |
| `verify` | `(memory_id) -> VerificationReport` | re-derives `content_hash`, walks the chain to the memory, reports status, links, conflicts, provenance. Does not mutate. |
| `explain` | `(memory_id) -> Explanation` | the full derivation: source, extraction, every supersession, every conflict, all four confidence components. |
| `link` | `(from_id, to_id, kind, *, weight=None, actor, created_at) -> link_hash` | appends a link event. Never rewrites an existing link. |
| `consolidate` | `(memory_ids, *, actor, created_at) -> proposal_id` | builds the proposal and queues it. **Does not apply.** |
| `supersede` | `(old_id, new_id, *, rationale, actor, created_at) -> proposal_id` | queues a supersession. Applies on approval. |
| `retract` | `(memory_id, *, rationale, actor, created_at) -> proposal_id` | queues an irreversible retraction. Applies on approval. |
| `resolve_contradiction` | `(review_item_id, decision, *, rationale, actor, created_at) -> decision_id` | the human gate. `decision` ∈ `PREFER_A`, `PREFER_B`, `KEEP_BOTH_UNRESOLVED`, `REJECT`. |
| `export` | `(*, since_seq=None, actor) -> bytes` | a verifiable snapshot: events + chain hashes + a manifest. |
| `import_snapshot` | `(payload, *, verify_chain=True, actor) -> count` | restores from an `export`, verifying the chain before accepting. |

### Interface rules

- `remember` is the **only** ingest path. No back doors.
- `consolidate`, `supersede`, `retract`, `resolve_contradiction` are the **only**
  state-changing paths, and all four require an approval event.
- `verify`, `explain`, `recall`, `search`, `export` are **read-only** and must be safe to
  call concurrently with writes.
- Every verb takes `actor` and an injected `created_at`. No verb reads the wall clock.
- `import_snapshot` refuses a chain that does not verify, and refuses to merge into a
  non-empty store unless the caller explicitly asks for it.
