"""Contradiction detection — record, propose, STOP.

A contradiction is a RELATIONSHIP plus an EVENT, never a resolution. This module's job
ends at "here is what we found and what we would lean toward". Applying that lean is a
governance action and happens in `governance.py`, behind a human approval event.

Deliberately conservative on detection: a false positive a human dismisses costs a
review item; a false negative that silently corrupts the store costs the store.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Sequence

from .models import (
    CONTRADICTION_ALGORITHM_VERSION,
    PROVENANCE_STRENGTH,
    ContradictionOutcome,
    Memory,
)

__all__ = ["Contradiction", "detect", "evaluate_factors", "propose"]

#: Markers that flip an assertion's polarity. Conservative by design.
_NEGATIONS = ("not ", "n't ", "no ", "never ", "without ", "cannot ", "unable to ")
_DISJOINT_WORDS = ("increased", "decreased", "enabled", "disabled", "true", "false",
                   "yes", "no", "active", "inactive", "approved", "rejected")

#: Opposing modal / permission pairs. If one claim asserts the strong term and the other
#: the weak term over a shared subject, they are mutually exclusive.
#:   "the system MUST never X"  vs  "the system MAY X"
_MODAL_PAIRS = (
    ("must", "may"), ("must", "can"), ("shall", "may"), ("required", "optional"),
    ("always", "sometimes"), ("never", "always"), ("forbidden", "permitted"),
    ("forbidden", "allowed"), ("prohibited", "allowed"), ("cannot", "can"),
    ("disallowed", "allowed"), ("mandatory", "voluntary"),
)


@dataclass(frozen=True)
class Contradiction:
    a_id: str
    b_id: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "algorithm_version": CONTRADICTION_ALGORITHM_VERSION,
            "a": self.a_id,
            "b": self.b_id,
            "reason": self.reason,
            "detail": self.detail,
        }


def _negations_present(text: str) -> set[str]:
    """The negation markers present in a claim."""
    lowered = f" {text.casefold()} "
    return {m for m in _NEGATIONS if m in lowered}


def _has_word(text: str, word: str) -> bool:
    """Word-boundary match, so 'may' does not fire on 'maybe' and 'can' not on 'cannot'."""
    return re.search(rf"\b{re.escape(word)}\b", text.casefold()) is not None


def _keys(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return {w for w in words if len(w) > 3}


def detect(a: Memory, b: Memory, *, min_shared_keys: int = 2) -> Contradiction | None:
    """Return a Contradiction when a and b are mutually exclusive, else None.

    Every signal first requires shared subject matter, so unrelated memories never collide.

      * ASYMMETRIC NEGATION — a negation marker present in one claim and absent from the
        other. Markers COMMON to both are ignored: two claims that both say "without
        approval" agree on that much, and treating the shared marker as the signal is
        exactly how a real conflict ("must never" vs "may") gets missed.
      * OPPOSING MODALS — one side asserts the strong term (must/shall/required) and the
        other the weak term (may/can/optional) over the same subject.
      * MUTUALLY EXCLUSIVE PREDICATES — straight antonym pairs (enabled/disabled, …).

    Deliberately permissive: a false positive costs one review item a human dismisses,
    while a false negative silently leaves a corrupt store looking settled.
    """
    keys_a, keys_b = _keys(a.claim), _keys(b.claim)
    shared = keys_a & keys_b
    if len(shared) < min_shared_keys:
        return None

    neg_a = _negations_present(a.claim)
    neg_b = _negations_present(b.claim)
    only_a, only_b = neg_a - neg_b, neg_b - neg_a
    if bool(only_a) != bool(only_b):
        present = only_a or only_b
        return Contradiction(
            a.memory_id, b.memory_id,
            reason="asymmetric negation over shared subject",
            detail={"shared_keys": sorted(shared), "markers": sorted(present)},
        )

    for strong, weak in _MODAL_PAIRS:
        # `weak` must not be a substring-shadow of `strong` (can vs cannot are distinct
        # words and legitimately oppose each other; both are handled as explicit pairs).
        if (_has_word(a.claim, strong) and _has_word(b.claim, weak)) or (
            _has_word(b.claim, strong) and _has_word(a.claim, weak)
        ):
            return Contradiction(
                a.memory_id, b.memory_id,
                reason="opposing modals over shared subject",
                detail={"strong": strong, "weak": weak, "shared_keys": sorted(shared)},
            )

    for i, term in enumerate(_DISJOINT_WORDS):
        for other in _DISJOINT_WORDS[i + 1:]:
            if (_has_word(a.claim, term) and _has_word(b.claim, other)) or (
                _has_word(b.claim, term) and _has_word(a.claim, other)
            ):
                return Contradiction(
                    a.memory_id, b.memory_id,
                    reason="mutually exclusive predicates over shared subject",
                    detail={"a_term": term, "b_term": other, "shared_keys": sorted(shared)},
                )
    return None


def evaluate_factors(
    a: Memory,
    b: Memory,
    *,
    source_authority: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Compare recency, provenance strength, confidence, and source authority.

    All four are returned separately; the proposal below is a *recommendation* built from
    them, never a decision.
    """
    authority = source_authority or {}
    recency_winner = a.memory_id if a.created_seq > b.created_seq else (
        b.memory_id if b.created_seq > a.created_seq else "TIE"
    )
    prov_a = PROVENANCE_STRENGTH.get(a.provenance_class.value, 0)
    prov_b = PROVENANCE_STRENGTH.get(b.provenance_class.value, 0)
    prov_winner = a.memory_id if prov_a > prov_b else (b.memory_id if prov_b > prov_a else "TIE")
    conf_winner = (
        a.memory_id if a.confidence.current > b.confidence.current
        else b.memory_id if b.confidence.current > a.confidence.current else "TIE"
    )
    auth_a = authority.get(a.source_id, 0)
    auth_b = authority.get(b.source_id, 0)
    auth_winner = a.memory_id if auth_a > auth_b else (b.memory_id if auth_b > auth_a else "TIE")

    return {
        "recency": {"winner": recency_winner, "a_seq": a.created_seq, "b_seq": b.created_seq},
        "provenance": {
            "winner": prov_winner,
            "a": a.provenance_class.value, "a_strength": prov_a,
            "b": b.provenance_class.value, "b_strength": prov_b,
        },
        "confidence": {
            "winner": conf_winner,
            "a": a.confidence.as_dict(), "b": b.confidence.as_dict(),
        },
        "source_authority": {"winner": auth_winner, "a": auth_a, "b": auth_b},
    }


