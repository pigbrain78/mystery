# Schemas

All JSON that is hashed is serialized by the ecosystem's canonical authority
(RFC 8785 JCS). Field order is therefore irrelevant to the digest; **field presence is
not** — an absent field and a `null` field hash differently. Treat the schemas below as
closed.

## Domain tags

Every digest is domain-separated so a hash from one context can never be replayed in
another. Tags are versioned strings; changing a tag invalidates every prior hash and is a
migration, not an edit.

**Two tag sets exist in this ecosystem, and picking the wrong one produces hashes nothing
else can reproduce.** See `reference/canonical-binding.md` for the recorded real binding.

Authoritative SAIL tags — use these when building against the existing memory subsystem or
any existing ledger (the converged `memory_brain` in the SAIL archive already hashes under
them, so digests stay comparable with the runtime, ledger and council digests):

| Purpose | Authoritative tag | Constant |
|---|---|---|
| memory content | `memory.content` | `DOMAIN_CONTENT_SAIL` |
| ledger event | `memory.ledger.event` | `DOMAIN_EVENT_SAIL` |
| provenance | `memory.provenance` | `DOMAIN_PROVENANCE_SAIL` |
| context package | `memory.context` | `DOMAIN_CONTEXT_SAIL` |
| snapshot | `memory.snapshot` | `DOMAIN_SNAPSHOT_SAIL` |
| graph / links | `memory.graph` | `DOMAIN_GRAPH_SAIL` |
| vector index | `memory.vectorindex` | `DOMAIN_VECTOR_SAIL` |
| failure id | `failure` | `DOMAIN_FAILURE_SAIL` |

This package's defaults — use only for a fresh standalone package with no existing ledger:

| Constant | Value |
|---|---|
| `DOMAIN_CONTENT` | `memory-branch:content:v1` |
| `DOMAIN_EVENT` | `memory-branch:ledger-event:v1` |
| `DOMAIN_LINK` | `memory-branch:link:v1` |
| `DOMAIN_APPROVAL` | `memory-branch:approval:v1` |
| `DOMAIN_FAILURE` | `memory-branch:failure:v1` |

### Genesis

Two conventions exist. The authoritative SAIL ledger uses `None` for the first event's
`previous_event_hash`. This package uses `GENESIS_HASH` — 64 ASCII zeros — as the
`prev_hash` of sequence 1. Both are internally consistent; **do not mix them inside one
ledger**, and keep the chain field name consistent (`prev_hash` here,
`previous_event_hash` in the SAIL ledger).

## Ledger event

Table `events`. **Append-only.**

| Column | Type | Notes |
|---|---|---|
| `seq` | INTEGER PK | contiguous from 1 |
| `event_id` | TEXT UNIQUE | uuid4 unless the caller supplies a deterministic id |
| `event_type` | TEXT | closed enum, below |
| `prev_hash` | TEXT | `event_hash` of `seq-1`, or `GENESIS_HASH` |
| `content_hash` | TEXT | `digest(DOMAIN_CONTENT, payload)` |
| `payload_json` | TEXT | canonical JSON of the payload |
| `actor` | TEXT | who or what caused the event |
| `created_at` | TEXT | RFC3339 UTC, **injected by the caller** |
| `schema_version` | INTEGER | `1` |
| `event_hash` | TEXT UNIQUE | see below |

```python
header = {
    "v": schema_version,          # 1
    "seq": seq,
    "event_id": event_id,
    "event_type": event_type,
    "prev_hash": prev_hash,
    "content_hash": content_hash,
    "actor": actor,
    "created_at": created_at,
}
event_hash = digest(DOMAIN_EVENT, header)
```

Note what is **excluded** from the header: `payload_json` itself. The payload enters the
chain only through `content_hash`, which keeps the hash input small and stable while still
binding the content.

### Event types

`MEMORY_CREATED`, `MEMORY_ENRICHED`, `MEMORY_SUPERSEDED`, `MEMORY_CORRECTED`,
`MEMORY_STATUS_CHANGED`, `MEMORY_RETRACTED`, `MEMORY_ARCHIVED`, `MEMORY_QUARANTINED`,
`LINK_CREATED`, `CONTRADICTION_DETECTED`, `CONTRADICTION_RESOLVED`, `DUPLICATE_DETECTED`,
`MERGE_APPLIED`, `CONSOLIDATION_CREATED`, `APPROVAL_GRANTED`, `APPROVAL_DENIED`,
`RETRIEVAL_SERVED`, `INGEST_REJECTED`.

