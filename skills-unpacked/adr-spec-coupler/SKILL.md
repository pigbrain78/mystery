---
name: adr-spec-coupler
description: Drafts a paired Architecture Decision Record (ADR) and companion Technical Specification in one pass — assigns the next monotonic ADR ID, enforces clean Title Case naming, scaffolds the standard 5-section spec structure, and wires reciprocal hyperlinks between the two documents. Use when the user asks to log an architecture decision, write an ADR, spec out a new subsystem, or says "couple an ADR and spec" / "log this decision."
---

# ADR + Spec Coupler

## Why this exists

Every major architecture decision in this workspace produces two documents: an ADR in
`05_DECISION_LEDGER` and a companion Technical Specification in `03_TECHNICAL_STACK`
(occasionally `02_PROJECTS`). Historically these were authored sequentially by hand, which
caused three recurring failures:

1. **ID collisions** — two ADRs assigned the same number (e.g. two separate `ADR-005` docs).
2. **Broken back-links** — the ADR is written first, so it can't link forward to a spec that
   doesn't exist yet; the reciprocal link only gets added if someone remembers a second pass.
3. **Inconsistent titles** — some docs land as `Title Case`, others as `UPPERCASE_SNAKE_CASE`,
   which breaks Drive search and sorting.

This skill collapses ADR+Spec authoring into one deterministic pass that eliminates all three.

## Preconditions — verify before writing anything

Do NOT assume `05_DECISION_LEDGER`, `03_TECHNICAL_STACK`, or an ADR index exist. Before
drafting anything:

1. Search Drive (`mcp__Google_Drive__search_files`) for a folder titled `05_DECISION_LEDGER`
   and for a file titled `ADR_INDEX.md` or `ADR_INDEX` inside it.
2. If the folder or index doc does not exist, **stop and tell the user** — do not invent a
   folder ID, guess a parent, or fabricate an ADR number. Ask where the ledger actually lives
   (a different Drive, a git repo, a different account) or offer to create the folder + index
   from scratch if the user confirms this is a fresh setup.
3. If the index exists, read it to find the highest existing ADR number. Never trust a
   number a user or prior doc states verbally — always re-derive it from the index or from a
   live search of `title contains 'ADR-'`, since verbal/historical claims are exactly how the
   ADR-005 duplicate collision happened in the first place.

## Step-by-step procedure

### 1. Resolve the next ADR ID
- Read `ADR_INDEX.md` (or equivalent registry doc) for the highest assigned number.
- Cross-check by searching Drive for `title contains 'ADR-'` and parsing the numeric suffixes
  of results — if the live search finds a higher number than the index records, the index is
  stale; reconcile it (update the index) before assigning a new ID.
- The new ID is `max(index, live-search) + 1`, formatted `ADR-0NN` (zero-padded to 3 digits).
- If a collision is ever found (two docs sharing one ID), do not silently renumber either one.
  Flag it to the user with both doc links and let them choose which keeps the number and which
  gets suffixed (`ADR-005B`) or bumped to the next free integer.

### 2. Collect the decision content from the user
Ask (or infer from conversation context) for:
- Problem/context being decided
- Decision drivers (constraints, forces)
- Considered options (at least 2)
- Chosen outcome and why
- Governed invariants this decision locks in (`NO X -> NO Y -> NO Z` style rules)
- The subsystem name the companion spec should cover

### 3. Create the ADR document
- Title: `ADR-0NN <Decision Name in Title Case>` — never UPPERCASE_SNAKE_CASE, never a
  trailing file-extension suffix like `.md` in the Drive title.
- Body sections, in order: `Status`, `Context`, `Decision Drivers`, `Considered Options`,
  `Decision Outcome`, `Governed Invariants`, `Linked Specification` (placeholder — filled in
  step 5).
- Create via `mcp__Google_Drive__create_file` with `mimeType: application/vnd.google-apps.document`,
  `parentId` = the `05_DECISION_LEDGER` folder ID resolved in the preconditions step.

### 4. Create the companion Technical Specification
- Title: `<Subsystem Name in Title Case> Spec` — Title Case, no SNAKE_CASE, no redundant
  `SOVEREIGN_` / project-name prefixing unless the user explicitly wants brand prefixing.
- Body follows the fixed 5-part blueprint used across this workspace:
  1. Metadata & Executive Purpose
  2. Architectural Model & Pipeline Flow (ASCII/Unicode diagram)
  3. Subsystem Functional Specifications & schemas (Pydantic/JSON)
  4. Verification Test Suite Matrix (Test ID | Category | Runner Script Path | Expected vs
     Actual | P99 Latency SLA | Pass Status)
  5. Governed System Invariants (`NO X -> NO Y -> NO Z` rules — should mirror/extend the
     ADR's invariants, not contradict them)
- Include a `Decided By` line at the top linking back to the ADR (link filled in step 5).
- Create via `mcp__Google_Drive__create_file` with `parentId` = the `03_TECHNICAL_STACK`
  (or `02_PROJECTS`, per user direction) folder ID.

### 5. Wire reciprocal links (this is the step that used to require a manual second pass)
- Once both docs exist, you have both `viewUrl`s.
- Use `mcp__Google_Drive__update_file` is for metadata only — to inject the actual hyperlink
  text into the document body, re-open each doc's content and append/replace the placeholder
  section with a markdown link to the other doc's `viewUrl`.
- ADR's `Linked Specification` section → link to the spec.
- Spec's `Decided By` section → link to the ADR.
- Do this in the same turn the docs are created so there is never a window where either doc
  is missing its counterpart link.

### 6. Update the ADR index
- Append a row to `ADR_INDEX.md`: `| ADR-0NN | <title> | <date> | <spec doc link> |`.
- This is what keeps step 1 honest for the next invocation — never skip it.

### 7. Report back
Give the user both Drive links, the assigned ADR number, and a one-line confirmation that
reciprocal links + index update are done. If any step above was skipped because a
precondition failed (no ledger folder, no index), say so explicitly instead of reporting
success.

## Hard rules
- Never fabricate a folder ID, file ID, or ADR number. Every ID used must come from a live
  `search_files` / `read_file_content` call in this session.
- Never silently resolve an ID collision — always surface it for a human decision.
- Never delete or overwrite an existing ADR/spec without explicit user approval.
- Title Case only for new document titles. No SNAKE_CASE, no trailing extensions in the
  Drive-visible title.
