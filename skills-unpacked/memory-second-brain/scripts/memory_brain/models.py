"""Frozen models. Closed enums, dataclasses, no behaviour beyond validation.

Enums here are CLOSED SETS. Adding a member is a SCHEMA_VERSION change, not a patch —
consumers switch on these values and an unrecognised member is a defect, so the set must
never grow silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = 1

#: Stamped on consolidation output and its event.
CONSOLIDATION_ALGORITHM_VERSION = "1.0.0"
#: Stamped on dedup config so a threshold change is visible in ledger history.
DEDUP_ALGORITHM_VERSION = "1.0.0"
#: Stamped on contradiction evaluation so old proposals stay explainable.
CONTRADICTION_ALGORITHM_VERSION = "1.0.0"


class _StrEnum(str, Enum):
    """String-mixin enum whose ``str()`` is its VALUE.

    Python 3.11 changed ``str()`` on a plain ``(str, Enum)`` mixin to return
    ``"ClassName.MEMBER"`` rather than the value. That silently breaks every
    ``str(x) == "MEMBER"`` comparison — an event gets mislabelled, a mismatch check
    passes when it should fail. Defining ``__str__`` once here removes the entire class
    of bug rather than patching each call site.
    """

    def __str__(self) -> str:
        # NOT super().__str__(): that is the 3.11+ qualified-name behaviour.
        return str(self.value)

    def __format__(self, spec: str) -> str:
        return format(self.value, spec)


class MemoryStatus(_StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    CONTRADICTED = "CONTRADICTED"
    RETRACTED = "RETRACTED"
    ARCHIVED = "ARCHIVED"
    QUARANTINED = "QUARANTINED"
    UNVERIFIED = "UNVERIFIED"


#: TERMINAL — a retracted memory never leaves this state.
TERMINAL_STATUSES = frozenset({MemoryStatus.RETRACTED})


class ProvenanceClass(_StrEnum):
    SOURCE = "SOURCE"
    OBSERVATION = "OBSERVATION"
    EXTRACTION = "EXTRACTION"
    INFERENCE = "INFERENCE"
    INTERPRETATION = "INTERPRETATION"
    VERIFICATION = "VERIFICATION"


#: Strength order for conflict evaluation. Strongest first. Provenance always outranks
#: importance — a high-importance memory can still be wrong.
PROVENANCE_STRENGTH: dict[str, int] = {
    ProvenanceClass.SOURCE.value: 6,
    ProvenanceClass.VERIFICATION.value: 5,
    ProvenanceClass.OBSERVATION.value: 4,
    ProvenanceClass.EXTRACTION.value: 3,
    ProvenanceClass.INTERPRETATION.value: 2,
    ProvenanceClass.INFERENCE.value: 1,
}


class RetentionClass(_StrEnum):
    PERMANENT = "PERMANENT"
    LONG = "LONG"
    STANDARD = "STANDARD"
    SHORT = "SHORT"
    EPHEMERAL = "EPHEMERAL"


class LinkKind(_StrEnum):
    CORRECTED_BY = "corrected_by"
    SUPERSEDED_BY = "superseded_by"
    DERIVED_FROM = "derived_from"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    CONSOLIDATED_FROM = "consolidated_from"
    DUPLICATE_OF = "duplicate_of"


class EventType(_StrEnum):
    MEMORY_CREATED = "MEMORY_CREATED"
    MEMORY_ENRICHED = "MEMORY_ENRICHED"
    MEMORY_SUPERSEDED = "MEMORY_SUPERSEDED"
    MEMORY_CORRECTED = "MEMORY_CORRECTED"
    MEMORY_STATUS_CHANGED = "MEMORY_STATUS_CHANGED"
    MEMORY_RETRACTED = "MEMORY_RETRACTED"
    MEMORY_ARCHIVED = "MEMORY_ARCHIVED"
    MEMORY_QUARANTINED = "MEMORY_QUARANTINED"
    LINK_CREATED = "LINK_CREATED"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    CONTRADICTION_RESOLVED = "CONTRADICTION_RESOLVED"
    DUPLICATE_DETECTED = "DUPLICATE_DETECTED"
    MERGE_APPLIED = "MERGE_APPLIED"
    CONSOLIDATION_CREATED = "CONSOLIDATION_CREATED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    RETRIEVAL_SERVED = "RETRIEVAL_SERVED"
    INGEST_REJECTED = "INGEST_REJECTED"


class ReviewKind(_StrEnum):
    PROBABLE_DUPLICATE = "PROBABLE_DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    CONTRADICTION = "CONTRADICTION"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    QUARANTINE_RELEASE = "QUARANTINE_RELEASE"


class ReviewState(_StrEnum):
    OPEN = "OPEN"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    EXPIRED = "EXPIRED"


class DuplicateClass(_StrEnum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    PROBABLE_DUPLICATE = "PROBABLE_DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    DISTINCT = "DISTINCT"


class ContradictionOutcome(_StrEnum):
    #: A proposal that A wins — applied only by an approval event.
    PREFER_A = "PREFER_A"
    #: A proposal that B wins — applied only by an approval event.
    PREFER_B = "PREFER_B"
    #: The honest answer when factors conflict or are close. First-class outcome.
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Confirmation:
    """Four separated confidence components. NEVER collapsed into one number."""

    source: float
    extraction: float
    inference: float
    current: float

    def __post_init__(self) -> None:
        # Validate HERE, not only in Memory. This model is public and is constructed on
        # its own (consolidation, retrieval, governance all build one directly), so a
        # range check that lives only in Memory lets an invalid confidence travel as a
        # valid object until something downstream trips over it.
        for name in ("source", "extraction", "inference", "current"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"confidence.{name} must be a number, got {type(value).__name__}")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"confidence.{name} out of range: {value!r}")

    def as_dict(self) -> dict[str, float]:
        return {
            "source": self.source,
            "extraction": self.extraction,
            "inference": self.inference,
            "current": self.current,
        }


@dataclass(frozen=True)
class Memory:
    memory_id: str
    created_seq: int
    status: MemoryStatus
    claim: str
    content_hash: str
    provenance_class: ProvenanceClass
    source_id: str
    confidence: Confirmation
    importance: int = 0
    valid_from: str | None = None
    valid_to: str | None = None
    retention_class: RetentionClass = RetentionClass.STANDARD
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("source", "extraction", "inference", "current"):
            value = getattr(self.confidence, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"confidence.{name} out of range: {value!r}")
        if not 0 <= self.importance <= 100:
            raise ValueError(f"importance out of range: {self.importance!r}")
        if not self.provenance_class:
            raise ValueError("every memory must carry a provenance class")

    def as_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "created_seq": self.created_seq,
            "status": self.status.value,
            "claim": self.claim,
            "content_hash": self.content_hash,
            "provenance_class": self.provenance_class.value,
            "source_id": self.source_id,
            "confidence": self.confidence.as_dict(),
            "importance": self.importance,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "retention_class": self.retention_class.value,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class ContextItem:
    memory_id: str
    event_seq: int
    claim: str
    status: str
    provenance_class: str
    confidence: dict[str, float]
    valid_from: str | None
    source_id: str
    why_included: str


@dataclass(frozen=True)
class ContextPackage:
    """The shared contract handed to consuming agents.

    An item without BOTH memory_id and event_seq is a bug. `conflicts` is non-optional:
    a relevant contested assertion is surfaced even when the caller did not ask.
    """

    package_id: str
    query: str
    generated_at: str
    policy: dict[str, Any]
    items: tuple[ContextItem, ...]
    conflicts: tuple[dict[str, Any], ...]
    coverage: dict[str, Any]
    truncated: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "query": self.query,
            "generated_at": self.generated_at,
            "policy": self.policy,
            "items": [
                {
                    "memory_id": i.memory_id,
                    "event_seq": i.event_seq,
                    "claim": i.claim,
                    "status": i.status,
                    "provenance_class": i.provenance_class,
                    "confidence": i.confidence,
                    "valid_from": i.valid_from,
                    "source_id": i.source_id,
                    "why_included": i.why_included,
                }
                for i in self.items
            ],
            "conflicts": list(self.conflicts),
            "coverage": self.coverage,
            "truncated": self.truncated,
        }
