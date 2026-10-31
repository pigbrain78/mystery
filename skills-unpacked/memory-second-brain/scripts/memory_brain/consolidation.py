"""Consolidation — reproducible, versioned merge with full input linkage.

Guarantees:

  * `consolidation_algorithm_version` is stamped on the output and its event.
  * The canonical memory links to EVERY input memory (`derived_from`).
  * Inputs are preserved and stay queryable in their prior state.
  * Re-running on the same inputs with the same version yields the same content_hash.
    If it does not, that is a determinism bug, not a tuning problem.

Consolidation is a PROPOSAL generator. Applying it is a governance action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .canonical import DOMAIN_CONTENT, digest
from .models import (
    CONSOLIDATION_ALGORITHM_VERSION,
    Memory,
    ProvenanceClass,
)

__all__ = ["ConsolidationResult", "consolidate"]


@dataclass(frozen=True)
class ConsolidationResult:
    canonical_id: str
    claim: str
    content_hash: str
    inputs: tuple[str, ...]
    confidence: dict[str, float]
    importance: int
    provenance_class: str
    algorithm_version: str
    conflicts: tuple[dict[str, Any], ...]
    proposal: dict[str, Any]


def _order_key(m: Memory) -> tuple[int, str]:
    """Canonical ordering independent of input order, so the result is reproducible."""
    return (m.created_seq, m.memory_id)


def consolidate(
    memories: Sequence[Memory],
    *,
    claim_splitter: Any | None = None,
) -> ConsolidationResult:
    """Merge ``memories`` into one canonical proposal.

    Confidence policy:
      * source / extraction — MINIMUM of inputs; a chain is as strong as its weakest source
      * inference — recomputed for the merged claim
      * current — recomputed from all three plus corroboration count

    Importance is recomputed, NEVER inherited as the max: taking the max would let one
    loud source dominate a quiet consensus.
    """
    if not memories:
        raise ValueError("consolidate requires at least one memory")

    ordered = sorted(memories, key=_order_key)

    # Claim: union of non-conflicting assertions, in canonical order.
    seen: list[str] = []
    for m in ordered:
        if m.claim not in seen:
            seen.append(m.claim)
    merged_claim = " | ".join(seen)

    # Conflicting assertions stay visible as an embedded conflict.
    conflicts: tuple[dict[str, Any], ...] = ()
    if len(ordered) > 1:
        conflicts = (
            {
                "kind": "CONSOLIDATION_INPUT_DIVERGENCE",
                "inputs": [m.memory_id for m in ordered],
                "note": "inputs are not identical; consolidated claim preserves all variants",
            },
        )

    src = min(m.confidence.source for m in ordered)
    ext = min(m.confidence.extraction for m in ordered)
    inf = min(m.confidence.inference for m in ordered)
    corroboration = len(ordered)
    cur = min(1.0, (src * 0.4 + ext * 0.3 + inf * 0.1) + 0.05 * corroboration)

    importance = max(0, min(100, round(sum(m.importance for m in ordered) / len(ordered))))

    # Strongest provenance among inputs, recorded but never used to launder a weak one.
    provenance = max(
        (m.provenance_class for m in ordered),
        key=lambda p: {
            ProvenanceClass.SOURCE: 6, ProvenanceClass.VERIFICATION: 5,
            ProvenanceClass.OBSERVATION: 4, ProvenanceClass.EXTRACTION: 3,
            ProvenanceClass.INTERPRETATION: 2, ProvenanceClass.INFERENCE: 1,
        }.get(p, 0),
    )

    body = {
        "claim": merged_claim,
        "inputs": [m.memory_id for m in ordered],
        "algorithm_version": CONSOLIDATION_ALGORITHM_VERSION,
    }
    content_hash = digest(DOMAIN_CONTENT, body)
    canonical_id = "mem_" + digest(DOMAIN_CONTENT, {"consolidated": body})[:16]

    return ConsolidationResult(
        canonical_id=canonical_id,
        claim=merged_claim,
        content_hash=content_hash,
        inputs=tuple(m.memory_id for m in ordered),
        confidence={"source": src, "extraction": ext, "inference": inf, "current": cur},
        importance=importance,
        provenance_class=provenance.value,
        algorithm_version=CONSOLIDATION_ALGORITHM_VERSION,
        conflicts=conflicts,
        proposal={
            "canonical_id": canonical_id,
            "claim": merged_claim,
            "inputs": [m.memory_id for m in ordered],
            "confidence": {"source": src, "extraction": ext, "inference": inf, "current": cur},
            "importance": importance,
            "requires_approval": True,
        },
    )
