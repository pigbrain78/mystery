"""TEST FIXTURE ONLY — NEVER BIND THIS IN PRODUCTION.

This is a stand-in canonicalization authority, provided solely so `python -m
memory_brain.selfcheck` and `e2e_memory_brain.py` can run in an environment where the
ecosystem's real authority (sail_canonical) is not installed.

Binding this as the production serializer subverts the one-authority rule: hashes
produced here would not match the rest of the ecosystem. Bind the real module via
MEMORY_BRAIN_CANONICAL_MODULE and treat any diff between the two as a migration.

This is NOT part of the skill and must not be shipped as one. It exists so the canonical
adapter's binding contract and the ledger can be exercised in an environment where the
ecosystem's real authority (sail_canonical) is absent.

It implements RFC 8785-style canonical JSON: sorted keys, no insignificant whitespace,
deterministic number formatting, and a refusal of non-finite floats.
"""

from __future__ import annotations

import hashlib
import json
import math


def _stringify(obj: object) -> str:
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError("non-finite float cannot be canonicalized")
        if obj == int(obj) and abs(obj) < 1e21:
            return str(int(obj))
        return json.dumps(obj, allow_nan=False)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_stringify(v) for v in obj) + "]"
    if isinstance(obj, dict):
        parts = []
        for key in sorted(obj.keys()):
            if not isinstance(key, str):
                raise TypeError("object keys must be strings")
            parts.append(json.dumps(key, ensure_ascii=False) + ":" + _stringify(obj[key]))
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"cannot canonicalize {type(obj).__name__}")


def canonical_json(obj: object) -> str:
    """RFC 8785 canonical JSON. Rejects non-finite floats."""
    return _stringify(obj)


def digest(domain: str, obj: object) -> str:
    """Domain-separated SHA-256: sha256(domain || 0x00 || canonical_json(obj))."""
    h = hashlib.sha256()
    h.update(domain.encode("utf-8"))
    h.update(b"\x00")
    h.update(canonical_json(obj).encode("utf-8"))
    return h.hexdigest()
