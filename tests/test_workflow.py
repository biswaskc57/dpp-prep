"""Evaluation tests for W-100, run through the single workflow (service layer).
Expected outcomes are listed in data/w100/expected_outcomes.yaml.

The StandInExtractor is a deterministic stand-in for the AI step, used so the
controls can be tested before the AI model is connected. HallucinatingExtractor
and OverconfidentExtractor deliberately behave badly, to test that the controls
catch them.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from dpp_prep.audit import AuditStore
from dpp_prep.extract import StandInExtractor
from dpp_prep.models import Actor, Evidence, Method, Proposal, Role, State
from dpp_prep.service import ActionRefused, PreparationService
from dpp_prep.states import TransitionRefused

ROOT = Path(__file__).resolve().parents[1]
BASE, VAR = ROOT / "data/w100/baseline", ROOT / "data/w100/variants"
ERP = ROOT / "data/w100/structured/erp_product_record.json"
PROFILE = ROOT / "config/elements_w100.yaml"
PATTERNS = ROOT / "config/standin_patterns_w100.yaml"

RITA = Actor(id="rita", role=Role.REVIEWER)        # reviewer
AKI = Actor(id="aki", role=Role.APPROVER)          # approver
RITA_AS_APPROVER = Actor(id="rita", role=Role.APPROVER)


def sources(**swap):
    """Baseline documents plus the ERP record; name=variant swaps one document."""
    docs = {p.stem: p for p in BASE.glob("*.md")}
    for original, variant in swap.items():
        docs[original] = VAR / f"{variant}.md"
    return list(docs.values()) + [ERP]


def run(extractor=None, audit=None, **swap) -> PreparationService:
    svc = PreparationService(PROFILE, extractor or StandInExtractor(PATTERNS), audit=audit)
    svc.start_run(sources(**swap))
    svc.prepare_product()
    return svc


def approve_all_checked(svc):
    for eid, r in svc.records.items():
        if r.state == State.CHECKED:
            svc.review(eid, RITA, r.proposals[0].id, evidence_inspected=True)
            svc.approve(eid, AKI)


class HallucinatingExtractor:
    """Invents a plausible Uw with a quote that is not in the document."""
    name = "hallucinating-test-extractor"

    def propose(self, d, doc):
        if d.id != "E06":
            return []
        return [Proposal(element_id="E06", value="1.1", unit="W/(m2K)", scope="1230 x 1480 mm",
                         product_id="W-100", produced_by=self.name,
                         evidence=Evidence(source=doc.name, quote="Uw = 1.1 W/(m2K) typical value"))]


class OverconfidentExtractor:
    """Uses a real quote about Ug (glazing only) to claim a Uw value."""
    name = "overconfident-test-extractor"

    def propose(self, d, doc):
        if d.id != "E06" or "Ug = 0.5" not in doc.text:
            return []
        line = next(l for l in doc.text.splitlines() if l.startswith("Ug = 0.5"))
        return [Proposal(element_id="E06", value="0.5", unit="W/(m2K)", scope="1230 x 1480 mm",
                         product_id="W-100", produced_by=self.name,
                         evidence=Evidence(source=doc.name, quote=line))]


# ------------------------------------------------------------------ T01 baseline

def test_T01_all_seven_elements_checked_on_baseline():
    svc = run()
    assert {e: r.state for e, r in svc.records.items()} == {e: State.CHECKED for e in svc.defs}
    for r in svc.records.values():
        for p in r.proposals:
            assert p.evidence.doc_sha256 and len(p.evidence.doc_sha256) == 64


def test_T01b_import_route_uses_no_ai():
    svc = run()
    for eid in ("E01", "E02", "E05"):
        assert all(p.method == Method.IMPORT for p in svc.records[eid].proposals)
    for eid in ("E03", "E04", "E06", "E07"):
        assert all(p.method == Method.AI for p in svc.records[eid].proposals)

# ------------------------------------------------------------------ missing and invented values

def test_T02_missing_value_stays_unresolved():
    svc = run(D1_datasheet="V1_D1_uw_missing", D3_performance_report="V1_D3_uw_missing")
    assert svc.records["E06"].state == State.UNRESOLVED


def test_T02b_invented_value_is_dropped_and_kept_in_the_diary():
    svc = run(HallucinatingExtractor(), D1_datasheet="V1_D1_uw_missing",
              D3_performance_report="V1_D3_uw_missing")
    r = svc.records["E06"]
    assert r.state == State.UNRESOLVED
    assert r.rejected, "the invented proposal must be kept, not deleted"
    events = svc.audit.events(svc.run_id, "E06")
    assert any(e["action"] == "dropped unsupported proposal" for e in events)


def test_T11_real_quote_about_the_wrong_attribute_does_not_support_value():
    svc = run(OverconfidentExtractor(), D1_datasheet="V6_D1_ug_only")
    r = svc.records["E06"]
    assert r.state == State.FLAGGED
    support = [c for c in r.checks if c.name == "support"]
    assert support and not any(c.passed for c in support)
    assert "Ug" in support[0].message

# ------------------------------------------------------------------ readiness gaps

def test_T03_conflict_flagged_then_resolved_by_reviewer_choice():
    svc = run(D3_performance_report="V2_D3_uw_conflict")
    r = svc.records["E06"]
    assert r.state == State.FLAGGED
    assert {p.value for p in r.proposals} == {"1.1", "1.3"}
    chosen = next(p for p in r.proposals if p.value == "1.1")
    svc.review("E06", RITA, chosen.id, evidence_inspected=True, note="datasheet and report aligned on 1.1")
    assert r.state == State.REVIEWED and r.value == "1.1"
    assert [p.value for p in r.rejected] == ["1.3"], "the rejected value must be kept"
    svc.approve("E06", AKI)
    pkg = svc.release(AKI)
    assert [e["value"] for e in pkg.elements if e["element_id"] == "E06"] == ["1.1"]


def test_T04_wrong_scope_flagged_and_cannot_be_accepted():
    svc = run(D3_performance_report="V3_D3_uw_other_size")
    r = svc.records["E06"]
    assert r.state == State.FLAGGED
    wrong = next(p for p in r.proposals if p.scope != "1230 x 1480 mm")
    with pytest.raises(ActionRefused):
        svc.review("E06", RITA, wrong.id, evidence_inspected=True)


def test_T05_wrong_product_flagged():
    svc = run(D2_supplier_declaration="V4_D2_wrong_product")
    r = svc.records["E03"]
    assert r.state == State.FLAGGED
    assert any(c.name == "identity" and not c.passed for c in r.checks)


def test_T06_failed_check_blocks_review_approval_and_export():
    svc = run(D2_supplier_declaration="V5_D2_composition_95")
    r = svc.records["E03"]
    assert r.state == State.FLAGGED
    with pytest.raises(ActionRefused):
        svc.review("E03", RITA, r.proposals[0].id, evidence_inspected=True)
    with pytest.raises(TransitionRefused):
        svc.approve("E03", AKI)
    assert "E03" in svc.release(AKI).excluded

# ------------------------------------------------------------------ authority

@pytest.mark.parametrize("who", [Actor(id="bot", role=Role.AI), Actor(id="rita", role=Role.REVIEWER),
                                 Actor(id="sys", role=Role.SYSTEM)])
def test_T07_only_the_approver_role_can_approve(who):
    svc = run()
    svc.review("E06", RITA, svc.records["E06"].proposals[0].id, evidence_inspected=True)
    with pytest.raises(ActionRefused):
        svc.approve("E06", who)
    svc.approve("E06", AKI)
    assert svc.records["E06"].state == State.APPROVED


def test_T07b_same_person_cannot_review_and_approve():
    svc = run()
    svc.review("E06", RITA, svc.records["E06"].proposals[0].id, evidence_inspected=True)
    with pytest.raises(TransitionRefused, match="same person"):
        svc.approve("E06", RITA_AS_APPROVER)


def test_T07c_review_requires_confirmed_evidence_inspection():
    svc = run()
    with pytest.raises(ActionRefused):
        svc.review("E06", RITA, svc.records["E06"].proposals[0].id, evidence_inspected=False)

# ------------------------------------------------------------------ handover

def test_T08_export_contains_only_approved_and_passes_schema(tmp_path):
    svc = run(D2_supplier_declaration="V4_D2_wrong_product")
    approve_all_checked(svc)
    out = tmp_path / "handover.json"
    pkg = svc.release(AKI, out)
    assert "E03" in pkg.excluded
    assert {e["element_id"] for e in pkg.elements} == {"E01", "E02", "E04", "E05", "E06", "E07"}
    data = json.loads(out.read_text())
    schema = json.loads((ROOT / "schemas/handover_v0.2.schema.json").read_text())
    jsonschema.validate(data, schema)
    assert all(e["reviewed_by"] == "rita" and e["approved_by"] == "aki" for e in data["elements"])


def test_T12_approval_is_bound_to_the_exact_version():
    svc = run()
    r = svc.records["E06"]
    svc.review("E06", RITA, r.proposals[0].id, evidence_inspected=True)
    svc.approve("E06", AKI)
    r.proposals[0].value = "0.9"          # content changes after approval
    pkg = svc.release(AKI)
    assert "E06" in pkg.excluded
    assert "earlier version" in pkg.excluded["E06"]


def test_T13_correction_restarts_checks_review_and_approval():
    svc = run()
    r = svc.records["E07"]
    svc.review("E07", RITA, r.proposals[0].id, evidence_inspected=True)
    svc.approve("E07", AKI)
    old = r.proposals[0]
    svc.correct("E07", RITA, "NW-PR-2026-014",
                Evidence(source="D3_performance_report.md", quote="**Report ID:** NW-PR-2026-014"))
    assert r.approval is None and r.review is None
    assert r.state == State.CHECKED
    assert old in r.rejected
    with pytest.raises(ActionRefused):
        svc.correct("E07", RITA, "NW-PR-2026-999",
                    Evidence(source="D3_performance_report.md", quote="Report ID: NW-PR-2026-999"))

# ------------------------------------------------------------------ diary

def test_T14_diary_persists_every_step(tmp_path):
    db = tmp_path / "audit.sqlite"
    svc = run(audit=AuditStore(str(db)))
    svc.review("E06", RITA, svc.records["E06"].proposals[0].id, evidence_inspected=True)
    with pytest.raises(TransitionRefused):
        svc.approve("E06", RITA_AS_APPROVER)
    svc.approve("E06", AKI)
    reopened = AuditStore(str(db)).events(svc.run_id)
    actions = [e["action"] for e in reopened]
    assert actions[0] == "run started"
    assert "refused" in actions and "-> approved" in actions
    started = json.loads(reopened[0]["detail"])
    assert len(started["sources"]) == 4 and started["extractor"].startswith("standin")
    assert not hasattr(AuditStore, "delete") and not hasattr(AuditStore, "update")
