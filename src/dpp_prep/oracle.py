"""Oracle proposer: proposes exactly what each document states (ground truth).

Not AI and not a research object. It is used to PRE-REGISTER expected outcomes:
running the oracle through the unchanged controls shows what those controls
do with faithful proposals, before any model sees the documents. Any later
difference between a model run and the oracle run is then caused by the model.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import ElementDefinition, Evidence, Method, Proposal, SourceDocument
from .ollama_extract import _lines_around, _span


class OracleExtractor:
    name = "oracle-ground-truth"

    def __init__(self, ground_truth_path: str | Path):
        self.gt = yaml.safe_load(Path(ground_truth_path).read_text(encoding="utf-8"))["documents"]

    def propose(self, d: ElementDefinition, doc: SourceDocument) -> list[Proposal]:
        if doc.kind != "document":
            return []
        entry = self.gt.get(Path(doc.name).stem)
        if entry is None:
            raise KeyError(f"no ground truth for document {doc.name}")
        out = []
        for s in entry.get("statements") or []:
            if s["element"] != d.id:
                continue
            span = _span(doc.text, s["quote"])
            if span is None:
                raise ValueError(f"ground-truth quote not found in {doc.name}: {s['quote']!r}")
            scope = s.get("scope") or None
            context = None
            if scope:
                c = _span(doc.text, scope)
                context = _lines_around(doc.text, *c) if c else None
            out.append(Proposal(
                element_id=d.id, value=str(s["value"]), unit=s.get("unit") or d.unit, scope=scope,
                product_id=entry["product"], method=Method.AI, produced_by=self.name,
                evidence=Evidence(source=doc.name, quote=_lines_around(doc.text, *span), context_quote=context)))
        return out
