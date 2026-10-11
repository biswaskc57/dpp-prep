"""Quick check before a full evaluation: is Ollama reachable, is the model there,
and does one document come back as usable proposals?

    python scripts/check_ollama.py --model qwen3.5:9b

Sends ONE document (the baseline datasheet) and prints what the model proposed
and whether each proposal survives the evidence check. Nothing is saved.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.ollama_extract import DEFAULT_HOST, OllamaExtractor  # noqa: E402
from dpp_prep.profile import load_profile                           # noqa: E402
from dpp_prep.sources import load_sources                           # noqa: E402
from dpp_prep.verify import keep_grounded                           # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default=DEFAULT_HOST)
    a = ap.parse_args()
    _, defs = load_profile(ROOT / "config/elements_w100.yaml")
    ext = OllamaExtractor(a.model, defs, ROOT / "config/langextract_examples.yaml", host=a.host)
    print(f"model {a.model}; digest {ext.digest() or 'NOT FOUND - run: ollama pull ' + a.model}")
    sources = load_sources([ROOT / "data/w100/baseline/D1_datasheet.md"])
    doc = next(iter(sources.values()))
    for d in defs.values():
        if d.route != "extract":
            continue
        props = ext.propose(d, doc)
        kept, dropped = keep_grounded(props, sources)
        for p in kept:
            print(f"  {d.id} {d.name}: {p.value!r}  quote found: {p.evidence.quote!r}")
        for p, why in dropped:
            print(f"  {d.id} {d.name}: {p.value!r}  DROPPED ({why})")
        if not props:
            print(f"  {d.id} {d.name}: nothing proposed")
    e = ext.raw_log[0]
    print(f"answer took {e['seconds']} s; parse error: {e['parse_error']}")


if __name__ == "__main__":
    main()
