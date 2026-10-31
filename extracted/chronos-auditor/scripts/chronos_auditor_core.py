"""
Chronos Auditor — Independent Verification Layer
=================================================
The entity whose job is: "Assume everything is wrong until proven correct."

Integrates with:
  - ForgeMaster   : verifies products before they ship
  - Manus Prime   : audits orchestration activity logs
  - Synapse Ledger: verifies ledger integrity
  - SAIL Governor : feeds verification results into governance decisions

Architecture: Adversarial verification with reproducible build checking.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Verdict(Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    NEEDS_REVIEW = "needs_review"


class AuditScope(Enum):
    LEDGER_INTEGRITY = "ledger_integrity"
    BUILD_REPRODUCIBILITY = "build_reproducibility"
    DETERMINISTIC_OUTPUT = "deterministic_output"
    VERSION_COMPARISON = "version_comparison"
    SILENT_DEGRADATION = "silent_degradation"
    CAPABILITY_VERIFICATION = "capability_verification"
    FULL_AUDIT = "full_audit"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AuditFinding:
    id: str
    scope: AuditScope
    verdict: Verdict
    severity: Severity
    title: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuditReport:
    id: str
    scope: AuditScope
    target_id: str
    target_name: str
    overall_verdict: Verdict = Verdict.INCONCLUSIVE
    findings: list[AuditFinding] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    auditor_signature: str = ""

    def finalize(self):
        self.completed_at = datetime.now(timezone.utc).isoformat()
        severities = [f.severity for f in self.findings]
        if any(s in (Severity.CRITICAL, Severity.HIGH) for s in severities):
            self.overall_verdict = Verdict.FAIL
        elif any(s == Severity.MEDIUM for s in severities):
            self.overall_verdict = Verdict.NEEDS_REVIEW
        elif all(f.verdict == Verdict.PASS for f in self.findings):
            self.overall_verdict = Verdict.PASS
        else:
            self.overall_verdict = Verdict.INCONCLUSIVE
        payload = f"{self.id}{self.scope.value}{self.target_id}{self.overall_verdict.value}{self.completed_at}"
        self.auditor_signature = hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class BuildReproduction:
    original_build_id: str
    reproduced: bool = False
    output_hash_match: bool = False
    dependency_hash_match: bool = False
    configuration_match: bool = False
    differences: list[str] = field(default_factory=list)


@dataclass
class VersionComparison:
    product_id: str
    version_a: str
    version_b: str
    api_changes: list[str] = field(default_factory=list)
    behavior_changes: list[str] = field(default_factory=list)
    performance_delta: dict[str, float] = field(default_factory=dict)
    security_score_delta: float = 0.0
    breaking_changes: bool = False


class ChronosAuditor:
    """
    Independent verification entity.
    Core philosophy: "Assume everything is wrong until proven correct."

    Responsibilities:
    - Verify ledger integrity (hash chain validation)
    - Reproduce builds (deterministic output checking)
    - Check deterministic outputs across runs
    - Compare versions (detect regressions, silent degradation)
    - Verify capability objects before marketplace release
    - Feed findings into SAIL Governor for promotion decisions
    """

    def __init__(self):
        self.reports: list[AuditReport] = []
        self.findings_log: list[AuditFinding] = []
        self._audit_counter: int = 0

    # ------------------------------------------------------------------
    # 1. Ledger Integrity
    # ------------------------------------------------------------------

    def verify_ledger_integrity(
        self, activity_log_entries: list[dict], target_name: str = "Activity Log"
    ) -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.LEDGER_INTEGRITY,
            target_id="ledger",
            target_name=target_name,
        )

        if not activity_log_entries:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.LEDGER_INTEGRITY,
                verdict=Verdict.INCONCLUSIVE,
                severity=Severity.INFO,
                title="Empty ledger",
                description="No entries to verify.",
            ))
            report.finalize()
            self.reports.append(report)
            return report

        prev_hash = "0" * 16
        total = len(activity_log_entries)
        broken = False

        for i, entry in enumerate(activity_log_entries):
            eid = entry.get("id", f"entry_{i}")
            ts = entry.get("timestamp", "")
            msg = entry.get("message", "")
            stored = entry.get("hash", "")
            expected = hashlib.sha256(f"{prev_hash}{eid}{ts}{msg}".encode()).hexdigest()[:16]

            if stored and expected != stored:
                broken = True
                report.findings.append(AuditFinding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    scope=AuditScope.LEDGER_INTEGRITY,
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    title=f"Hash chain broken at entry {i}",
                    description=f"Entry hash {stored} != expected {expected}.",
                    evidence={"entry_index": i, "stored": stored, "expected": expected},
                    recommendation="Investigate immediately — possible tampering.",
                ))
                break
            prev_hash = stored or expected

        if not broken:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.LEDGER_INTEGRITY,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="Ledger integrity verified",
                description=f"All {total} entries form a valid hash chain.",
                evidence={"total_entries": total, "final_hash": prev_hash},
            ))

        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 2. Build Reproduction
    # ------------------------------------------------------------------

    def reproduce_build(self, build_spec: dict, target_name: str = "Build") -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.BUILD_REPRODUCIBILITY,
            target_id=build_spec.get("build_id", "unknown"),
            target_name=target_name,
        )

        repro = BuildReproduction(original_build_id=build_spec.get("build_id", "unknown"))

        exp_deps = build_spec.get("dependencies", {})
        act_deps = build_spec.get("actual_dependencies", {})
        if exp_deps and act_deps:
            repro.dependency_hash_match = (exp_deps == act_deps)
            if not repro.dependency_hash_match:
                repro.differences.append("Dependency mismatch.")

        exp_cfg = build_spec.get("configuration", {})
        act_cfg = build_spec.get("actual_configuration", {})
        if exp_cfg and act_cfg:
            repro.configuration_match = (exp_cfg == act_cfg)
            if not repro.configuration_match:
                repro.differences.append("Configuration mismatch.")

        exp_hash = build_spec.get("expected_output_hash", "")
        act_hash = build_spec.get("actual_output_hash", "")
        if exp_hash and act_hash:
            repro.output_hash_match = (exp_hash == act_hash)
            if not repro.output_hash_match:
                repro.differences.append(f"Output hash mismatch: {exp_hash} vs {act_hash}.")

        repro.reproduced = repro.output_hash_match and repro.dependency_hash_match and repro.configuration_match

        if repro.reproduced:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.BUILD_REPRODUCIBILITY,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="Build reproduced successfully",
                description="All hashes match — build is deterministic.",
                evidence={"reproduction": asdict(repro)},
            ))
        else:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.BUILD_REPRODUCIBILITY,
                verdict=Verdict.FAIL,
                severity=Severity.HIGH,
                title="Build reproduction failed",
                description="; ".join(repro.differences),
                evidence={"reproduction": asdict(repro)},
                recommendation="Review dependency pinning and build configuration.",
            ))

        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 3. Deterministic Output
    # ------------------------------------------------------------------

    def check_deterministic_output(self, runs: list[dict], target_name: str = "Output") -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.DETERMINISTIC_OUTPUT,
            target_id="output",
            target_name=target_name,
        )

        if len(runs) < 2:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.DETERMINISTIC_OUTPUT,
                verdict=Verdict.INCONCLUSIVE,
                severity=Severity.INFO,
                title="Insufficient runs",
                description="Need at least 2 runs to compare.",
            ))
            report.finalize()
            self.reports.append(report)
            return report

        hashes = [r.get("output_hash", "") for r in runs]
        unique_hashes = set(h for h in hashes if h)

        if len(unique_hashes) == 1:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.DETERMINISTIC_OUTPUT,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="Deterministic output confirmed",
                description=f"All {len(runs)} runs produced identical output.",
                evidence={"run_count": len(runs), "output_hash": list(unique_hashes)[0]},
            ))
        else:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.DETERMINISTIC_OUTPUT,
                verdict=Verdict.FAIL,
                severity=Severity.HIGH,
                title="Non-deterministic output detected",
                description=f"{len(unique_hashes)} unique outputs across {len(runs)} runs.",
                evidence={"unique_outputs": len(unique_hashes), "run_count": len(runs)},
                recommendation="Identify sources of non-determinism (timestamps, random seeds, external state).",
            ))

        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 4. Version Comparison
    # ------------------------------------------------------------------

    def compare_versions(
        self, product_id: str, version_a: str, version_b: str,
        specs: dict[str, dict], target_name: str = "Version"
    ) -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.VERSION_COMPARISON,
            target_id=product_id,
            target_name=target_name,
        )

        spec_a = specs.get(version_a, {})
        spec_b = specs.get(version_b, {})

        comp = VersionComparison(product_id=product_id, version_a=version_a, version_b=version_b)

        # API changes
        api_a = spec_a.get("api_spec", "")
        api_b = spec_b.get("api_spec", "")
        if api_a != api_b:
            comp.api_changes.append(f"API spec changed between {version_a} and {version_b}")

        # Security score
        sec_a = spec_a.get("security_score", 0)
        sec_b = spec_b.get("security_score", 0)
        comp.security_score_delta = sec_b - sec_a
        if comp.security_score_delta < 0:
            comp.breaking_changes = True
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.VERSION_COMPARISON,
                verdict=Verdict.FAIL,
                severity=Severity.HIGH,
                title="Security regression detected",
                description=f"Security score dropped from {sec_a} to {sec_b} (delta: {comp.security_score_delta}).",
                evidence=asdict(comp),
                recommendation="Do not promote — fix security regression first.",
            ))

        # Performance delta
        perf_a = spec_a.get("performance", {})
        perf_b = spec_b.get("performance", {})
        for metric in set(list(perf_a.keys()) + list(perf_b.keys())):
            delta = perf_b.get(metric, 0) - perf_a.get(metric, 0)
            if delta != 0:
                comp.performance_delta[metric] = delta
                if delta > 0 and "latency" in metric.lower():
                    report.findings.append(AuditFinding(
                        id=f"find_{uuid.uuid4().hex[:8]}",
                        scope=AuditScope.VERSION_COMPARISON,
                        verdict=Verdict.NEEDS_REVIEW,
                        severity=Severity.MEDIUM,
                        title=f"Performance regression in {metric}",
                        description=f"{metric} increased by {delta}.",
                        evidence=asdict(comp),
                        recommendation="Review performance impact before promoting.",
                    ))

        if not report.findings:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.VERSION_COMPARISON,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="Version comparison clean",
                description=f"No regressions between {version_a} and {version_b}.",
                evidence=asdict(comp),
            ))

        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 5. Silent Degradation Detection
    # ------------------------------------------------------------------

    def detect_silent_degradation(
        self, metrics_history: list[dict], target_name: str = "Service"
    ) -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.SILENT_DEGRADATION,
            target_id="degradation",
            target_name=target_name,
        )

        if len(metrics_history) < 2:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.SILENT_DEGRADATION,
                verdict=Verdict.INCONCLUSIVE,
                severity=Severity.INFO,
                title="Insufficient history",
                description="Need at least 2 data points to detect trends.",
            ))
            report.finalize()
            self.reports.append(report)
            return report

        # Simple trend detection: compare first half average to second half average
        mid = len(metrics_history) // 2
        first_half = metrics_history[:mid]
        second_half = metrics_history[mid:]

        degradations = []
        metric_keys = set()
        for entry in metrics_history:
            metric_keys.update(entry.get("metrics", {}).keys())

        for key in metric_keys:
            first_vals = [e.get("metrics", {}).get(key, 0) for e in first_half]
            second_vals = [e.get("metrics", {}).get(key, 0) for e in second_half]
            avg_first = sum(first_vals) / len(first_vals) if first_vals else 0
            avg_second = sum(second_vals) / len(second_vals) if second_vals else 0

            if avg_first > 0:
                pct_change = ((avg_second - avg_first) / avg_first) * 100
                # For latency/error metrics, increase is bad
                if "error" in key.lower() or "latency" in key.lower():
                    if pct_change > 10:
                        degradations.append(f"{key}: +{pct_change:.1f}% (worsening)")
                # For throughput/success metrics, decrease is bad
                elif "throughput" in key.lower() or "success" in key.lower():
                    if pct_change < -10:
                        degradations.append(f"{key}: {pct_change:.1f}% (declining)")

        if degradations:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.SILENT_DEGRADATION,
                verdict=Verdict.FAIL,
                severity=Severity.HIGH,
                title="Silent degradation detected",
                description="; ".join(degradations),
                evidence={"degradations": degradations},
                recommendation="Investigate root cause — system is slowly degrading.",
            ))
        else:
            report.findings.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.SILENT_DEGRADATION,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="No degradation detected",
                description="All metrics stable across the observation window.",
            ))

        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 6. Capability Verification (pre-marketplace gate)
    # ------------------------------------------------------------------

    def verify_capability(self, capability: dict, target_name: str = "Capability") -> AuditReport:
        self._audit_counter += 1
        report = AuditReport(
            id=f"audit_{self._audit_counter:04d}",
            scope=AuditScope.CAPABILITY_VERIFICATION,
            target_id=capability.get("id", "unknown"),
            target_name=target_name,
        )

        checks = []

        # Required fields
        required = ["id", "version", "creator", "name", "description", "provenance_hash"]
        for field in required:
            if not capability.get(field):
                checks.append(AuditFinding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    scope=AuditScope.CAPABILITY_VERIFICATION,
                    verdict=Verdict.FAIL,
                    severity=Severity.HIGH,
                    title=f"Missing required field: {field}",
                    description=f"Capability object is missing '{field}'.",
                    recommendation="Complete all required metadata before publishing.",
                ))

        # Security score threshold
        sec_score = capability.get("security_score", 0)
        if sec_score < 7.0:
            checks.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.CAPABILITY_VERIFICATION,
                verdict=Verdict.FAIL,
                severity=Severity.HIGH,
                title="Security score below threshold",
                description=f"Security score {sec_score} < 7.0 minimum.",
                recommendation="Address security gaps before marketplace release.",
            ))

        # Governance status
        gov = capability.get("governance_status", "pending")
        if gov != "approved":
            checks.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.CAPABILITY_VERIFICATION,
                verdict=Verdict.NEEDS_REVIEW,
                severity=Severity.MEDIUM,
                title="Governance not approved",
                description=f"Governance status is '{gov}', not 'approved'.",
                recommendation="Obtain SAIL Governor sign-off.",
            ))

        if not checks:
            checks.append(AuditFinding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                scope=AuditScope.CAPABILITY_VERIFICATION,
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                title="Capability verified",
                description="All checks passed — ready for marketplace.",
                evidence=capability,
            ))

        report.findings = checks
        report.finalize()
        self.reports.append(report)
        self.findings_log.extend(report.findings)
        return report

    # ------------------------------------------------------------------
    # 7. Full Audit (all scopes)
    # ------------------------------------------------------------------

    def full_audit(
        self,
        activity_log: list[dict] | None = None,
        build_spec: dict | None = None,
        output_runs: list[dict] | None = None,
        version_specs: dict | None = None,
        metrics_history: list[dict] | None = None,
        capability: dict | None = None,
        target_name: str = "Full Audit",
    ) -> list[AuditReport]:
        reports = []
        if activity_log is not None:
            reports.append(self.verify_ledger_integrity(activity_log, f"{target_name} — Ledger"))
        if build_spec is not None:
            reports.append(self.reproduce_build(build_spec, f"{target_name} — Build"))
        if output_runs is not None:
            reports.append(self.check_deterministic_output(output_runs, f"{target_name} — Output"))
        if version_specs is not None:
            # version_specs: {"product_id": ..., "version_a": ..., "version_b": ..., "specs": {...}}
            reports.append(self.compare_versions(
                version_specs["product_id"], version_specs["version_a"],
                version_specs["version_b"], version_specs["specs"],
                f"{target_name} — Versions",
            ))
        if metrics_history is not None:
            reports.append(self.detect_silent_degradation(metrics_history, f"{target_name} — Degradation"))
        if capability is not None:
            reports.append(self.verify_capability(capability, f"{target_name} — Capability"))
        return reports

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def dashboard(self) -> dict:
        total = len(self.reports)
        passed = sum(1 for r in self.reports if r.overall_verdict == Verdict.PASS)
        failed = sum(1 for r in self.reports if r.overall_verdict == Verdict.FAIL)
        needs_review = sum(1 for r in self.reports if r.overall_verdict == Verdict.NEEDS_REVIEW)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_audits": total,
            "passed": passed,
            "failed": failed,
            "needs_review": needs_review,
            "pass_rate_pct": round((passed / total) * 100, 1) if total else 0,
            "recent_findings": [
                {"title": f.title, "verdict": f.verdict.value, "severity": f.severity.value}
                for f in self.findings_log[-10:]
            ],
            "reports": [
                {
                    "id": r.id, "scope": r.scope.value, "target": r.target_name,
                    "verdict": r.overall_verdict.value, "findings_count": len(r.findings),
                }
                for r in self.reports[-20:]
            ],
        }

    def get_promotion_recommendation(self, target_id: str) -> dict:
        """Produce a SAIL Governor-ready promotion recommendation."""
        relevant = [r for r in self.reports if r.target_id == target_id]
        if not relevant:
            return {"promote": False, "reason": "No audit data available."}

        latest = relevant[-1]
        if latest.overall_verdict == Verdict.PASS:
            return {"promote": True, "reason": "All audits passed.", "signature": latest.auditor_signature}
        elif latest.overall_verdict == Verdict.NEEDS_REVIEW:
            return {"promote": False, "reason": "Audit requires human review.", "findings": len(latest.findings)}
        else:
            return {"promote": False, "reason": f"Audit failed: {latest.overall_verdict.value}."}


# ---------------------------------------------------------------------------
# Smoke Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ca = ChronosAuditor()

    # 1. Ledger integrity
    log = [
        {"id": "e1", "timestamp": "2026-01-01T00:00:00Z", "message": "init", "hash": ""},
        {"id": "e2", "timestamp": "2026-01-01T00:01:00Z", "message": "delegated", "hash": ""},
    ]
    # Pre-compute hashes for a valid chain
    prev = "0" * 16
    for e in log:
        e["hash"] = hashlib.sha256(f"{prev}{e['id']}{e['timestamp']}{e['message']}".encode()).hexdigest()[:16]
        prev = e["hash"]

    r1 = ca.verify_ledger_integrity(log, "Test Ledger")
    print(f"Ledger: {r1.overall_verdict.value}")

    # 2. Build reproduction
    r2 = ca.reproduce_build({
        "build_id": "b001",
        "dependencies": {"fastapi": "0.100.0"},
        "actual_dependencies": {"fastapi": "0.100.0"},
        "configuration": {"env": "prod"},
        "actual_configuration": {"env": "prod"},
        "expected_output_hash": "abc123",
        "actual_output_hash": "abc123",
    }, "Test Build")
    print(f"Build: {r2.overall_verdict.value}")

    # 3. Deterministic output
    r3 = ca.check_deterministic_output([
        {"output_hash": "xyz"}, {"output_hash": "xyz"}, {"output_hash": "xyz"},
    ], "Test Output")
    print(f"Deterministic: {r3.overall_verdict.value}")

    # 4. Version comparison
    r4 = ca.compare_versions("prod_001", "1.0.0", "1.1.0", {
        "1.0.0": {"security_score": 8.5, "performance": {"latency_ms": 45}},
        "1.1.0": {"security_score": 9.0, "performance": {"latency_ms": 42}},
    }, "Test Product")
    print(f"Versions: {r4.overall_verdict.value}")

    # 5. Silent degradation
    r5 = ca.detect_silent_degradation([
        {"metrics": {"error_rate": 0.01, "latency_p99": 100}},
        {"metrics": {"error_rate": 0.01, "latency_p99": 102}},
        {"metrics": {"error_rate": 0.02, "latency_p99": 105}},
        {"metrics": {"error_rate": 0.03, "latency_p99": 115}},
    ], "Test Service")
    print(f"Degradation: {r5.overall_verdict.value}")

    # 6. Capability verification
    r6 = ca.verify_capability({
        "id": "cap_001", "version": "1.0.0", "creator": "ForgeMaster",
        "name": "Test Capability", "description": "A test.",
        "provenance_hash": "abc", "security_score": 8.5, "governance_status": "approved",
    }, "Test Capability")
    print(f"Capability: {r6.overall_verdict.value}")

    # Dashboard
    dash = ca.dashboard()
    print(f"\n--- CHRONOS DASHBOARD ---")
    print(f"Audits: {dash['total_audits']} | Pass: {dash['passed']} | Fail: {dash['failed']} | Review: {dash['needs_review']}")
    print(f"Pass rate: {dash['pass_rate_pct']}%")
