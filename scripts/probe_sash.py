"""Post-hoc probe of the sash-only case (thesis 6.4.4, Figure 6.x row D).

NOT part of the pre-registered evaluation. Designed on 18 October 2026, after
inspecting the results of the 17-18 October model runs. Uses the frozen
evidence check and rule checks (dpp-prep v0.3.2, commit 2be1ea5) unchanged.

The recorded proposal: gemma4:12b (digest 6114515d...), production-like tier,
scenario real_sash_only, element E03, document R2b_supplier_declaration_sash_only;
identical in all three runs (model_outputs_ollama-gemma4-12b_realistic_md_20261018-023008.jsonl).
In the run, the model reported product id "PP-SA-100" (the sash part number).

The probe runs the same checks the preparation service runs (keep_grounded,
then run_checks and all_passed) twice:
  1. as recorded, product id PP-SA-100
  2. counterfactual, product id W-100, everything else unchanged

    python scripts/probe_sash.py            # prints both results
    python scripts/probe_sash.py --write    # also saves docs/evaluation/probe_sash_result.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.checks import all_passed, run_checks       # noqa: E402
from dpp_prep.models import Evidence, Proposal           # noqa: E402
from dpp_prep.profile import load_profile                # noqa: E402
from dpp_prep.sources import load_sources                # noqa: E402
from dpp_prep.verify import keep_grounded                # noqa: E402

DOC = ROOT / "data/w100/realistic/R2b_supplier_declaration_sash_only.md"
ELEMENT = "E03"
EXPECTED_PRODUCT = "W-100"
VALUE = "pine wood 74 %, aluminium 21 %, EPDM seals 4 %, steel fittings 1 %."
QUOTE = ("Sash profile set, share of sash mass: pine wood 74 %, aluminium 21 %, "
         "EPDM seals 4 %, steel fittings 1 %.")


def run(product_id: str) -> dict:
    _, defs = load_profile(ROOT / "config/elements_w100.yaml")
    d = defs[ELEMENT]
    sources = load_sources([DOC])
    p = Proposal(element_id=ELEMENT, value=VALUE, product_id=product_id,
                 evidence=Evidence(source=DOC.name, quote=QUOTE), produced_by="gemma4:12b (recorded)")
    kept, dropped = keep_grounded([p], sources)
    if not kept:
        return {"product_id": product_id, "quote_found": False, "failed_checks": [],
                "state": "unresolved", "reason": dropped[0][1]}
    results = run_checks(d, kept, EXPECTED_PRODUCT)
    return {"product_id": product_id, "quote_found": True,
            "checks": {c.name: c.passed for c in results},
            "failed_checks": [c.name for c in results if not c.passed],
            "state": "checked" if all_passed(results) else "flagged"}


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    out = {"probe": "sash-only E03, post hoc (not pre-registered)", "frozen_code": "v0.3.2 (2be1ea5)",
           "element": ELEMENT, "document": DOC.name, "value": VALUE, "quote": QUOTE,
           "recorded": run("PP-SA-100"), "counterfactual": run(EXPECTED_PRODUCT)}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if "--write" in argv:
        path = ROOT / "docs/evaluation/probe_sash_result.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"written to {path}")


if __name__ == "__main__":
    main()
