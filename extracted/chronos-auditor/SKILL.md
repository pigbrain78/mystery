---
name: chronos-auditor
description: Independent verification layer — assumes everything is wrong until
  proven correct. Verifies ledger integrity, reproduces builds, checks
  deterministic outputs, compares versions, and detects silent deg
triggers:
  - audit this
  - verify the ledger
  - reproduce this build
  - compare versions
  - Chronos
  - is this deterministic
---

## When to use

The user wants to independently verify something in the Meta Software Factory — audit an activity log, reproduce a build, check for deterministic outputs, compare versions for regressions, detect silent degradation, or verify a capability before marketplace release. Use when the user says "audit this", "verify the ledger", "reproduce this build", "compare versions", "Chronos", "is this deterministic", or "check for degradation".

## Inputs

- **action** (required): One of `ledger`, `reproduce`, `deterministic`, `compare`, `degradation`, `capability`, `full`, `dashboard`.
- **activity_log** (for ledger/full): List of activity log entry dicts with id, timestamp, message, hash.
- **build_spec** (for reproduce/full): Dict with build_id, dependencies, actual_dependencies, configuration, actual_configuration, expected_output_hash, actual_output_hash.
- **output_runs** (for deterministic/full): List of dicts, each with output_hash.
- **version_specs** (for compare/full): Dict with product_id, version_a, version_b, specs (dict of version→{security_score, performance, api_spec}).
- **metrics_history** (for degradation/full): List of dicts, each with a `metrics` sub-dict.
- **capability** (for capability/full): Dict with id, version, creator, name, description, provenance_hash, security_score, governance_status.
- **target_name** (optional): Human-readable name for the audit target.

## Steps

### 1. Import the engine

```python
import sys
sys.path.insert(0, '<workspace_root>/scripts/')
from chronos_auditor_core import ChronosAuditor, Verdict, AuditScope, Severity

ca = ChronosAuditor()
```

### 2. Execute the requested action

#### ledger — Verify hash chain integrity

```python
report = ca.verify_ledger_integrity(activity_log, target_name)
```

Reports whether the hash chain is intact or broken. A CRITICAL finding means possible tampering.

#### reproduce — Reproduce a build

```python
report = ca.reproduce_build(build_spec, target_name)
```

Checks dependency hashes, configuration hashes, and output hashes. Reports whether the build is reproducible and deterministic.

#### deterministic — Check output determinism

```python
report = ca.check_deterministic_output(output_runs, target_name)
```

Compares output hashes across multiple runs. A FAIL means non-determinism detected.

#### compare — Compare two versions

```python
report = ca.compare_versions(
    product_id, version_a, version_b, specs, target_name
)
```

Detects API changes, security regressions, and performance regressions between versions.

#### degradation — Detect silent degradation

```python
report = ca.detect_silent_degradation(metrics_history, target_name)
```

Compares first-half to second-half metric averages. Flags worsening error rates, latency, and declining throughput/success rates.

#### capability — Pre-marketplace verification

```python
report = ca.verify_capability(capability, target_name)
```

Checks required fields, security score threshold (7.0), and governance approval status.

#### full — Run all applicable audits

```python
reports = ca.full_audit(
    activity_log=log, build_spec=build, output_runs=runs,
    version_specs=versions, metrics_history=metrics, capability=cap,
    target_name=target_name,
)
```

Runs every audit where data is provided. Returns a list of AuditReports.

#### dashboard — Audit overview

```python
dash = ca.dashboard()
```

Presents total audits, pass/fail/review counts, pass rate, and recent findings.

### 3. Present findings

For each audit report, present:
- Overall verdict (PASS / FAIL / NEEDS_REVIEW / INCONCLUSIVE)
- Each finding with severity, title, description, and recommendation
- If the verdict is FAIL or NEEDS_REVIEW, clearly state what must be fixed before promotion

### 4. Feed into SAIL Governor

After audits complete, call `get_promotion_recommendation(target_id)` to produce a structured recommendation the SAIL Governor can consume:

```python
rec = ca.get_promotion_recommendation(target_id)
# {"promote": True/False, "reason": "...", "signature": "..."}
```

Store the recommendation via `remember_fact`.

## Gotchas

- Chronos is adversarial by design — it assumes everything is wrong. A PASS verdict means the target survived rigorous scrutiny.
- The ledger integrity check requires pre-computed hashes in the log entries. If hashes are missing, compute them first using the same chaining algorithm as Manus Prime's ActivityLog.
- Build reproduction requires both expected and actual values in the build_spec. If the user only has one side, ask for the other.
- Silent degradation detection uses a simple first-half vs second-half comparison. For production use, consider statistical methods (moving average, CUSUM).
- Version comparison needs specs for both versions. If the user only has one version's data, run a partial comparison and flag what's missing.
