# ADR 0001: Local language models through Ollama

**Recorded after the change.** The change was made on 11 Oct 2026 (v0.3.1)
before this record was written; this record was added on 13 Oct 2026 when
the rule in CLAUDE.md was found not to have been followed.

## Context
The evaluation needs real language-model proposals. The cloud route through
LangExtract could not be used:
- gemini-2.5-flash was withdrawn for new users;
- gemini-3.8-flash returned HTTP 503 ("high demand") on 8 Oct 2026, and the
  runner stopped at the first failed call;
- paid API credit was outside the study's budget.
Cloud models can also change or disappear without notice, which weakens
reproducibility.

## Decision
Add a second language-model adapter, `src/dpp_prep/ollama_extract.py`, that
calls open-weight models running locally through Ollama:
- one call per document; answer bound to a JSON schema built from the
  element profile;
- temperature 0, seed 42, thinking switched off where the model supports it;
- model digest recorded with every answer;
- the model's quote is passed on unchanged, so the existing evidence check
  (verify.py) drops quotes that are not in the document and the diary records
  why (the LangExtract adapter discarded them itself);
- every raw answer saved to a JSONL file; `--replay` repeats a run exactly
  without the model.
Models used: qwen3.5:4b, qwen3.5:9b, gemma4:12b.

## What did not change
`states.py`, `checks.py`, `verify.py`, `service.py`, `models.py` and
`schemas/` are identical to v0.3; the W-100 documents and expected outcomes
are unchanged. Check: `git diff v0.3 v0.3.1 -- src/dpp_prep/checks.py
src/dpp_prep/states.py src/dpp_prep/verify.py schemas/ data/ config/` prints
nothing.

## Consequences
- The AI step can be evaluated without cost or rate limits, and reproduced.
- Local 4-12B models are weaker than frontier cloud models and are not what
  commercial DPP vendors use; Chapter 4 and 7 must say so.
- Tests O01-O09 cover the adapter with a fake transport and a fake HTTP
  server; fault injection still detects 12 of 12 removed safeguards.
