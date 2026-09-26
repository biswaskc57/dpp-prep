# dpp-prep specification, version 0.3

Changes from 0.2: PDF reading with page numbers; LangExtract adapter (tested with a
LangExtract-shaped fake, no real model yet); review screen; evaluation runner with
scenarios written in advance; diary safe for the review screen's threads.

This document is the implementation contract. Every rule here has a test.

## 1. Purpose in one sentence

Prepare DPP-relevant product information so that nothing leaves the tool unless
its evidence supports it, its rules pass, a named reviewer chose it after seeing
the evidence, and a different named approver approved that exact version.

## 2. Information model — what the tool keeps

| Thing | Plain meaning | Key contents |
|---|---|---|
| Profile | The wish list | Elements, how each is obtained (`route`), required words in the quote, unit, scope, which checks apply, profile version |
| Source | A document or structured record | Name, text, page texts for PDFs, SHA-256 fingerprint |
| Proposal | One candidate value | ID, value, unit, scope, product, method (AI, import, manual), who produced it |
| Evidence | Where the value came from | Source, page, exact quote, context quote, position, document fingerprint |
| Check result | Outcome of one rule | Name, passed or not, reason, which proposal |
| Review decision | A reviewer's choice | Reviewer ID, chosen proposal, evidence inspected (yes/no), record version, note |
| Approval | An approver's decision | Approver ID, record version |
| Record | Everything about one element | State, proposals, rejected proposals (kept, never deleted), checks, review, approval, log |
| Record version | A fingerprint of the proposals and their evidence | Changes whenever a value or its evidence changes |

## 3. Process model — states and who may move them

| From | To | Who | Conditions |
|---|---|---|---|
| required | proposed | AI, system (import), reviewer | Evidence found in the source |
| required | unresolved | AI, system | No supported value found. Nothing is invented |
| proposed | checked | system | Checks ran and all passed |
| proposed | flagged | system, reviewer | A check failed |
| checked / flagged | reviewed | reviewer | Evidence inspected; chosen value passes all checks; other proposals kept as rejected |
| reviewed | approved | approver | Checks ran on the current version and passed; a reviewer decision exists for the current version; chosen value passed its support check; approver named and different from the reviewer |
| approved | released | approver | Approval is for the current version; checks still pass |
| checked / flagged / reviewed / approved / unresolved | proposed | reviewer | A correction with its own supported evidence. Clears checks, review and approval |

Approval re-verifies every condition itself, so a record that reached
"reviewed" by an irregular path still cannot be approved.

Mandatory check failures cannot be overridden by a person. A failed value must
be corrected (with evidence) or left unapproved. An exception path is not part
of v0.2; if added later, it must keep the failed check and the written reason.

## 4. Components

| Component | File | Built or reused |
|---|---|---|
| Wish list | `config/elements_w100.yaml` | Configuration |
| Reader | `sources.py`: Markdown, JSON, PDF page by page (PyMuPDF) | PyMuPDF reused; Docling planned for complex layouts |
| Suggester | `extract.LangExtractExtractor` (real AI), `StandInExtractor` (deterministic) | LangExtract reused |
| Importer | `extract.StructuredImporter` | Built (no AI) |
| Fact-checker | `verify.py` + `checks.support` | Built |
| Rule checker | `checks.py` | Built |
| Gatekeeper rules | `states.py` | Built |
| Workflow | `service.py` | Built |
| Diary | `audit.py` (SQLite, append-only, thread-safe) | Built |
| Handover | `export.py` + `schemas/handover_v0.2.schema.json` | Built; CIRPASS-2 mapping later |
| Review screen | `app/review_app.py` (Streamlit) | Built on Streamlit |
| Evaluation runner | `scripts/evaluate.py`, `config/evaluation_scenarios.yaml` | Built |

LangExtract adapter decisions: one call per document, results cached; only
extractions anchored to a non-empty stretch of the document become proposals;
the quote is the full source line around the anchored span; few-shot examples
use a different fictitious product (door D-200) and include a Ug line with no
extraction; every raw model output is written to the diary.

## 5. Evaluation

| Kind | How | Status |
|---|---|---|
| Normal path | T01, T01b on the baseline documents | Passing |
| Missing and invented values | T02, T02b | Passing |
| Wrong attribute, scope, product | T11, T04, T05 | Passing |
| Conflicts | T03 | Passing |
| Failed checks cannot be bypassed | T06, audit regressions 02 and 03 | Passing |
| Authority | T07, T07b, T07c, rule-layer tests | Passing |
| Version binding and corrections | T12, T13 | Passing |
| Handover and diary | T08, T14 | Passing |
| PDF input with page numbers | P01–P03 | Passing |
| LangExtract adapter handling of model output | L01–L05, with a LangExtract-shaped fake | Passing |
| Review screen shows value beside evidence; no pre-selection; refusals shown | U01–U05 (Streamlit AppTest) | Passing |
| Evaluation runner, repeated runs | E01; stand-in: 49 of 49 outcomes as expected (Markdown and PDF) | Passing |
| Do the tests detect removed safeguards? | `scripts/fault_injection.py`: 12 of 12 | Passing |
| Real AI behaviour | `scripts/evaluate.py --extractor langextract --model ... --runs 3` | Waiting for model choice and API key |
| Authentic documents | Small set of public datasheets | Not started |
| Practitioner walkthrough of the review screen | Tiivi interview | Not started |

Synthetic cases show controlled behaviour; they do not establish performance
on real manufacturing documents. Screen tests use Streamlit's AppTest, not a
real browser or real users.

## 6. Handover contract

- Format: JSON, validated against `schemas/handover_v0.2.schema.json` (JSON Schema 2020-12).
- Contains only approved records whose approval matches their current version.
- Each element carries value, unit, scope, method, source, document fingerprint,
  quote, quote position, reviewer, approver and record version.
- Excluded elements are listed with the reason.
- Passing the schema shows structural conformity only. It does not show factual
  correctness, regulatory compliance or organisational authorisation.
- A CIRPASS-2-compatible mapping is a later, optional step. The CIRPASS-2
  validator accepts uploaded JSON Schemas or SHACL templates and its software is
  experimental; it is a demonstration target, not a dependency.

## 7. Known limitations of v0.3

- No real AI model has been run yet; the adapter is tested with a fake that
  imitates LangExtract's output objects.
- PDFs are read with PyMuPDF as plain text per page; tables and complex
  layouts need Docling, which is not wired in.
- Identities (rita, aki) are simulated; there is no real login.
- The diary is durable and append-only in code, but not tamper-proof against
  someone editing the database file directly.
- Quote positions are measured in whitespace-normalised text.
- All test documents are invented; authentic documents are still to be added.
