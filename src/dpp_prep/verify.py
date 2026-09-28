"""Fact-checker, part 1: is the quote really in the source? (R02, R03, R04)

Plain code, not AI. A proposal survives only if its quote (and its context
quote, if any) can be found in the named source. When found, the position
and the document fingerprint are stored, so the evidence can be traced later.
For structured records, the named field must hold exactly the proposed value.

Whether the quote actually *supports* the value is checked separately, in
checks.support(), because a real quote can still be misused for a wrong value.
"""
from __future__ import annotations

import re
from typing import Union

from .models import Proposal, SourceDocument

Sources = dict[str, Union[str, SourceDocument]]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def locate(quote: str, text: str) -> tuple[int, int] | None:
    """Find a quote in a text, tolerant of whitespace and case. Returns positions
    in the normalised text, which is enough to show where the quote sits."""
    q, t = _norm(quote), _norm(text)
    if not q:
        return None
    i = t.find(q)
    return (i, i + len(q)) if i >= 0 else None


def _as_doc(name: str, src: Union[str, SourceDocument]) -> SourceDocument:
    return src if isinstance(src, SourceDocument) else SourceDocument(name=name, text=src)


def verify_grounding(p: Proposal, sources: Sources) -> tuple[bool, str]:
    raw = sources.get(p.evidence.source)
    if raw is None:
        return False, f"source {p.evidence.source!r} not provided"
    doc = _as_doc(p.evidence.source, raw)

    if doc.kind == "structured":
        field = p.evidence.field
        if not field or not doc.data or field not in doc.data:
            return False, f"field {field!r} not in structured record"
        if str(doc.data[field]).strip() != p.value.strip():
            return False, f"field {field!r} holds {doc.data[field]!r}, not {p.value!r}"
        p.evidence.doc_sha256 = doc.sha256
        return True, ""

    span = locate(p.evidence.quote, doc.text)
    if not span:
        return False, "quote not found in source"
    if p.evidence.context_quote and not locate(p.evidence.context_quote, doc.text):
        return False, "context quote not found in source"
    p.evidence.start, p.evidence.end = span
    p.evidence.doc_sha256 = doc.sha256
    if doc.pages:
        p.evidence.page = next((i for i, page in enumerate(doc.pages, 1)
                                if locate(p.evidence.quote, page)), None)
    return True, ""


def keep_grounded(proposals: list[Proposal], sources: Sources) -> tuple[list[Proposal], list[tuple[Proposal, str]]]:
    """Split proposals into those whose evidence is found in the source and those
    that are not. Dropped proposals are returned with the reason, so they can be
    written to the audit record rather than silently discarded."""
    kept, dropped = [], []
    for p in proposals:
        ok, reason = verify_grounding(p, sources)
        if ok:
            kept.append(p)
        else:
            dropped.append((p, reason))
    return kept, dropped
