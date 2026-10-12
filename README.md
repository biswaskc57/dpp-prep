# dpp-prep v0.3.2

Master's thesis prototype: governed preparation of DPP-relevant manufacturing
information. AI may propose a value; the tool decides whether it is supported,
checked, reviewed and authorised before it is handed over.

Illustrative product: **W-100**, a fictitious timber-aluminium window.
All product data in `data/` is invented research data.

## The flow in one line

    wish list + documents (Markdown or PDF) -> suggest (AI or import) -> fact-check
      -> rule-check -> reviewer chooses on the review screen
      -> different approver approves this exact version -> schema-checked export
    (every step, including every refusal and every raw AI output, goes into the diary)

## Run it

    pip install -e ".[dev]"
    pytest                                   # 39 tests
    streamlit run app/review_app.py          # the review screen
    python scripts/run_demo.py               # the story, step by step
    python scripts/evaluate.py               # all scenarios, outcome vs expectation
    python scripts/fault_injection.py        # do the tests notice removed safeguards?

## With a real AI model (once chosen)

    export LANGEXTRACT_API_KEY=...           # your key
    python scripts/evaluate.py --extractor langextract --model <model-id> --runs 3

Local model through Ollama (v0.3.1), no API key needed:

    ollama pull qwen3.5:9b
    python scripts/check_ollama.py --model qwen3.5:9b          # one document, quick check
    python scripts/evaluate.py --extractor ollama --model qwen3.5:9b --runs 3
    python scripts/evaluate.py --replay out/model_outputs_<...>.jsonl   # repeat a run exactly

Production-like documents (v0.3.2) and the analysis:

    python scripts/evaluate.py --tier realistic --extractor ollama --model qwen3.5:9b --runs 3
    python scripts/analyse.py                     # all results in out/ -> out/analysis/summary.md
    python scripts/preregister.py                 # only to re-derive expectations; already done 12 Oct 2026

Each run is kept; the results table lists every outcome that differs from
what was expected in `config/evaluation_scenarios.yaml`.

## Where things are

    config/     wish list, stand-in patterns, LangExtract examples, evaluation scenarios
    src/        engine: sources, extract, verify, checks, states, service, audit, export
    app/        review screen (Streamlit)
    schemas/    handover schema (JSON Schema)
    data/w100/  baseline documents, variants, PDFs, ERP record, expected outcomes
    tests/      workflow, rules, PDF, adapter, screen, runner, audit regressions
    scripts/    demo, evaluation, fault injection, PDF generation
    docs/       specification v0.3, architecture, process, traceability, development log

## Status

See docs/specification_v0.3.md, sections 5 and 7. Not yet done: a real AI run,
authentic documents, Docling for complex PDFs, CIRPASS-2 mapping.
