"""dpp-sources: a small MCP server for the W-100 demo (SPEC.md v1.3; v1.4 adds DPP_POOL for the agent probe).

An AI client can read the fictional W-100 sources and submit candidate values.
The candidate is checked by the UNCHANGED dpp-prep pipeline (commit 08d5840),
run from a read-only copy in vendor/. The AI never decides its own outcome (D1),
and there are no tools for review, approval, readiness or release (D4).

Run:  python server.py        (stdio transport, for Claude Desktop or the MCP Inspector)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True                  # D2: never write into the vendor copy

ROOT = Path(__file__).resolve().parent
VENDOR = Path(os.environ.get("DPP_PREP_VENDOR", ROOT / "vendor" / "dpp-prep-08d5840"))
sys.path.insert(0, str(VENDOR / "src"))

from typing import Annotated                                       # noqa: E402

from pydantic import Field                                          # noqa: E402
from mcp.server.fastmcp import FastMCP                            # noqa: E402
from dpp_prep.audit import AuditStore                             # noqa: E402
from dpp_prep.models import Evidence, Method, Proposal, sha256     # noqa: E402
from dpp_prep.service import PreparationService                    # noqa: E402
from dpp_prep.sources import load_source                           # noqa: E402

PROFILE = VENDOR / "config" / "elements_w100.yaml"
FROZEN = "frozen dpp-prep v0.3.2 pipeline (commit 08d5840)"
NOT_EXECUTED = ["review", "approval", "readiness assessment", "package release"]

# D5: fixed allowlist. Source IDs map to files; paths are never built from client input.
W = "data/w100/"
SOURCE_MAP: dict[str, tuple[str, str, str]] = {
    # id: (relative path in the vendor copy, set, title)
    "erp_product_record": (W + "structured/erp_product_record.json", "structured", "ERP product record (export)"),
    "D1_datasheet": (W + "baseline/D1_datasheet.md", "baseline", "Product datasheet"),
    "D2_supplier_declaration": (W + "baseline/D2_supplier_declaration.md", "baseline", "Supplier material declaration (frame)"),
    "D3_performance_report": (W + "baseline/D3_performance_report.md", "baseline", "Performance report NW-PR-2026-014"),
    "V1_D1_uw_missing": (W + "variants/V1_D1_uw_missing.md", "variant", "Datasheet without Uw"),
    "V1_D3_uw_missing": (W + "variants/V1_D3_uw_missing.md", "variant", "Performance report without Uw"),
    "V2_D3_uw_conflict": (W + "variants/V2_D3_uw_conflict.md", "variant", "Performance report with a different Uw"),
    "V3_D3_uw_other_size": (W + "variants/V3_D3_uw_other_size.md", "variant", "Performance report, other reference size"),
    "V4_D2_wrong_product": (W + "variants/V4_D2_wrong_product.md", "variant", "Supplier declaration for another product"),
    "V5_D2_composition_95": (W + "variants/V5_D2_composition_95.md", "variant", "Supplier declaration, shares sum to 95 %"),
    "V6_D1_ug_only": (W + "variants/V6_D1_ug_only.md", "variant", "Datasheet with glazing-only Ug"),
    "R1_datasheet": (W + "realistic/R1_datasheet.md", "production-like", "Product datasheet"),
    "R2_supplier_declaration": (W + "realistic/R2_supplier_declaration.md", "production-like", "Supplier material declaration"),
    "R2b_supplier_declaration_sash_only": (W + "realistic/R2b_supplier_declaration_sash_only.md", "production-like", "Supplier declaration, sash only"),
    "R3_performance_report": (W + "realistic/R3_performance_report.md", "production-like", "Performance report"),
    "R4_declaration_of_performance": (W + "realistic/R4_declaration_of_performance.md", "production-like", "Declaration of performance"),
    "R5_old_performance_report": (W + "realistic/R5_old_performance_report.md", "production-like", "Older performance report"),
}

mcp = FastMCP("dpp-sources", log_level="WARNING")

# Agent probe (v1.4, 29 Oct 2026): optional document pool. When DPP_POOL is set, only that
# pool's documents are visible, under NEUTRAL names (doc_1, doc_2, ...) so that the agent
# cannot infer a document's role from its file name. Scoring maps the neutral names back
# (probe/pool_key.yaml). Without DPP_POOL the server behaves exactly as v1.3.
POOLS: dict[str, list[str]] = {   # order = neutral numbering (fixed, deliberately not sorted)
    "basic": ["D3_performance_report", "D1_datasheet", "D2_supplier_declaration"],
    "realistic": ["R3_performance_report", "R1_datasheet", "R4_declaration_of_performance", "R2_supplier_declaration"],
    "stale": ["R5_old_performance_report", "R2_supplier_declaration", "R1_datasheet", "R4_declaration_of_performance", "R3_performance_report"],
    "sash": ["R4_declaration_of_performance", "R2b_supplier_declaration_sash_only", "R3_performance_report", "R1_datasheet"],
}
POOL = os.environ.get("DPP_POOL") or None
if POOL is not None and POOL not in POOLS:
    raise SystemExit(f"unknown DPP_POOL {POOL!r}; choose from {sorted(POOLS)}")
NEUTRAL = {f"doc_{i}": sid for i, sid in enumerate(POOLS[POOL], 1)} if POOL else {}
REAL_TO_NEUTRAL = {v: k for k, v in NEUTRAL.items()}


def _resolve(source_id: str) -> str | None:
    """Neutral name -> real source id in pool mode; names outside the pool give None."""
    if POOL is None or source_id == "erp_product_record":
        return source_id
    return NEUTRAL.get(source_id)


def _mask(obj):
    """Replace real file names in tool output by neutral names (pool mode only)."""
    if POOL is None:
        return obj
    if isinstance(obj, dict):
        return {k: _mask(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask(v) for v in obj]
    if isinstance(obj, str):
        for real, neutral in REAL_TO_NEUTRAL.items():
            obj = obj.replace(real + ".md", neutral).replace(real, neutral)
    return obj



def _load(source_id: str):
    real = _resolve(source_id)
    entry = SOURCE_MAP.get(real) if real else None          # only exact keys; "../x" etc. never match
    if entry is None:
        return None, {"error": f"unknown source_id {source_id!r}; call list_sources for the allowed IDs"}
    return load_source(VENDOR / entry[0]), None


@mcp.tool()
def get_product(product_id: str) -> dict:
    """Return the fictional ERP record for a product (the structured, no-AI source).
    Corresponds to the BPMN activity 'Import value from structured record'."""
    doc, err = _load("erp_product_record")
    if err:
        return err
    if doc.data.get("product_id") != product_id:
        return {"error": f"no record for product {product_id!r}"}
    record = {k: v for k, v in doc.data.items() if not k.startswith("_")}
    return {"source_id": "erp_product_record", "record": record, "sha256": doc.sha256,
            "note": "fictional research data"}


@mcp.tool()
def list_sources(product_id: str) -> dict:
    """List the sources available for a product, with their identity (fingerprint).
    Corresponds to the BPMN activity 'Select source documents and records'."""
    if product_id != "W-100":
        return {"error": f"no sources for product {product_id!r}"}
    out = []
    if POOL is not None:
        for neutral, real in [("erp_product_record", "erp_product_record"), *NEUTRAL.items()]:
            doc = load_source(VENDOR / SOURCE_MAP[real][0])
            out.append({"source_id": neutral,
                        "title": "ERP product record (export)" if real == "erp_product_record" else "Document",
                        "kind": "structured record" if doc.kind == "structured" else "document",
                        "sha256": doc.sha256})
        return {"product_id": product_id, "sources": out, "note": "fictional research data"}
    for sid, (rel, set_, title) in SOURCE_MAP.items():
        doc = load_source(VENDOR / rel)
        out.append({"source_id": sid, "title": title, "set": set_,
                    "kind": "structured record" if doc.kind == "structured" else "document",
                    "sha256": doc.sha256})
    return {"product_id": product_id, "sources": out, "note": "fictional research data"}


@mcp.tool()
def read_source(source_id: str) -> dict:
    """Return the full text of one allowed source and its fingerprint.
    Read the text, then propose a value with an exact quote via run_candidate_checks."""
    doc, err = _load(source_id)
    if err:
        return err
    return {"source_id": source_id, "text": doc.text, "sha256": doc.sha256}


class _CandidateExtractor:
    """Feeds exactly one external candidate into the frozen extractor slot."""
    name = "mcp-candidate"

    def __init__(self, element_id: str, doc_name: str, proposal: Proposal):
        self.element_id, self.doc_name, self.proposal = element_id, doc_name, proposal

    def propose(self, d, doc):
        if d.id == self.element_id and doc.name == self.doc_name:
            return [self.proposal]
        return []


@mcp.tool()
def run_candidate_checks(
        element_id: Annotated[str, Field(description="element to prepare, e.g. 'E06'")],
        value: Annotated[str, Field(description="the value only, exactly as written in the quote, "
                                                "WITHOUT unit or size, e.g. '1.1' or "
                                                "'Pine wood 78 %, aluminium 18 %, ...'")],
        quote: Annotated[str, Field(description="exact text copied from the source that contains the value, "
                                                "its unit and the size or scope it applies to")],
        source_id: Annotated[str, Field(description="source_id from list_sources, e.g. 'doc_2'")],
        unit: Annotated[str | None, Field(description="unit exactly as written in the quote, e.g. 'W/(m2K)'; "
                                                      "omit if the element has no unit")] = None,
        scope: Annotated[str | None, Field(description="size or scope the value applies to, as written in the "
                                                       "quote, e.g. '1230 x 1480 mm'; omit if none")] = None,
        product_id: Annotated[str | None, Field(description="product identifier that the source states the value "
                                                            "belongs to, e.g. 'W-100'")] = None) -> dict:
    """Submit ONE candidate value with its exact supporting quote. Put the value, its unit and its
    scope in separate fields (value without unit). The server loads the source itself and runs the
    unchanged dpp-prep evidence check and rule checks. Returns each check with its reason and the
    resulting state ('checked' or 'flagged'). It does NOT review, approve, assess readiness or
    release. Only for elements taken from documents (E03, E04, E06, E07)."""
    doc, err = _load(source_id)
    if err:
        return err
    if doc.kind != "document":
        return {"error": "structured records are imported, not quoted; use get_product"}
    service = PreparationService(PROFILE, extractor=None, audit=AuditStore(":memory:"))
    d = service.defs.get(element_id)
    if d is None:
        return {"error": f"unknown element {element_id!r}; known: {sorted(service.defs)}"}
    if d.route != "extract":
        return {"error": f"{element_id} is imported from the structured record, not proposed from documents"}

    candidate = Proposal(element_id=element_id, value=value, unit=unit, scope=scope, product_id=product_id,
                         evidence=Evidence(source=doc.name, quote=quote), method=Method.AI,
                         produced_by="mcp-client")
    service.extractor = _CandidateExtractor(element_id, doc.name, candidate)
    service.start_run([VENDOR / SOURCE_MAP[_resolve(source_id)][0]])
    service.prepare_product()
    r = service.records[element_id]

    kept = any(p.id == candidate.id for p in r.proposals)
    dropped = next((e.detail for e in r.log if e.action == "dropped unsupported proposal"), None)
    return _mask({
        "element_id": element_id,
        "element": d.description,
        "source_id": source_id,
        "source_sha256": doc.sha256,
        "quote_found": kept,
        "dropped_reason": None if kept else dropped,
        "checks": [{"name": c.name, "passed": c.passed, "reason": c.message} for c in r.checks],
        "state": r.state.value,
        "state_source": FROZEN,
        "not_executed": NOT_EXECUTED,
        "note": "'checked' means the configured checks passed; it does not mean DPP-ready.",
    })


if __name__ == "__main__":
    mcp.run()