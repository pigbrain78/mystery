---
name: memory-second-brain
description: Build and extend a provenance-aware, cryptographically auditable
  memory subsystem — append-only hash-chained ledger, dedup, contradiction
  detection, consolidation, hybrid retrieval, and human-gated re
triggers:
  - build a memory second brain
  - add a memory subsystem
  - provenance-aware memory layer
  - contradiction detection over memory
  - append-only memory ledger
  - consolidate and retrieve memories
---

## When to use

Any request to design, implement, extend, or audit a **persistent shared memory layer**
for an agent ecosystem — ingesting information, extracting claims, classifying memories,
assigning confidence, tracking provenance, detecting duplicates and contradictions,
consolidating, retrieving grounded context, or governing corrections. Also use it to
review an existing memory implementation against the invariants below.

This is **not** a notes app, a chatbot scratchpad, or a plain vector store. If the request
is "save this text so I can search it," the skill does not apply.

The output is a **module the ecosystem imports**, not a screen. Client applications
(web control room, SwiftUI cockpit, other agents) are thin projection layers over the
service verbs defined in `reference/retrieval.md`.

## Doctrine — non-negotiables

Read these before writing a line. Every step below assumes them.

1. **One canonicalization authority.** There is exactly one serializer/hasher in the
   ecosystem. `memory_brain/canonical.py` is a *thin adapter* over it — never a second
   implementation. If the authority is unavailable, **fail closed**; do not substitute.
2. **Append-only.** History is never edited or deleted. Corrections, supersessions,
   retractions are new events. Enforce this in the store itself (SQLite `RAISE(ABORT)`
   triggers), not only in code.
3. **Provenance outranks importance.** A high-importance memory can still be wrong.
   Every memory carries its provenance class and full confidence breakdown.
4. **Confidence is four separated components** — source, extraction, inference, current.
   Never collapsed into one number. Always explainable.
5. **Nothing resolves silently.** Dedup above exact-match and every contradiction route
   to a review queue. Resolution is a human-approved ledger event.
6. **Deterministic.** Same inputs → same hashes, same replay, same derived state.
   No wall-clock reads inside hashing; timestamps are injected.
7. **Memory quality over memory quantity.** Quarantine beats absorbing.
8. **Governance before execution.** No autonomous state change reaches a memory.

## Inputs

Collect or infer before starting. Ask only for what you cannot infer.

| Input | Meaning | Default |
|---|---|---|
| `root` | Directory to create `memory_brain/` in | current package root |
| `canonical_module` | Import name **or** file path of the ecosystem's canonicalization authority | `sail_canonical` |
| `db_path` | SQLite file for the ledger + derived store | `memory_brain.db` |
| `scope` | Which subsystems to build this pass | all |
| `interface_verbs` | Service verbs the ecosystem expects | the 12 in `reference/retrieval.md` |

## Steps

1. **Recon before writing — and decide build-vs-extend.** Locate the canonical authority.
   `import` it (or load by path) and **inspect its real API** — do not assume function
   names from this skill or from any prior session. Record what you found in
   `memory_brain/CANONICAL_BINDING.md`.

   **If the ecosystem is Slick's (the SAIL / Pocket OS world), do not re-derive it.** The
   binding is already recorded in `reference/canonical-binding.md`: module `sail_canonical`,
   source sha256
   `7a45813c4b8ac1044333d91abc63355b986cc8aa89179d71e9b7bb3e8f593856`, serializer
   `canonical_json`, digest `digest(domain, value)`, framing
   `sha256(b"sail:domain:" + ascii(domain) + canonical_bytes(value))`. Confirm the source
   hash still matches before trusting it.

   **Then decide build-vs-extend.** If the ecosystem already has `memory_brain`, **extend
   it — do not scaffold a second package.** It is a 23-module package with a `MemoryAPI`
   facade, an append-only `ledger_events` chain, and its own convergence test that locks
   the adapter to the authority across serialization, float edge cases and domain digests.
   A fresh scaffold bypasses every one of those guarantees while looking correct.
   `verify_build.py` enforces a `no second canonicalization authority` check.

2. **Scaffold the package** — *only if there is nothing to extend.* Create the module
   layout in `reference/architecture.md`. Copy the pattern modules from this skill's
   `scripts/memory_brain/` as the starting point, then adapt — they are correct skeletons,
   not finished product.

