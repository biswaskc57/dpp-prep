"""Row-by-row tests: every rule of every DMN table is hit by one input and gives the specified output.

Expected outputs and rule IDs are taken from the approved specification (sheet 'DMN status rules',
research matrix v0.27, D044) and the W3–W5 specification of tables A and B.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmn_runner import Engine  # noqa: E402

E = Engine()

BASE = {  # an element where everything passed and no human decision exists yet
    "Quality criterion configured": True, "Approval statement": "stated required",
    "Validity statement": "not stated", "Quality statement": "stated required",
    "Supported proposal exists": True, "Not in sources and obtain failed": False,
    "Alignment checks": "all passed", "Value type check": "passed", "Support check": "passed",
    "Evidence inspected": False, "All configured checks": "all passed",
    "Approval on this version": "none", "Source validity": "unknown",
    "Number of criteria": 1, "Failed criteria": 0, "Insufficient criteria": 0,
}


def run(cond, **over):
    data = {**BASE, **{k.replace("_", " "): v for k, v in over.items()}}
    data["Condition"] = cond
    return E.condition_status(data)


# ---------------------------------------------------------------- Table A (FIRST)
@pytest.mark.parametrize("cond,over,expected,rule", [
    ("Aligned", {}, "applicable", "A1"),
    ("Of sufficient quality", {}, "applicable", "A2"),
    ("Of sufficient quality", {"Quality criterion configured": False, "Quality statement": "stated not required"}, "not applicable", "A3"),
    ("Authorised", {}, "applicable", "A4"),
    ("Authorised", {"Approval statement": "stated not required"}, "not applicable", "A5"),
    ("Current", {"Validity statement": "stated required"}, "applicable", "A6"),
    ("Current", {"Validity statement": "stated not required"}, "not applicable", "A7"),
    ("Current", {}, "cannot yet determine", "A8"),
    ("Of sufficient quality", {"Quality criterion configured": False}, "cannot yet determine", "A8"),
])
def test_table_a(cond, over, expected, rule):
    r = E.condition_status({**BASE, **over, "Condition": cond})
    assert (r["applicability"], r["applicability_rule"]) == (expected, rule)


# ---------------------------------------------------------------- Available status (UNIQUE)
@pytest.mark.parametrize("sup,nis,expected,rule", [(True, False, "met", "AV1"), (False, True, "not met", "AV2"), (False, False, "not yet assessed", "AV3")])
def test_available_status(sup, nis, expected, rule):
    r = E.condition_status({**BASE, "Condition": "Available", "Supported proposal exists": sup,
                            "Not in sources and obtain failed": nis})
    assert (r["available_status"], r["available_rule"]) == (expected, rule)


# ---------------------------------------------------------------- Table B aggregation (FIRST)
@pytest.mark.parametrize("n,f,i,expected,rule", [
    (0, 0, 0, "no criteria", "B-agg-4"), (2, 1, 1, "not met", "B-agg-1"),
    (2, 0, 1, "not yet assessed", "B-agg-2"), (2, 0, 0, "met", "B-agg-3")])
def test_table_b_aggregation(n, f, i, expected, rule):
    r = E.condition_status({**BASE, "Condition": "Of sufficient quality", "Number of criteria": n,
                            "Failed criteria": f, "Insufficient criteria": i})
    assert (r["quality_status"], r["quality_rule"]) == (expected, rule)


# ---------------------------------------------------------------- Table B per criterion (UNIQUE)
@pytest.mark.parametrize("args,expected,rule", [
    (("composition", "evaluated", "all", "yes"), "pass", "B-crit-1"),
    (("composition", "evaluated", "all", "no"), "fail", "B-crit-2"),
    (("composition", "evaluated", "partial or malformed"), "insufficient evidence", "B-crit-3"),
    (("composition", "evaluated", "none"), "insufficient evidence", "B-crit-4"),
    (("consistency", "evaluated", "n/a", "n/a", "agree"), "pass", "B-crit-5"),
    (("consistency", "evaluated", "n/a", "n/a", "disagree"), "fail", "B-crit-6"),
    (("composition", "not evaluated"), "insufficient evidence", "B-crit-7"),
    (("consistency", "not evaluated"), "insufficient evidence", "B-crit-7"),
])
def test_table_b_criterion(args, expected, rule):
    assert E.criterion_result(*args) == (expected, rule)


# ---------------------------------------------------------------- Table C (FIRST)
@pytest.mark.parametrize("cond,over,expected,rule", [
    ("Authorised", {"Approval statement": "stated not required"}, "not required", "C1"),
    ("Current", {}, "not yet assessed", "C2"),
    ("Available", {}, "met", "C3"),
    ("Available", {"Supported proposal exists": False, "Not in sources and obtain failed": True}, "not met", "C4"),
    ("Available", {"Supported proposal exists": False}, "not yet assessed", "C5"),
    ("Aligned", {"Supported proposal exists": False}, "not yet assessed", "C6"),
    ("Aligned", {}, "met", "C7"),
    ("Aligned", {"Alignment checks": "any failed"}, "not met", "C8"),
    ("Representable", {}, "met", "C9"),
    ("Representable", {"Value type check": "failed"}, "not met", "C10"),
    ("Of sufficient quality", {}, "met", "C11"),
    ("Of sufficient quality", {"Failed criteria": 1}, "not met", "C12"),
    ("Of sufficient quality", {"Insufficient criteria": 1}, "not yet assessed", "C13"),
    ("Evidenced", {"Support check": "failed"}, "not met", "C14"),
    ("Evidenced", {"Evidence inspected": True}, "met", "C15"),
    ("Evidenced", {}, "not yet assessed", "C16"),
    ("Validated", {}, "met", "C17"),
    ("Validated", {"All configured checks": "any failed"}, "not met", "C18"),
    ("Authorised", {"Approval on this version": "approved"}, "met", "C19"),
    ("Authorised", {"Approval on this version": "refused"}, "not met", "C20"),
    ("Authorised", {}, "not yet assessed", "C21"),
    ("Current", {"Validity statement": "stated required", "Source validity": "within"}, "met", "C22"),
    ("Current", {"Validity statement": "stated required", "Source validity": "expired or superseded"}, "not met", "C23"),
    ("Current", {"Validity statement": "stated required"}, "not yet assessed", "C24"),
])
def test_table_c(cond, over, expected, rule):
    r = E.condition_status({**BASE, **over, "Condition": cond})
    assert (r["status"], r["status_rule"]) == (expected, rule)


def test_every_rule_is_covered():
    """Each rule ID in the DMN files appears in at least one test above (C25 is the safety default)."""
    import inspect
    src = inspect.getsource(sys.modules[__name__])
    for table, ids in E.ids.items():
        for rid in ids:
            if rid != "C25":
                assert f'"{rid}"' in src, f"{table}: rule {rid} has no test"


def test_missing_information_is_never_met():
    """Framework rule: missing information never becomes 'met' by default."""
    for cond in ("Aligned", "Representable", "Of sufficient quality", "Evidenced", "Validated", "Authorised", "Current"):
        r = E.condition_status({**BASE, "Condition": cond, "Supported proposal exists": False})
        assert r["status"] != "met", cond
