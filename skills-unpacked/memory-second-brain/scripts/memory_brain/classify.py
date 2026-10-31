"""Classification — candidate to memory class, retention, importance.

Importance is computed here and kept INDEPENDENT of provenance: a loud, central-sounding
claim with an INFERENCE origin does not become more trustworthy. Provenance always
outranks importance.

Deterministic: same candidate + same policy -> same classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .extract import Candidate
from .models import ProvenanceClass, RetentionClass

__all__ = ["Classification", "Policy", "classify", "retention_for"]

#: High-signal terms that mark durable, decision-relevant material.
_DURABLE_TERMS = (
    "policy", "contract", "decision", "requirement", "architecture", "schema",
    "standard", "must", "shall", "version", "invariant", "protocol",
)
#: Material that should not sit in the active store unexamined.
_SENSITIVE_TERMS = ("password", "secret", "token", "api key", "credential", "private key")
#: Transient material.
_EPHEMERAL_TERMS = ("today", "yesterday", "temporary", "for now", "just testing")


@dataclass(frozen=True)
class Policy:
    """One versioned place for classification rules, so a change is visible in history."""

    version: str = "1.0.0"
    min_extraction_confidence: float = 0.35
    #: Below this, current confidence the memory is committed as UNVERIFIED, not ACTIVE.
    min_active_confidence: float = 0.40


@dataclass(frozen=True)
class Classification:
    provenance_class: ProvenanceClass
    retention_class: RetentionClass
    importance: int
    quarantine: bool
    rationale: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "provenance_class": self.provenance_class.value,
            "retention_class": self.retention_class.value,
            "importance": self.importance,
            "quarantine": self.quarantine,
            "rationale": self.rationale,
            "policy_version": Policy().version,
        }


def retention_for(candidate: Candidate, *, importance: int) -> RetentionClass:
    text = candidate.claim.casefold()
    if any(t in text for t in _EPHEMERAL_TERMS):
        return RetentionClass.EPHEMERAL
    if candidate.provenance_class in (ProvenanceClass.SOURCE, ProvenanceClass.VERIFICATION):
        return RetentionClass.LONG
    if importance >= 70:
        return RetentionClass.LONG
    return RetentionClass.STANDARD


def classify(candidate: Candidate, policy: Policy | None = None) -> Classification:
    """Assign class, retention, and importance, and decide whether to quarantine.

    Quarantine beats absorption: ambiguous, sensitive, or unverified input goes to
    QUARANTINED rather than into the active store.
    """
    pol = policy or Policy()
    text = candidate.claim.casefold()

    score = 0
    signals: list[str] = []

    if candidate.provenance_class in (ProvenanceClass.SOURCE, ProvenanceClass.VERIFICATION):
        score += 25
        signals.append("authoritative_provenance")
    if candidate.provenance_class == ProvenanceClass.INFERENCE:
        score -= 10
        signals.append("inferred_material")
    hits = [t for t in _DURABLE_TERMS if t in text]
    if hits:
        score += min(20, 5 * len(hits))
        signals.append(f"durable_terms:{','.join(hits)}")
    if len(candidate.entities) >= 2:
        score += 10
        signals.append("entity_rich")
    if len(candidate.claim) > 160:
        score += 5
        signals.append("substantive_length")

    importance = max(0, min(100, 40 + score))

    sensitive = [t for t in _SENSITIVE_TERMS if t in text]
    quarantine = bool(sensitive) or candidate.confidence["extraction"] < pol.min_extraction_confidence
    if sensitive:
        signals.append(f"sensitive:{','.join(sensitive)}")
    if candidate.confidence["extraction"] < pol.min_extraction_confidence:
        signals.append("low_extraction_confidence")

    return Classification(
        provenance_class=candidate.provenance_class,
        retention_class=retention_for(candidate, importance=importance),
        importance=importance,
        quarantine=quarantine,
        rationale={"signals": signals, "policy_version": pol.version},
    )
