# Agent probe (post hoc, illustrative) — 29 Oct 2026

An AI agent (local model via Ollama, tool calling) gets a task such as "Prepare E06 for
product W-100" and may use only the four MCP tools. It must find and read the documents
itself, propose a value with an exact quote, and submit it to the **unchanged** demonstrator
controls. No tool exists for review, approval, readiness or release.

This is a separate assessment of an agent workflow that uses the demonstrator's controls.
It is not part of the frozen evaluation, and nothing in `vendor/` is changed.

## What is new
| File | Purpose |
|---|---|
| `server.py` (v1.4) | `DPP_POOL` setting: only one pool's documents are visible, under neutral names `doc_1…` (no file names, neutral titles); without it the server is unchanged |
| `probe/pool_key.yaml` | hidden key, written before any run: suitability of each document per element and the expected value or abstention |
| `probe/agent_probe.py` | the agent loop (Ollama ↔ MCP), one JSON log per task |
| `probe/score.py` | compares logs with the key; writes `scores.csv` and `summary.md` |
| `tests/test_probe.py` | 6 tests (pool mode, masking, scoring) |

## Pilot (16 tasks)
Elements Uw (E06) and frame composition (E03) × pools `basic`, `realistic`,
`stale` (adds a superseded test report), `sash` (supplier declaration for the sash only)
× prompt A (plain) and B (evidence-first). Model: qwen3.5:9b, temperature 0, seed 42,
thinking off, at most 15 tool calls per task.

## Run on the Mac
```bash
cd ~/Desktop/thesis/dpp-prep-mcp            # wherever you unzipped it
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                            # expect: 20 passed
python probe/agent_probe.py --model qwen3.5:9b --only basic:E06:A     # 1 smoke-test task
python probe/agent_probe.py --model qwen3.5:9b                         # the 16-task pilot
python probe/score.py probe/runs/<folder printed at the end>
```
Stability check afterwards (4 tasks, one more run each):
```bash
python probe/agent_probe.py --model qwen3.5:9b --repeat 1 --only basic:E06:A --only stale:E06:B --only sash:E03:A --only realistic:E03:B
```

## Known properties (state them when reporting)
- The check tool takes one candidate at a time, so the controls' **conflict check cannot fire**; noticing disagreement between documents is left to the agent.
- On the realistic documents even a correct Uw can be flagged (literal unit/size comparison, pre-registered), so outcomes are scored against the key, not against "checked".
- The controls do **not** know that a document is superseded or covers only a component; if an outdated or component value reaches "checked", that is recorded as a control limitation.
- Check results are shown to the agent on purpose (it may correct itself); the log records what it submitted before and after feedback.
- Small numbers, synthetic documents, one model: illustrative only.

## Change log
- 29 Oct 2026, after the first smoke test and before the pilot: the parameter descriptions of
  `run_candidate_checks` were clarified (value without unit; unit and scope in their own fields).
  In the smoke test the agent found the right document and quote but put the unit inside the
  value and left unit and scope empty, so the checks failed on the interface, not on the
  information. The checks themselves are unchanged. The smoke-test log is kept.