"""Memory Second Brain — shared memory layer for the ecosystem.

Public surface. Clients import from here and call these verbs; they never touch the
ledger directly.

    from memory_brain import service
    memory_id = service.remember(...)
    package   = service.recall(...)
"""

from .models import (
    ProvenanceClass,
    MemoryStatus,
    RetentionClass,
    LinkKind,
    EventType,
    ReviewKind,
    Confirmation,
    Memory,
    ContextPackage,
)
from .canonical import (
    canonical_json,
    digest,
    CanonicalAuthorityUnavailable,
    DOMAIN_CONTENT,
    DOMAIN_EVENT,
    DOMAIN_LINK,
    DOMAIN_APPROVAL,
    DOMAIN_FAILURE,
    GENESIS_HASH,
)
from .ledger import Ledger, LedgerIntegrityError

__all__ = [
    "ProvenanceClass",
    "MemoryStatus",
    "RetentionClass",
    "LinkKind",
    "EventType",
    "ReviewKind",
    "Confirmation",
    "Memory",
    "ContextPackage",
    "canonical_json",
    "digest",
    "CanonicalAuthorityUnavailable",
    "Ledger",
    "LedgerIntegrityError",
    "DOMAIN_CONTENT",
    "DOMAIN_EVENT",
    "DOMAIN_LINK",
    "DOMAIN_APPROVAL",
    "DOMAIN_FAILURE",
    "GENESIS_HASH",
]
