"""Handover (R10): only approved, unchanged, still-valid records leave the tool.

build_export() only *builds* the package; it changes nothing. Releasing
(marking records as released and writing the file) requires a named approver
and happens in PreparationService.release(). The package is validated against
a versioned JSON Schema; passing it shows structural conformity only, not
factual correctness or regulatory compliance.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import jsonschema

from .models import Record, State, now
from .states import _release_problems

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "handover_v0.2.schema.json"


def releasable(r: Record) -> tuple[bool, str]:
    if r.state != State.APPROVED:
        return False, f"not approved (state: {r.state.value})"
    problems = _release_problems(r)
    return (not problems), "; ".join(problems)


def build_export(product_id: str, records: list[Record], names: Optional[dict[str, str]] = None,
                 run_id: str = "unspecified", profile_version: str = "unspecified",
                 released_by: str = "unspecified") -> "Package":
    included, excluded = [], {}
    for r in records:
        ok, reason = releasable(r)
        if not ok:
            excluded[r.element_id] = reason
            continue
        p = r.selected
        span = [p.evidence.start, p.evidence.end] if p.evidence.start is not None else None
        included.append({
            "element_id": r.element_id, "name": (names or {}).get(r.element_id, r.element_id),
            "value": p.value, "unit": p.unit, "scope": p.scope, "method": p.method.value,
            "source": p.evidence.source, "doc_sha256": p.evidence.doc_sha256, "span": span,
            "quote": p.evidence.quote, "reviewed_by": r.review.reviewer_id,
            "approved_by": r.approval.approver_id, "record_version": r.version,
        })
    return Package({
        "schema_version": "0.2", "product_id": product_id, "profile_version": profile_version,
        "run_id": run_id, "generated_at": now(), "released_by": released_by,
        "elements": included, "excluded": excluded,
    })


class Package(dict):
    @property
    def elements(self) -> list[dict]:
        return self["elements"]

    @property
    def excluded(self) -> dict[str, str]:
        return self["excluded"]

    def validate(self, schema_path: Path = SCHEMA_PATH) -> None:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        jsonschema.validate(self, schema)

    def write(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self, indent=2, ensure_ascii=False), encoding="utf-8")
