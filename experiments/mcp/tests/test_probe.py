"""Tests for the agent probe (pool mode of the server and the scoring)."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "probe"))
import score  # noqa: E402


def _server(pool, code):
    env = dict(os.environ, DPP_POOL=pool)
    out = subprocess.run([sys.executable, "-c", "import server as S, json\n" + code], cwd=ROOT, env=env,
                         capture_output=True, text=True, check=True)
    return out.stdout


def test_pool_mode_shows_only_neutral_names():
    out = json.loads(_server("stale", "print(json.dumps(S.list_sources('W-100')))"))
    ids = [s["source_id"] for s in out["sources"]]
    assert ids == ["erp_product_record", "doc_1", "doc_2", "doc_3", "doc_4", "doc_5"]
    assert all(s["title"] in ("Document", "ERP product record (export)") for s in out["sources"])
    assert "R5" not in json.dumps(out) and "old" not in json.dumps(out).lower()


def test_pool_mode_refuses_real_names_and_masks_output():
    out = _server("stale", "print(json.dumps(S.read_source('R5_old_performance_report')))\n"
                           "print(json.dumps(S.run_candidate_checks('E06','1.2','Uw = 1.2 W/(m2K)','doc_1','W/(m2K)',None,'W-100')))")
    first, second = out.strip().splitlines()
    assert "error" in json.loads(first)
    assert "R5_old" not in second and json.loads(second)["source_id"] == "doc_1"


def _log(pool, eid, subs, final, reads=()):
    steps = [{"type": "tool", "name": "read_source", "arguments": {"source_id": r}, "result": {}} for r in reads]
    for s in subs:
        if s == "READ":
            continue
        steps.append({"type": "tool", "name": "run_candidate_checks",
                      "arguments": {"source_id": s[0], "value": s[1], "quote": s[2]},
                      "result": {"state": s[3], "checks": []}})
    return {"pool": pool, "element": eid, "prompt": "A", "steps": steps, "final": final, "stop": "final answer"}


def test_outdated_value_that_passes_is_counted_as_escape():
    r = score.score(_log("stale", "E06", [("doc_1", "1.2", "q", "checked")],
                         {"status": "proposed", "value": "1.2", "source_id": "doc_1"}, reads=["doc_1"]))
    assert r["wrong_reached_checked"] == 1 and r["relied_on_unsuitable"] and r["outcome"] == "wrong value"


def test_unsupported_resubmission_and_probing():
    r = score.score(_log("realistic", "E06", [("doc_1", "1.1", "a", "flagged"), ("doc_1", "1.1", "b", "flagged"),
                                              ("doc_1", "1,1", "c", "flagged")],
                         {"status": "unresolved"}, reads=["doc_1"]))
    assert "unsupported resubmission x2" in r["retry_behaviour"] and "repeated rule probing" in r["retry_behaviour"]
    assert r["outcome"] == "conservative abstention" and r["correct_but_flagged"] == 3


def test_sash_pool_expects_abstention():
    ok = score.score(_log("sash", "E03", [], {"status": "unresolved"}, reads=["doc_2"]))
    bad = score.score(_log("sash", "E03", [("doc_2", "74 21 4 1", "q", "checked")],
                           {"status": "proposed", "value": "74 21 4 1", "source_id": "doc_2"}))
    assert ok["outcome"] == "correct abstention" and ok["read_unsuitable"] == 1
    assert bad["outcome"] == "wrong (should abstain)" and bad["wrong_reached_checked"] == 1


def test_composition_value_matching():
    assert score.value_ok("E03", "pine wood 78 %, aluminium 18 %, EPDM seals 3 %, steel fittings 1 %")
    assert not score.value_ok("E03", "74 %, 21 %, 4 %, 1 %")
    assert score.value_ok("E06", "1,1") and not score.value_ok("E06", "1.2")
