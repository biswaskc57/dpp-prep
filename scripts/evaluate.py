"""Evaluation runner: every scenario, several runs, outcome vs expectation.

    python scripts/evaluate.py                          # stand-in extractor
    python scripts/evaluate.py --extractor langextract --model gemini-2.5-flash --runs 3
    python scripts/evaluate.py --format pdf

For LangExtract, set the API key first: export LANGEXTRACT_API_KEY=...
Writes out/evaluation_<extractor>_<timestamp>.csv and a diary database.
Every run is kept, including unexpected outcomes; nothing is filtered.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.audit import AuditStore                 # noqa: E402
from dpp_prep.extract import LangExtractExtractor, StandInExtractor  # noqa: E402
from dpp_prep.profile import load_profile             # noqa: E402
from dpp_prep.service import PreparationService       # noqa: E402

PROFILE = ROOT / "config/elements_w100.yaml"
DOCS = ["D1_datasheet", "D2_supplier_declaration", "D3_performance_report"]


def make_extractor(kind: str, model: str | None):
    if kind == "standin":
        return StandInExtractor(ROOT / "config/standin_patterns_w100.yaml")
    _, defs = load_profile(PROFILE)
    return LangExtractExtractor(model, defs, ROOT / "config/langextract_examples.yaml")


def paths(swap: dict, fmt: str) -> list[Path]:
    out = []
    for n in DOCS:
        name = swap.get(n, n)
        if fmt == "pdf":
            out.append(ROOT / "data/w100/pdf" / f"{name}.pdf")
        else:
            folder = "variants" if n in swap else "baseline"
            out.append(ROOT / "data/w100" / folder / f"{name}.md")
    return out + [ROOT / "data/w100/structured/erp_product_record.json"]


def evaluate(kind: str = "standin", model: str | None = None, runs: int = 1, fmt: str = "md",
             out_dir: Path = ROOT / "out", extractor_factory=None) -> tuple[Path, list[dict]]:
    scenarios = yaml.safe_load((ROOT / "config/evaluation_scenarios.yaml").read_text(encoding="utf-8"))
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = kind if kind == "standin" else f"{kind}-{model}"
    audit = AuditStore(str(out_dir / f"evaluation_{label}_{stamp}.sqlite"))
    rows = []
    for run in range(1, runs + 1):
        for name, sc in scenarios.items():
            ext = extractor_factory() if extractor_factory else make_extractor(kind, model)
            svc = PreparationService(PROFILE, ext, audit=audit)
            run_id = svc.start_run(paths(sc["swap"], fmt))
            svc.prepare_product()
            for eid, r in svc.records.items():
                expected = sc["expect"].get(eid, "checked")
                rows.append({
                    "run": run, "scenario": name, "run_id": run_id, "element": eid,
                    "expected": expected, "actual": r.state.value,
                    "match": expected == r.state.value,
                    "values": " | ".join(p.value for p in r.proposals),
                    "dropped": len(r.rejected),
                    "failed_checks": "; ".join(f"{c.name}" for c in r.checks if not c.passed),
                })
    csv_path = out_dir / f"evaluation_{label}_{fmt}_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return csv_path, rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", choices=["standin", "langextract"], default="standin")
    ap.add_argument("--model", default=None, help="model id for LangExtract, e.g. gemini-2.5-flash")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--format", choices=["md", "pdf"], default="md")
    a = ap.parse_args()
    if a.extractor == "langextract" and not a.model:
        ap.error("--model is required with --extractor langextract")
    csv_path, rows = evaluate(a.extractor, a.model, a.runs, a.format)
    matched = sum(r["match"] for r in rows)
    print(f"{matched} of {len(rows)} element outcomes matched the expectation")
    for r in rows:
        if not r["match"]:
            print(f"  run {r['run']} {r['scenario']} {r['element']}: expected {r['expected']}, "
                  f"got {r['actual']} ({r['failed_checks'] or r['values'] or 'no value'})")
    print(f"results: {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
