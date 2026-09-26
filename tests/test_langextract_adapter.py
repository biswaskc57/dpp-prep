"""LangExtract adapter, tested without an API key.

langextract.extract is replaced by a fake that returns the same kind of
object the real library returns (AnnotatedDocument with Extractions and
character intervals). This tests the adapter's handling of model output;
it does NOT test how well a real model extracts. That is a separate
evaluation, run once a model provider is chosen.
"""
from __future__ import annotations

import re
from pathlib import Path

import langextract as lx
import pytest

from dpp_prep.extract import LangExtractExtractor
from dpp_prep.models import Method, State
from dpp_prep.profile import load_profile
from dpp_prep.service import PreparationService

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config/elements_w100.yaml"
EXAMPLES = ROOT / "config/langextract_examples.yaml"
BASE = ROOT / "data/w100/baseline"
ERP = ROOT / "data/w100/structured/erp_product_record.json"

CALLS: list[dict] = []


def _span(text, needle, cls, **attrs):
    i = text.find(needle)
    assert i >= 0, needle
    return lx.data.Extraction(extraction_class=cls, extraction_text=needle,
                              char_interval=lx.data.CharInterval(start_pos=i, end_pos=i + len(needle)),
                              alignment_status=lx.data.AlignmentStatus.MATCH_EXACT, attributes=attrs)


def fake_extract(text_or_documents, prompt_description, examples, model_id, api_key=None, **kw):
    """Behaves like a model that finds what is there, and invents one value."""
    text = text_or_documents
    CALLS.append({"prompt": prompt_description, "examples": examples, "model_id": model_id})
    ex = []
    m = re.search(r"Product ID:(?:\*\*)?\s*(\S+)", text)
    if m:
        ex.append(_span(text, m.group(1), "document_product_id", value=m.group(1)))
    for line in text.splitlines():
        if line.startswith("Uw = "):
            num = line.split()[2]
            ex.append(_span(text, line.strip(), "thermal_transmittance_uw",
                            value=num, unit="W/(m2K)", scope="1230 x 1480 mm"))
        if line.startswith("Pine wood"):
            ex.append(_span(text, line.strip(), "frame_material_composition", value=line.strip()))
        if "riple glazing" in line:
            seg = line[line.index("riple glazing") - 1:].strip()
            ex.append(_span(text, seg, "glazing_specification", value=seg))
    if "NW-PR-2026-014" in text:
        ex.append(_span(text, "NW-PR-2026-014", "performance_report_id", value="NW-PR-2026-014"))
    # an extraction the model could not anchor in the text (e.g. from its own knowledge)
    ex.append(lx.data.Extraction(extraction_class="thermal_transmittance_uw", extraction_text="Uw 0.8",
                                 char_interval=None, attributes={"value": "0.8"}))
    return lx.data.AnnotatedDocument(text=text, extractions=ex)


@pytest.fixture
def svc(monkeypatch):
    CALLS.clear()
    monkeypatch.setattr(lx, "extract", fake_extract)
    _, defs = load_profile(PROFILE)
    ext = LangExtractExtractor("fake-model", defs, EXAMPLES, api_key="not-used")
    s = PreparationService(PROFILE, ext)
    s.start_run(list(BASE.glob("*.md")) + [ERP])
    s.prepare_product()
    return s


def test_L01_adapter_output_passes_the_same_controls(svc):
    assert {r.state for r in svc.records.values()} == {State.CHECKED}
    for eid in ("E03", "E04", "E06", "E07"):
        assert all(p.method == Method.AI and p.produced_by == "langextract:fake-model"
                   for p in svc.records[eid].proposals)


def test_L02_unanchored_model_output_is_discarded_but_recorded(svc):
    values = {p.value for p in svc.records["E06"].proposals}
    assert "0.8" not in values and values == {"1.1"}
    outputs = [e for e in svc.audit.events(svc.run_id) if e["action"] == "model output"]
    assert len(outputs) == 3 and any('"span": null' in e["detail"] for e in outputs)


def test_L03_one_call_per_document_with_prompt_and_foreign_examples(svc):
    assert len(CALLS) == 3, "results must be cached per document, not one call per element"
    call = CALLS[0]
    assert "Do not infer" in call["prompt"] and "glazing-only Ug" in call["prompt"]
    example_text = call["examples"][0].text
    assert "D-200" in example_text and "W-100" not in example_text


def test_L04_example_extractions_are_exact_substrings_of_the_example_text():
    _, defs = load_profile(PROFILE)
    ex = LangExtractExtractor("x", defs, EXAMPLES).examples()[0]
    for e in ex.extractions:
        assert e.extraction_text in ex.text, e.extraction_text


def test_L05_empty_extraction_is_not_treated_as_grounded():
    empty = lx.data.Extraction(extraction_class="thermal_transmittance_uw", extraction_text="",
                               char_interval=lx.data.CharInterval(start_pos=0, end_pos=0))
    assert not LangExtractExtractor._grounded(empty)
