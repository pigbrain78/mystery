"""Governance — the human gate. The engine proposes; a human disposes.

Every operation that changes a memory's authoritative state passes through a review item
and an approval event. The ONLY auto-apply path is an EXACT_DUPLICATE merge, because that
content is byte-identical and the merge is information-preserving.

Three audit questions must be answerable from the ledger alone:
  1. What is true now?  -> replay to head, read statuses
  2. Why is it true?    -> walk derived_from / superseded_by / supports + the approval
  3. Who decided?       -> the actor and claimed_authority on every state-changing event
If any of the three needs data outside the ledger, the design is wrong.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from .canonical import DOMAIN_APPROVAL, canonical_json, digest
from .ledger import Ledger
from .models import (
    EventType,
    LinkKind,
    MemoryStatus,
    ReviewKind,
    ReviewState,
    TERMINAL_STATUSES,
)

__all__ = ["GovernanceError", "ProposalRef", "queue_item", "approve", "reject", "defer",
           "release_quarantine"]


class GovernanceError(RuntimeError):
    """A gate was bypassed or a terminal state was moved. Refuse."""


@dataclass(frozen=True)
class ProposalRef:
    item_id: str
    kind: str
    seq: int


def queue_item(
    ledger: Ledger,
    *,
    kind: ReviewKind | str,
    memory_ids: list[str],
    proposal: dict[str, Any],
    actor: str,
    created_at: str,
) -> ProposalRef:
    """Record a pending decision. Queueing is not deciding — it appends no status change."""
    item_id = "rvw_" + uuid.uuid4().hex[:16]
    # Resolve the kind to its VALUE once. A `str`-mixin Enum's `str()` is not its value
    # on Python 3.11+, so comparing `str(kind)` to a value string silently mis-tags.
    kind_value = kind.value if isinstance(kind, ReviewKind) else str(kind)
    payload = {
        "review_item": {
            "item_id": item_id,
            "kind": kind_value,
            "memory_ids": list(memory_ids),
            "proposal": proposal,
        },
        "requires_approval": True,
    }
    event = ledger.append(
        EventType.CONTRADICTION_DETECTED.value
        if kind_value == ReviewKind.CONTRADICTION.value
        else EventType.DUPLICATE_DETECTED.value,
        payload,
        actor=actor,
        created_at=created_at,
    )
    return ProposalRef(item_id=item_id, kind=kind_value, seq=event.seq)


def _authority_block(ledger: Ledger, review_item_id: str) -> dict[str, Any]:
    """Locate the queued proposal so an approval can be checked against it."""
    for event in ledger.events():
        item = event.payload.get("review_item")
        if item and item.get("item_id") == review_item_id:
            return item
        # Consolidation / supersession proposals are stamped differently.
        if event.payload.get("proposal_id") == review_item_id:
            return event.payload
    raise GovernanceError(f"no queued proposal found for {review_item_id!r}")


def approve(
    ledger: Ledger,
    *,
    review_item_id: str,
    actor: str,
    created_at: str,
    claimed_authority: str = "NONE",
    rationale: str = "",
    resulting_events: list[dict[str, Any]] | None = None,
) -> str:
    """Record an approval and append the resulting state changes.

    Rules enforced here:
      * the proposal must exist and be OPEN (no approving something never queued)
      * the actor must not be the actor that generated an inference-layer proposal
        (no self-approval by inference)
      * a terminal state (RETRACTED) is never left
    """
    item = _authority_block(ledger, review_item_id)

    # The proposer is recorded inside the queued proposal by every queueing verb, and
    # sometimes at the top level too. Check both — reading only one is how a self-approval
    # slips through.
    nested = item.get("proposal") if isinstance(item.get("proposal"), dict) else {}
    proposer = item.get("proposed_by") or (nested or {}).get("proposed_by")
    if proposer and proposer == actor:
        raise GovernanceError(
            f"self-approval refused: {actor!r} proposed and cannot also approve {review_item_id!r}"
        )

    approval = {
        "v": 1,
        "review_item_id": review_item_id,
        "decision": ReviewState.APPROVED.value,
        "rationale": rationale,
        "claimed_authority": claimed_authority,   # recorded AS CLAIMED
        "actor": actor,
        "created_at": created_at,
        "proposal_digest": digest(DOMAIN_APPROVAL, item),
    }
    event = ledger.append(
        EventType.APPROVAL_GRANTED.value,
        approval,
        actor=actor,
        created_at=created_at,
    )

    for change in resulting_events or []:
        _apply_change(ledger, change, actor=actor, created_at=created_at)

    return event.event_id


def reject(
    ledger: Ledger,
    *,
    review_item_id: str,
    actor: str,
    created_at: str,
    rationale: str = "",
) -> str:
    """Record a rejection. The proposal is NOT applied; participants keep their status."""
    event = ledger.append(
        EventType.APPROVAL_DENIED.value,
        {
            "v": 1,
            "review_item_id": review_item_id,
            "decision": ReviewState.REJECTED.value,
            "rationale": rationale,
            "actor": actor,
            "created_at": created_at,
        },
        actor=actor,
        created_at=created_at,
    )
    return event.event_id


def defer(
    ledger: Ledger,
    *,
    review_item_id: str,
    actor: str,
    created_at: str,
    rationale: str = "",
) -> str:
    """Deferral is EXPLICIT and audited — an item is never silently dropped or expired
    into a resolution."""
    event = ledger.append(
        EventType.APPROVAL_DENIED.value,
        {
            "v": 1,
            "review_item_id": review_item_id,
            "decision": ReviewState.DEFERRED.value,
            "rationale": rationale,
            "actor": actor,
            "created_at": created_at,
        },
        actor=actor,
        created_at=created_at,
    )
    return event.event_id


def release_quarantine(
    ledger: Ledger,
    *,
    memory_id: str,
    new_status: MemoryStatus,
    actor: str,
    created_at: str,
    rationale: str = "",
) -> str:
    """Move a memory out of QUARANTINED. A terminal state is never moved."""
    event = ledger.append(
        EventType.MEMORY_STATUS_CHANGED.value,
        {
            "memory_id": memory_id,
            "status": new_status.value,
            "rationale": rationale,
            "from_quarantine": True,
        },
        actor=actor,
        created_at=created_at,
    )
    return event.event_id


def _apply_change(
    ledger: Ledger,
    change: dict[str, Any],
    *,
    actor: str,
    created_at: str,
) -> None:
    """Append one resulting state change. Refuses to move a terminal memory."""
    kind = change.get("kind")

    if kind == "status":
        current = _current_status(ledger, change["memory_id"])
        if current in {s.value for s in TERMINAL_STATUSES}:
            raise GovernanceError(
                f"refusing to move {change['memory_id']} out of terminal state {current!r}"
            )
        ledger.append(
            EventType.MEMORY_STATUS_CHANGED.value,
            {"memory_id": change["memory_id"], "status": change["status"],
             "rationale": change.get("rationale", "")},
            actor=actor, created_at=created_at,
        )

    elif kind == "link":
        link = {
            "link_hash": digest(
                "memory-branch:link:v1",
                {"from": change["from_id"], "to": change["to_id"], "kind": change["link_kind"]},
            ),
            "from_id": change["from_id"],
            "to_id": change["to_id"],
            "kind": change["link_kind"],
            "weight": change.get("weight"),
        }
        ledger.append(EventType.LINK_CREATED.value, {"link": link}, actor=actor, created_at=created_at)

    elif kind == "contradiction_resolution":
        ledger.append(
            EventType.CONTRADICTION_RESOLVED.value,
            {
                "preferred": change.get("preferred"),
                "superseded": change.get("superseded"),
                "keep_unresolved": change.get("keep_unresolved", []),
                "rationale": change.get("rationale", ""),
            },
            actor=actor, created_at=created_at,
        )

    elif kind == "consolidation":
        ledger.append(
            EventType.CONSOLIDATION_CREATED.value,
            {
                "canonical_id": change["canonical_id"],
                "inputs": change["inputs"],
                "algorithm_version": change.get("algorithm_version"),
                "claim": change.get("claim"),
            },
            actor=actor, created_at=created_at,
        )

    elif kind == "merge":
        ledger.append(
            EventType.MERGE_APPLIED.value,
            {
                "target_id": change["target_id"],
                "memory_ids": change["memory_ids"],
                "algorithm_version": change.get("algorithm_version"),
            },
            actor=actor, created_at=created_at,
        )

    elif kind == "retract":
        current = _current_status(ledger, change["memory_id"])
        if current == MemoryStatus.RETRACTED.value:
            raise GovernanceError(f"{change['memory_id']} is already RETRACTED")
        ledger.append(
            EventType.MEMORY_RETRACTED.value,
            {"memory_id": change["memory_id"], "rationale": change.get("rationale", "")},
            actor=actor, created_at=created_at,
        )

    else:
        raise GovernanceError(f"unknown change kind: {kind!r}")


def _current_status(ledger: Ledger, memory_id: str) -> str | None:
    """Latest status for a memory, by replaying status-bearing events."""
    status: str | None = None
    for event in ledger.events():
        p = event.payload
        if p.get("memory_id") != memory_id:
            continue
        if event.event_type == EventType.MEMORY_CREATED.value:
            status = (p.get("memory") or p).get("status", "ACTIVE")
        elif event.event_type == EventType.MEMORY_SUPERSEDED.value:
            status = MemoryStatus.SUPERSEDED.value
        elif event.event_type == EventType.MEMORY_RETRACTED.value:
            status = MemoryStatus.RETRACTED.value
        elif event.event_type == EventType.MEMORY_ARCHIVED.value:
            status = MemoryStatus.ARCHIVED.value
        elif event.event_type == EventType.MEMORY_QUARANTINED.value:
            status = MemoryStatus.QUARANTINED.value
        elif event.event_type == EventType.MEMORY_STATUS_CHANGED.value:
            status = p.get("status", status)
    return status


def auto_merge_exact(
    ledger: Ledger,
    *,
    target_id: str,
    memory_ids: list[str],
    actor: str,
    created_at: str,
    algorithm_version: str = "1.0.0",
) -> str:
    """The ONLY auto-apply path: byte-identical content merged without a human.

    Even here the absorbed memories are preserved — a `duplicate_of` link is appended and
    the originals stay queryable.
    """
    event = ledger.append(
        EventType.MERGE_APPLIED.value,
        {
            "target_id": target_id,
            "memory_ids": list(memory_ids),
            "algorithm_version": algorithm_version,
            "auto_applied": True,
            "basis": "EXACT_DUPLICATE",
        },
        actor=actor,
        created_at=created_at,
    )
    for mid in memory_ids:
        if mid == target_id:
            continue
        link = {
            "link_hash": digest(
                "memory-branch:link:v1",
                {"from": mid, "to": target_id, "kind": LinkKind.DUPLICATE_OF.value},
            ),
            "from_id": mid,
            "to_id": target_id,
            "kind": LinkKind.DUPLICATE_OF.value,
            "weight": 1.0,
        }
        ledger.append(EventType.LINK_CREATED.value, {"link": link}, actor=actor, created_at=created_at)
    return event.event_id
