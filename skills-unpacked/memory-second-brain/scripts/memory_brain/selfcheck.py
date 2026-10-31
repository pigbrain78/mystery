"""Runnable acceptance probe. `python -m memory_brain.selfcheck`

Covers the rows of the acceptance matrix that need only the ledger and the canonical
binding: 1-6 and 17-18. Rows 7-16 and 19-22 need the full ingest / retrieval / governance
stack and belong in the test suite, not here.

Exit code is 0 only when every row passes.
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

from .canonical import (
    CanonicalAuthorityUnavailable,
    binding_report,
    canonical_json,
    digest,
)
from .ledger import Ledger, LedgerIntegrityError

RESULTS: list[tuple[str, bool, str]] = []


def _record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


def row_1_chain_integrity() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = Ledger(Path(d) / "t.db")
        for i in range(5):
            led.append("MEMORY_CREATED", {"n": i}, actor="test", created_at="2026-01-01T00:00:00Z")
        report = led.verify_chain()
        led.close()
    _record("1 chain integrity", report.ok and report.length == 5, f"length={report.length}")


def row_2_tamper_detection() -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.db"
        led = Ledger(path)
        for i in range(3):
            led.append("MEMORY_CREATED", {"n": i}, actor="test", created_at="2026-01-01T00:00:00Z")
        led.close()

        # Bypass the triggers exactly as an attacker or a bad migration would.
        raw = sqlite3.connect(path, isolation_level=None)
        raw.execute("DROP TRIGGER events_no_update")
        raw.execute("UPDATE events SET payload_json = ? WHERE seq = 2", ('{"n": 99}',))
        raw.close()

        led2 = Ledger(path)
        report = led2.verify_chain()
        led2.close()
    _record(
        "2 tamper detection",
        (not report.ok) and report.broken_at == 2,
        f"broken_at={report.broken_at} reason={report.reason}",
    )


def row_3_append_only() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = Ledger(Path(d) / "t.db")
        led.append("MEMORY_CREATED", {"n": 0}, actor="test", created_at="2026-01-01T00:00:00Z")
        blocked_update = blocked_delete = False
        try:
            led._conn.execute("UPDATE events SET actor = 'x' WHERE seq = 1")
        except sqlite3.IntegrityError:
            blocked_update = True
        try:
            led._conn.execute("DELETE FROM events WHERE seq = 1")
        except sqlite3.IntegrityError:
            blocked_delete = True
        led.close()
    _record("3 append-only enforcement", blocked_update and blocked_delete,
            f"update_blocked={blocked_update} delete_blocked={blocked_delete}")


def row_4_deterministic_replay() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = Ledger(Path(d) / "t.db")
        for i in range(4):
            led.append("MEMORY_CREATED", {"n": i}, actor="test", created_at="2026-01-01T00:00:00Z")
        a = led.verify_chain()
        b = led.verify_chain()
        h1 = [e.event_hash for e in led.events()]
        h2 = [e.event_hash for e in led.events()]
        led.close()
    _record("4 deterministic replay", a == b and h1 == h2, f"head={a.head_hash}")


def row_5_end_inclusive() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = Ledger(Path(d) / "t.db")
        for i in range(10):
            led.append("MEMORY_CREATED", {"n": i}, actor="test", created_at="2026-01-01T00:00:00Z")
        at5 = list(led.events(end=5))
        at10 = list(led.events(end=10))
        led.close()
    _record(
        "5 end-inclusive replay",
        len(at5) == 5 and len(at10) == 10 and at5[-1].seq == 5,
        f"end=5 -> {len(at5)} events, end=10 -> {len(at10)} events",
    )


def row_6_history_immutable() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = Ledger(Path(d) / "t.db")
        led.append("MEMORY_CREATED",
                   {"memory_id": "mem_1", "status": "ACTIVE"},
                   actor="test", created_at="2026-01-01T00:00:00Z")
        led.append("MEMORY_SUPERSEDED",
                   {"memory_id": "mem_1"},
                   actor="test", created_at="2026-01-02T00:00:00Z")
        early = list(led.events(end=1))[0].payload["status"]
        late = [e for e in led.events()][-1].event_type
        led.close()
    _record("6 history immutable", early == "ACTIVE" and late == "MEMORY_SUPERSEDED")


def row_17_authority_binding() -> None:
    try:
        report = binding_report()
        ok, detail = True, f"module={report['module']} serializer={report['serializer']}"
    except CanonicalAuthorityUnavailable as exc:
        ok, detail = False, str(exc)
    _record("17 canonical authority binding", ok, detail)


def row_18_non_finite() -> None:
    """Same bad input -> same failure id, and the serializer must refuse non-finite."""
    try:
        canonical_json({"x": float("nan")})
        _record("18 non-finite float", False, "serializer accepted NaN — canonicalization is unsafe")
    except Exception as exc:  # noqa: BLE001 — any refusal is correct here
        _record("18 non-finite float", True, f"refused by serializer: {type(exc).__name__}")


def main() -> int:
    print("memory_brain selfcheck")
    print("=" * 60)
    for fn in (
        row_1_chain_integrity,
        row_2_tamper_detection,
        row_3_append_only,
        row_4_deterministic_replay,
        row_5_end_inclusive,
        row_6_history_immutable,
        row_17_authority_binding,
        row_18_non_finite,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — a crashing row is a failed row
            _record(fn.__name__, False, f"raised {type(exc).__name__}: {exc}")

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print("=" * 60)
    print(f"OVERALL: {'PASS' if passed == total else 'FAIL'} ({passed}/{total})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
