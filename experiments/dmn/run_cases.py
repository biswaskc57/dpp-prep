"""Run the DMN readiness step on frozen dpp-prep run outputs (post hoc, illustrative; D044).

Reads   <out>/evaluation_<proposer>_*.csv  (element states and failed checks per run)
        <out>/evaluation_<proposer>_*.sqlite (check messages, for composition totals)
Writes  results/readiness_<proposer>_<tier>.csv and results/summary.md

Input derivation (documented in README; nothing here decides a status — the DMN does):
- Supported proposal exists: the element did not end 'unresolved' (a supported value was kept).
- Alignment checks: 'any failed' if identity, unit or scope failed for any candidate.
- Value type / Support check: 'failed' if that check failed for any candidate.
- All configured checks: 'any failed' if any check failed.
- Evidence inspected = False, Approval on this version = 'none': the batch runs had no human review.
- Source validity = 'unknown': the sources carry no validity rule that the runs recorded.
- Requirement statements (illustrative W-100 assumptions): approval stated required; validity not stated;
  quality stated required; quality criteria configured for E03 (composition) and E04, E06, E07 (source consistency).
- Composition criterion (E03): from composition_sum; 'none' if no shares were found (total 0 %), else 'all'
  with total within / outside tolerance. 'Partial or malformed' cannot be detected by the frozen check.
- Consistency criterion (E04, E06, E07): 'disagree' if the conflict check failed, otherwise 'agree'.
- No supported candidate → criterion 'not evaluated'.

Usage: python run_cases.py <dpp-prep out folder> [proposer ...]
"""
from __future__ import annotations

import csv
import glob
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from dmn_runner import CONDITIONS, Engine

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CRITERIA = {"E03": "composition", "E04": "consistency", "E06": "consistency", "E07": "consistency"}
REQUIREMENT = {"Approval statement": "stated required", "Validity statement": "not stated",
               "Quality statement": "stated required"}
SHORT = {"met": "met", "not met": "NOT MET", "not yet assessed": "open", "not required": "n/a"}


def composition_totals(db: Path) -> dict:
    """(run_id, element) -> list of totals from failed composition_sum messages."""
    out = {}
    if not db.exists():
        return out
    con = sqlite3.connect(db)
    for run_id, el, detail in con.execute(
            "select run_id, element_id, detail from events where action = 'checks run'"):
        for msg in json.loads(detail or "{}").get("failed", []):
            m = re.match(r"composition_sum: shares add up to ([\d.]+) %", msg)
            if m:
                out.setdefault((run_id, el), []).append(float(m.group(1)))
    return out


def criterion_inputs(element, supported, failed, totals):
    kind = CRITERIA.get(element)
    if kind is None:
        return None
    if not supported:
        return (kind, "not evaluated")
    if kind == "composition":
        if "composition_sum" not in failed:
            return (kind, "evaluated", "all", "yes")
        if any(t != 0 for t in totals):
            return (kind, "evaluated", "all", "no")
        return (kind, "evaluated", "none")
    return (kind, "evaluated", "n/a", "n/a", "disagree" if "conflict" in failed else "agree")


def readiness_of(statuses):
    if any(s == "not met" for s in statuses):
        return "not ready"
    if all(s in ("met", "not required") for s in statuses):
        return "ready"
    return "undetermined"


