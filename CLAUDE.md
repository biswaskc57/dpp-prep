# dpp-prep — rules for Claude

## What this project is
Master's thesis prototype. Governed preparation of DPP-relevant information:
AI proposes values; code verifies evidence and rules; a named reviewer chooses;
a different named approver approves the exact version; only then is it exported.
See docs/specification_v0.3.md and docs/architecture.md.

## How we work
- Plan before changing anything. Wait for my approval of the plan.
- One small change at a time. Write or update the test first, then the code.
- Explain every change in plain words: what changed and why.
- Run `pytest` after every change. Report the result.
- Never commit, push or tag. I commit myself.

## Never change without a decision record in docs/adr/
- The approval and state rules (src/dpp_prep/states.py)
- The checks and evidence verification (checks.py, verify.py)
- The handover schema (schemas/)
- The W-100 test documents and expected outcomes (data/w100/)

## Honesty rules
- Never weaken or delete a test to make it pass. If a test fails, tell me why.
- Never invent results. Report exactly what the tests and scripts output.
- Mark anything uncertain as uncertain.1§