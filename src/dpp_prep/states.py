"""Who may move a record, and when (R08).

v0.1 asked only:  role + current state            -> allowed?
v0.2 asks:        role + current state + conditions -> allowed?

The conditions (guards) are concentrated where authority is exercised:
approval and release. Approval re-verifies everything itself, so a record
that reached "reviewed" by an irregular path still cannot be approved.

Every attempt, allowed or refused, is written to the record's log (R09).
"""
from __future__ import annotations

from typing import Optional

from .checks import all_passed
from .models import Approval, Record, Role, State

S, R = State, Role
_CORRECTABLE = (S.CHECKED, S.FLAGGED, S.REVIEWED, S.APPROVED, S.UNRESOLVED)

ALLOWED: dict[tuple[State, State], set[Role]] = {
    (S.REQUIRED, S.PROPOSED): {R.AI, R.SYSTEM, R.REVIEWER},
    (S.REQUIRED, S.UNRESOLVED): {R.AI, R.SYSTEM},
    (S.PROPOSED, S.CHECKED): {R.SYSTEM},
    (S.PROPOSED, S.FLAGGED): {R.SYSTEM, R.REVIEWER},
    (S.CHECKED, S.REVIEWED): {R.REVIEWER},
    (S.CHECKED, S.FLAGGED): {R.SYSTEM, R.REVIEWER},
    (S.FLAGGED, S.REVIEWED): {R.REVIEWER},
    (S.REVIEWED, S.APPROVED): {R.APPROVER},
    (S.REVIEWED, S.FLAGGED): {R.REVIEWER, R.APPROVER},
    (S.APPROVED, S.RELEASED): {R.APPROVER},
    **{(s, S.PROPOSED): {R.REVIEWER} for s in _CORRECTABLE},   # corrections restart the flow
}


class TransitionRefused(Exception):
    pass


def _approval_problems(r: Record, actor_id: Optional[str]) -> list[str]:
    problems = []
    if not r.checks:
        problems.append("no check results recorded")
    elif r.checks_version != r.version:
        problems.append("checks were run on an earlier version")
    elif not all_passed(r.checks):
        failed = ", ".join(c.name for c in r.checks if not c.passed)
        problems.append(f"failed checks: {failed}")
    if not r.review:
        problems.append("no reviewer decision recorded")
    else:
        if not r.review.evidence_inspected:
            problems.append("reviewer did not confirm inspecting the evidence")
        if r.review.record_version != r.version:
            problems.append("review was made on an earlier version")
        sel = r.selected
        if sel is None:
            problems.append("selected proposal not found")
        elif not any(c.name == "support" and c.passed and c.proposal_id == sel.id for c in r.checks):
            problems.append("selected value has no passed support check")
        if actor_id is None:
            problems.append("approver not identified")
        elif actor_id == r.review.reviewer_id:
            problems.append("the same person may not review and approve")
    return problems


def _release_problems(r: Record) -> list[str]:
    problems = []
    if not r.approval:
        problems.append("no approval recorded")
    elif r.approval.record_version != r.version:
        problems.append("approval was given for an earlier version")
    if not all_passed(r.checks):
        problems.append("checks no longer pass")
    return problems


def guard(r: Record, target: State, role: Role, actor_id: Optional[str]) -> list[str]:
    if role not in ALLOWED.get((r.state, target), set()):
        return [f"{role.value} may not move {r.state.value} -> {target.value}"]
    if target == S.CHECKED and r.checks and not all_passed(r.checks):
        return ["checks did not all pass"]
    if target == S.APPROVED:
        return _approval_problems(r, actor_id)
    if target == S.RELEASED:
        return _release_problems(r)
    return []


def can_transition(r: Record, target: State, role: Role, actor_id: Optional[str] = None) -> bool:
    return not guard(r, target, role, actor_id)


def transition(r: Record, target: State, role: Role, detail: str = "",
               actor_id: Optional[str] = None) -> Record:
    problems = guard(r, target, role, actor_id)
    if problems:
        r.note(role, "refused", f"{r.state.value} -> {target.value}: " + "; ".join(problems), actor_id)
        raise TransitionRefused(f"{r.element_id}: " + "; ".join(problems))
    r.note(role, f"{r.state.value} -> {target.value}", detail, actor_id)
    if target == S.PROPOSED and r.state != S.REQUIRED:      # a correction: earlier decisions no longer hold
        r.checks, r.checks_version, r.review, r.approval = [], None, None, None
    if target == S.APPROVED:
        r.approval = Approval(approver_id=actor_id, record_version=r.version)
    r.state = target
    return r
