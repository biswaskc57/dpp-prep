# ADR 0002: Production-like tier, ground truth and oracle pre-registration

**Recorded after the change.** The change was made on 12 Oct 2026 (v0.3.2)
before this record was written; this record was added on 13 Oct 2026 when
the rule in CLAUDE.md (W-100 test documents and expected outcomes) was found
not to have been followed.

## Context
The original W-100 documents are short and uniform. They make each fault easy
to attribute but say little about real manufacturer documents, which have
tables, several product variants, mixed languages and typographic units.

## Decision
1. **Add, do not change.** A second tier of documents was added in
   `data/w100/realistic/` (Markdown) and `data/w100/pdf_realistic/` (PDF):
   a two-variant datasheet with Finnish labels and W/(m²K) notation; a
   supplier declaration with frame and sash tables; a full test report with a
   second, informative Uw; a Declaration of Performance; a replaced older
   report; a sash-only declaration. Three scenarios in
   `config/evaluation_scenarios_realistic.yaml`.
2. **Ground truth.** `config/ground_truth.yaml` records, per document, what it
   states for each element, which values belong to something else
   (distractors), and per scenario the value that should finally be released.
3. **Expectations fixed before any model run.** An oracle proposer
   (`src/dpp_prep/oracle.py`) submits exactly the stated values through the
   unchanged controls (`scripts/preregister.py`). The resulting end states are
   the expectations, saved with the date and the SHA-256 of every document.
   Test R02 fails if a document changes afterwards.
4. **Method check.** The oracle reproduces all 49 hand-written simple-tier
   expectations from September 2026 (test R01).

## What did not change
The simple-tier documents (`data/w100/baseline`, `variants`, `pdf`,
`structured`), `expected_outcomes.yaml`, `config/evaluation_scenarios.yaml`,
the element profile, the controls and the schema are identical to v0.3.
Check: `git diff v0.3 v0.3.2 -- data/w100/baseline data/w100/variants
data/w100/pdf data/w100/structured data/w100/expected_outcomes.yaml
config/evaluation_scenarios.yaml config/elements_w100.yaml src/dpp_prep/checks.py
src/dpp_prep/states.py src/dpp_prep/verify.py schemas/` prints nothing.

## Known irregularity
On 12 Oct, after the pre-registration run, three simple-tier quotes in
`ground_truth.yaml` were changed from `**Report ID:** NW-PR-2026-014` to
`NW-PR-2026-014`, because the Markdown asterisks are absent from the PDFs.
This affects only the simple tier's oracle, not the realistic expectations
(their document fingerprints are unchanged) and not any hand-written
expectation.

## Pre-registered findings (before any model saw the documents)
- Faithful proposals of Uw are flagged in every realistic scenario: the
  controls compare units and sizes literally (W/(m²K) vs W/(m2K), × vs x) and
  the Declaration of Performance omits the reference size.
- The stand-in reaches 15 of 21 expected outcomes on the realistic tier.

## Consequences
- The evaluation can separate "the controls behave as specified" (simple tier)
  from "the controls meet production notation" (realistic tier).
- The controls stay frozen; their literalness is reported as a finding, not
  fixed.
