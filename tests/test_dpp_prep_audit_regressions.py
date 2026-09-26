"""Supplemental regression tests for v0.1 audit.
Place this file in dpp-prep/tests/.  These tests are EXPECTED TO FAIL on
v0.1.  They document previously undetected safeguards to implement.
"""
from pathlib import Path
import pytest
from dpp_prep.checks import run_checks
from dpp_prep.export import build_export
from dpp_prep.extract import keep_grounded
from dpp_prep.models import Evidence, Proposal, Record, Role, State
from dpp_prep.profile import load_profile
from dpp_prep.states import TransitionRefused, transition
ROOT = Path(__file__).resolve().parents[1]
PRODUCT, DEFS = load_profile(ROOT / "config" / "elements_w100.yaml")
def test_regression_01_quote_must_support_proposed_value():
    """A real quote must not certify an unrelated/invented numerical value."""
    name = "D1_datasheet.md"
    text = (ROOT / "data/w100/baseline" / name).read_text(encoding="utf-8")
    proposal = Proposal(
        element_id="E06", value="9.9", unit="W/(m2K)",
        product_id="W-100", scope="1230 x 1480 mm",
        evidence=Evidence(
            source=name,
            quote="Uw = 1.1 W/(m2K) for reference size 1230 x 1480 mm.",
        ),
    )
    kept, _ = keep_grounded([proposal], {name: text})
    if kept:
        checks = run_checks(DEFS["E06"], kept, PRODUCT["id"], "1230 x 1480 mm")
        assert not all(check.passed for check in checks), (
            "Wrong value 9.9 was accepted using a genuine quote that says 1.1"
        )
def test_regression_02_failed_checks_block_approval_even_after_review():
    """Review must not silently override failed deterministic checks."""
    text = (ROOT / "data/w100/variants/V5_D2_composition_95.md").read_text(encoding="utf-8")
    proposal = Proposal(
        element_id="E03", value="Pine wood 73 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 %.",
        unit="%", product_id="W-100",
        evidence=Evidence(source="V5_D2_composition_95.md", quote="Pine wood 73 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 %."),
    )
    r = Record(element_id="E03", proposals=[proposal])
    transition(r, State.PROPOSED, Role.AI)
    r.checks = run_checks(DEFS["E03"], [proposal], PRODUCT["id"])
    assert any(not check.passed for check in r.checks)
    transition(r, State.FLAGGED, Role.SYSTEM)
    transition(r, State.REVIEWED, Role.REVIEWER)
    with pytest.raises(TransitionRefused):
        transition(r, State.APPROVED, Role.APPROVER)
    assert not build_export(PRODUCT["id"], [r]).elements
def test_regression_03_checks_and_review_event_must_precede_approval():
    """Permitted role and state alone do not demonstrate checks or review."""
    proposal = Proposal(
        element_id="E06", value="1.1", unit="W/(m2K)", product_id="W-100",
        scope="1230 x 1480 mm", evidence=Evidence(source="D1_datasheet.md", quote="Uw = 1.1"),
    )
    r = Record(element_id="E06", proposals=[proposal])
    transition(r, State.PROPOSED, Role.AI)
    transition(r, State.CHECKED, Role.SYSTEM)  # no checks have been run
    transition(r, State.REVIEWED, Role.REVIEWER)  # no evidence inspection logged
    with pytest.raises(TransitionRefused):
        transition(r, State.APPROVED, Role.APPROVER)
