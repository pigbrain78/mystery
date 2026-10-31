"""Extraction — raw input to candidate claims, with EXTRACTION provenance.

Deterministic by construction: rule-based segmentation and normalization only. No
sampling, no model calls, no clock reads. The same input yields the same candidates in
the same order on every host — which is what lets a replay reproduce a store.

A candidate is a *proposal*: it carries no authority until `remember` commits it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .models import ProvenanceClass

__all__ = ["Candidate", "extract"]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{2,}")
_BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+")
_WS = re.compile(r"\s+")

#: Below this many characters a fragment is not a usable claim.
MIN_CLAIM_CHARS = 12
#: Cap per input so one document cannot flood the ledger.
MAX_CANDIDATES = 500


@dataclass(frozen=True)
class Candidate:
    claim: str
    provenance_class: ProvenanceClass
    source_id: str
    confidence: dict[str, float]
    entities: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    ordinal: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "provenance_class": self.provenance_class.value,
            "source_id": self.source_id,
            "confidence": dict(self.confidence),
            "entities": list(self.entities),
            "tags": list(self.tags),
            "ordinal": self.ordinal,
        }


def _split_units(text: str) -> list[str]:
    units: list[str] = []
    for block in _SENT_SPLIT.split(text):
        stripped = _BULLET.sub("", block.strip())
        if stripped:
            units.append(stripped)
    return units


def _entities(claim: str) -> tuple[str, ...]:
    """Capitalized multi-word runs, plus dotted/quoted tokens. Deterministic, ordered."""
    found: list[str] = []
    for match in re.findall(r"\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*\b", claim):
        if match not in found:
            found.append(match)
    for match in re.findall(r"`([^`]+)`|\"([^\"]+)\"", claim):
        token = match[0] or match[1]
        if token and token not in found:
            found.append(token)
    return tuple(found)


def extract(
    text: str,
    *,
    source_id: str,
    provenance_class: ProvenanceClass = ProvenanceClass.EXTRACTION,
    source_confidence: float = 0.9,
    extraction_confidence: float = 0.8,
    tags: Iterable[str] = (),
    max_candidates: int = MAX_CANDIDATES,
) -> list[Candidate]:
    """Segment ``text`` into candidate claims.

    ``inference_confidence`` is 0.0 for extraction — nothing was inferred. Keeping it
    explicit rather than absent is what makes the four-part breakdown honest.
    """
    base_tags = tuple(dict.fromkeys(tags))
    out: list[Candidate] = []
    for ordinal, unit in enumerate(_split_units(text or "")):
        claim = _WS.sub(" ", unit).strip()
        if len(claim) < MIN_CLAIM_CHARS:
            continue
        out.append(
            Candidate(
                claim=claim,
                provenance_class=provenance_class,
                source_id=source_id,
                confidence={
                    "source": float(source_confidence),
                    "extraction": float(extraction_confidence),
                    "inference": 0.0,
                    "current": float(min(source_confidence, extraction_confidence)),
                },
                entities=_entities(claim),
                tags=base_tags,
                ordinal=ordinal,
            )
        )
        if len(out) >= max_candidates:
            break
    return out
