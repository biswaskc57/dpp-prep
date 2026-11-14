"""Run the frozen dpp-prep demonstrator on real public documents (phase 3, post hoc).

Nothing in ../dpp-prep is changed: this script only imports it. Product-specific settings
(product identifier, reference size, which documents) are configuration in config/.
The element rules for E03 and E06 are copied unchanged from dpp-prep/config/elements_w100.yaml.

    python run_real.py --extractor standin                     # dry run of the plumbing (no model)
    python run_real.py --extractor ollama --model qwen3.5:9b   # real run
Writes out/evaluation_<label>_real_md_<stamp>.csv (+ .sqlite diary, + raw model answers .jsonl),
in the same format as dpp-prep's evaluate.py, so dpp-prep-dmn/run_cases.py can read it.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
_CANDIDATES = [os.environ.get("DPP_PREP"), HERE.parent / "dpp-prep",
               HERE.parent / "dpp-prep-mcp" / "vendor" / "dpp-prep-08d5840"]   # frozen read-only copy
DPP = next(Path(c).resolve() for c in _CANDIDATES if c and (Path(c) / "src" / "dpp_prep").exists())
sys.path.insert(0, str(DPP / "src"))

from dpp_prep.audit import AuditStore                                      # noqa: E402
from dpp_prep.extract import StandInExtractor                              # noqa: E402
from dpp_prep.ollama_extract import DEFAULT_HOST, OllamaExtractor, ResponseRecorder  # noqa: E402
from dpp_prep.profile import load_profile                                  # noqa: E402
from dpp_prep.service import PreparationService                            # noqa: E402

SCENARIOS = HERE / "config" / "real_scenarios.yaml"
EXAMPLES = DPP / "config" / "langextract_examples.yaml"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", choices=["standin", "ollama"], default="standin")
    ap.add_argument("--model")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--num-ctx", type=int, default=24576, help="frozen evaluation used 8192; real EPDs are longer")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per model call (long documents)")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--only", help="run one scenario, e.g. cetonia")
    a = ap.parse_args()
    if a.extractor == "ollama" and not a.model:
        ap.error("--model is required with --extractor ollama")

    scenarios = {k: v for k, v in yaml.safe_load(SCENARIOS.read_text(encoding="utf-8")).items()
                 if not k.startswith("_") and (not a.only or k == a.only)}
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = "standin" if a.extractor == "standin" else f"ollama-{a.model}".replace(":", "-").replace("/", "-")
    audit = AuditStore(str(out / f"evaluation_{label}_real_{stamp}.sqlite"))
    recorder = ResponseRecorder(out / f"model_outputs_{label}_real_{stamp}.jsonl") if a.extractor == "ollama" else None
    print(f"dpp-prep used (read only): {DPP}")
    rows = []
    for run in range(1, a.runs + 1):
        for name, sc in scenarios.items():
            profile = HERE / "config" / sc["profile"]
            _, defs = load_profile(profile)
            if a.extractor == "standin":
                ext = StandInExtractor(DPP / "config/standin_patterns_w100.yaml")
            else:
                ext = OllamaExtractor(a.model, defs, EXAMPLES, host=a.host, seed=a.seed,
                                      recorder=recorder, num_ctx=a.num_ctx, timeout=a.timeout)
                ext.run_label = f"real/run{run}/{name}"
            svc = PreparationService(profile, ext, audit=audit)
            run_id = svc.start_run([HERE / "docs" / d for d in sc["docs"]])
            svc.prepare_product()
            for eid, r in svc.records.items():
                expected = sc.get("expect", {}).get(eid, "?")
                rows.append({"tier": "real", "run": run, "scenario": name, "run_id": run_id, "element": eid,
                             "expected": expected, "actual": r.state.value, "match": expected == r.state.value,
                             "values": " | ".join(p.value for p in r.proposals), "dropped": len(r.rejected),
                             "failed_checks": "; ".join(c.name for c in r.checks if not c.passed),
                             "messages": " | ".join(c.message for c in r.checks if not c.passed)})
            print(f"run {run} {name}: " + ", ".join(f"{e}={r.state.value}" for e, r in svc.records.items()), flush=True)
    path = out / f"evaluation_{label}_real_md_{stamp}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{sum(r['match'] for r in rows)} of {len(rows)} outcomes matched the pre-registered expectation")
    print(f"results: {path}")


if __name__ == "__main__":
    main()