def propose(a: Memory, b: Memory, factors: dict[str, Any]) -> dict[str, Any]:
    """Turn factor evaluations into a proposal with its rationale.

    When the factors conflict or are close, this returns UNRESOLVED — the honest answer,
    and a first-class outcome, not a failure to decide.
    """
    winners = [
        factors["recency"]["winner"],
        factors["provenance"]["winner"],
        factors["confidence"]["winner"],
        factors["source_authority"]["winner"],
    ]
    decisive = [w for w in winners if w != "TIE"]

    for candidate in (a.memory_id, b.memory_id):
        votes = sum(1 for w in decisive if w == candidate)
        # Require a clear majority of decisive factors; a 1-vote margin is "close".
        if votes >= 3 and votes > len(decisive) - votes:
            outcome = (
                ContradictionOutcome.PREFER_A if candidate == a.memory_id
                else ContradictionOutcome.PREFER_B
            )
            return {
                "preferred": candidate,
                "outcome": outcome.value,
                "rationale": f"{votes} of {len(decisive)} decisive factors favour {candidate}",
                "factors": factors,
                "requires_approval": True,
            }

    return {
        "preferred": None,
        "outcome": ContradictionOutcome.UNRESOLVED.value,
        "rationale": "factors conflict or are close; no safe preference",
        "factors": factors,
        "requires_approval": True,
    }
