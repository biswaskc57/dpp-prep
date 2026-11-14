# DMN readiness results for the public-EPD run

Input: `experiments/public-epd/results/run_2026-10-29/` (the reported run).
Command, from `experiments/dmn/` with pyDMNrules 1.4.5 and pySFeel 1.4.2:

    python run_cases.py ../public-epd/results/run_2026-10-29 standin ollama-gemma4-12b ollama-qwen3.5-4b ollama-qwen3.5-9b

Provenance: these results were first computed on 29 Oct 2026 in an AI-assisted
workspace (Claude) from the saved run files, not on the author's computer. They were
re-executed on 14 Nov 2026 with the pinned versions above and added here. The three
language-model files are byte-identical to the 29 Oct files. The stand-in file is new:
the 29 Oct stand-in file came from a test with placeholder documents and is not used.

Result (three language models, 30 element outcomes): 15 flagged -> not ready,
15 unresolved -> undetermined, none ready. Stand-in: 10 unresolved -> undetermined.
The DMN rule tests (tests/test_rules.py) passed: 50 tests.
