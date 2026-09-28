"""Suggester slot (AI step) and the direct-import route.

Any extractor returns Proposals. Nothing an extractor says is trusted:
every proposal passes through verify.keep_grounded() and checks.support().

StandInExtractor   deterministic, pattern-based; lets the controls be tested
                   before the AI model is connected. NOT the research object.
LangExtractExtractor  slot for the real AI step (model provider still open).
StructuredImporter the non-AI route: values taken directly from a record.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

import yaml

from .models import ElementDefinition, Evidence, Method, Proposal, SourceDocument
from .verify import keep_grounded  # re-exported for callers and tests

__all__ = ["Extractor", "StandInExtractor", "LangExtractExtractor", "StructuredImporter", "keep_grounded"]


class Extractor(Protocol):
    name: str
    def propose(self, d: ElementDefinition, doc: SourceDocument) -> list[Proposal]: ...


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start:end if end >= 0 else len(text)].strip()


class StandInExtractor:
    name = "standin-patterns-v0.2"

    def __init__(self, patterns_path: str | Path):
        cfg = yaml.safe_load(Path(patterns_path).read_text(encoding="utf-8"))
        self.product_re = re.compile(cfg["product_id"])
        self.patterns = cfg["elements"]

    def propose(self, d: ElementDefinition, doc: SourceDocument) -> list[Proposal]:
        spec = self.patterns.get(d.id)
        if not spec or doc.kind != "document":
            return []
        m = re.search(spec["value"], doc.text, re.M)
        if not m:
            return []
        pid = self.product_re.search(doc.text)
        scope = context = None
        if "context" in spec:
            c = re.search(spec["context"], doc.text)
            if c:
                scope, context = c.group(1), _line_of(doc.text, c.start())
        value = m.group(1).replace(",", ".") if d.value_type == "number" else m.group(1)
        return [Proposal(
            element_id=d.id, value=value, unit=d.unit, scope=scope,
            product_id=pid.group(1) if pid else None, method=Method.AI, produced_by=self.name,
            evidence=Evidence(source=doc.name, quote=_line_of(doc.text, m.start()), context_quote=context),
        )]


class LangExtractExtractor:
    """The real AI step, using LangExtract.

    One LangExtract call per document extracts all 'extract'-route elements at
    once. Design decisions:
      * Only extractions LangExtract could anchor to a character position in
        the document become Proposals. Anything else (e.g. inferred from the
        model's own knowledge) is discarded and written to raw_log.
      * The quote is the full source line(s) around the anchored span, so the
        support check sees the label and unit, not just the number.
      * Few-shot examples use a different fictitious product, so the evaluation
        is not contaminated by showing the model W-100's answers.
    Nothing returned here is trusted: keep_grounded() and checks.support()
    re-verify every proposal.

    The API key is read from the environment variable LANGEXTRACT_API_KEY
    unless passed explicitly.
    """

    PRODUCT_CLASS = "document_product_id"

    def __init__(self, model_id: str, defs: dict, examples_path: str | Path,
                 api_key: str | None = None, **lx_kwargs):
        self.model_id = model_id
        self.name = f"langextract:{model_id}"
        self.defs = {d.name: d for d in defs.values() if d.route == "extract"}
        self.examples_path = Path(examples_path)
        self.api_key = api_key
        self.lx_kwargs = lx_kwargs
        self.raw_log: list[dict] = []
        self._cache: dict[str, object] = {}

    def prompt(self) -> str:
        lines = [
            "Extract the following product information from the document.",
            "Use exact text from the document for every extraction.",
            "Do not infer, calculate or use outside knowledge. If an item is not stated, do not extract it.",
            "A value for a part (for example a glazing-only Ug value) is not a value for the whole product.",
            "Set the attribute 'value' to the value only; add 'unit' and 'scope' when the document states them.",
            f"- {self.PRODUCT_CLASS}: the product identifier the document is about",
        ]
        lines += [f"- {n}: {d.description}" for n, d in self.defs.items()]
        return "\n".join(lines)

    def examples(self):
        import langextract as lx
        cfg = yaml.safe_load(self.examples_path.read_text(encoding="utf-8"))
        return [lx.data.ExampleData(text=cfg["text"], extractions=[
            lx.data.Extraction(extraction_class=e["class"], extraction_text=e["text"],
                               attributes=e.get("attributes") or {})
            for e in cfg["extractions"]])]

    def _annotate(self, doc: SourceDocument):
        if doc.sha256 in self._cache:
            return self._cache[doc.sha256]
        import langextract as lx
        result = lx.extract(text_or_documents=doc.text, prompt_description=self.prompt(),
                            examples=self.examples(), model_id=self.model_id,
                            api_key=self.api_key, **self.lx_kwargs)
        self._cache[doc.sha256] = result
        self.raw_log.append({"source": doc.name, "model": self.model_id, "extractions": [
            {"class": e.extraction_class, "text": e.extraction_text, "attributes": e.attributes,
             "span": [e.char_interval.start_pos, e.char_interval.end_pos] if e.char_interval else None,
             "alignment": getattr(e.alignment_status, "name", None)}
            for e in (result.extractions or [])]})
        return result

    @staticmethod
    def _grounded(e) -> bool:
        """Anchored to a real, non-empty stretch of the document."""
        ci = e.char_interval
        return (ci is not None and ci.start_pos is not None and ci.end_pos is not None
                and ci.end_pos > ci.start_pos and bool((e.extraction_text or "").strip()))

    @staticmethod
    def _lines_around(text: str, start: int, end: int) -> str:
        a = text.rfind("\n", 0, start) + 1
        b = text.find("\n", end)
        return text[a:b if b >= 0 else len(text)].strip()

    def propose(self, d: ElementDefinition, doc: SourceDocument) -> list[Proposal]:
        if doc.kind != "document" or d.name not in self.defs:
            return []
        result = self._annotate(doc)
        extractions = result.extractions or []
        pid = next((e.extraction_text.strip() for e in extractions
                    if e.extraction_class == self.PRODUCT_CLASS and self._grounded(e)), None)
        proposals = []
        for e in extractions:
            if e.extraction_class != d.name or not self._grounded(e):
                continue
            attrs = e.attributes or {}
            value = str(attrs.get("value") or e.extraction_text).strip()
            if d.value_type == "number":
                value = value.replace(",", ".")
            scope = attrs.get("scope")
            context = None
            if scope:
                i = doc.text.find(str(scope))
                context = self._lines_around(doc.text, i, i + len(str(scope))) if i >= 0 else None
            quote = self._lines_around(doc.text, e.char_interval.start_pos, e.char_interval.end_pos)
            proposals.append(Proposal(
                element_id=d.id, value=value, unit=attrs.get("unit") or d.unit,
                scope=str(scope) if scope else None, product_id=pid,
                method=Method.AI, produced_by=self.name,
                evidence=Evidence(source=doc.name, quote=quote, context_quote=context)))
        return proposals


class StructuredImporter:
    """Non-AI route: take the value straight from a structured record."""
    name = "structured-import-v0.2"

    def propose(self, d: ElementDefinition, doc: SourceDocument, product_id_field: str = "product_id") -> list[Proposal]:
        if doc.kind != "structured" or not doc.data or d.import_field not in doc.data:
            return []
        value = str(doc.data[d.import_field])
        unit = doc.data.get("size_unit") if d.unit else None
        return [Proposal(
            element_id=d.id, value=value, unit=unit, product_id=doc.data.get(product_id_field),
            method=Method.IMPORT, produced_by=self.name,
            evidence=Evidence(source=doc.name, field=d.import_field, quote=f"{d.import_field}: {value}"),
        )]
