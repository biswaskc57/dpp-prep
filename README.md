# dpp-prep

Demonstrator for the master's thesis *Possibilities of AI in Preparing DPP Information
in Manufacturing* (Biswas KC, Haaga-Helia University of Applied Sciences, 2026).

dpp-prep prepares information for a Digital Product Passport (DPP) under explicit
control. An AI model or a rule-based extractor may **propose** a value, but code checks
that its quoted evidence exists in the source and that the value passes defined rules.
A named reviewer then selects a value after inspecting the evidence, and a different,
named approver approves that exact version. Only approved values are exported.

The test product is **W-100**, a fictitious timber-aluminum window. All product data
in `data/` is invented research data.

## Versions

| Tag / commit | What it is |
|---|---|
| `v0.3.2` (commit `fcc17ef`) | **The evaluated version.** Commit `2be1ea5` adds only `CLAUDE.md` and decision records; code, tests and data are identical. |
| `08d5840` | Post hoc sash probe (18 Oct 2026): `scripts/probe_sash.py`, tests PR01–PR02 |
| `9e7d08e` | Correction of the analysis script (count of items without a value) |
| later commits | Saved results and post hoc experiments, added 14 Nov 2026 (see below) |

Nothing in `src/`, `config/`, `data/` or `schemas/` changed after `v0.3.2`.

## The flow

    information profile + documents (Markdown or PDF) + ERP record
      -> propose (AI, rule-based stand-in, or direct import)
      -> evidence check (is the quote in the source?) -> rule checks
      -> reviewer selects a value after inspecting the evidence
      -> a different approver approves this exact version
      -> schema-checked JSON handover
    Every step, including refusals and raw AI output, is written to an event diary.

## Run it

    pip install -e ".[dev]"
    pytest                                    # 55 tests (52 at v0.3.2, plus R05, PR01, PR02)
    python scripts/run_demo.py                # the workflow, step by step
    python scripts/evaluate.py                # all basic scenarios with the stand-in
    python scripts/fault_injection.py         # remove each of 12 safeguards; do the tests notice?
    streamlit run app/review_app.py           # review screen

Local language models through Ollama (as in the evaluation):

    ollama pull qwen3.5:9b
    python scripts/evaluate.py --extractor ollama --model qwen3.5:9b --runs 3
    python scripts/evaluate.py --tier realistic --extractor ollama --model qwen3.5:9b --runs 3
    python scripts/evaluate.py --replay <model_outputs_...jsonl>   # repeat a run from saved answers
    python scripts/analyse.py <folder>                             # summary of all results in a folder

The evaluation used qwen3.5:4b, qwen3.5:9b and gemma4:12b with temperature 0, a fixed
seed, no reasoning output and a context window of 8,192 tokens, on an Apple M1 with 16 GB.

## Where things are

    src/dpp_prep/   engine: sources, extract, verify, checks, states, service, audit, export
    config/         information profile, stand-in patterns, evaluation scenarios, ground truth
    data/w100/      basic and production-like test documents, PDFs, ERP record, expected outcomes
    schemas/        handover schema (JSON Schema)
    tests/          workflow, rules, PDF, adapters, review screen, runner, analysis, probe
    scripts/        demo, evaluation, analysis, fault injection, pre-registration, probe
    app/            review screen (Streamlit)
    docs/           specification v0.3, architecture, process, traceability, devlog,
                    decision records (adr/), framework cases and probe records (evaluation/)
    results/        saved outputs of the evaluated runs (17–18 Oct 2026)
    experiments/    post hoc work: public-EPD run, DMN decision tables, MCP connection
    out_interrupted_2250/   an interrupted run (17 Oct, 22:47), restarted at 23:01; not used

## Evaluation records

- `results/evaluation_2026-10-17/`: result CSVs and model responses of all 18 language-model
  runs plus the stand-in and reference proposer (770 element outcomes), the run log, and the
  analysis before and after the correction in `9e7d08e`, and the SQLite event diaries of
  the same runs (added 16 Nov 2026; `experiments/dmn/run_cases.py` reads them).
- `experiments/models/`: the BPMN and data-model versions described in thesis Appendix 3.
- `docs/evaluation/framework_cases_v1_assessment.xlsx`: the case assessment worksheet
  (statuses, supporting case sentences, change log).
- Expected outcomes: `config/evaluation_scenarios.yaml` (basic set) and
  `config/evaluation_scenarios_realistic.yaml` (production-like set, derived on
  12 Oct 2026 by `scripts/preregister.py`). Both were in the repository before the runs.
- `docs/evaluation/framework_cases_v1.md`: the seven fictional cases, fixed before classification.
- `docs/evaluation/probe_sash.md`: the post hoc sash probe and its result.

See `experiments/README.md` for the post hoc work.

## Limits

This is a research demonstrator, not a production system. It uses file-based sources,
simulated identities and a structured handover package rather than a complete passport.
Review and approval in the tests are simulated. The results describe controlled runs
with three local models and synthetic documents for one product.
