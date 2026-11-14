"""Tests for the dpp-sources MCP server (SPEC.md §8). Written before server.py.

Expected results come from SPEC.md §6. If the frozen pipeline behaves differently,
the test is changed to report the observed result openly; the frozen code is never changed.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VENDOR = ROOT / "vendor" / "dpp-prep-08d5840"


def _tree_hash(folder: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(folder)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


VENDOR_HASH_BEFORE = _tree_hash(VENDOR)

import server  # noqa: E402  (imported after the hash, so the hash covers the untouched copy)

UW_UNIT, REF = "W/(m2K)", "1230 x 1480 mm"
SASH_VALUE = "pine wood 74 %, aluminium 21 %, EPDM seals 4 %, steel fittings 1 %."
SASH_QUOTE = ("Sash profile set, share of sash mass: pine wood 74 %, aluminium 21 %, "
              "EPDM seals 4 %, steel fittings 1 %.")


def failed(result):
    return sorted(c["name"] for c in result["checks"] if not c["passed"])


# ---------------------------------------------------------------- T1 get_product
def test_t1_get_product_returns_erp_record_with_fingerprint():
    r = server.get_product("W-100")
    assert r["source_id"] == "erp_product_record"
    assert r["record"]["product_id"] == "W-100"
    assert r["record"]["nominal_size"] == "1230 x 1480"
    text = (VENDOR / "data/w100/structured/erp_product_record.json").read_text(encoding="utf-8")
    assert r["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_t1b_unknown_product_is_refused():
    assert "error" in server.get_product("X-999")


# ---------------------------------------------------------------- T2 list_sources
def test_t2_list_sources_lists_only_allowlisted_files():
    listed = server.list_sources("W-100")["sources"]
    ids = {s["source_id"] for s in listed}
    assert ids == set(server.SOURCE_MAP)
    for s in listed:
        assert s["kind"] in ("document", "structured record")
        assert s["set"] in ("baseline", "variant", "production-like", "structured")
        assert len(s["sha256"]) == 64


# ---------------------------------------------------------------- T3 read_source
def test_t3_read_source_returns_text_and_fingerprint():
    r = server.read_source("D1_datasheet")
    assert "Uw = 1.1 W/(m2K)" in r["text"]
    assert len(r["sha256"]) == 64


def test_t3b_read_source_refuses_unknown_and_path_tricks():
    for bad in ["unknown", "../x", "../../config/elements_w100.yaml", "/etc/passwd", ""]:
        assert "error" in server.read_source(bad), bad


# ---------------------------------------------------------------- T4–T7 scenarios (SPEC §6)
def test_t4_s1_supported_uw_is_checked():
    r = server.run_candidate_checks(
        element_id="E06", value="1.1",
        quote="Uw = 1.1 W/(m2K) for reference size 1230 x 1480 mm.",
        source_id="D1_datasheet", unit=UW_UNIT, scope=REF, product_id="W-100")
    assert r["quote_found"] is True
    assert failed(r) == []
    assert r["state"] == "checked"
    assert set(r["not_executed"]) >= {"review", "approval", "readiness assessment", "package release"}


def test_t4b_s1_note_short_quote_fails_scope():
    r = server.run_candidate_checks(
        element_id="E06", value="1.1", quote="Uw = 1.1 W/(m2K)",
        source_id="D3_performance_report", unit=UW_UNIT, scope=REF, product_id="W-100")
    assert r["quote_found"] is True
    assert failed(r) == ["scope"]
    assert r["state"] == "flagged"


def test_t5_s2_ug_value_is_flagged_by_support():
    r = server.run_candidate_checks(
        element_id="E06", value="0.5",
        quote="Ug = 0.5 W/(m2K) (glazing only, centre of pane).",
        source_id="V6_D1_ug_only", unit=UW_UNIT, scope=REF, product_id="W-100")
    assert r["quote_found"] is True
    assert "support" in failed(r)
    assert "scope" in failed(r)
    assert r["state"] == "flagged"


def test_t6_s3a_sash_with_supplier_article_is_flagged_by_identity():
    r = server.run_candidate_checks(
        element_id="E03", value=SASH_VALUE, quote=SASH_QUOTE,
        source_id="R2b_supplier_declaration_sash_only", unit="%", product_id="PP-SA-100")
    assert r["quote_found"] is True
    assert failed(r) == ["identity"]
    assert r["state"] == "flagged"


def test_t7_s3b_sash_with_reported_w100_passes_known_limitation():
    r = server.run_candidate_checks(
        element_id="E03", value=SASH_VALUE, quote=SASH_QUOTE,
        source_id="R2b_supplier_declaration_sash_only", unit="%", product_id="W-100")
    assert r["quote_found"] is True
    assert failed(r) == []
    assert r["state"] == "checked"       # known limitation, SPEC §4.5 and §6


# ---------------------------------------------------------------- extra: behaviour from SPEC §4.5
def test_quote_not_in_source_is_dropped_and_unresolved():
    r = server.run_candidate_checks(
        element_id="E06", value="0.9", quote="Uw = 0.9 W/(m2K) for reference size 1230 x 1480 mm.",
        source_id="D1_datasheet", unit=UW_UNIT, scope=REF, product_id="W-100")
    assert r["quote_found"] is False
    assert r["state"] == "unresolved"
    assert r["dropped_reason"]


def test_import_route_element_is_refused():
    r = server.run_candidate_checks(element_id="E01", value="W-100", quote="W-100",
                                    source_id="D1_datasheet")
    assert "error" in r


def test_structured_record_cannot_be_used_as_document_evidence():
    r = server.run_candidate_checks(element_id="E06", value="1.1", quote="1.1",
                                    source_id="erp_product_record")
    assert "error" in r


# ---------------------------------------------------------------- T8 no writes
def test_t8_no_writes_to_vendor_copy_or_repository():
    assert _tree_hash(VENDOR) == VENDOR_HASH_BEFORE
    repo = os.environ.get("DPP_PREP_REPO", "/home/claude/dpp-prep")
    if Path(repo, ".git").exists():
        out = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True)
        assert out.stdout.strip() == ""
