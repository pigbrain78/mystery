# Recorded canonical binding — sail_canonical (verified 2026-09-12)

This is the **real, inspected** binding for this user's ecosystem. It is not a template and
not a guess: it was read off the source and proven with hashes. Bind to *this* before
scaffolding anything, and re-verify the source hash still matches before relying on it.

## Authority

| Field | Value |
|---|---|
| module (dotted) | `sail_canonical` |
| file | `sail_canonical.py` |
| source sha256 | `7a45813c4b8ac1044333d91abc63355b986cc8aa89179d71e9b7bb3e8f593856` |
| provenance | present and byte-identical in both the 1.1.3 runtime archive and the 1.2.0dev canonical-converged archive, and matching `BUILD_MANIFEST.json` |
| dependency | `rfc8785==0.1.4` (the module performs true RFC 8785 JCS via this library) |

Two independently produced archives carry the same 5,139-byte source and pin the same
hash, so there is exactly one authority and no ambiguity about which one.

| Bound callable | Real name | Signature |
|---|---|---|
| serializer | `canonical_json` | `canonical_json(value) -> str` |
| serializer (bytes) | `canonical_bytes` | `canonical_bytes(value) -> bytes` |
| digest | `digest` | `digest(domain, value) -> hex` — **2-arg, domain first** |

Also public: `sha256_hex`, `failure_id`, `ratification_message`, `sign_ratification`,
`verify_ratification`.

## Proof invocation

```
python -c "import sail_canonical as m; print(m.canonical_json({'b':1,'a':2}))"
  -> {"a":2,"b":1}

python -c "import sail_canonical as m; print(m.digest('memory.content', {'a':1}))"
  -> 296d726143547e245227346623bf61748f4a4c8585bf819001dab5b6fe5eb49a

python -c "import sail_canonical as m; print(m.digest('memory.ledger.event', {'a':1}))"
  -> 4d03be01086ef7902c8b3345ab5f8510af3a795b2cea40c1c9b283abc9e467d8
```

## RFC 8785 number behaviour (proven live)

| input | output | note |
|---|---|---|
| `-1e-7` | `-1e-7` | a naive local formatter emitted `-.1e-7`, which reparses to `-1e-8` — silent value corruption |
| `1e21` | `1e+21` | exponent form above the threshold |
| `1.0` | `1` | integral floats collapse |
| `NaN` | raises `FloatDomainError` | RFC 8785 forbids non-finite; fails closed |

## The digest framing — do not assume it

The real construction, read off the source:

```python
_DOMAIN_TAG = b"sail:domain:"
def digest(domain, value):
    body = canonical_bytes(value)
    if isinstance(domain, str):
        domain = domain.encode("ascii")
    return hashlib.sha256(_DOMAIN_TAG + domain + body).hexdigest()
```

Two consequences:

- the framing uses the ASCII prefix `sail:domain:` with **no NUL separator**;
- domain labels must be **ASCII**.

`memory_brain/canonical.py` reproduces this framing exactly, so its digests are
byte-identical to the authority's.

## Authoritative domain tags

The converged `memory_brain` uses these dot-notation tags under the same `sail:domain:`
scheme, keeping memory digests comparable with the runtime, ledger and council digests:

| Purpose | Tag |
|---|---|
| memory content | `memory.content` |
| ledger event | `memory.ledger.event` |
| provenance | `memory.provenance` |
| context package | `memory.context` |
| snapshot | `memory.snapshot` |
| graph / links | `memory.graph` |
| vector index | `memory.vectorindex` |
| failure id | `failure` |

## Verification run

| Check | Result |
|---|---|
| archive test suite | **128 passed** |
| `verify_build.py` | **ALL CHECKS PASSED**, including `no second canonicalization authority` |
| dependency install order | `rfc8785`, `PyNaCl`, then `fastapi`/`uvicorn`/`pydantic`/`httpx` |

`verify_build.py` actively enforces the single-authority rule. A build that introduces a
parallel serializer or a parallel domain scheme is caught there, not in review.

## Conventions the authoritative build already uses — adopt, do not reinvent

The archive contains a working, converged `memory_brain` (23 modules, `MemoryAPI` facade).
It is the baseline for anything built against this ecosystem.

| Aspect | Authoritative | Do not reintroduce |
|---|---|---|
| digest framing | `sail:domain:` + ascii domain + canonical bytes | NUL-separated framing |
| domain tags | dot notation (`memory.content`) | colon notation (`memory-branch:content:v1`) |
| genesis | `None` | 64-zero sentinel string |
| ledger table | `ledger_events` | `events` |
| chain field | `previous_event_hash` | `prev_hash` |
| entry facade | `MemoryAPI` | a parallel service surface |
| digest arg order | `digest(value, domain)` in the memory adapter | mixing orders |

## Before building: decide build-vs-extend

If the ecosystem already has `memory_brain`, **extend it** — do not scaffold a second
package. The archive's convergence test (`test_memory_canonical_convergence.py`) locks the
adapter to the authority across serialization, float edge cases and domain digests, and
guards the `-1e-7` regression. A fresh package would bypass every one of those guarantees
while looking correct.
