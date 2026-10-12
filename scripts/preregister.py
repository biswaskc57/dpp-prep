"""Pre-register expected outcomes for the realistic tier, before any model run.

1. Validation: the oracle (proposes exactly what each document states) is run
   on the simple tier; it must reproduce all expectations written in
   September 2026. This shows the oracle method gives the same expectations as
   the hand-written ones.
2. Pre-registration: the oracle is run on the realistic tier through the
   UNCHANGED controls. The resulting end states are written into
   config/evaluation_scenarios_realistic.yaml as the expectations, together
   with the date and the SHA-256 of every document, so that any later change
   to a document is visible.

    python scripts/preregister.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts/evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def main() -> None:
    out = ROOT / "out" / "preregistration"
    _, rows = ev.evaluate("oracle", None, 1, "md", out_dir=out, tier="simple")
    bad = [r for r in rows if not r["match"]]
    print(f"validation on simple tier: {len(rows) - len(bad)} of {len(rows)} expectations reproduced by the oracle")
    for r in bad:
        print(f"  MISMATCH {r['scenario']} {r['element']}: expected {r['expected']}, oracle {r['actual']}")
    if bad:
        sys.exit("oracle does not reproduce the simple-tier expectations; not pre-registering")

    path = ev.SCENARIO_FILES["realistic"]
    scenarios = {k: v for k, v in yaml.safe_load(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    for fmt in ("md", "pdf"):
        _, rows = ev.evaluate("oracle", None, 1, fmt, out_dir=out, tier="realistic")
        for name, sc in scenarios.items():
            key = "expect" if fmt == "md" else "expect_pdf"
            sc[key] = {r["element"]: r["actual"] for r in rows
                       if r["scenario"] == name and r["actual"] != "checked"}
            sc.setdefault("reasons", {})
            for r in rows:
                if r["scenario"] == name and r["actual"] != "checked" and fmt == "md":
                    sc["reasons"][r["element"]] = r["failed_checks"] or "no supported value"
    docs = sorted({d for sc in scenarios.values() for d in sc["docs"]})
    hashes = {d: hashlib.sha256((ROOT / "data/w100/realistic" / f"{d}.md").read_bytes()).hexdigest() for d in docs}
    header = ("# Production-like tier (added 12 Oct 2026, v0.3.1).\n"
              f"# Expectations PRE-REGISTERED by scripts/preregister.py on {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
              "# by running the oracle (faithful proposals from config/ground_truth.yaml) through the\n"
              "# unchanged controls, before any language model saw these documents.\n"
              "# expect: Markdown documents; expect_pdf: the PDF versions. Elements not listed: checked.\n"
              "# reasons: which control produced a non-checked state for a faithful proposal.\n")
    body = yaml.safe_dump({**scenarios, "_document_sha256": hashes}, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(header + body, encoding="utf-8")
    for name, sc in scenarios.items():
        print(f"{name}: expect {sc['expect'] or 'all checked'}; pdf {sc['expect_pdf'] or 'all checked'}")
        for e, why in sc["reasons"].items():
            print(f"    {e}: {why}")


if __name__ == "__main__":
    main()
