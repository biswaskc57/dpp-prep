"""The evaluation runner works with the LangExtract adapter path and keeps every run."""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import langextract as lx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from test_langextract_adapter import fake_extract  # noqa: E402

spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts/evaluate.py")
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)


def test_E01_runner_with_langextract_adapter_keeps_every_run(monkeypatch, tmp_path):
    monkeypatch.setattr(lx, "extract", fake_extract)
    from dpp_prep.extract import LangExtractExtractor
    from dpp_prep.profile import load_profile
    _, defs = load_profile(ROOT / "config/elements_w100.yaml")
    factory = lambda: LangExtractExtractor("fake-model", defs, ROOT / "config/langextract_examples.yaml")  # noqa: E731
    csv_path, rows = evaluate.evaluate("langextract", "fake-model", runs=2, out_dir=tmp_path,
                                       extractor_factory=factory)
    assert {r["run"] for r in rows} == {1, 2}
    assert len(rows) == 2 * 7 * 7
    assert all(r["match"] for r in rows)
    assert sum(1 for _ in csv.DictReader(csv_path.open())) == len(rows)
