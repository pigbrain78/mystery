# Recording the canonical binding

Step 1 of the skill is *recon the authority and record what you found*. Do not skip it,
and do not record it from memory or from a prior session — the file on disk is the only
source of truth.

## Procedure

1. Locate the authority. Either it is importable:

   ```
   python -c "import sail_canonical, inspect; print(sail_canonical.__file__)"
   ```

   or it is a file somewhere in the tree — find it by path and load it directly.

2. Inspect its REAL API. Do not assume names. Read the module and record which callables
   actually exist:

   ```
   python -c "import sail_canonical as m; print([n for n in dir(m) if not n.startswith('_')])"
   ```

   The adapter probes, in order:
   - serializer: `canonical_json`, `dumps_canonical`, `canonicalize`, `jcs_dumps`
   - digest: `digest`, `domain_digest`, `hash_domain`, `content_hash`

   If the real module exposes none of these, write a thin adapter *inside* the authority's
   own repo — never a second serializer inside `memory_brain`.

3. Prove it, with a hash. Run one canonicalization and one digest through the real module
   and paste the outputs. Use a tag from the authoritative set (see
   `reference/canonical-binding.md`), not a tag you invented:

   ```
   python -c "
   import sail_canonical as m
   print(m.canonical_json({'b':1,'a':2}))
   print(m.digest('memory.content', {'a':1}))
   "
   ```

   Then confirm the framing, since a wrong framing is invisible until another system
   cannot reproduce a hash. The real scheme is
   `sha256(b'sail:domain:' + ascii(domain) + canonical_bytes(value))` — no NUL separator.

   If you are binding to this user's existing ecosystem, the answer is already recorded:
   read `reference/canonical-binding.md` and verify the source hash still matches
   `7a45813c4b8ac1044333d91abc63355b986cc8aa89179d71e9b7bb3e8f593856` rather than
   re-deriving it.

4. Persist this file. Fill in:

   ```
   module:        <dotted name>
   file:          <resolved path>
   serializer:    <the callable actually bound>
   digest:        <the callable actually bound>
   proof_json:    <output of step 3, line 1>
   proof_digest:  <output of step 3, line 2>
   probed_missing: <names probed and absent, if any>
   ```

## Why this matters

Every hash in the memory store is produced by that authority. If the binding is guessed
wrong, the store will *look* healthy — the chain verifies against itself — while being
unreproducible by every other system in the ecosystem. The failure is silent and total.
It surfaces only when another system tries to verify a hash and cannot.

`python -m memory_brain.selfcheck` row 17 asserts the binding resolves at all. It cannot
assert the binding is the *right* module — only this record, made by inspection, does that.
