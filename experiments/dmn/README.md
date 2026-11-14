# dpp-prep-dmn: the DMN readiness step, executed post hoc

Executes the readiness step of BPMN v0.6 (Figure 9c) as standard DMN 1.3 decision tables on the **frozen** dpp-prep run outputs. Decision D044 in research matrix v0.27; specification in sheet "DMN status rules".

**Status:** post hoc and illustrative. The requirement statements for W-100 are assumptions. This is not part of the pre-registered evaluation, and it does not change the demonstrator or its results.

## Files

| File | Content |
|---|---|
| `dmn/readiness.dmn` | Table A (Applicability, FIRST), Available status (UNIQUE), Table B aggregation (Quality status, FIRST), Table C (Condition status, FIRST); C requires the other three |
| `dmn/quality_criterion.dmn` | Table B per criterion (Criterion result, UNIQUE) |
| `gen_dmn.py` | writes both `.dmn` files from the specification; every rule carries its ID (A1…, AV1…, B-crit-…, B-agg-…, C1…) |
| `dmn_runner.py` | calls the DMN engine; no decision logic of its own |
| `run_cases.py` | derives DMN inputs from the run outputs and writes `results/` |
| `tests/test_rules.py` | 50 tests: every rule is hit by one input and gives the specified output and rule ID; missing information never becomes "met" |
| `results/` | readiness per element and condition (CSV) and `summary.md` |

## Engine

The engine is **pyDMNrules 1.4.5** (FEEL via pySFeel 1.4.2), an open-source DMN engine that reads standard DMN XML.

- **Camunda DMN**, which DMN4DQ used, could not be installed in the build environment. The `.dmn` files are standard and can be opened in Camunda Modeler or another DMN tool.
- **Chaining:** pyDMNrules did not pass the results of the required decisions (Applicability, Available status, Quality status) to Table C. `dmn_runner.py` therefore evaluates in two passes: pass 1 computes the three decisions, and pass 2 evaluates Table C with those results given as input. Each call checks that the three results are identical in both passes. A standard engine chains them natively; that was not tested here.

## Setup on the Mac

pyDMNrules lists a PyPI package "statistics" that fails to build; the standard library already provides it. Install without it:

```bash
cd ~/path/to/dpp-prep-dmn
python3 -m venv .venv && source .venv/bin/activate
pip install --no-deps pyDMNrules==1.4.5 pySFeel==1.4.2 sly==0.5
pip install pytz python-dateutil openpyxl pandas pytest
python -m pytest                     # expect: 50 passed
```

## Running it

**Oracle and stand-in:**

```bash
python run_cases.py ~/Desktop/thesis/dpp-prep-repo/out oracle standin
```

**Model runs**: use the proposer names exactly as they appear in the file names. Check with `ls out/evaluation_*.csv` first:

```bash
python run_cases.py ~/Desktop/thesis/dpp-prep-repo/out ollama-gemma4-12b ollama-qwen3.5-9b ollama-qwen3.5-4b
```

## How inputs are derived (no status is decided here; the DMN decides)

- **Supported proposal exists:** the element did not end "unresolved".
- **Alignment checks:** identity, unit or scope failed for any candidate → "any failed".
- **Value type, support:** failed for any candidate → "failed".
- **All configured checks:** any failed check → "any failed".
- **Evidence inspected, approval:** the batch runs had no human review, so these are False and "none".
- **Source validity:** "unknown"; the runs recorded no validity rule.
- **Requirement statements** (illustrative W-100 assumptions):
  - approval: stated required;
  - validity: not stated;
  - quality: stated required;
  - quality criteria are configured for E03 (composition sum) and for E04, E06 and E07 (source consistency).
- **Composition criterion:** no shares found (total 0 %) → "none"; otherwise "all", with the total within or outside 100 % ± 0.5. The frozen check cannot detect "partial or malformed" shares, so rule B-crit-3 cannot fire on these runs.
- **Consistency criterion:** conflict check failed → "disagree", otherwise "agree".

## Results (oracle and stand-in, 27 October 2026)

| Proposer | Tier | checked → ready | checked → undetermined | flagged → not ready | unresolved → undetermined |
|---|---|---|---|---|---|
| oracle | simple | 0 | 44 | 4 | 1 |
| oracle | realistic | 0 | 15 | 5 | 1 |
| stand-in | simple | 0 | 44 | 4 | 1 |
| stand-in | realistic | 0 | 9 | 9 | 3 |

1. **No "checked" element is "ready".** Evidenced, Authorised and Current stay "not yet assessed", because no review, approval or validity rule exists in a batch run. *Workflow progress is not readiness.*
2. **Every "flagged" element is "not ready".** The DMN never contradicts the demonstrator's checks, and it names the conditions behind each flag (e.g. composition 95 % → quality and validated not met; wrong product → aligned and validated not met).
3. **Every "unresolved" element is "undetermined", not "not met".** An AI miss is not treated as absence.
4. **Quality is "not yet assessed" for E01, E02 and E05.** No quality criterion is configured for these elements while quality is stated as required, so Table A cannot decide (rule A8). This follows from the assumptions and is reported as such.
