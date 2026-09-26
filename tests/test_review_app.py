"""Review screen, driven like a user with Streamlit's AppTest (no browser).
Covers T09: the value is shown beside its source sentence."""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "review_app.py")


@pytest.fixture
def at():
    a = AppTest.from_file(APP, default_timeout=30)
    a.run()
    assert not a.exception
    return a


def html_blocks(a) -> str:
    return " ".join(m.value for m in a.markdown)


def test_U01_value_is_shown_beside_its_source_sentence(at):
    text = html_blocks(at)
    assert "<mark>Uw = 1.1 W/(m2K) for reference size 1230 x 1480 mm.</mark>" in text


def test_U02_no_value_preselected_and_inspection_box_unticked(at):
    assert at.radio(key="sel_E07").value is None
    assert at.checkbox(key="insp_E07").value is False


def test_U03_accepting_without_inspection_is_refused(at):
    pid = at.session_state["svc"].records["E07"].proposals[0].id
    at.radio(key="sel_E07").set_value(pid)
    at.button(key="accept_E07").click().run()
    assert any("Refused" in e.value for e in at.error)
    assert at.session_state["svc"].records["E07"].state.value == "checked"


def test_U04_review_then_approve_by_different_person_then_release(at):
    svc = at.session_state["svc"]
    pid = svc.records["E07"].proposals[0].id
    at.radio(key="sel_E07").set_value(pid)
    at.checkbox(key="insp_E07").check()
    at.button(key="accept_E07").click().run()
    assert svc.records["E07"].state.value == "reviewed"
    at.selectbox(key="user").select("rita — trying to approve").run()
    at.button(key="approve_E07").click().run()
    assert any("same person" in e.value for e in at.error)
    at.selectbox(key="user").select("aki — approver").run()
    at.button(key="approve_E07").click().run()
    assert svc.records["E07"].state.value == "approved"
    at.button(key="release").click().run()
    pkg = at.session_state["package"]
    assert [e["element_id"] for e in pkg["elements"]] == ["E07"]


def test_U05_pdf_scenario_shows_page_numbers(at):
    at.radio(key="fmt").set_value("PDF").run()
    assert not at.exception
    captions = " ".join(c.value for c in at.caption)
    assert "page 2" in captions
