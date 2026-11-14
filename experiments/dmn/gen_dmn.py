"""Generate the two standard DMN 1.3 files from the approved specification (D044).

Each rule is written once here, with its ID from the specification (A1..A8, AV1..AV3,
B-crit-1..7, B-agg-1..4, C1..C26), so the .dmn files, the tests and the thesis tables agree.
Run: python gen_dmn.py   → writes dmn/readiness.dmn and dmn/quality_criterion.dmn
"""
from pathlib import Path
from xml.sax.saxutils import escape

NS = "https://www.omg.org/spec/DMN/20191111/MODEL/"
OUT = Path(__file__).resolve().parent / "dmn"


def S(*vals):            # FEEL list of string values for a unary test
    return ",".join(f'"{v}"' for v in vals)


def NOT(*vals):
    return f"not({S(*vals)})"


ANY = "-"

# ------------------------------------------------------------------ readiness.dmn
INPUTS = [  # name, typeRef
    ("Condition", "string"),
    ("Quality criterion configured", "boolean"),
    ("Approval statement", "string"),
    ("Validity statement", "string"),
    ("Quality statement", "string"),
    ("Supported proposal exists", "boolean"),
    ("Not in sources and obtain failed", "boolean"),
    ("Alignment checks", "string"),
    ("Value type check", "string"),
    ("Support check", "string"),
    ("Evidence inspected", "boolean"),
    ("All configured checks", "string"),
    ("Approval on this version", "string"),
    ("Source validity", "string"),
    ("Number of criteria", "number"),
    ("Failed criteria", "number"),
    ("Insufficient criteria", "number"),
]

C5 = ("Available", "Aligned", "Representable", "Evidenced", "Validated")

TABLE_A = dict(
    name="Applicability", hit="FIRST",
    inputs=["Condition", "Quality criterion configured", "Approval statement", "Validity statement", "Quality statement"],
    rules=[
        ("A1", [S(*C5), ANY, ANY, ANY, ANY], "applicable"),
        ("A2", [S("Of sufficient quality"), "true", ANY, ANY, ANY], "applicable"),
        ("A3", [S("Of sufficient quality"), "false", ANY, ANY, S("stated not required")], "not applicable"),
        ("A4", [S("Authorised"), ANY, S("stated required"), ANY, ANY], "applicable"),
        ("A5", [S("Authorised"), ANY, S("stated not required"), ANY, ANY], "not applicable"),
        ("A6", [S("Current"), ANY, ANY, S("stated required"), ANY], "applicable"),
        ("A7", [S("Current"), ANY, ANY, S("stated not required"), ANY], "not applicable"),
        ("A8", [ANY, ANY, ANY, ANY, ANY], "cannot yet determine"),
    ])

TABLE_AV = dict(
    name="Available status", hit="UNIQUE",
    inputs=["Supported proposal exists", "Not in sources and obtain failed"],
    rules=[
        ("AV1", ["true", ANY], "met"),
        ("AV2", ["false", "true"], "not met"),
        ("AV3", ["false", "false"], "not yet assessed"),
    ])

TABLE_BAGG = dict(
    name="Quality status", hit="FIRST",
    inputs=["Number of criteria", "Failed criteria", "Insufficient criteria"],
    rules=[
        ("B-agg-4", ["0", ANY, ANY], "no criteria"),
        ("B-agg-1", [ANY, ">0", ANY], "not met"),
        ("B-agg-2", [ANY, ANY, ">0"], "not yet assessed"),
        ("B-agg-3", [ANY, ANY, ANY], "met"),
    ])

C_IN = ["Condition", "Applicability", "Available status", "Alignment checks", "Value type check",
        "Quality status", "Support check", "Evidence inspected", "All configured checks",
        "Approval on this version", "Source validity"]


def c(cond=ANY, app=ANY, av=ANY, al=ANY, vt=ANY, q=ANY, sup=ANY, insp=ANY, allc=ANY, appr=ANY, val=ANY):
    return [cond, app, av, al, vt, q, sup, insp, allc, appr, val]


TABLE_C = dict(
    name="Condition status", hit="FIRST", inputs=C_IN,
    rules=[
        ("C1", c(app=S("not applicable")), "not required"),
        ("C2", c(app=S("cannot yet determine")), "not yet assessed"),
        ("C3", c(cond=S("Available"), av=S("met")), "met"),
        ("C4", c(cond=S("Available"), av=S("not met")), "not met"),
        ("C5", c(cond=S("Available"), av=S("not yet assessed")), "not yet assessed"),
        ("C6", c(av=NOT("met")), "not yet assessed"),
        ("C7", c(cond=S("Aligned"), al=S("all passed")), "met"),
        ("C8", c(cond=S("Aligned"), al=S("any failed")), "not met"),
        ("C9", c(cond=S("Representable"), vt=S("passed")), "met"),
        ("C10", c(cond=S("Representable"), vt=S("failed")), "not met"),
        ("C11", c(cond=S("Of sufficient quality"), q=S("met")), "met"),
        ("C12", c(cond=S("Of sufficient quality"), q=S("not met")), "not met"),
        ("C13", c(cond=S("Of sufficient quality"), q=S("not yet assessed", "no criteria")), "not yet assessed"),
        ("C14", c(cond=S("Evidenced"), sup=S("failed")), "not met"),
        ("C15", c(cond=S("Evidenced"), sup=S("passed"), insp="true"), "met"),
        ("C16", c(cond=S("Evidenced"), sup=S("passed"), insp="false"), "not yet assessed"),
        ("C17", c(cond=S("Validated"), allc=S("all passed")), "met"),
        ("C18", c(cond=S("Validated"), allc=S("any failed")), "not met"),
        ("C19", c(cond=S("Authorised"), appr=S("approved")), "met"),
        ("C20", c(cond=S("Authorised"), appr=S("refused")), "not met"),
        ("C21", c(cond=S("Authorised"), appr=S("none")), "not yet assessed"),
        ("C22", c(cond=S("Current"), val=S("within")), "met"),
        ("C23", c(cond=S("Current"), val=S("expired or superseded")), "not met"),
        ("C24", c(cond=S("Current"), val=S("unknown")), "not yet assessed"),
        ("C25", c(), "not yet assessed"),
    ])

