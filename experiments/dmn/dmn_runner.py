"""Execute the DMN readiness step (D044) with the pyDMNrules engine.

The decision logic lives only in dmn/readiness.dmn and dmn/quality_criterion.dmn.
This module only (1) calls the engine, (2) passes upstream decision results to Table C
explicitly, because pyDMNrules did not propagate them in our tests (a standard engine such
as Camunda chains them natively; not tested here), and (3) maps the engine's rule index to
the rule IDs of the specification (A1…, AV1…, B-agg-…, C1…, B-crit-…).
"""
from __future__ import annotations

import re
from pathlib import Path

import pyDMNrules

ROOT = Path(__file__).resolve().parent
DMN_DIR = ROOT / "dmn"
CONDITIONS = ["Available", "Aligned", "Representable", "Of sufficient quality",
              "Evidenced", "Validated", "Authorised", "Current"]
UPSTREAM = ["Applicability", "Available status", "Quality status"]


def _rule_ids(dmn_text: str) -> dict[str, list[str]]:
    """Rule IDs per decision, in table order, from the <description> of each rule."""
    out, current = {}, None
    for line in dmn_text.splitlines():
        m = re.search(r'<decision id="[^"]+" name="([^"]+)"', line)
        if m:
            current = m.group(1)
            out[current] = []
        m = re.search(r"<rule id=\"[^\"]+\"><description>([^<]+)</description>", line)
        if m and current:
            out[current].append(m.group(1))
    return out


class Engine:
    def __init__(self, dmn_dir: Path = DMN_DIR):
        self.readiness_xml = (dmn_dir / "readiness.dmn").read_text(encoding="utf-8")
        self.criterion_xml = (dmn_dir / "quality_criterion.dmn").read_text(encoding="utf-8")
        self.readiness = pyDMNrules.DMN()
        self.criterion = pyDMNrules.DMN()
        for eng, xml in ((self.readiness, self.readiness_xml), (self.criterion, self.criterion_xml)):
            status = eng.useXML(xml)
            if status:
                raise RuntimeError(f"DMN load failed: {status}")
        self.ids = {**_rule_ids(self.readiness_xml), **_rule_ids(self.criterion_xml)}

    def _decide(self, eng, data):
        status, results = eng.decide(data)
        if status:
            raise RuntimeError(f"DMN evaluation error: {status}")
        results = results if isinstance(results, list) else [results]
        out = {}
        for r in results:
            table = r["Executed Rule"][1]
            idx = int(r["Executed Rule"][2].split(".")[1])
            out[table] = (r["Result"][f"{table}.{table}"], self.ids[table][idx])
        return out

    def criterion_result(self, criterion_type, evaluation_state, parse_state="n/a",
                         total_within_tolerance="n/a", agreement="n/a"):
        res = self._decide(self.criterion, {
            "Criterion type": criterion_type, "Evaluation state": evaluation_state,
            "Parse state": parse_state, "Total within tolerance": total_within_tolerance,
            "Agreement": agreement})
        return res["Criterion result"]

    def condition_status(self, inputs: dict) -> dict:
        """inputs: all readiness.dmn input data incl. 'Condition'. Returns outputs and rule IDs."""
        first = self._decide(self.readiness, inputs)                      # pass 1: A, AV, B-agg
        passed = {k: first[k][0] for k in UPSTREAM}
        second = self._decide(self.readiness, {**inputs, **passed})       # pass 2: C with upstream results
        for k in UPSTREAM:                                                # consistency check
            if second[k][0] != passed[k]:
                raise RuntimeError(f"upstream result changed between passes: {k}")
        return {"condition": inputs["Condition"],
                "applicability": first["Applicability"][0], "applicability_rule": first["Applicability"][1],
                "available_status": first["Available status"][0], "available_rule": first["Available status"][1],
                "quality_status": first["Quality status"][0], "quality_rule": first["Quality status"][1],
                "status": second["Condition status"][0], "status_rule": second["Condition status"][1]}

    def element(self, base: dict) -> list[dict]:
        return [self.condition_status({**base, "Condition": c}) for c in CONDITIONS]
