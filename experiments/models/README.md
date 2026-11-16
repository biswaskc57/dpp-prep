# Process and data models (thesis Appendix 3)

Design artifacts, not code. Only the demonstrator (`src/`) was implemented and
evaluated. These files were added to the repository on 16 Nov 2026 from the author's
working folder; they were not committed at the time they were made. File names are
kept as they were. Dates are file dates (≈) unless a decision-log entry is given.

## BPMN (`bpmn/`)

| File | Date | Version | Status |
|---|---|---|---|
| `dpp-prep_preparation_process.bpmn` | ≈28 Sep 2026 | first model | superseded |
| `dpp-prep_preparation_process_v0.4.bpmn` | ≈5 Oct 2026 | v0.4 (after supervisor feedback, D014) | superseded |
| `dpp-prep_preparation_process_v0.4.1.bpmn` | ≈15 Oct 2026 | v0.4.1 | superseded |
| `dpp-prep_preparation_process_v0.5.bpmn` | ≈15 Oct 2026 | v0.5 | superseded |
| `dpp-prep_preparation_process_v0.5.1.bpmn` | ≈15 Oct 2026 | v0.5.1 | superseded |
| `dpp-prep_preparation_process_v0.5.2.bpmn` | ≈17 Oct 2026 | v0.5.2, locked and audited against the code (D028; thesis Section 6.3, Table A4) | initial model, audited |
| `dpp-prep_preparation_process_v0.6.bpmn` | ≈26 Oct 2026 | v0.6, all three levels in one file | refined design, not implemented |
| `dpp-prep_preparation_process_v0.6_product_level.bpmn` | ≈25 Oct 2026 | v0.6 product level | refined design, not implemented |
| `dpp-prep_preparation_process_v0.6_element_level.bpmn` | ≈26 Oct 2026 | v0.6 element level | refined design, not implemented |
| `dpp-prep_preparation_process_v0.6_readiness_subprocess.bpmn` | ≈25 Oct 2026 | v0.6 readiness assessment | refined design, not implemented |
| `Figure8_product_level.bpmn` | ≈28 Oct 2026 | v0.6 product level, thesis figure edition | labels only changed from v0.6 |
| `Figure9_element_level.bpmn` | ≈28 Oct 2026 | v0.6 element level, thesis figure edition | labels only changed from v0.6 |
| `Figure10_readiness_step.bpmn` | ≈28 Oct 2026 | v0.6 readiness assessment, thesis figure edition | labels only changed from v0.6 |

The "Figure" numbers in file names are working numbers from October 2026 and may
differ from the figure numbers in the final thesis.

## Data model (`data_model/`)

Only images exist; the data models were drawn as figures, with no separate editable source.

| File | Date | Version | Status |
|---|---|---|---|
| `Figure8_dpp-prep_data_model.png` | ≈15 Oct 2026 | earliest data-model figure (uncertain whether this is v1) | superseded |
| `Figure8_data_model_v2.png`, `_v3.png` | ≈16 Oct 2026 | v2, v3 | superseded |
| `Figure8_data_model_v4.png` | ≈16 Oct 2026 | v4, marks implemented and conceptual parts; audited with BPMN v0.5.2 | initial model, audited |
| `Figure8_data_model_v5.png`, `_v5.1.png` | ≈25 Oct 2026 | v5, v5.1 (D040, D041) | refined design, not implemented |
| `Figure8_data_model_v5.2.png`, `.svg` | ≈26 Oct 2026 | v5.2 | refined design, not implemented |
| `Figure11_conceptual_data_model.png`, `.svg` | ≈28 Oct 2026 | conceptual data model, thesis figure edition | refined design, not implemented |

## Decision model

The DMN tables are in `experiments/dmn/`. They were run after the evaluation, on the
saved outputs in `results/evaluation_2026-10-17/`, and are not part of the demonstrator.