3. **Bind canonical first.** `canonical.py` must expose `canonical_json(obj) -> str` and
   `digest(domain, obj) -> str`. Resolve them from the real authority. If resolution
   fails, raise `CanonicalAuthorityUnavailable` with the candidate names probed and the
   file inspected. **Do not fall back to `json.dumps`.** Verify with the RFC 8785
   conformance vectors the authority already ships.

4. **Build the ledger.** `ledger.py`: append-only, hash-chained, SQLite-backed. Install
   the no-UPDATE / no-DELETE triggers. Implement `append`, `verify_chain`, `get`,
   `events`, and `rebuild`. See `reference/schemas.md` for the exact event header and
   domain tags. A chain that fails to verify is a **hard stop**, not a warning.

5. **Build the models.** `models.py`: the frozen enums and dataclasses — status,
   provenance class, relationship kind, confidence breakdown, retention class. Enums are
   closed sets; adding a member is a schema-version change, not a patch.

6. **Build dedup — and WIRE IT INTO INGEST.** `dedup.py`: evaluate all seven signals,
   keep them separate, return a classification (`EXACT_DUPLICATE` / `PROBABLE_DUPLICATE` /
   `POSSIBLE_DUPLICATE` / `DISTINCT`). **Auto-merge only on `EXACT_DUPLICATE`.** Everything
   else → review queue. Then confirm `remember` actually *calls* it: a dedup engine the
   ingest path never invokes is dead code that passes every review, and non-exact
   duplicates are then ingested silently with no human ever seeing the decision. Assert it
   with a near-duplicate pair — two claims differing in one word — and check that a
   `POSSIBLE_DUPLICATE`/`PROBABLE_DUPLICATE` review item appears.

7. **Build contradiction detection.** `contradiction.py`: detect, record the relationship
   *and* a ledger event, evaluate recency / provenance strength / confidence / source
   authority — then **stop**. Emit either `ACTIVE` + `SUPERSEDED` *proposal*, or both
   `UNRESOLVED`. Proposals apply only through the governance gate in step 11.

8. **Build consolidation.** `consolidation.py`: reproducible and versioned. Stamp
   `consolidation_algorithm_version` on every output. The canonical memory links back to
   **every** input memory; originals are preserved and stay queryable.

9. **Build retrieval.** `retrieval.py` + `context.py`: hybrid (lexical + vector +
   graph-expansion), reranked, then assembled into a **Context Package** — the shared
   contract handed to other agents. Every item cites `memory_id`, `event_seq`,
   provenance class, and the confidence breakdown. Ungrounded output is a bug.

10. **Expose the service surface.** `service.py`: implement the 12 verbs as the frozen
    interface. Verb signatures and semantics are in `reference/retrieval.md`. Clients
    never touch the ledger directly.

11. **Wire the governance gates.** Every mutating verb that changes a memory's state
    (`consolidate`, `supersede`, `retract`, and applying a contradiction resolution)
    must route through the review queue and require an explicit human approval that
    appends its own ledger event. See `reference/governance.md`.

12. **Verify before declaring done.** Run the acceptance matrix in
    `reference/verification.md`. It must prove, on the real authority: historical memory
    cannot be silently modified, ledger tampering is detectable, replay is deterministic
    and end-inclusive, derived state rebuilds byte-identically, and contradictions stay
    visible until a human decides. Run `python -m memory_brain.selfcheck` and
    `scripts/e2e_memory_brain.py` too.

## Gotchas

- **The digest framing is not what you would assume.** `sail_canonical.digest(domain, value)`
  is `sha256(b"sail:domain:" + domain.encode("ascii") + canonical_bytes(value))` — the ASCII
  prefix `sail:domain:`, **no NUL separator**, ASCII-only domain. A `domain + 0x00 + json`
  framing produces hashes nothing else in the ecosystem can reproduce, and the failure is
  invisible until another system fails to verify. Read the framing off the source; never
  infer it.
- **There are two domain-tag sets in this ecosystem.** The authoritative one is dot
  notation (`memory.content`, `memory.ledger.event`); the versioned colon tags
  (`memory-branch:content:v1`) belong only to a fresh standalone package with no existing
  ledger. Mixing them silently orphans every previously written hash. See
  `reference/canonical-binding.md`.
