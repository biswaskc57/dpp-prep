# dpp-real: the frozen demonstrator on real public documents (phase 3, post hoc)

Uses dpp-prep **read only** (found at $DPP_PREP, ../dpp-prep or ../dpp-prep-mcp/vendor/dpp-prep-08d5840).
No code in dpp-prep is changed. Element rules E03/E06 are copied unchanged; only the product block differs.

    docs/      original public PDFs, renamed P1_... P5_ (see SOURCES.md); never edited
    config/    elements_real_<product>.yaml, real_scenarios.yaml (pre-registered states), real_key.yaml (answers)
    out/       evaluation_*_real_*.csv / .sqlite / model_outputs_*.jsonl  (same format as dpp-prep)

Order: download -> fill SOURCES.md -> verify real_key.yaml -> confirm expectations -> commit -> run.

Known deviation from the frozen evaluation: num_ctx 24576 (was 8192) and timeout 1800 s, because real EPDs
are 10-30 pages. Model, temperature 0, seed and prompt are unchanged.
