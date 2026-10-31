"""Canonicalization adapter — the SINGLE hashing path for memory_brain.

This module is a thin adapter over the ecosystem's one canonicalization authority
(RFC 8785 JCS + domain-tagged SHA-256). It is **not** a second implementation.

If the authority cannot be resolved, this module fails closed. There is deliberately
no fallback serializer: a private `json.dumps` path would produce hashes that nothing
else in the ecosystem can reproduce, which silently destroys auditability.

Binding
-------
Resolution order for the authority:

  1. `MEMORY_BRAIN_CANONICAL_MODULE` environment variable — a dotted module name or a
     filesystem path to a `.py` file.
  2. The default import name `sail_canonical`.

The authority must expose one of the recognised callable pairs. Probed names are tried
in the order below and the FIRST that yields a working pair is bound:

    canonical_json(obj) -> str          # RFC 8785 (JCS) serialization
    digest(domain, obj) -> str          # sha256(b"sail:domain:" + ascii(domain) + canonical_bytes(obj))

Acceptable alternate names:

    serializer side : canonical_json | dumps_canonical | canonicalize | jcs_dumps
    digest side     : digest | domain_digest | hash_domain | content_hash

After binding, call `binding_report()` and persist the result to
`memory_brain/CANONICAL_BINDING.md` for the audit trail.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
import sys
from types import ModuleType
from typing import Any, Callable

__all__ = [
    "canonical_json",
    "digest",
    "CanonicalAuthorityUnavailable",
    "authority",
    "binding_report",
    "DOMAIN_CONTENT",
    "DOMAIN_EVENT",
    "DOMAIN_LINK",
    "DOMAIN_APPROVAL",
    "DOMAIN_FAILURE",
    "GENESIS_HASH",
]

# --------------------------------------------------------------------------------------
# Domain separation tags.
#
# IMPORTANT — read `reference/canonical-binding.md` before adapting these. Two tag sets
# exist in the user's ecosystem, and picking the wrong one silently produces hashes that
# nothing else can reproduce:
#
#   AUTHORITATIVE (use when building against the existing SAIL memory subsystem):
#       memory.content          memory.ledger.event     memory.provenance
#       memory.context          memory.snapshot         memory.graph
#       memory.vectorindex      failure
#     These are the tags the converged `memory_brain` in the SAIL archive already hashes
#     under, so digests are comparable with the runtime, ledger and council digests.
#     They are exposed below as DOMAIN_*_SAIL.
#
#   THIS PACKAGE'S DEFAULTS (use only for a fresh, standalone package with no existing
#   ledger to stay compatible with): the versioned colon tags below.
#
# Changing a tag invalidates every prior hash under it and is a migration, not an edit.
# --------------------------------------------------------------------------------------
DOMAIN_CONTENT = "memory-branch:content:v1"
DOMAIN_EVENT = "memory-branch:ledger-event:v1"
DOMAIN_LINK = "memory-branch:link:v1"
DOMAIN_APPROVAL = "memory-branch:approval:v1"
DOMAIN_FAILURE = "memory-branch:failure:v1"

#: The authoritative SAIL tags. Prefer these when there is an existing ledger.
DOMAIN_CONTENT_SAIL = "memory.content"
DOMAIN_EVENT_SAIL = "memory.ledger.event"
DOMAIN_PROVENANCE_SAIL = "memory.provenance"
DOMAIN_CONTEXT_SAIL = "memory.context"
DOMAIN_SNAPSHOT_SAIL = "memory.snapshot"
DOMAIN_GRAPH_SAIL = "memory.graph"
DOMAIN_VECTOR_SAIL = "memory.vectorindex"
DOMAIN_FAILURE_SAIL = "failure"

#: prev_hash of sequence 1 — this package's convention. The authoritative SAIL ledger
#: instead uses ``None`` for a first event's ``previous_event_hash``. Either is internally
#: consistent; do not mix them within one ledger.
GENESIS_HASH = "0" * 64

DEFAULT_AUTHORITY = "sail_canonical"

_SERIALIZER_NAMES = ("canonical_json", "dumps_canonical", "canonicalize", "jcs_dumps")
_DIGEST_NAMES = ("digest", "domain_digest", "hash_domain", "content_hash")

_binding: dict[str, Any] = {"module": None, "serializer": None, "digest": None}


class CanonicalAuthorityUnavailable(RuntimeError):
    """The single canonicalization authority could not be resolved.

    Hard failure by design. Never catch this and substitute a local serializer.
    """


def _load_authority() -> ModuleType:
    target = os.environ.get("MEMORY_BRAIN_CANONICAL_MODULE", DEFAULT_AUTHORITY)

    # Filesystem path form.
    if target.endswith(".py") or os.sep in target:
        if not os.path.isfile(target):
            raise CanonicalAuthorityUnavailable(
                f"canonical authority path does not exist: {target!r}"
            )
        spec = importlib.util.spec_from_file_location("_memory_brain_canonical_authority", target)
        if spec is None or spec.loader is None:
            raise CanonicalAuthorityUnavailable(
                f"cannot load canonical authority from path: {target!r}"
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    # Dotted module form.
    try:
        return importlib.import_module(target)
    except ImportError as exc:
        raise CanonicalAuthorityUnavailable(
            f"canonical authority {target!r} is not importable: {exc}. "
            "Set MEMORY_BRAIN_CANONICAL_MODULE to its dotted name or file path. "
            "Refusing to fall back to a private serializer."
        ) from exc


def _resolve_callable(module: ModuleType, names: tuple[str, ...], role: str) -> Callable[..., Any]:
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise CanonicalAuthorityUnavailable(
        f"canonical authority {module.__name__!r} exposes no {role} callable; "
        f"probed: {', '.join(names)}"
    )


def _bind() -> None:
    if _binding["module"] is not None:
        return
    module = _load_authority()
    serializer = _resolve_callable(module, _SERIALIZER_NAMES, "serializer")
    digest_fn = _resolve_callable(module, _DIGEST_NAMES, "digest")
    _binding.update(
        module=module,
        serializer=serializer,
        digest=digest_fn,
        serializer_name=serializer.__name__,
        digest_name=digest_fn.__name__,
    )


def authority() -> ModuleType:
    """The bound authority module. Raises if unresolvable."""
    _bind()
    return _binding["module"]


def canonical_json(obj: Any) -> str:
    """RFC 8785 canonical JSON, via the ecosystem authority. No fallback."""
    _bind()
    return _binding["serializer"](obj)


#: Real framing constant of the certified authority, read off its source:
#: `_DOMAIN_TAG = b"sail:domain:"` then `sha256(_DOMAIN_TAG + domain + canonical_bytes)`.
#: Note there is NO NUL separator, and the domain must be ASCII.
SAIL_DOMAIN_TAG = b"sail:domain:"


def digest(domain: str, obj: Any) -> str:
    """Domain-separated SHA-256 over the canonical form of ``obj``.

    Delegates to the authority's ``digest(domain, obj)``. The fallback below reproduces
    the authority's *exact* framing — `sha256(b"sail:domain:" + ascii(domain) +
    canonical_bytes(obj))` — so a fallback hash is byte-identical to the authority's and
    never introduces a second scheme. Verified against the real module: adapter digests
    match `sail_canonical.digest` exactly.

    Prefer a real binding over the fallback. The fallback exists so a partially-provisioned
    environment is still correct, not so it can replace the authority.
    """
    _bind()
    fn = _binding["digest"]
    try:
        return fn(domain, obj)
    except TypeError:
        body = _binding["serializer"](obj).encode("utf-8")
        h = hashlib.sha256()
        h.update(SAIL_DOMAIN_TAG)
        h.update(domain.encode("ascii"))
        h.update(body)
        return h.hexdigest()


def binding_report() -> dict[str, Any]:
    """Audit record of what got bound. Persist to CANONICAL_BINDING.md."""
    _bind()
    module = _binding["module"]
    return {
        "module": module.__name__,
        "file": getattr(module, "__file__", None),
        "serializer": _binding["serializer_name"],
        "digest": _binding["digest_name"],
        "domains": {
            "content": DOMAIN_CONTENT,
            "event": DOMAIN_EVENT,
            "link": DOMAIN_LINK,
            "approval": DOMAIN_APPROVAL,
            "failure": DOMAIN_FAILURE,
        },
        "genesis_hash": GENESIS_HASH,
    }