- **Genesis and chain-field names differ between the two ledgers.** Authoritative:
  `previous_event_hash`, `None` for the first event, table `ledger_events`. This package:
  `prev_hash`, 64-zero `GENESIS_HASH`, table `events`. Both are internally consistent —
  never mix them within one ledger.
- **`str()` on a `str`-mixin Enum is NOT its value on Python 3.11+.** `str(MyEnum.MEMBER)`
  returns `"MyEnum.MEMBER"`, so every `str(x) == "MEMBER"` comparison silently fails —
  events get mislabelled and mismatch checks pass when they should fail. Give every enum
  base a `__str__` returning `self.value`, and compare `.value` on the enum branch.
  Verify with `python -c "from models import E; print(repr(str(E.M)))"`.
- **Never invent the canonical API.** Inspecting is cheap; guessing desynchronizes every
  hash in the system. This is the single most expensive mistake available here.
- **Validate ranges on the small public models, not only on the big one.** `Confirmation`
  is constructed directly by consolidation, retrieval, and governance — so a range check
  that lives only in `Memory.__post_init__` lets an invalid confidence travel as a valid
  object until something downstream trips over it. Give every public value model its own
  `__post_init__`.
- **A module-level constant that is compared, not stored, is the bug shape to watch.** "We
  have `dedup.py`" and "ingest consults `dedup.py`" are different claims; only a test
  settles which one is true.
- **A shared negation marker is not evidence of disagreement.** Two claims that both say
  "without approval" agree on that much. Detect contradictions from markers present in
  ONE claim but not the other, plus opposing modals (must/shall vs may/can) and antonym
  pairs — otherwise a real conflict ("must never resolve" vs "may resolve") is missed
  entirely.
- **Detection must append the relationship, not only the queue item.** A queued review
  item with no `contradicts` link makes the conflict unfindable at retrieval time. Append
  the link in the same step, and have the projection read participants from the nested
  review item, not a top-level key that may be absent.
- **Self-approval checks must read the nested proposal.** The proposer is recorded inside
  the queued proposal payload; checking only a top-level key lets an inference layer
  approve its own proposal.
- **Query parameters in SQLite need `?` binds, not f-strings** — and the append-only
  triggers will abort a bulk "migration" script that tries to rewrite rows. That abort is
  correct behavior; fix the approach, not the trigger.
- **A derived store is not the ledger.** If the projection and the ledger disagree, the
  ledger wins and the projection is rebuilt. Never patch the projection.
- **Timestamps are injected, never read inside a hash.** `datetime.now()` inside the
  event path makes replay non-deterministic and the chain unverifiable.
- **Non-finite floats destroy canonicalization.** Reject `NaN`/`Infinity` at ingest with a
  deterministic failure id rather than letting them reach the serializer. The authority
  raises `FloatDomainError`; normalize that to your own failure id.
- **Exact-hash dedup is a hash collision away from wrong.** Keep the seven signals
  separate even when the answer looks obvious — the breakdown is the audit trail.
- **Watch the `-1e-7` class of bug.** A hand-rolled float formatter emitted `-.1e-7`,
  which reparses to `-1e-8` — silent value corruption in the content itself. This is
  exactly why serialization must delegate to the certified authority rather than being
  re-implemented.

## Reference files

- `reference/architecture.md` — module layout, data flow, integration contract
- `reference/schemas.md` — ledger event schema, memory record, enums, domain tags
- `reference/canonical-binding.md` — **the recorded real binding** (verified hashes, framing, tags)
- `reference/engines.md` — dedup signals, contradiction, consolidation algorithms
- `reference/retrieval.md` — hybrid retrieval, Context Package, the 12 service verbs
- `reference/governance.md` — review queue, human gates, authority and audit
- `reference/verification.md` — acceptance matrix and failure semantics
- `reference/canonical-binding-template.md` — how to record a binding in a new ecosystem
- `scripts/memory_brain/` — pattern modules to copy and adapt
- `scripts/e2e_memory_brain.py` — end-to-end acceptance harness (run it)
- `scripts/_fixture_canonical_authority.py` — TEST FIXTURE ONLY, never bind in production
