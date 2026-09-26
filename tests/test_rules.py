"""Rule-layer tests: each approval guard on its own.

The service refuses many bad actions early, so its tests never reach the
rules underneath. These tests start from a record that meets every approval
condition, remove exactly one condition, and call the rules directly. This
proves each guard works even if the layer above it were bypassed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from dpp_prep.extract import StandInExtractor
from dpp_prep.models import Actor, Role, State
from dpp_prep.service import PreparationService
from dpp_prep.states import TransitionRefused, can_transition, transition

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ready():
    """An E06 record that meets every approval condition."""
    svc = PreparationService(ROOT / "config/elements_w100.yaml",
                             StandInExtractor(ROOT / "config/standin_patterns_w100.yaml"))
    svc.start_run(list((ROOT / "data/w100/baseline").glob("*.md"))
                  + [ROOT / "data/w100/structured/erp_product_record.json"])
    svc.prepare_product()
    r = svc.records["E06"]
    svc.review("E06", Actor(id="rita", role=Role.REVIEWER), r.proposals[0].id, evidence_inspected=True)
    assert can_transition(r, State.APPROVED, Role.APPROVER, "aki")
    return r


def test_rule_ai_cannot_approve_even_when_everything_else_is_valid(ready):
    with pytest.raises(TransitionRefused):
        transition(ready, State.APPROVED, Role.AI, actor_id="bot")


def test_rule_failed_check_on_current_version_blocks_approval(ready):
    next(c for c in ready.checks if c.name == "identity").passed = False
    with pytest.raises(TransitionRefused, match="failed checks"):
        transition(ready, State.APPROVED, Role.APPROVER, actor_id="aki")


def test_rule_missing_review_blocks_approval(ready):
    ready.review = None
    with pytest.raises(TransitionRefused, match="no reviewer decision"):
        transition(ready, State.APPROVED, Role.APPROVER, actor_id="aki")


def test_rule_unidentified_approver_is_refused(ready):
    with pytest.raises(TransitionRefused, match="not identified"):
        transition(ready, State.APPROVED, Role.APPROVER)
