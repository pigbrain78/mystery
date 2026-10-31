---
name: recovery-manifest-sync
description: Verifies a recovery bundle (snapshot tarball, RECOVERY_MANIFEST.json, TEST_MANIFEST.json, BASELINE.json, PROVENANCE.md) against its master manifests, computes SHA-256 digests, reconciles test-suite counts across a version bump, and detects unbounded recursive subprocess invocations in verification scripts before they cause timeouts. Use when the user asks to verify a recovery snapshot, reconcile a version bump, check manifest drift, or debug a recovery/verification script that hangs or times out.
---

# Recovery Manifest Sync

## Why this exists

Recovery bundles (`SOVEREIGN_RECOVERY/SNAPSHOT.tar.gz` + `RECOVERY_MANIFEST.json` +
`TEST_MANIFEST.json` + `BASELINE.json` + `PROVENANCE.md`) get re-verified every time the test
count changes (observed lineage: 164 → 171 → 200 → 207 → 215 → 222 → 235 → 254 → 305 tests).
Each bump previously required a manual reconciliation pass across four files, plus a manual
check that the verification harness wasn't about to recurse into itself. This skill automates
both.

## Precondition — verify the bundle actually exists before running anything

Do not assume `scripts/verify_recovery.py`, `scripts/build_recovery.py`, or any
`SOVEREIGN_RECOVERY/` path exists in the current working tree or connected filesystem. Confirm
with `ls` / `find` (or the device-bridge equivalent if the files live on the user's machine)
before invoking anything. If the paths aren't there, say so and ask where the recovery bundle
actually lives — do not fabricate hash values, test counts, or a "pass" result.

## Step-by-step procedure

### 1. Locate the manifest set
Find, in this order of preference: `RECOVERY_MANIFEST.json`, `TEST_MANIFEST.json`,
`BASELINE.json`, `PROVENANCE.md`, and the snapshot archive itself
(`SOVEREIGN_RECOVERY/SNAPSHOT.tar.gz` or equivalent). Read all four before touching the
archive.

### 2. Hash verification
- Extract the snapshot to a scratch directory (never in place over the live tree).
- Compute SHA-256 for every file the manifest tracks:
  `sha256sum $(find <extracted_dir> -type f) `.
- Diff the computed digests against `RECOVERY_MANIFEST.json`'s recorded hashes.
- Flag: (a) any file whose hash doesn't match (drift), (b) any file present in the extracted
  tree but absent from the manifest (untracked), (c) any file the manifest lists but that is
  missing from the extraction (deleted-but-not-reconciled).

### 3. Test suite reconciliation
- Parse `total_unique_tests` (or equivalent field) from `TEST_MANIFEST.json`.
- Actually count test functions/cases in the test tree (e.g.
  `grep -rE '^\s*(def test_|it\(|test\(' <test_dir> | wc -l` — adapt the pattern to the
  actual test framework in use) and compare to the manifest's declared count.
- If they disagree, report the delta and the specific files responsible — do not just say
  "mismatch," name the tests that are untracked or the count that's stale.

### 4. Recursion-guard check (the ADR-004/self-healing failure class)
This is the specific failure this skill exists to catch: a verification script that iterates
over every suite in the manifest, where one of those suites itself shells out to the same
verification script, causing unbounded recursive spawning until the process times out.

- Statically scan the verifier entrypoint (e.g. `scripts/verify_recovery.py`) for any
  `subprocess.run` / `subprocess.Popen` / `os.system` call whose target path resolves back to
  itself, directly or via a script it's known to invoke.
- Cross-reference against the test manifest: does any test file (e.g. a
  `TestRecoveryGate`-style class) invoke the verifier script in a subprocess? If that test is
  itself discovered and run *by* the verifier, that's the recursion loop.
- If found, do not just flag it — propose the concrete guard: an environment variable or CLI
  flag (e.g. `RECOVERY_VERIFY_NO_RECURSE=1`) that the verifier sets before invoking itself and
  checks for on entry, short-circuiting to a no-op/pass-through instead of re-spawning. Show
  the actual diff, don't describe it abstractly.

### 5. Lineage reconciliation report
Produce a structured report (Markdown, or a Google Doc via `mcp__Google_Drive__create_file`
if the user's other recovery docs live in Drive) covering:
- Previous test count → new test count, and the delta's source files
- Hash verification result (pass/fail, with the specific drifted/untracked/missing files if
  any)
- Recursion-guard status (clean, or the specific loop found + the proposed fix)
- `PROVENANCE.md` update — append a dated entry recording this reconciliation pass

### 6. Governance gate
If hash drift or an unguarded recursion path is found, this is a **stop-and-escalate**
condition, not an auto-fix condition — per the standing rule that nothing gets silently
deleted or auto-repaired without approval. Present the finding and the proposed fix; apply the
fix only after the user confirms.

## Output format
Default to a JSON summary object for programmatic reuse, e.g.:

```json
{
  "bundle": "sovereign_recovery_v305.zip",
  "hash_check": {"status": "pass", "drifted": [], "untracked": [], "missing": []},
  "test_reconciliation": {"manifest_count": 305, "actual_count": 305, "delta": 0},
  "recursion_guard": {"status": "clean", "finding": null},
  "next_action": "none"
}
```
followed by a short prose summary for the human reader.

## Hard rules
- Never report a hash/test-count/recursion result you didn't actually compute in this run.
- Never auto-delete untracked files — list them and let the user decide.
- Never apply a recursion-guard fix without showing the diff and getting confirmation.
