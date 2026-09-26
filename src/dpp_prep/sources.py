"""Load source documents and structured records, with fingerprints.

.md / .txt   plain text documents
.pdf         PDFs, read page by page with PyMuPDF, so evidence can name its page.
             Docling (layout and tables) is the planned upgrade for complex PDFs;
             it is not wired in yet.
.json        structured records, e.g. an ERP export (the no-AI import route)
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import SourceDocument


def _read_pdf(p: Path) -> list[str]:
    import pymupdf
    with pymupdf.open(p) as doc:
        return [page.get_text() for page in doc]


def load_source(path: str | Path) -> SourceDocument:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        pages = _read_pdf(p)
        return SourceDocument(name=p.name, kind="document", text="\n".join(pages), pages=pages)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return SourceDocument(name=p.name, kind="structured", text=text, data=json.loads(text))
    return SourceDocument(name=p.name, kind="document", text=text)


def load_sources(paths) -> dict[str, SourceDocument]:
    docs = [load_source(p) for p in paths]
    return {d.name: d for d in docs}
