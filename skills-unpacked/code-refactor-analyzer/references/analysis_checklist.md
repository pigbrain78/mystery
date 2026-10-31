# Deep Analysis Checklist

Use this when the user wants a thorough pass, not just a quick read. Load only the relevant language section.

## Python
- Unused imports/functions: `grep -rn "^def \|^class "` cross-referenced with call sites.
- Mutable default args (`def f(x=[])`) — common bug source.
- Bare `except:` blocks swallowing errors.
- Blocking calls inside `async def` functions.
- SQLAlchemy: N+1 query patterns, missing `.close()`/context managers on sessions.
- Secrets: scan for `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN` assigned as literals.

## JavaScript / TypeScript
- `any` types masking real shape (TS).
- Unhandled promise rejections, missing `try/catch` around `await`.
- Direct DOM manipulation inside React components (should be refs/state).
- `useEffect` with missing/incorrect dependency arrays.
- `eval()`, `dangerouslySetInnerHTML`, unsanitized template injection.
- Duplicated fetch/error-handling logic across components — candidate for a shared hook.

## Cross-language duplication detection
- Group functions by rough signature (name similarity, arg count, return shape).
- Flag any block of >5 lines repeated verbatim or near-verbatim in 2+ places.
- For repeated retry/backoff/logging/validation logic specifically — these are the highest-value extraction targets.

## Security pass (always run regardless of language)
- Hardcoded credentials or keys.
- Missing input validation on anything reaching a DB query, shell command, or file path.
- Overly broad CORS / auth bypass conditions.
- Dependencies with known CVEs (flag for user to check, don't assume version without checking).