`RETRIEVAL_SERVED` is optional and off by default — logging reads is a policy decision, not
a requirement, and it costs chain length on hot paths.

## Memory record (derived projection)

Table `memories`. Rebuilt from the ledger; **never patched in place.**

| Column | Notes |
|---|---|
| `memory_id` | stable id, distinct from `event_id` |
| `created_seq` | ledger sequence that created it |
| `status` | see status enum |
| `claim` | the assertion, normalized |
| `content_hash` | `digest(DOMAIN_CONTENT, claim + provenance)` |
| `provenance_class` | see provenance enum |
| `source_id` | pointer to the origin (doc id, URL, conversation id) |
| `importance` | integer 0–100, **independent of provenance** |
| `source_confidence` | 0.0–1.0 |
| `extraction_confidence` | 0.0–1.0 |
| `inference_confidence` | 0.0–1.0 |
| `current_confidence` | 0.0–1.0, the only one that moves over time |
| `valid_from` / `valid_to` | RFC3339 UTC or NULL |
| `retention_class` | see retention enum |
| `tags` | canonical JSON array |

### Status enum

`ACTIVE`, `SUPERSEDED`, `CONTRADICTED`, `RETRACTED`, `ARCHIVED`, `QUARANTINED`,
`UNVERIFIED`.

Historical records stay queryable forever. A status change appends an event; the previous
row state remains reconstructible by replaying with an `end` bound.

### Provenance class

`SOURCE`, `OBSERVATION`, `EXTRACTION`, `INFERENCE`, `INTERPRETATION`, `VERIFICATION`.

Rough ordering for conflict evaluation (strongest first): `SOURCE` > `VERIFICATION` >
`OBSERVATION` > `EXTRACTION` > `INTERPRETATION` > `INFERENCE`. A `VERIFICATION` of an
`INFERENCE` does not promote the inference's origin — both stay recorded.

### Retention class

`PERMANENT`, `LONG`, `STANDARD`, `SHORT`, `EPHEMERAL`. Retention governs archival, never
deletion — nothing leaves the ledger.

## Links (graph)

Table `memory_links`. `digest(DOMAIN_LINK, link)` gives `link_hash`.

| Field | Notes |
|---|---|
| `from_id` / `to_id` | memory ids |
| `kind` | `corrected_by`, `superseded_by`, `derived_from`, `contradicts`, `supports`, `consolidated_from`, `duplicate_of` |
| `created_seq` | event that created the link |
| `weight` | 0.0–1.0 where meaningful |

Links are directed and never rewritten. A superseded link stays in the graph — that is how
"memory evolution is graph-linked" is auditable.

## Review queue

Table `review_queue`. Backs every human gate.

| Field | Notes |
|---|---|
| `item_id` | id |
| `kind` | `PROBABLE_DUPLICATE`, `POSSIBLE_DUPLICATE`, `CONTRADICTION`, `LOW_CONFIDENCE`, `QUARANTINE_RELEASE` |
| `memory_ids` | JSON array of participants |
| `proposal_json` | the recommended resolution, with its evidence |
| `created_seq` | event that queued it |
| `state` | `OPEN`, `APPROVED`, `REJECTED`, `DEFERRED`, `EXPIRED` |
| `decided_seq` | the approval event, or NULL |

An `OPEN` item is never silently dropped. Deferral is explicit and audited.

## Failure id

Non-finite floats, unparseable input, and oversized payloads are rejected with a
deterministic failure id rather than an exception carrying a wall-clock timestamp:

```python
failure_id = digest(DOMAIN_FAILURE, {
    "kind": kind,               # "NON_FINITE_FLOAT" | "SCHEMA_VIOLATION" | ...
    "input_digest": digest(DOMAIN_CONTENT, safe_projection(input)),
    "reason": reason,
})
```

Same bad input → same failure id, every run, on every host.
