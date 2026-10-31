"""Context Package assembly — the shared contract handed to consuming agents.

Rules that make this checkable rather than aspirational:

  * Every item cites memory_id AND event_seq. An item missing either is a bug.
  * The four-part confidence breakdown travels WHOLE. A consumer may not receive a
    single collapsed number.
  * `conflicts` is non-optional. If a relevant assertion is contested, the package says
    so even when the caller never asked.
  * `truncated: true` must be visible — a silently truncated package reads as "this is
    all there is", the most dangerous failure mode in retrieval.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .canonical import DOMAIN_CONTENT, digest
from .models import ContextItem, ContextPackage
from .retrieval import Candidate

__all__ = ["build_package"]


def _conflicts_for(conn: sqlite3.Connection, ids: list[str]) -> list[dict[str, Any]]:
    """Surface every contradiction touching the retrieved set, resolved or not.

    A conflict is reported even when both sides are absent from `items` — the caller
    needs to know the assertion is contested.
    """
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT from_id, to_id, created_seq FROM memory_links"
        f" WHERE kind = 'contradicts'"
        f" AND (from_id IN ({placeholders}) OR to_id IN ({placeholders}))",
        (*ids, *ids),
    ).fetchall()

    conflicts: list[dict[str, Any]] = []
    for row in rows:
        a, b = row["from_id"], row["to_id"]
        a_row = conn.execute(
            "SELECT status, current_confidence, provenance_class, created_seq"
            " FROM memories WHERE memory_id = ?", (a,)
        ).fetchone()
        b_row = conn.execute(
            "SELECT status, current_confidence, provenance_class, created_seq"
            " FROM memories WHERE memory_id = ?", (b,)
        ).fetchone()

        # State derives from the actual statuses, not from the fact a link exists.
        if a_row and b_row and {a_row["status"], b_row["status"]} == {"ACTIVE", "SUPERSEDED"}:
            state = "RESOLVED"
            preferred = a if a_row["status"] == "ACTIVE" else b
        elif a_row and b_row and a_row["status"] == "CONTRADICTED" and b_row["status"] == "CONTRADICTED":
            state = "UNRESOLVED"
            preferred = None
        else:
            state = "UNRESOLVED"
            preferred = None

        proposal: dict[str, Any] = {"preferred": preferred}
        if preferred is None:
            proposal["rationale"] = "awaiting human resolution"
        else:
            proposal["rationale"] = "recorded approval resolved this pair"

        conflicts.append(
            {
                "a": a,
                "b": b,
                "state": state,
                "proposal": proposal,
                "open_review": conn.execute(
                    "SELECT item_id FROM review_queue WHERE kind = 'CONTRADICTION'"
                    " AND state = 'OPEN' AND memory_ids LIKE ?",
                    (f"%{a}%",),
                ).fetchone() is not None,
            }
        )
    return conflicts


def build_package(
    conn: sqlite3.Connection,
    query: str,
    candidates: list[Candidate],
    *,
    generated_at: str,
    limit: int = 12,
    min_confidence: float = 0.0,
    include_contradicted: bool = True,
) -> ContextPackage:
    """Assemble the Context Package. Pure given (query, candidates, generated_at)."""
    total_matched = len(candidates)

    eligible = [
        c for c in candidates
        if c.confidence["current"] >= min_confidence
        and (include_contradicted or c.status != "CONTRADICTED")
    ]
    selected = eligible[:limit]
    truncated = len(eligible) > len(selected)

    items = tuple(
        ContextItem(
            memory_id=c.memory_id,
            event_seq=c.event_seq,
            claim=c.claim,
            status=c.status,
            provenance_class=c.provenance_class,
            confidence=dict(c.confidence),
            valid_from=c.valid_from,
            source_id=c.source_id,
            why_included="; ".join(c.why) or "matched filter",
        )
        for c in selected
    )

    # Conflicts are computed over the WHOLE matched set, not just the returned page —
    # a conflict on a truncated-away item still matters.
    conflicts = tuple(_conflicts_for(conn, [c.memory_id for c in eligible]))

    unresolved = sum(1 for c in conflicts if c["state"] == "UNRESOLVED")
    package_id = "ctx_" + digest(
        DOMAIN_CONTENT,
        {"query": query, "ids": [i.memory_id for i in items], "at": generated_at},
    )[:16]

    return ContextPackage(
        package_id=package_id,
        query=query,
        generated_at=generated_at,
        policy={
            "max_items": limit,
            "min_confidence": min_confidence,
            "include_contradicted": include_contradicted,
        },
        items=items,
        conflicts=conflicts,
        coverage={
            "matched": total_matched,
            "eligible": len(eligible),
            "returned": len(items),
            "unresolved_conflicts": unresolved,
        },
        truncated=truncated,
    )
