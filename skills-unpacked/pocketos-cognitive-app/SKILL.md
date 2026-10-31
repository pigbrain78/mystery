---
name: pocketos-cognitive-app
description: Build or extend PocketOS-style personal cognitive apps with a canonical backend, second-brain memory, Cognitive Twin, AI Shadow, governed proposals, typed API clients, SSE refresh, and security-aware mobile/web UX. Use when implementing or auditing cognitive control surfaces, knowledge capture systems, or AI-assisted personal operating systems.
---

# PocketOS Cognitive App

Use this skill to build the client control surface for a personal cognitive substrate. Work incrementally from the existing backend; do not replace or silently fork the backend architecture.

## Constitutional invariant

Preserve this rule in every feature:

> Memory may inform execution. Memory may not authorize execution.

The authority chain is **LLM proposes → council evaluates → governance authorizes → human ratifies → kernel executes → ledger records**. The client only displays canonical state and submits requests. It must never manufacture authority, ratification, capability, hashes, sequence numbers, ledger position, or execution readiness.

AI Shadow always exposes **AUTHORITY: NONE**, **CAN EXECUTE: NO**, and **CAN RATIFY: NO**. Cognitive Twin is representational and advisory; inferred information must not look verified.

## Start by inspecting

1. Inspect the repository, existing backend, mobile/web project, tests, manifests, and any OpenAPI artifact.
2. Locate the authoritative source of truth for memory, projects, decisions, governance, events, and ledger state.
3. Compare the requested contract with served routes. If `/api/v1` is required but absent, stop and report the conflict; only add a thin versioned alias surface after the user chooses it.
4. Never fabricate a missing OpenAPI contract. Derive only from executable backend behavior, clearly label it as derived, and prefer adding typed server response models.
5. Check project instructions and create a concise `todo.md` tracker for features and verification.

## Build order

Follow one milestone at a time. Verify each milestone before moving on.

1. **Application shell:** navigation, dark-first design tokens, safe-area layout, authentication boundary, typed transport, and routing.
2. **Cognitive cockpit:** current state, focus, projects, open loops, recent memories, Twin, Shadow, pending decisions, events, and system status. Use strong hierarchy and avoid fake metrics.
3. **Memory:** governed capture, browse/search, detail, epistemic state, confidence, provenance, evidence, contradictions, and history. Capture may be initiated by the client; canonical persistence and verification stay server-side.
4. **Cognitive Twin:** consume the canonical projection. Render focus, projects, loops, memories, observations, relationships, confidence, epistemic labels, evidence, and provenance. Do not implement Twin reasoning in UI.
5. **AI Shadow:** consume a separate advisory projection. Render observation, insight, warning, opportunity, question, recommendation, or proposal with confidence/evidence/provenance and an explicit no-authority boundary.
6. **Shadow-to-proposal:** submit a Shadow item to a backend proposal endpoint. The backend must create an ordinary governed proposal and record Shadow authority as `NONE`; it must not ratify, grant capability, or execute.
7. **Projects and Open Loops:** add canonical read projections derived by the backend. Do not create isolated client project data.
8. **Decisions and governance:** keep proposal, council, ratification, capability, execution, outcome, and evidence states separate. Use backend responses as authoritative.
9. **Evidence and ledger:** expose why the system believes something and append-only event details. Historical events are read-only.
10. **Replay, bookmarks, graph, and search:** accept deep-link inputs only as lookup hints; validate targets through the backend. Display only canonical relationships.
11. **Live sync:** subscribe to the existing SSE/event stream. Treat events as observations, then refetch authoritative Twin/Shadow/state projections. On disconnect, close cleanly, reconnect with backoff where supported, resynchronize, and label stale state.
12. **Accessibility and polish:** support screen readers, keyboard navigation, Dynamic Type, reduced motion, non-color state cues, and sufficient contrast.

## API/client pattern

Keep the boundary:

```text
UI → typed domain client → transport → PocketOS API
```

Create typed modules for system, memory, projects, cognitiveTwin, aiShadow, decisions, governance, evidence, ledger, replay, events, search, and authentication. Avoid `any`. Keep API base URL configuration explicit (for example `EXPO_PUBLIC_POCKETOS_API_URL`). If the URL is absent, show a clearly labeled development/checkpoint mirror or an unavailable state; never silently pretend fixtures are live.

For SSE:

```text
receive observation → validate/parse → refetch authoritative projection → update UI
```

Never treat an SSE event as proof that the client caused a mutation. Never create a second event ledger in the client.

## Security and negative tests

Before delivery, test that the client cannot execute pending or rejected decisions; execute by forging authority or permission fields; make permission alone sufficient without ratification and capability validation; manufacture ratification locally; turn `INFERRED` into `VERIFIED`; make AI Shadow output authoritative; edit replay history, canonical sequences, or hashes; bypass capability requirements; or treat an SSE observation as mutation proof.

Exercise the real backend wherever possible. Test unauthorized capture and proposal requests, not only successful renders.

## Verification and delivery

After each milestone:

1. Run backend contract and protection checks.
2. Run TypeScript/lint/build checks.
3. Run unit and integration tests; record skipped tests explicitly.
4. Capture representative mobile/web screenshots.
5. Check important buttons and links for a complete flow or an honest backend-support message.
6. Update `todo.md`.
7. Save one reviewable checkpoint at the milestone boundary and report what is live, mirrored, blocked by backend support, and next.

Do not claim completeness because screens render. Definition of done requires real API integration, canonical persistence, clear epistemic/authority states, live synchronization, offline/stale handling, accessibility, and negative security coverage.

## References

Read `references/api-contract-checklist.md` when recovering or versioning an API contract. Read `references/security-tests.md` when implementing governance, proposals, execution, replay, or event synchronization.
