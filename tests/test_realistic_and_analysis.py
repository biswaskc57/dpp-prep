"""Realistic tier, oracle pre-registration and the analysis script (v0.3.2)."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import yaml

from dpp_prep.ollama_extract import ResponseRecorder

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ev = _load("evaluate")
an = _load("analyse")


def test_R01_oracle_reproduces_every_expectation_in_both_tiers_and_formats(tmp_path):
    for tier in ("simple", "realistic"):
        for fmt in ("md", "pdf"):
            _, rows = ev.evaluate("oracle", None, 1, fmt, out_dir=tmp_path, tier=tier)
            assert all(r["match"] for r in rows), (tier, fmt, [r for r in rows if not r["match"]])


def test_R02_realistic_documents_unchanged_since_preregistration():
    data = yaml.safe_load((ROOT / "config/evaluation_scenarios_realistic.yaml").read_text(encoding="utf-8"))
    for doc, digest in data["_document_sha256"].items():
        assert hashlib.sha256((ROOT / f"data/w100/realistic/{doc}.md").read_bytes()).hexdigest() == digest, doc


def test_R03_preregistered_realistic_expectations_are_as_recorded():
    data = yaml.safe_load((ROOT / "config/evaluation_scenarios_realistic.yaml").read_text(encoding="utf-8"))
    assert data["real_baseline"]["expect"] == {"E06": "flagged"}
    assert data["real_stale_report"]["expect"] == {"E04": "flagged", "E06": "flagged", "E07": "flagged"}
    assert data["real_sash_only"]["expect"] == {"E03": "unresolved", "E06": "flagged"}


def _sloppy(payload, sha):
    """A model that grabs distractors: the sash composition and the replaced report."""
    text = payload["messages"][1]["content"].split("Now extract from this document:\n", 1)[1]
    ex = []
    for line in text.splitlines():
        s = line.strip()
        if "Sash profile set, share" in s:
            ex.append({"element": "frame_material_composition", "quote": s, "value": s.split(": ", 1)[1],
                       "unit": "", "scope": ""})
        if "replaces NW-PR-2025-031" in s:
            ex.append({"element": "performance_report_id", "quote": s, "value": "NW-PR-2025-031",
                       "unit": "", "scope": ""})
    return json.dumps({"product_id": "W-100", "extractions": ex})


class _T:
    digest = "sha256:fake"

    def __init__(self, f):
        self.f = f

    def __call__(self, p, s):
        return self.f(p, s)


def test_R04_analysis_finds_escapes_and_classifies_distractors(tmp_path):
    rec = ResponseRecorder(tmp_path / "model_outputs_ollama-sloppy_realistic_md_20261012-120000.jsonl")
    ev.evaluate("ollama", "sloppy", runs=1, out_dir=tmp_path, tier="realistic",
                extractor_factory=ev.ollama_factory("sloppy", recorder=rec, transport=_T(_sloppy)))
    an.main([str(tmp_path)])
    esc = list(csv.DictReader((tmp_path / "analysis/escapes.csv").open(encoding="utf-8")))
    assert {(e["scenario"], e["element"]) for e in esc} >= {("real_sash_only", "E03"), ("real_baseline", "E07")}
    props = list(csv.DictReader((tmp_path / "analysis/proposals.csv").open(encoding="utf-8")))
    assert any(p["class"] == "distractor" and p["element"] == "E03" for p in props)
    assert any(p["class"] == "distractor" and p["element"] == "E07" for p in props)


def test_R05_empty_answers_are_counted_apart_from_proposals():
    """An item without a value is not a proposal: the adapter discards it before any check
    (ollama_extract: blank or null value -> skipped). The analysis must do the same, so that
    'quote not found' only counts real proposals whose quote is not in the document."""
    text = "Uw = 1.1 W/(m2K)\nUf = 1.3 W/(m2K)\n"
    answer = {"product_id": "W-100", "extractions": [
        {"element": "uw", "value": "1.1", "quote": "Uw = 1.1 W/(m2K)"},       # correct
        {"element": "uw", "value": "1.3", "quote": "Uf = 1.3 W/(m2K)"},       # genuine quote, wrong value
        {"element": "uw", "value": "1.1", "quote": "Uw is 1.1 everywhere"},   # quote not in the document
        {"element": "uw", "value": "", "quote": "Uw = 1.1 W/(m2K)"},          # empty
        {"element": "uw", "value": None, "quote": ""},                        # null
        {"element": "uw", "value": "   ", "quote": "x"},                      # blank
    ]}
    entries = [(1, "s", "doc", {"raw": json.dumps(answer), "seconds": 1.0, "_doc_text": text})]
    docs_gt = {"doc": {"product": "W-100", "statements": [{"element": "E06", "value": "1.1"}]}}
    c, props = an.analyse_proposals(entries, docs_gt, {"uw": "E06"})
    assert c["empty"] == 3
    assert c["proposals"] == 3
    assert (c["correct"], c["other wrong"], c["quote not found"]) == (1, 1, 1)
    assert c["proposals"] == c["correct"] + c["distractor"] + c["other wrong"] + c["quote not found"]
    assert [p["class"] for p in props].count("empty") == 3
