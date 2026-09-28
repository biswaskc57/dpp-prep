# dpp-prep specification, version 0.2

This document is the implementation contract. Every rule here has a test.

## 1. Purpose in one sentence

Prepare DPP-relevant product information so that nothing leaves the tool unless
its evidence supports it, its rules pass, a named reviewer chose it after seeing
the evidence, and a different named approver approved that exact version.

## 2. Information model — what the tool keeps

| Thing | Plain meaning | Key contents |
|---|---|---|
| Profile | The wish list | Elements, how each is obtained (`route`), required words in the quote, unit, scope, which checks apply, profile version |
| Source | A document or structured record | Name, text, SHA-256 fingerprint |
| Proposal | One candidate value | ID, value, unit, scope, product, method (AI, import, manual), who produced it |
| Evidence | Where the value came from | Source, exact quote, context quote, position, document fingerprint |
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
| Reader | `sources.py` (text); Docling planned for PDF | Docling to be reused |
| Suggester | `extract.py`: stand-in now, LangExtract slot | LangExtract to be reused |
| Importer | `extract.StructuredImporter` | Built (no AI) |
| Fact-checker | `verify.py` + `checks.support` | Built |
| Rule checker | `checks.py` | Built |
| Gatekeeper rules | `states.py` | Built |
| Workflow | `service.py` | Built |
| Diary | `audit.py` (SQLite, append-only) | Built |
| Handover | `export.py` + `schemas/handover_v0.2.schema.json` | Built; CIRPASS-2 mapping later |

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
| Do the tests detect removed safeguards? | `scripts/fault_injection.py`: 10 of 10 | Passing |
| Real AI behaviour | Rerun the same cases with LangExtract, record every run | Not started |
| Authentic documents | Small set of public datasheets | Not started |
| Review screen shows value beside evidence | T09, manual walkthrough | Screen not built |

Synthetic cases show controlled behaviour; they do not establish performance
on real manufacturing documents.

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

## 7. Known limitations of v0.2

- The suggester is a deterministic stand-in; no real AI model is connected yet.
- Documents are Markdown text; PDF reading with Docling is not yet connected.
- Identities (rita, aki) are simulated; there is no real login.
- The diary is durable and append-only in code, but not tamper-proof against
  someone editing the database file directly.
- Quote positions are measured in whitespace-normalised text.
