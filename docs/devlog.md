# Development log

## 2026-09-25
- Chose W-100 (fictitious timber-aluminium window), 7 information elements.
  Carbon footprint and recycled content left out: no supporting data, and
  inventing environmental claims would undermine the evaluation.
- Chose stack: Docling (reading), LangExtract (AI proposals), Pydantic,
  Streamlit, SQLite. AASbyLLM, remake_dpp and Rohrschneider's repository
  kept as references only.
- Built v0.1: data model, role-and-state rules, rule checks, grounding
  verification, export gate. Wrote W-100 baseline documents and five
  one-change variants, with expected outcomes written before running tests.
- Design decision: a proposal is kept only if its quote is found in the
  source by plain code, regardless of what the extractor claims.
- 11 tests pass. Mutation check: allowing AI to approve fails T07;
  disabling the quote check fails T02b. The tests detect both faults.
- Open: AI model provider for LangExtract.

## 2026-09-25 (later): independent audit and v0.2
- Independent audit of v0.1 found three bypasses: a real quote could support an
  invented value; a failed check could be reviewed, approved and exported; and
  approval did not require completed checks or a real review. Its three
  regression tests fail on v0.1 (reproduced) and pass on v0.2.
- Design insight for Chapter 6: rules on *who* may act are not enough. Each
  transition also needs *preconditions*, and approval must be bound to the
  exact version it approved.
- v0.2 changes: support check (value in quote, right label, unit, scope stated);
  proposal IDs; reviewer chooses one proposal, others kept as rejected;
  evidence inspection must be confirmed; two-person rule; version-bound
  approval; corrections need evidence and restart checks, review and approval;
  single service layer; append-only SQLite diary; schema-validated export;
  import route without AI for E01, E02, E05; all seven elements covered.
- Governance decision: mandatory check failures cannot be overridden by a
  person in v0.2. Exception path deferred; if added, it must keep the failed
  check and a written reason.
- Test method: 25 tests pass. Fault injection now automated
  (scripts/fault_injection.py). First run detected 7 of 10 removed safeguards;
  the 3 misses were guards shielded by the service layer. Added rule-layer
  tests; now 10 of 10 detected.
- Open: model provider for LangExtract; Docling; review screen; authentic
  documents; CIRPASS-2 mapping.

## 2026-09-26: v0.3
- PDF reading (PyMuPDF), page by page; evidence now names the page. Test PDFs
  generated reproducibly by scripts/make_pdfs.py, with the thermal section of
  D3 on page 2 so page tracking is genuinely tested.
- LangExtract adapter written against the real library interface (inspected,
  not assumed). Few-shot examples use a different fictitious product (door
  D-200) to avoid contaminating the evaluation, and include a Ug line with no
  extraction. Raw model output is written to the diary.
- A test fault exposed a real adapter weakness: an empty extraction counted as
  anchored at position 0. Adapter now requires a non-empty span (test L05).
- Review screen (Streamlit): value beside highlighted source sentence, no
  pre-selection, inspection box unticked by default, role-based actions; all
  rules enforced by the service underneath. Tested with Streamlit AppTest.
- Integration bug found by the screen tests: SQLite refused use across
  Streamlit's threads. Diary now shares its connection under a lock.
- Evaluation runner with scenarios written in advance; stand-in extractor:
  49 of 49 outcomes as expected, Markdown and PDF.
- 39 tests pass. Fault injection extended to the adapter: 12 of 12 detected.
- Open: model provider and API key; authentic documents; Docling for complex
  PDFs; CIRPASS-2 mapping; practitioner walkthrough.

## 2026-10-11: v0.3.1, local language model through Ollama
- Cloud route blocked in practice: gemini-2.5-flash withdrawn for new users,
  gemini-3.8-flash returned 503 (high demand) on 8 Oct 2026; no budget for
  paid API credit. Decision: run the AI step on local open-weight models.
- Added `ollama_extract.OllamaExtractor`: one call per document to Ollama's
  /api/chat; answer forced into a JSON schema built from the element profile;
  temperature 0, seed 42, thinking off where supported; model digest recorded.
- Design change against the LangExtract adapter: unanchored model quotes are
  no longer discarded inside the adapter. They are passed on, so the ordinary
  evidence check drops them and the diary records the reason. The controls
  themselves are unchanged.
- Every raw answer is saved to out/model_outputs_*.jsonl; `--replay` repeats a
  run exactly from that file, without the model (reproducibility).
- `scripts/check_ollama.py`: one-document check before a full run.
- Tests O01-O09 (fake transport and a fake HTTP server): 48 tests pass;
  fault injection still 12 of 12. No real model run yet at this point.

## 2026-10-12: v0.3.2, production-like tier, oracle pre-registration, analysis
- Realistic tier (data/w100/realistic, PDFs in data/w100/pdf_realistic): a
  longer datasheet with two product variants, Finnish labels and typographic
  units; a supplier declaration with frame and sash tables and recycled
  content; a full test report with Ug/Uf/Psi inputs and a second, informative
  Uw at another size; a Declaration of Performance; a replaced older report;
  a sash-only declaration. Three scenarios: real_baseline, real_stale_report,
  real_sash_only.
- config/ground_truth.yaml: what each document states, distractors, and the
  value that should finally be released per scenario.
- Oracle proposer (proposes exactly what each document states). Validation:
  it reproduces all 49 simple-tier expectations written in September.
  Pre-registration: run through the UNCHANGED controls on the realistic tier
  before any model saw the documents; expectations, date and document
  SHA-256 written to config/evaluation_scenarios_realistic.yaml.
- Pre-registered finding: faithful proposals of the thermal value are
  flagged in every realistic scenario, because the controls compare units and
  scopes literally (W/(m²K) vs W/(m2K), × vs x) and the Declaration of
  Performance does not state the reference size. The controls are too
  literal for production notation. Not fixed: the controls stay frozen; this
  is reported as a finding.
- Stand-in on the realistic tier: 15 of 21 (its patterns do not find the
  product identifier in the new layouts) - fixed rules do not transfer.
- scripts/analyse.py: state-level (outcomes matched, escapes, over-flagged,
  stability) and proposal-level measures (correct, distractor, quote not
  found, precision, recall, unwarranted proposals, product id, parse errors,
  identical runs, seconds per call). Works on v0.3.1 output too.
- PDF generator wraps long lines (no breaks at hyphens); simple-tier PDFs kept
  byte-identical to v0.3.
- 52 tests pass; fault injection 12 of 12.
