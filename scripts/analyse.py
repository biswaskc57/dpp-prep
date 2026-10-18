"""Analyse evaluation results: accuracy of the proposers and behaviour of the controls.

    python scripts/analyse.py              # reads every result in out/
    python scripts/analyse.py out/ --out out/analysis

Reads the evaluation CSVs (end states) and, for language-model runs, the saved
model answers (model_outputs_*.jsonl), and compares them with
config/ground_truth.yaml. Writes:
  out/analysis/summary.md      one table, one row per proposer, tier and format
  out/analysis/summary.csv     the same numbers
  out/analysis/proposals.csv   every model proposal with its classification
  out/analysis/escapes.csv     every element that reached "checked" with a wrong value

Measures (all reported as counts with their denominators)
  State level, all proposers (from the CSV):
    outcomes matched   end state equals the pre-registered expectation
    escapes            element reached "checked" although its value is wrong or
                       no value should be released (the key safety measure)
    over-flagged       expected "checked" but ended flagged/unresolved
    stable elements    same end state in every run
  Proposal level, language models only (from the saved answers):
    correct            value matches what that document states for the element
    distractor         value belongs to something else in the document (Ug, Uf,
                       another variant, a replaced report, the sash)
    quote not found    the quote is not in the document (invented evidence;
                       the evidence check drops these)
    other wrong        anything else
    empty              items without a value; the adapter discards them before
                       any check, so they are not proposals (counted apart)
    precision          correct / all proposals (empty items excluded)
    value recall       statements found / statements in the documents (every
                       value a document states, required for the element or not)
    unwarranted        proposals for an element the document says nothing about
    product id correct the identifier the model reported equals the document's
    parse errors       answers that were not valid JSON
    identical runs     share of (scenario, document) answers identical in all runs
    seconds per call   mean and maximum
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dpp_prep.ollama_extract import _span          # noqa: E402
from dpp_prep.profile import load_profile         # noqa: E402

AI_ELEMENTS = ("E03", "E04", "E06", "E07")
SCEN = {"simple": ROOT / "config/evaluation_scenarios.yaml",
        "realistic": ROOT / "config/evaluation_scenarios_realistic.yaml"}
SIMPLE_DOCS = ["D1_datasheet", "D2_supplier_declaration", "D3_performance_report"]


# ------------------------------------------------------------ comparison
def _num(v) -> float | None:
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v))
    return float(m.group().replace(",", ".")) if m else None


def _percents(v) -> list[float]:
    return sorted(float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", str(v)))


def _text(v) -> str:
    return re.sub(r"[^a-z0-9\-]+", " ", str(v).lower()).strip()


def same(element: str, a, b) -> bool:
    if a is None or b is None:
        return False
    if element == "E06":
        x, y = _num(a), _num(b)
        return x is not None and x == y
    if element == "E03":
        return _percents(a) == _percents(b) and bool(_percents(a))
    if element == "E07":
        return re.sub(r"\s+", "", str(a)).upper() == re.sub(r"\s+", "", str(b)).upper()
    ta, tb = _text(a), _text(b)
    return bool(ta and tb) and (ta in tb or tb in ta)


# --------------------------------------------------------------- loading
def load_gt():
    gt = yaml.safe_load((ROOT / "config/ground_truth.yaml").read_text(encoding="utf-8"))
    return gt["documents"], gt["truth"]


def truth_for(truth: dict, scenario: str, element: str):
    over = truth.get(scenario) or {}
    return over[element] if element in over else truth["_default"].get(element)


def scenarios(tier: str) -> dict:
    data = yaml.safe_load(SCEN[tier].read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def scenario_docs(tier: str, sc: dict) -> list[str]:
    if "docs" in sc:
        return list(sc["docs"])
    return [sc["swap"].get(n, n) for n in SIMPLE_DOCS]


def parse_name(path: Path):
    """evaluation_<label>[_realistic]_<fmt>_<stamp>.csv / model_outputs_<label>[_<tier>]_<fmt>_<stamp>.jsonl"""
    m = re.match(r"(?:evaluation|model_outputs)_(.+?)_(md|pdf)_(\d{8}-\d{6})$", path.stem)
    if not m:
        return None
    label, fmt, stamp = m.groups()
    tier = "simple"
    for t in ("realistic", "simple"):
        if label.endswith("_" + t):
            label, tier = label[: -len(t) - 1], t
    return label, tier, fmt, stamp


def _secs(stamp: str) -> float:
    from datetime import datetime
    return datetime.strptime(stamp, "%Y%m%d-%H%M%S").timestamp()


def pair_files(folder: Path):
    csvs = {}
    for p in folder.glob("evaluation_*.csv"):
        k = parse_name(p)
        if k:
            csvs.setdefault(k[:3], []).append((k[3], p))
    jsonls = {}
    for p in folder.glob("model_outputs_*.jsonl"):
        k = parse_name(p)
        if k:
            jsonls.setdefault(k[:3], []).append((k[3], p))
    out = []
    for key, items in csvs.items():
        for stamp, p in sorted(items):
            # the saved answers belong to the evaluation started closest in time
            cands = sorted(jsonls.get(key, []), key=lambda sj: abs(_secs(sj[0]) - _secs(stamp)))
            out.append((key, p, cands[0][1] if cands else None))
    return out


# -------------------------------------------------------------- analysis
def analyse_states(rows, truth):
    res = {"rows": len(rows), "matched": sum(r["match"] == "True" for r in rows), "escapes": [], "over": 0}
    by = defaultdict(set)
    for r in rows:
        by[(r["scenario"], r["element"])].add(r["actual"])
        if r["expected"] == "checked" and r["actual"] != "checked":
            res["over"] += 1
        if r["actual"] == "checked" and r["element"] in AI_ELEMENTS:
            t = truth_for(truth, r["scenario"], r["element"])
            vals = [v.strip() for v in r["values"].split(" | ") if v.strip()]
            if t is None or any(not same(r["element"], v, t) for v in vals):
                res["escapes"].append({"run": r["run"], "scenario": r["scenario"], "element": r["element"],
                                       "values": r["values"], "truth": t})
    res["stable"] = sum(len(s) == 1 for s in by.values())
    res["elements"] = len(by)
    return res


def label_entries(entries, tier, runs):
    """Attach (run, scenario, doc) to every saved answer, from its run label or by call order."""
    scs = scenarios(tier)
    order = [(run, name, doc) for run in range(1, runs + 1) for name, sc in scs.items()
             for doc in scenario_docs(tier, sc)]
    out = []
    for i, e in enumerate(entries):
        doc = Path(e["source"]).stem
        lab = e.get("run") or ""
        m = re.match(r"(?:\w+/)?run(\d+)/(.+)$", lab)
        if m:
            run, name = int(m.group(1)), m.group(2)
        elif i < len(order) and order[i][2] == doc:
            run, name = order[i][0], order[i][1]
        else:
            run, name = None, None
        out.append((run, name, doc, e))
    return out


def analyse_proposals(entries, docs_gt, name_to_id):
    c = defaultdict(int)
    props, found = [], set()
    statements = set()
    seconds, raws = [], defaultdict(set)
    for run, scen, doc, e in entries:
        seconds.append(e.get("seconds") or 0)
        raws[(scen, doc)].add(e.get("raw", ""))
        g = docs_gt.get(doc, {"product": None, "statements": []})
        for s in g.get("statements") or []:
            statements.add((run, scen, doc, s["element"], str(s["value"])))
        if e.get("parse_error"):
            c["parse_errors"] += 1
            continue
        try:
            parsed = json.loads(e["raw"])
        except Exception:  # noqa: BLE001
            c["parse_errors"] += 1
            continue
        c["answers"] += 1
        pid = (parsed.get("product_id") or "").strip()
        c["pid_total"] += 1
        c["pid_correct"] += pid == g.get("product")
        doc_text = e.get("_doc_text")
        for x in parsed.get("extractions") or []:
            eid = name_to_id.get(x.get("element"))
            if eid is None:
                continue
            value = "" if x.get("value") is None else str(x.get("value")).strip()
            quote = "" if x.get("quote") is None else str(x.get("quote")).strip()
            if not value:
                # Same rule as the adapter (ollama_extract): an item without a value is
                # discarded before any check, so it is not a proposal. Counted apart.
                c["empty"] += 1
                props.append({"run": run, "scenario": scen, "document": doc, "element": eid, "value": "",
                              "unit": x.get("unit", ""), "scope": x.get("scope", ""), "quote": quote,
                              "class": "empty", "document_states": "; ".join(
                                  str(s["value"]) for s in (g.get("statements") or []) if s["element"] == eid)
                              or "(nothing)"})
                continue
            c["proposals"] += 1
            stmts = [s for s in (g.get("statements") or []) if s["element"] == eid]
            dis = [d for d in (g.get("distractors") or []) if d["element"] == eid]
            quote_found = bool(doc_text and quote and _span(doc_text, quote))
            hit = next((s for s in stmts if same(eid, value, s["value"])), None)
            if not stmts:
                c["unwarranted"] += 1
            if doc_text is not None and not quote_found:
                cls = "quote not found"
            elif hit:
                cls = "correct"
                found.add((run, scen, doc, eid, str(hit["value"])))
            elif any(same(eid, value, d["value"]) for d in dis):
                cls = "distractor"
            else:
                cls = "other wrong"
            c[cls] += 1
            props.append({"run": run, "scenario": scen, "document": doc, "element": eid, "value": value,
                          "unit": x.get("unit", ""), "scope": x.get("scope", ""), "quote": quote,
                          "class": cls, "document_states": "; ".join(str(s["value"]) for s in stmts) or "(nothing)"})
    c["statements"] = len(statements)
    c["found"] = len(found & statements)
    c["identical_runs"] = sum(len(v) == 1 for v in raws.values())
    c["answer_groups"] = len(raws)
    c["sec_mean"] = round(statistics.mean(seconds), 1) if seconds else 0
    c["sec_max"] = round(max(seconds), 1) if seconds else 0
    return c, props


def attach_doc_texts(entries, tier, fmt):
    from dpp_prep.sources import load_source
    cache = {}
    for _, _, doc, e in entries:
        if doc not in cache:
            if tier == "realistic":
                p = ROOT / ("data/w100/pdf_realistic" if fmt == "pdf" else "data/w100/realistic") / f"{doc}.{fmt}"
            elif fmt == "pdf":
                p = ROOT / "data/w100/pdf" / f"{doc}.pdf"
            else:
                folder = "baseline" if doc in SIMPLE_DOCS else "variants"
                p = ROOT / "data/w100" / folder / f"{doc}.md"
            cache[doc] = load_source(p).text if p.exists() else None
        e["_doc_text"] = cache[doc]


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.0f} %)" if b else "–"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default=str(ROOT / "out"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    folder = Path(a.folder)
    outdir = Path(a.out) if a.out else folder / "analysis"
    outdir.mkdir(parents=True, exist_ok=True)
    docs_gt, truth = load_gt()
    _, defs = load_profile(ROOT / "config/elements_w100.yaml")
    name_to_id = {d.name: d.id for d in defs.values()}

    summary, all_props, all_esc = [], [], []
    for (label, tier, fmt), csv_path, jsonl in sorted(pair_files(folder), key=lambda x: (x[0][1], x[0][0], x[0][2])):
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        runs = max(int(r["run"]) for r in rows)
        st = analyse_states(rows, truth)
        row = {"proposer": label, "tier": tier, "format": fmt, "runs": runs,
               "outcomes matched": pct(st["matched"], st["rows"]),
               "escapes": len(st["escapes"]), "over-flagged": st["over"],
               "stable elements": pct(st["stable"], st["elements"])}
        for e in st["escapes"]:
            all_esc.append({"proposer": label, "tier": tier, "format": fmt, **e})
        if jsonl is not None:
            entries = [json.loads(x) for x in jsonl.read_text(encoding="utf-8").splitlines() if x.strip()]
            labelled = label_entries(entries, tier, runs)
            attach_doc_texts(labelled, tier, fmt)
            c, props = analyse_proposals(labelled, docs_gt, name_to_id)
            row.update({
                "proposals": c["proposals"], "correct": c["correct"], "distractor": c["distractor"],
                "quote not found": c["quote not found"], "other wrong": c["other wrong"],
                "empty": c["empty"],
                "precision": pct(c["correct"], c["proposals"]), "value recall": pct(c["found"], c["statements"]),
                "unwarranted": c["unwarranted"], "product id correct": pct(c["pid_correct"], c["pid_total"]),
                "parse errors": c["parse_errors"], "identical runs": pct(c["identical_runs"], c["answer_groups"]),
                "seconds per call (mean/max)": f"{c['sec_mean']} / {c['sec_max']}",
                "model digest": entries[0].get("digest") if entries else ""})
            for p in props:
                all_props.append({"proposer": label, "tier": tier, "format": fmt, **p})
        summary.append(row)

    if not summary:
        sys.exit(f"no evaluation_*.csv files found in {folder}")
    cols = list(dict.fromkeys(k for r in summary for k in r))
    with (outdir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(summary)
    for name, data in (("proposals.csv", all_props), ("escapes.csv", all_esc)):
        with (outdir / name).open("w", newline="", encoding="utf-8") as f:
            if data:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
    md = ["# Evaluation summary", "", f"Source folder: {folder}", ""]
    for tier in ("simple", "realistic"):
        part = [r for r in summary if r["tier"] == tier]
        if not part:
            continue
        md += [f"## {tier.capitalize()} tier", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        md += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in part]
        md.append("")
    if all_esc:
        md += ["## Escapes (wrong or unwarranted values that reached \"checked\")", ""]
        md += [f"- {e['proposer']} {e['tier']}/{e['format']} run {e['run']} {e['scenario']} {e['element']}: "
               f"{e['values']} (should be: {e['truth']})" for e in all_esc]
    (outdir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwritten to {outdir}")


if __name__ == "__main__":
    main()
