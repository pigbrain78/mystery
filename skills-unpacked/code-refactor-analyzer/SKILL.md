---
name: code-refactor-analyzer
description: Analyzes a single file or an entire codebase for dead code, duplication, weak architecture, security risk, and drift, then produces working refactored code plus a reusable snippet library. Use this skill whenever the user asks to "analyze this code," "refactor," "clean up," "harden," "find reusable snippets," "audit this repo/file," or pastes/uploads code and asks what's wrong with it or how to improve it — even if they don't use the word "skill" or "refactor" explicitly. Also trigger when the user wants a project/code review with scoring (uniqueness, security, readiness, maintainability, scalability). Do NOT use for pure syntax-error debugging with no analysis/refactor intent, or for generating brand-new code from scratch with nothing to analyze.
---

# Code Refactor Analyzer

A deterministic-first, LLM-advisory skill for turning messy code into working, hardened, reusable code — without silently deleting anything the user hasn't approved.

## Core loop

Every run follows this sequence. Do not skip steps; each one feeds the next.

```
CAPTURE → CLASSIFY → CONTEXTUALIZE → RECOMMEND → APPROVE → EXECUTE → AUDIT → LEARN
```

1. **CAPTURE** — Ingest the target (see Scope below). Never analyze from memory/assumption; read the actual file(s).
2. **CLASSIFY** — Tag each file/function: `active`, `dead/unused`, `duplicate`, `risky`, `untested`. Use `grep`/`ast`-based checks where possible, not guesses.
3. **CONTEXTUALIZE** — For each flagged item, identify: what calls it, what it depends on, why it's likely there, what breaks if it's touched.
4. **RECOMMEND** — Produce the Project Review (format below) with concrete hotfixes and refactor diffs.
5. **APPROVE** — Anything marked for deletion or behavior change is `pending approval`, not applied. Present it; wait for explicit go-ahead before executing destructive changes.
6. **EXECUTE** — Apply approved changes. Write refactored files. Extract reusable snippets into the snippet library (see below).
7. **AUDIT** — Log what changed, what was skipped, and why, in a plain changelog block at the end of the response.
8. **LEARN** — Note any pattern worth reusing next time (e.g., "this codebase always duplicates its retry logic") so future passes can check for it.

## Scope selection

Ask only if genuinely ambiguous — otherwise infer from what's provided:
- **Single file**: user pastes/uploads one file, or names one path.
- **Codebase/repo**: user points at a directory, uploads multiple files, or says "this repo"/"this project."
If scope is unclear (e.g., a single file that obviously imports from siblings you don't have), state the assumption you're proceeding with rather than blocking.

## Analysis dimensions

For every file/function evaluated, check:
- **Duplication** — near-identical logic repeated across files/functions (candidate for extraction into a shared snippet).
- **Dead code** — unreferenced functions, unreachable branches, commented-out blocks.
- **Security** — hardcoded secrets, unsanitized input, unbounded shell/eval calls, missing auth checks.
- **Determinism** — business logic that should be deterministic but currently depends on non-deterministic LLM output or unguarded randomness.
- **Coupling/fragility** — hidden dependencies, tight coupling, missing error handling, no tests.
- **Reusability** — self-contained logic that could become a versioned snippet for future projects.

## Output format (Project Review)

Always structure the response this way, JSON-first for the machine-readable parts, prose only where it adds judgment:

```json
{
  "overview": "1-3 sentence summary of what this code/repo does",
  "scope": "single_file | codebase",
  "files_analyzed": ["path1", "path2"],
  "findings": [
    {
      "location": "path:line_or_function",
      "type": "duplication | dead_code | security | fragility | reusable_candidate",
      "severity": "low | medium | high",
      "root_cause": "why this exists / what it symptoms of",
      "recommendation": "smallest high-leverage fix"
    }
  ],
  "scores": {
    "logic_quality": 0,
    "security": 0,
    "maintainability": 0,
    "scalability": 0,
    "readiness": 0
  },
  "pending_approval": [
    {"item": "path/function", "action": "delete | rewrite | move", "reason": "..."}
  ]
}
```

Follow the JSON block with:
- **Immediate hotfixes** — small, safe, apply-now changes (no approval needed if purely additive/non-destructive: e.g. adding error handling, adding tests).
- **Refactored code** — actual diffs or full replacement files for anything approved or non-destructive.
- **Next 3 highest-leverage moves** — ranked, concrete, not conceptual.

Never apply `delete` or behavior-changing `rewrite` actions from `pending_approval` without the user explicitly confirming. Mark unused code as `recyclable`, not gone — move it to a `_recycle/` note or comment block rather than deleting outright unless told otherwise.

## Reusable snippet library

When extracting reusable logic:
1. Save it under `snippets/<category>/<name>.md` (or the user's preferred location) with: purpose, inputs/outputs, dependencies, and a usage example.
2. Never extract a snippet that contains secrets, credentials, or environment-specific hardcoded values — parameterize those first.
3. Prefer extracting the *smallest deterministic unit* (a single function/class), not whole modules, unless the module is genuinely atomic.

## Hard rules

- Read actual file contents before making any claim — never infer behavior from a filename or a prior summary.
- No permanent deletion without explicit user approval; default to `recyclable`/`pending_approval`.
- Never invent dependencies, APIs, or capabilities that aren't in the code.
- State every assumption explicitly if scope or intent is ambiguous.
- Flag security risks even if the user didn't ask about security.
- If the codebase is large, analyze in passes (e.g., by directory) and say so rather than silently sampling a subset and presenting it as complete.

## Workflow reference

See `references/analysis_checklist.md` for the full per-language checklist (Python/JS/TS specifics) when doing a deep pass.
