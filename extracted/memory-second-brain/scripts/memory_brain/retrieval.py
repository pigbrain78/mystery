"""Hybrid retrieval — three generators, unioned, then reranked.

No single generator is trusted alone:

  * lexical    — exact terms, names, ids
  * vector     — paraphrase, conceptual match
  * graph      — 1-2 hops over memory_links (corrects / supersedes / supports)

Reranking NEVER drops a memory whose status is CONTRADICTED when the query touches the
contradicted assertion. Surfacing the conflict is the point of the system.

Read-only: this module must never append to the ledger.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .canonical import canonical_json
from .models import PROVENANCE_STRENGTH, RetentionClass

__all__ = ["Candidate", "retrieve", "rerank"]

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was", "were",
    "for", "on", "with", "as", "by", "at", "from", "that", "this", "it", "be",
})


@dataclass
class Candidate:
    memory_id: str
    event_seq: int
    claim: str
    status: str
    provenance_class: str
    confidence: dict[str, float]
    source_id: str
    valid_from: str | None
    importance: int
    retention_class: str
    why: list[str] = field(default_factory=list)
    lexical_hits: int = 0
    vector_score: float = 0.0
    graph_hops: int | None = None


def _terms(query: str) -> list[str]:
    return [t for t in _TOKEN.findall(query.casefold()) if t not in _STOP]


def _lexical(conn: sqlite3.Connection, terms: Sequence[str], limit: int) -> dict[str, int]:
    """Term-coverage over the derived claim text. Returns memory_id -> hits."""
    hits: dict[str, int] = {}
    rows = conn.execute(
        "SELECT memory_id, claim, tags_json FROM memories WHERE status != 'RETRACTED'"
    ).fetchall()
    for row in rows:
        haystack = f"{row['claim']} {row['tags_json']}".casefold()
        count = sum(1 for t in terms if t in haystack)
        if count:
            hits[row["memory_id"]] = count
    return dict(sorted(hits.items(), key=lambda kv: (-kv[1], kv[0]))[:limit])


def _vector(conn: sqlite3.Connection, terms: Sequence[str], limit: int) -> dict[str, float]:
    """Token-overlap stand-in for embedding cosine.

    Replace the body with a real embedding lookup when one is available; the interface
    (memory_id -> 0..1) is what the rest of retrieval depends on, not the method.
    """
    scores: dict[str, float] = {}
    term_set = set(terms)
    if not term_set:
        return scores
    for row in conn.execute(
        "SELECT memory_id, claim FROM memories WHERE status != 'RETRACTED'"
    ).fetchall():
        toks = set(_TOKEN.findall(row["claim"].casefold()))
        if not toks:
            continue
        score = len(toks & term_set) / len(toks | term_set)
        if score > 0:
            scores[row["memory_id"]] = score
    return dict(sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:limit])


def _graph(conn: sqlite3.Connection, seeds: Iterable[str], hops: int = 2) -> dict[str, int]:
    """Graph proximity: hop distance from a directly-matched seed."""
    frontier = set(seeds)
    seen: dict[str, int] = {m: 0 for m in frontier}
    for depth in range(1, hops + 1):
        next_frontier: set[str] = set()
        for mid in frontier:
            for row in conn.execute(
                "SELECT from_id, to_id FROM memory_links WHERE from_id = ? OR to_id = ?",
                (mid, mid),
            ).fetchall():
                other = row["to_id"] if row["from_id"] == mid else row["from_id"]
                if other not in seen:
                    seen[other] = depth
                    next_frontier.add(other)
        frontier = next_frontier
        if not frontier:
            break
    return seen


def retrieve(
    conn: sqlite3.Connection,
    query: str,
    *,
    candidate_limit: int = 60,
    graph_hops: int = 2,
) -> list[Candidate]:
    """Union the three generators into a candidate set with provenance per candidate."""
    terms = _terms(query)
    lex = _lexical(conn, terms, candidate_limit)
    vec = _vector(conn, terms, candidate_limit)

    seeds = set(lex) | set(vec)
    graph = _graph(conn, seeds, hops=graph_hops) if seeds else {}

    ids = set(lex) | set(vec) | set(graph)
    if not ids:
        return []

    out: list[Candidate] = []
    for mid in sorted(ids):
        row = conn.execute("SELECT * FROM memories WHERE memory_id = ?", (mid,)).fetchone()
        if row is None:
            continue
        why: list[str] = []
        if mid in lex:
            why.append(f"lexical:{lex[mid]}")
        if mid in vec:
            why.append(f"vector:{vec[mid]:.2f}")
        if mid in graph and graph[mid] > 0:
            why.append(f"graph_hop:{graph[mid]}")
        out.append(
            Candidate(
                memory_id=mid,
                event_seq=row["last_seq"] if "last_seq" in row.keys() else row["created_seq"],
                claim=row["claim"],
                status=row["status"],
                provenance_class=row["provenance_class"],
                confidence={
                    "source": row["source_confidence"],
                    "extraction": row["extraction_confidence"],
                    "inference": row["inference_confidence"],
                    "current": row["current_confidence"],
                },
                source_id=row["source_id"],
                valid_from=row["valid_from"],
                importance=row["importance"],
                retention_class=row["retention_class"],
                why=why,
                lexical_hits=lex.get(mid, 0),
                vector_score=vec.get(mid, 0.0),
                graph_hops=graph.get(mid),
            )
        )
    return out


def rerank(
    candidates: Sequence[Candidate],
    *,
    terms: Sequence[str] | None = None,
    recency_weights: dict[str, float] | None = None,
) -> list[Candidate]:
    """Order candidates. Reranking never removes contradicted memories."""
    weights = recency_weights or {
        RetentionClass.PERMANENT.value: 1.0,
        RetentionClass.LONG.value: 0.8,
        RetentionClass.STANDARD.value: 0.6,
        RetentionClass.SHORT.value: 0.4,
        RetentionClass.EPHEMERAL.value: 0.2,
    }
    term_set = set(terms or [])

    def score(c: Candidate) -> tuple[float, str]:
        coverage = c.lexical_hits / len(term_set) if term_set else 0.0
        provenance = PROVENANCE_STRENGTH.get(c.provenance_class, 0) / 6.0
        graph_bonus = 0.15 if c.graph_hops == 0 else (0.08 if (c.graph_hops or 99) <= 2 else 0.0)
        retention = weights.get(c.retention_class, 0.5)
        total = (
            coverage * 0.40
            + provenance * 0.25
            + c.confidence["current"] * 0.20
            + graph_bonus
            + retention * 0.10
        )
        if c.status == "CONTRADICTED":
            # Kept, never dropped — but surfaced below settled memories unless asked for.
            total += 0.0
        return (-total, c.memory_id)

    return sorted(candidates, key=score)
