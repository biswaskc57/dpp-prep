"""Turn the W-100 Markdown test documents into PDFs (reproducible).

Markdown markup is stripped so the PDFs look like ordinary documents. In the
performance report, everything from "## Thermal transmittance" onwards is put
on page 2, so that page tracking in the evidence is genuinely tested.

Run from the project root:  python scripts/make_pdfs.py
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SETS = [([ROOT / "data/w100/baseline", ROOT / "data/w100/variants"], ROOT / "data/w100/pdf"),
        ([ROOT / "data/w100/realistic"], ROOT / "data/w100/pdf_realistic")]      # realistic tier: v0.3.1
PAGE_BREAK_BEFORE = ("## Thermal transmittance", "## 3. Result", "## 6. Declared performance", "## Technical data")


def plain(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line)
    return line.replace("**", "").replace("*", "").rstrip()


def to_pdf(md: Path, out: Path) -> None:
    lines = md.read_text(encoding="utf-8").splitlines()
    pages, current = [], []
    for line in lines:
        if line.startswith(PAGE_BREAK_BEFORE) and current:
            pages.append(current)
            current = []
        current.append(plain(line))
    pages.append(current)
    doc = pymupdf.open()
    for page_lines in pages:
        page = doc.new_page(width=595, height=842)          # A4
        y = 72
        for text in page_lines:
            for part in textwrap.wrap(text, 88, break_on_hyphens=False, break_long_words=False) or [""]:   # wrap long lines as a real document would
                if y > 800:
                    page = doc.new_page(width=595, height=842)
                    y = 72
                page.insert_text((72, y), part, fontsize=10, fontname="helv")
                y += 14
    doc.set_metadata({"title": md.stem, "subject": "Fictitious W-100 test document"})
    doc.save(out, garbage=4, deflate=True)
    doc.close()


def main() -> None:
    for folders, out in SETS:
        out.mkdir(parents=True, exist_ok=True)
        for folder in folders:
            for md in sorted(folder.glob("*.md")):
                to_pdf(md, out / f"{md.stem}.pdf")
                print("wrote", (out / f"{md.stem}.pdf").relative_to(ROOT))


if __name__ == "__main__":
    main()