def run(out_dir: Path, proposers):
    eng = Engine()
    RESULTS.mkdir(exist_ok=True)
    lines = ["# DMN readiness step on frozen run outputs (post hoc, illustrative)", "",
             "Statuses: met · NOT MET · open = not yet assessed · n/a = not required. "
             "Readiness: ready = all applicable conditions met; not ready = any not met; undetermined otherwise.", ""]
    overview = ["## Overview: demonstrator state vs DMN readiness (element outcomes, all runs)", "",
                "| proposer | tier | checked → ready | checked → undetermined | checked → not ready | flagged → not ready | flagged → other | unresolved → undetermined |",
                "|---|---|---|---|---|---|---|---|"]
    for prop in proposers:
        for csv_path in sorted(set(out_dir.glob(f"evaluation_{prop}_*.csv"))):
            if "_pdf_" in csv_path.name:
                continue
            rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
            if not rows:
                continue
            tier = rows[0]["tier"]
            stem = csv_path.name.replace("_md_", "_").rsplit(".", 1)[0]
            db = out_dir / (stem + ".sqlite")
            if not db.exists():
                cands = sorted(out_dir.glob(f"evaluation_{prop}{'_realistic' if tier == 'realistic' else ''}_2*.sqlite"))
                db = cands[0] if cands else db
            totals = composition_totals(db)
            out_rows, tally = [], Counter()
            for r in rows:
                failed = set(filter(None, (x.strip() for x in r["failed_checks"].split(";"))))
                supported = r["actual"] != "unresolved"
                crit = criterion_inputs(r["element"], supported, failed, totals.get((r["run_id"], r["element"]), []))
                n = f = i = 0
                crit_res = crit_rule = ""
                if crit:
                    crit_res, crit_rule = eng.criterion_result(*crit)
                    n, f, i = 1, int(crit_res == "fail"), int(crit_res == "insufficient evidence")
                base = {**REQUIREMENT,
                        "Quality criterion configured": r["element"] in CRITERIA,
                        "Supported proposal exists": supported, "Not in sources and obtain failed": False,
                        "Alignment checks": "any failed" if failed & {"identity", "unit", "scope"} else "all passed",
                        "Value type check": "failed" if "value_type" in failed else "passed",
                        "Support check": "failed" if "support" in failed else "passed",
                        "Evidence inspected": False,
                        "All configured checks": "any failed" if failed else "all passed",
                        "Approval on this version": "none", "Source validity": "unknown",
                        "Number of criteria": n, "Failed criteria": f, "Insufficient criteria": i}
                res = eng.element(base)
                statuses = [x["status"] for x in res]
                ready = readiness_of(statuses)
                tally[(r["actual"], ready)] += 1
                out_rows.append({"tier": tier, "run": r["run"], "scenario": r["scenario"], "element": r["element"],
                                 "demonstrator_state": r["actual"], "failed_checks": r["failed_checks"],
                                 "criterion": crit[0] if crit else "", "criterion_result": crit_res, "criterion_rule": crit_rule,
                                 **{c: x["status"] for c, x in zip(CONDITIONS, res)},
                                 **{c + " rule": x["status_rule"] for c, x in zip(CONDITIONS, res)},
                                 "readiness": ready})
            overview.append(f"| {prop} | {tier} | {tally[('checked','ready')]} | {tally[('checked','undetermined')]} | "
                            f"{tally[('checked','not ready')]} | {tally[('flagged','not ready')]} | "
                            f"{sum(n for (a, b), n in tally.items() if a == 'flagged' and b != 'not ready')} | "
                            f"{tally[('unresolved','undetermined')]} |")
            target = RESULTS / f"readiness_{prop}_{tier}.csv"
            with target.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
                w.writeheader()
                w.writerows(out_rows)
            lines += [f"## {prop}, {tier} tier ({len(out_rows)} element outcomes)", "",
                      "| scenario | element | demonstrator | " + " | ".join(CONDITIONS) + " | readiness |",
                      "|---|---|---|" + "---|" * len(CONDITIONS) + "---|"]
            seen = set()
            for o in out_rows:
                key = (o["scenario"], o["element"])
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"| {o['scenario']} | {o['element']} | {o['demonstrator_state']} | "
                             + " | ".join(SHORT[o[c]] for c in CONDITIONS) + f" | {o['readiness']} |")
            lines += ["", "Demonstrator state × readiness (all runs): "
                      + "; ".join(f"{a} → {b}: {n}" for (a, b), n in sorted(tally.items())), ""]
    overview += [""]
    (RESULTS / "summary.md").write_text("\n".join(lines[:3] + overview + lines[3:]), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "dpp-prep" / "out"
    props = sys.argv[2:] or ["oracle", "standin"]
    run(out, props)
