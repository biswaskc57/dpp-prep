"""Ollama adapter (v0.3.1), tested without Ollama.

The HTTP call is replaced by a fake transport that answers like a model would.
This tests how the adapter handles model output and that the unchanged
controls act on it. It does NOT test how well a real model extracts; that is
the evaluation run.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path

from dpp_prep.models import Method, State
from dpp_prep.ollama_extract import OllamaExtractor, ReplayResponses, ResponseRecorder
from dpp_prep.profile import load_profile
from dpp_prep.service import PreparationService

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config/elements_w100.yaml"
EXAMPLES = ROOT / "config/langextract_examples.yaml"
BASE = ROOT / "data/w100/baseline"
VAR = ROOT / "data/w100/variants"
ERP = ROOT / "data/w100/structured/erp_product_record.json"


def _doc_text(payload: dict) -> str:
    return payload["messages"][1]["content"].split("Now extract from this document:\n", 1)[1]


def faithful(payload: dict, sha: str, invent: bool = False, ug_as_uw: bool = False) -> str:
    """Answers like a model that copies what is there."""
    text = _doc_text(payload)
    out = []
    m = re.search(r"Product ID:(?:\*\*)?\s*(\S+)", text)
    pid = m.group(1) if m else ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Uw = "):
            out.append({"element": "thermal_transmittance_uw", "quote": s, "value": s.split()[2],
                        "unit": "W/(m2K)", "scope": "1230 x 1480 mm"})
        if ug_as_uw and s.startswith("Ug = "):
            out.append({"element": "thermal_transmittance_uw", "quote": s, "value": s.split()[2],
                        "unit": "W/(m2K)", "scope": "1230 x 1480 mm"})
        if s.startswith("Pine wood"):
            out.append({"element": "frame_material_composition", "quote": s, "value": s, "unit": "", "scope": ""})
        if "riple glazing" in s:
            seg = s[s.index("riple glazing") - 1:]
            out.append({"element": "glazing_specification", "quote": seg, "value": seg, "unit": "", "scope": ""})
    if "NW-PR-2026-014" in text:
        out.append({"element": "performance_report_id", "quote": "NW-PR-2026-014", "value": "NW-PR-2026-014",
                    "unit": "", "scope": ""})
    if invent:
        out.append({"element": "thermal_transmittance_uw", "quote": "Uw = 0.8 W/(m2K) certified",
                    "value": "0.8", "unit": "W/(m2K)", "scope": "1230 x 1480 mm"})
    return json.dumps({"product_id": pid, "extractions": out})


class Fake:
    """Transport stand-in that also records every request."""
    digest = "sha256:fake"

    def __init__(self, answer=faithful, **kw):
        self.answer, self.kw, self.calls = answer, kw, []

    def __call__(self, payload, sha):
        self.calls.append(payload)
        return self.answer(payload, sha, **self.kw)


def _svc(transport, docs, recorder=None):
    _, defs = load_profile(PROFILE)
    ext = OllamaExtractor("fake-model", defs, EXAMPLES, transport=transport, recorder=recorder)
    svc = PreparationService(PROFILE, ext)
    svc.start_run(docs + [ERP])
    svc.prepare_product()
    return svc, ext


BASELINE = [BASE / "D1_datasheet.md", BASE / "D2_supplier_declaration.md", BASE / "D3_performance_report.md"]


def test_O01_faithful_model_output_passes_the_same_controls():
    svc, _ = _svc(Fake(), BASELINE)
    assert all(r.state == State.CHECKED for r in svc.records.values())
    uw = svc.records["E06"].proposals
    assert all(p.method == Method.AI and p.produced_by == "ollama:fake-model" for p in uw)
    assert all(p.evidence.doc_sha256 for p in uw)


def test_O02_invented_quote_is_dropped_by_the_evidence_check_and_kept_in_the_record():
    svc, _ = _svc(Fake(invent=True), BASELINE)
    r = svc.records["E06"]
    assert "0.8" in [p.value for p in r.rejected]
    assert "0.8" not in [p.value for p in r.proposals]
    assert r.state == State.CHECKED


def test_O03_unreadable_answer_gives_no_proposals_and_is_logged():
    svc, ext = _svc(Fake(answer=lambda p, s: "Sure! The Uw value is 1.1."), BASELINE)
    assert all(svc.records[e].state == State.UNRESOLVED for e in ("E03", "E04", "E06", "E07"))
    assert all(svc.records[e].state == State.CHECKED for e in ("E01", "E02", "E05"))   # import route, no AI
    assert ext.raw_log and all(e["parse_error"] for e in ext.raw_log)


def test_O04_glazing_value_offered_as_whole_window_value_fails_the_support_check():
    docs = [VAR / "V6_D1_ug_only.md", BASE / "D2_supplier_declaration.md", BASE / "D3_performance_report.md"]
    svc, _ = _svc(Fake(ug_as_uw=True), docs)
    r = svc.records["E06"]
    failed = [c for c in r.checks if not c.passed]
    assert r.state == State.FLAGGED
    assert any(c.name == "support" for c in failed)


def test_O05_request_is_fixed_schema_bound_and_uses_the_foreign_example():
    fake = Fake()
    svc, ext = _svc(fake, BASELINE)
    assert len(fake.calls) == 3                                    # one call per document, cached
    p = fake.calls[0]
    assert p["options"]["temperature"] == 0 and p["options"]["seed"] == 42
    assert p["think"] is False and p["stream"] is False
    enum = p["format"]["properties"]["extractions"]["items"]["properties"]["element"]["enum"]
    assert set(enum) == {"frame_material_composition", "glazing_specification",
                         "thermal_transmittance_uw", "performance_report_id"}
    example = p["messages"][1]["content"].split("Now extract from this document:")[0]
    assert "D-200" in example and "W-100" not in example
    assert "Do not infer" in p["messages"][0]["content"]


def test_O06_recorded_answers_replay_to_the_same_outcome(tmp_path):
    spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts/evaluate.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    rec = tmp_path / "answers.jsonl"
    live = ev.ollama_factory("fake-model", recorder=ResponseRecorder(rec), transport=Fake(invent=True))
    _, rows1 = ev.evaluate("ollama", "fake-model", runs=2, out_dir=tmp_path, extractor_factory=live)
    replay = ReplayResponses(rec)
    assert replay.model == "fake-model" and replay.digest == "sha256:fake"
    _, rows2 = ev.evaluate("replay", "fake-model", runs=2, out_dir=tmp_path,
                           extractor_factory=ev.ollama_factory("fake-model", transport=replay))
    strip = lambda rows: [{k: v for k, v in r.items() if k != "run_id"} for r in rows]  # noqa: E731
    assert strip(rows1) == strip(rows2)
    assert len(rows1) == 2 * 7 * 7 and all(r["match"] for r in rows1)
    assert sum(1 for _ in csv.DictReader(next(tmp_path.glob("evaluation_replay*.csv")).open())) == len(rows2)


def test_O07_replay_refuses_answers_recorded_for_another_document(tmp_path):
    rec = tmp_path / "a.jsonl"
    rec.write_text(json.dumps({"doc_sha256": "x", "raw": "{}", "model": "m", "digest": "d"}) + "\n")
    replay = ReplayResponses(rec)
    try:
        _svc(replay, BASELINE)
    except Exception as e:  # noqa: BLE001
        assert "replay mismatch" in str(e)
    else:
        raise AssertionError("replay should refuse a mismatched answer")


# ------------------------------------------------------- real HTTP path
import threading  # noqa: E402
from http.server import BaseHTTPRequestHandler, HTTPServer  # noqa: E402

import pytest  # noqa: E402

from dpp_prep import ollama_extract  # noqa: E402


def _server(behaviour):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send(200, {"models": [{"name": "fake-model", "model": "fake-model", "digest": "abc123"}]})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            code, obj = behaviour(payload)
            self._send(code, obj)

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


def test_O08_http_path_retries_drops_unsupported_think_and_records_digest(monkeypatch):
    monkeypatch.setattr(ollama_extract.time, "sleep", lambda s: None)
    seen = {"n": 0, "think": []}

    def behaviour(payload):
        seen["n"] += 1
        seen["think"].append("think" in payload)
        if seen["n"] == 1:
            return 503, {"error": "busy"}
        if "think" in payload:
            return 400, {"error": "\"fake-model\" does not support thinking"}
        return 200, {"message": {"content": faithful(payload, "")}}

    srv, host = _server(behaviour)
    try:
        _, defs = load_profile(PROFILE)
        ext = OllamaExtractor("fake-model", defs, EXAMPLES, host=host)
        svc = PreparationService(PROFILE, ext)
        svc.start_run(BASELINE + [ERP])
        svc.prepare_product()
    finally:
        srv.shutdown()
    assert all(r.state == State.CHECKED for r in svc.records.values())
    assert seen["think"][:3] == [True, True, False]       # 503 retried, then thinking switch dropped
    assert ext.raw_log[0]["digest"] == "abc123"


def test_O09_missing_model_gives_a_plain_instruction():
    srv, host = _server(lambda p: (404, {"error": "model 'x' not found"}))
    try:
        _, defs = load_profile(PROFILE)
        ext = OllamaExtractor("qwen3.5:9b", defs, EXAMPLES, host=host)
        svc = PreparationService(PROFILE, ext)
        svc.start_run(BASELINE + [ERP])
        with pytest.raises(ollama_extract.OllamaError, match="ollama pull qwen3.5:9b"):
            svc.prepare_product()
    finally:
        srv.shutdown()
