"""Duplicate detection — seven independent signals, never collapsed.

The signals are returned SEPARATELY, even when the answer looks obvious. The breakdown
is the audit trail; collapsing it into one score is exactly what lets a system quietly
merge two distinct facts and destroy one of them.

Auto-merge is available ONLY on EXACT_DUPLICATE, because that content is byte-identical
and the merge is information-preserving. Everything else is a human decision.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .canonical import DOMAIN_CONTENT, digest
from .models import DEDUP_ALGORITHM_VERSION, DuplicateClass

__all__ = ["DuplicateSignals", "DedupConfig", "evaluate", "classify", "normalize_claim"]

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)


@dataclass(frozen=True)
class DedupConfig:
    """Thresholds in ONE versioned object, so a change is visible in ledger history."""

    version: str = DEDUP_ALGORITHM_VERSION
    semantic_threshold: float = 0.86
    probable_semantic: float = 0.92
    entity_overlap_probable: float = 0.80
    entity_overlap_possible: float = 0.50
    claim_similarity_probable: float = 0.85
    claim_similarity_possible: float = 0.55


def normalize_claim(text: str) -> str:
    """Case, whitespace, unicode NFKC, punctuation folded. Deterministic, no locale."""
    folded = unicodedata.normalize("NFKC", text or "").casefold()
    folded = _PUNCT.sub(" ", folded)
    return _WS.sub(" ", folded).strip()


@dataclass(frozen=True)
class DuplicateSignals:
    """All seven signals, plus the raw values behind them. Input to `classify`."""

    exact_hash: bool
    normalized_hash: bool
    semantic_similarity: float
    entity_overlap: float
    claim_similarity: float
    source_relationship: str          # SAME | DERIVED | UNRELATED
    temporal_relationship: str        # OVERLAP | DISJOINT | UNKNOWN
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "algorithm_version": DEDUP_ALGORITHM_VERSION,
            "EXACT_HASH": self.exact_hash,
            "NORMALIZED_HASH": self.normalized_hash,
            "SEMANTIC_SIMILARITY": self.semantic_similarity,
            "ENTITY_OVERLAP": self.entity_overlap,
            "CLAIM_SIMILARITY": self.claim_similarity,
            "SOURCE_RELATIONSHIP": self.source_relationship,
            "TEMPORAL_RELATIONSHIP": self.temporal_relationship,
            "detail": self.detail,
        }


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def evaluate(
    *,
    claim_a: str,
    claim_b: str,
    content_hash_a: str | None = None,
    content_hash_b: str | None = None,
    entities_a: Sequence[str] = (),
    entities_b: Sequence[str] = (),
    claim_struct_a: Sequence[str] = (),
    claim_struct_b: Sequence[str] = (),
    semantic_similarity: float | None = None,
    source_id_a: str = "",
    source_id_b: str = "",
    valid_from_a: str | None = None,
    valid_from_b: str | None = None,
) -> DuplicateSignals:
    """Compute all seven signals. Callers supply whatever evidence they have; missing
    evidence yields a conservative value (0.0 / UNKNOWN) rather than a guess."""
    norm_a, norm_b = normalize_claim(claim_a), normalize_claim(claim_b)

    hash_a = content_hash_a or digest(DOMAIN_CONTENT, {"claim": claim_a})
    hash_b = content_hash_b or digest(DOMAIN_CONTENT, {"claim": claim_b})
    norm_hash_a = digest(DOMAIN_CONTENT, {"normalized": norm_a})
    norm_hash_b = digest(DOMAIN_CONTENT, {"normalized": norm_b})

    if semantic_similarity is None:
        # No embedding available -> lexical fallback, clearly marked in `detail`.
        toks_a, toks_b = set(norm_a.split()), set(norm_b.split())
        semantic_similarity = _jaccard(toks_a, toks_b)
        lexical = True
    else:
        lexical = False

    if source_id_a and source_id_b:
        source_rel = "SAME" if source_id_a == source_id_b else "UNRELATED"
    else:
        source_rel = "UNRELATED"

    if valid_from_a and valid_from_b:
        temporal = "OVERLAP" if valid_from_a == valid_from_b else "UNKNOWN"
    else:
        temporal = "UNKNOWN"

    return DuplicateSignals(
        exact_hash=(hash_a == hash_b),
        normalized_hash=(norm_hash_a == norm_hash_b),
        semantic_similarity=float(semantic_similarity),
        entity_overlap=_jaccard(entities_a, entities_b),
        claim_similarity=_jaccard(claim_struct_a, claim_struct_b),
        source_relationship=source_rel,
        temporal_relationship=temporal,
        detail={
            "semantic_source": "lexical_fallback" if lexical else "embedding",
            "normalized_a": norm_a,
            "normalized_b": norm_b,
        },
    )


def classify(signals: DuplicateSignals, config: DedupConfig | None = None) -> DuplicateClass:
    """Map signals to a class. Never auto-escalates to EXACT_DUPLICATE."""
    cfg = config or DedupConfig()

    if signals.exact_hash:
        return DuplicateClass.EXACT_DUPLICATE

    strong = sum([
        signals.normalized_hash,
        signals.semantic_similarity >= cfg.probable_semantic,
        signals.entity_overlap >= cfg.entity_overlap_probable,
        signals.claim_similarity >= cfg.claim_similarity_probable,
        signals.source_relationship == "SAME",
    ])
    if strong >= 2:
        return DuplicateClass.PROBABLE_DUPLICATE

    weak = sum([
        signals.semantic_similarity >= cfg.semantic_threshold,
        signals.entity_overlap >= cfg.entity_overlap_possible,
        signals.claim_similarity >= cfg.claim_similarity_possible,
        signals.temporal_relationship == "OVERLAP",
    ])
    if weak >= 1:
        return DuplicateClass.POSSIBLE_DUPLICATE

    return DuplicateClass.DISTINCT
