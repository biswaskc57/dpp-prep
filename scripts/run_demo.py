"""End-to-end demo for W-100, printed as a readable story.

Scenario: the performance report states a different Uw than the datasheet
(a conflict), and the supplier's frame composition adds up to only 95 %.

Run from the project root:  python scripts/run_demo.py
Writes out/handover.json and out/audit.sqlite
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.audit import AuditStore                      # noqa: E402
from dpp_prep.extract import StandInExtractor              # noqa: E402
from dpp_prep.models import Actor, Role, State             # noqa: E402
from dpp_prep.service import ActionRefused, PreparationService  # noqa: E402
from dpp_prep.states import TransitionRefused              # noqa: E402

OUT = ROOT / "out"
RITA = Actor(id="rita", role=Role.REVIEWER)
AKI = Actor(id="aki", role=Role.APPROVER)


def say(step: str, text: str = "") -> None:
    print(f"\n=== {step} ===")
    if text:
        print(text)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "audit.sqlite").unlink(missing_ok=True)
    svc = PreparationService(ROOT / "config/elements_w100.yaml",
                             StandInExtractor(ROOT / "config/standin_patterns_w100.yaml"),
                             audit=AuditStore(str(OUT / "audit.sqlite")))
    base, var = ROOT / "data/w100/baseline", ROOT / "data/w100/variants"
    sources = [base / "D1_datasheet.md", var / "V2_D3_uw_conflict.md",
               var / "V5_D2_composition_95.md", ROOT / "data/w100/structured/erp_product_record.json"]

    say("1. Start", "Documents loaded and fingerprinted; run opened in the diary.")
    run_id = svc.start_run(sources)
    print(f"run id: {run_id}")

    say("2. Suggest, fact-check and rule-check every element")
    svc.prepare_product()
    for eid, r in svc.records.items():
        values = ", ".join(sorted({p.value[:40] for p in r.proposals})) or "-"
        route = svc.defs[eid].route
        print(f"{eid} {svc.defs[eid].name:<28} {route:<8} {r.state.value:<10} {values}")
        for c in r.checks:
            if not c.passed:
                print(f"      check failed: {c.name}: {c.message}")

    say("3. Reviewer rita resolves the Uw conflict",
        "She compares both values with their quotes and chooses 1.1.")
    r = svc.records["E06"]
    chosen = next(p for p in r.proposals if p.value == "1.1")
    svc.review("E06", RITA, chosen.id, evidence_inspected=True,
               note="Report value 1.3 contradicts datasheet; 1.1 confirmed with manufacturer.")
    print(f"E06 now {r.state.value}; kept but not selected: {[p.value for p in r.rejected]}")

    say("4. Reviewer tries to accept the 95 % composition")
    try:
        svc.review("E03", RITA, svc.records["E03"].proposals[0].id, evidence_inspected=True)
    except ActionRefused as e:
        print(f"refused: {e}")

    say("5. Rita reviews the remaining checked elements")
    for eid, rec in svc.records.items():
        if rec.state == State.CHECKED:
            svc.review(eid, RITA, rec.proposals[0].id, evidence_inspected=True)
    print("reviewed:", [e for e, x in svc.records.items() if x.state == State.REVIEWED])

    say("6. Rita tries to approve her own review")
    try:
        svc.approve("E06", Actor(id="rita", role=Role.APPROVER))
    except TransitionRefused as e:
        print(f"refused: {e}")

    say("7. Approver aki approves the reviewed elements")
    for eid, rec in svc.records.items():
        if rec.state == State.REVIEWED:
            svc.approve(eid, AKI)
    print("approved:", [e for e, x in svc.records.items() if x.state == State.APPROVED])

    say("8. Release: only approved, unchanged records leave the tool")
    pkg = svc.release(AKI, OUT / "handover.json")
    print("released:", [e["element_id"] for e in pkg.elements])
    for eid, why in pkg.excluded.items():
        print(f"excluded {eid}: {why}")
    print("handover file passed its schema check: out/handover.json")

    say("9. The diary")
    events = svc.audit.events(run_id)
    refused = [e for e in events if e["action"] == "refused"]
    print(f"{len(events)} events recorded, including {len(refused)} refusals, in out/audit.sqlite")


if __name__ == "__main__":
    main()