# ------------------------------------------------------------------ quality_criterion.dmn
B_INPUTS = [("Criterion type", "string"), ("Evaluation state", "string"), ("Parse state", "string"),
            ("Total within tolerance", "string"), ("Agreement", "string")]
TABLE_BCRIT = dict(
    name="Criterion result", hit="UNIQUE",
    inputs=[n for n, _ in B_INPUTS],
    rules=[
        ("B-crit-1", [S("composition"), S("evaluated"), S("all"), S("yes"), ANY], "pass"),
        ("B-crit-2", [S("composition"), S("evaluated"), S("all"), S("no"), ANY], "fail"),
        ("B-crit-3", [S("composition"), S("evaluated"), S("partial or malformed"), ANY, ANY], "insufficient evidence"),
        ("B-crit-4", [S("composition"), S("evaluated"), S("none"), ANY, ANY], "insufficient evidence"),
        ("B-crit-5", [S("consistency"), S("evaluated"), ANY, ANY, S("agree")], "pass"),
        ("B-crit-6", [S("consistency"), S("evaluated"), ANY, ANY, S("disagree")], "fail"),
        ("B-crit-7", [ANY, S("not evaluated"), ANY, ANY, ANY], "insufficient evidence"),
    ])


def _id(s):
    return "".join(ch if ch.isalnum() else "_" for ch in s)


def table_xml(t, types, required_inputs, required_decisions):
    did = "d_" + _id(t["name"])
    out = [f'  <decision id="{did}" name="{escape(t["name"])}">',
           f'    <variable id="v_{did}" name="{escape(t["name"])}" typeRef="string"/>']
    for n in required_inputs:
        out.append(f'    <informationRequirement id="ir_{did}_{_id(n)}"><requiredInput href="#in_{_id(n)}"/></informationRequirement>')
    for n in required_decisions:
        out.append(f'    <informationRequirement id="ir_{did}_{_id(n)}"><requiredDecision href="#d_{_id(n)}"/></informationRequirement>')
    out.append(f'    <decisionTable id="t_{did}" hitPolicy="{t["hit"]}">')
    for i, n in enumerate(t["inputs"]):
        out.append(f'      <input id="i_{did}_{i}" label="{escape(n)}"><inputExpression id="e_{did}_{i}" typeRef="{types.get(n, "string")}"><text>{escape(n)}</text></inputExpression></input>')
    out.append(f'      <output id="o_{did}" name="{escape(t["name"])}" typeRef="string"/>')
    for rid, entries, result in t["rules"]:
        out.append(f'      <rule id="r_{_id(rid)}"><description>{rid}</description>')
        for j, e in enumerate(entries):
            out.append(f'        <inputEntry id="ie_{_id(rid)}_{j}"><text>{escape(e)}</text></inputEntry>')
        out.append(f'        <outputEntry id="oe_{_id(rid)}"><text>"{result}"</text></outputEntry></rule>')
    out += ['    </decisionTable>', '  </decision>']
    return "\n".join(out)


def model(name, inputs, tables):
    types = dict(inputs)
    decision_names = {t["name"] for t, _, _ in tables}
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<definitions xmlns="{NS}" id="{_id(name)}" name="{escape(name)}" namespace="http://dpp-prep.thesis/{_id(name)}">']
    used = {n for t, ri, _ in tables for n in ri}
    for n, ty in inputs:
        if n in used:
            xml.append(f'  <inputData id="in_{_id(n)}" name="{escape(n)}"><variable id="v_in_{_id(n)}" name="{escape(n)}" typeRef="{ty}"/></inputData>')
    for t, ri, rd in tables:
        xml.append(table_xml(t, types, ri, rd))
    xml.append("</definitions>\n")
    return "\n".join(xml)


def main():
    OUT.mkdir(exist_ok=True)
    readiness = model("DPP readiness step (Figure 9c)", INPUTS, [
        (TABLE_A, TABLE_A["inputs"], []),
        (TABLE_AV, TABLE_AV["inputs"], []),
        (TABLE_BAGG, TABLE_BAGG["inputs"], []),
        (TABLE_C, [n for n in C_IN if n not in ("Applicability", "Available status", "Quality status")],
         ["Applicability", "Available status", "Quality status"]),
    ])
    (OUT / "readiness.dmn").write_text(readiness, encoding="utf-8")
    crit = model("Quality criterion (Table B, per criterion)", B_INPUTS, [(TABLE_BCRIT, TABLE_BCRIT["inputs"], [])])
    (OUT / "quality_criterion.dmn").write_text(crit, encoding="utf-8")
    print("written:", *(p.name for p in OUT.glob("*.dmn")))


if __name__ == "__main__":
    main()
