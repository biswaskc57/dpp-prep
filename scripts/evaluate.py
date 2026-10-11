"""Evaluation runner: every scenario, several runs, outcome vs expectation.

    python scripts/evaluate.py                          # stand-in extractor
    python scripts/evaluate.py --extractor langextract --model gemini-2.5-flash --runs 3
    python scripts/evaluate.py --format pdf
    python scripts/evaluate.py --extractor ollama --model qwen3.5:9b --runs 3      # local model (v0.3.1)
    python scripts/evaluate.py --replay out/model_outputs_<...>.jsonl            # repeat a saved run exactly

For LangExtract, set the API key first: export LANGEXTRACT_API_KEY=...
For Ollama, the Ollama app must be running and the model pulled (ollama pull <model>).
Writes out/evaluation_<extractor>_<timestamp>.csv and a diary database; for Ollama
also out/model_outputs_<...>.jsonl with every raw model answer, for replay.
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
from dpp_prep.ollama_extract import (DEFAULT_HOST, OllamaExtractor,  # noqa: E402
                                     ReplayResponses, ResponseRecorder)
from dpp_prep.profile import load_profile             # noqa: E402
from dpp_prep.service import PreparationService       # noqa: E402

PROFILE = ROOT / "config/elements_w100.yaml"
DOCS = ["D1_datasheet", "D2_supplier_declaration", "D3_performance_report"]


EXAMPLES = ROOT / "config/langextract_examples.yaml"


def make_extractor(kind: str, model: str | None):
    if kind == "standin":
        return StandInExtractor(ROOT / "config/standin_patterns_w100.yaml")
    _, defs = load_profile(PROFILE)
    return LangExtractExtractor(model, defs, EXAMPLES)


def ollama_factory(model: str, recorder=None, transport=None, host: str = DEFAULT_HOST, seed: int = 42):
    """One fresh extractor per scenario, sharing the recorder (or the replay file)."""
    _, defs = load_profile(PROFILE)
    return lambda: OllamaExtractor(model, defs, EXAMPLES, host=host, seed=seed,
                                   recorder=recorder, transport=transport)


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
    label = kind if kind == "standin" else f"{kind}-{model}".replace(":", "-").replace("/", "-")
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
    ap.add_argument("--extractor", choices=["standin", "langextract", "ollama"], default="standin")
    ap.add_argument("--model", default=None, help="model id, e.g. gemini-3.8-flash or qwen3.5:9b")
    ap.add_argument("--host", default=DEFAULT_HOST, help="Ollama address")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--replay", default=None, help="saved model_outputs_*.jsonl to repeat a run without the model")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--format", choices=["md", "pdf"], default="md")
    a = ap.parse_args()
    factory = None
    kind, model = a.extractor, a.model
    if a.replay:
        replay = ReplayResponses(a.replay)
        kind, model = "replay", replay.model
        factory = ollama_factory(replay.model, transport=replay)
        print(f"replaying {len(replay.entries)} saved answers from {replay.model} ({replay.digest})")
    elif a.extractor in ("langextract", "ollama") and not a.model:
        ap.error(f"--model is required with --extractor {a.extractor}")
    elif a.extractor == "ollama":
        safe = a.model.replace(":", "-").replace("/", "-")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rec_path = ROOT / "out" / f"model_outputs_ollama-{safe}_{a.format}_{stamp}.jsonl"
        factory = ollama_factory(a.model, recorder=ResponseRecorder(rec_path), host=a.host, seed=a.seed)
        print(f"model {a.model}; digest {factory().digest()}; raw answers -> {rec_path.relative_to(ROOT)}")
    csv_path, rows = evaluate(kind, model, a.runs, a.format, extractor_factory=factory)
    matched = sum(r["match"] for r in rows)
    print(f"{matched} of {len(rows)} element outcomes matched the expectation")
    for r in rows:
        if not r["match"]:
            print(f"  run {r['run']} {r['scenario']} {r['element']}: expected {r['expected']}, "
                  f"got {r['actual']} ({r['failed_checks'] or r['values'] or 'no value'})")
    print(f"results: {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
