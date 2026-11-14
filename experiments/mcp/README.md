# dpp-prep-mcp: MCP demo for the W-100 preparation controls

A small MCP server ("dpp-sources") that lets an AI client read the fictional W-100 sources and submit candidate values to the **unchanged** dpp-prep checks. The full specification is in `SPEC.md` (v1.3, frozen).

**Status:** exploratory integration demonstration for the thesis appendix. It is not part of the evaluation, it does not execute or validate BPMN v0.6, and it shows no industrial integration. "Checked" means the configured checks passed; it does not mean DPP-ready.

## What is in the folder

| File | Purpose |
|---|---|
| `server.py` | the MCP server: four tools |
| `demo_client.py` | a script that talks to the server over MCP and runs the scenarios |
| `tests/test_server.py` | 14 tests (SPEC §8) |
| `vendor/dpp-prep-08d5840/` | read-only copy of the frozen dpp-prep (git archive of commit 08d5840) |
| `requirements.txt` | pinned versions |
| `SPEC.md` | the specification |

## The four tools

| Tool | What it does | Corresponding BPMN activity (Figure 9b) |
|---|---|---|
| `get_product(product_id)` | returns the fictional ERP record | Import value from structured record |
| `list_sources(product_id)` | lists the allowed sources with fingerprints | Select source documents and records |
| `read_source(source_id)` | returns one source's text and fingerprint | Propose value with supporting evidence (the AI reads) |
| `run_candidate_checks(...)` | runs the frozen evidence and rule checks on a candidate | Locate evidence; Run rule checks |

There are no tools for review, approval, readiness or release. That absence is deliberate (SPEC D4).

## Setup on the Mac

```bash
cd ~/path/to/dpp-prep-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest            # expect: 14 passed
python demo_client.py       # runs the scenarios over MCP
```

## Using it with Claude Desktop (AI-agent demonstration)

1. Open Claude Desktop → Settings → Developer → Edit Config. This opens `claude_desktop_config.json`.
2. Add the server, using **absolute paths**:

```json
{
  "mcpServers": {
    "dpp-sources": {
      "command": "/Users/YOU/path/to/dpp-prep-mcp/.venv/bin/python",
      "args": ["/Users/YOU/path/to/dpp-prep-mcp/server.py"]
    }
  }
}
```

3. Restart Claude Desktop. The tools appear under the tools icon.
4. Example prompts:
   - "Use the dpp-sources tools. List the sources for W-100, find the whole-window thermal transmittance Uw, and check your candidate value with run_candidate_checks."
   - "Now try the glazing value Ug from V6_D1_ug_only as if it were Uw, and tell me what the checks say."
   - "Read the sash-only supplier declaration and check its composition as the frame material composition E03."

Exact menu names may differ between Claude Desktop versions.

## Fallback: MCP Inspector (tool-call feasibility only)

If Claude Desktop does not work within about 30 minutes, use the official MCP Inspector (needs Node.js):

```bash
npx @modelcontextprotocol/inspector /Users/YOU/path/to/dpp-prep-mcp/.venv/bin/python /Users/YOU/path/to/dpp-prep-mcp/server.py
```

It opens in the browser, where you call each tool by hand. With the Inspector or `demo_client.py`, a person or a script calls the tools. Describe the result only as **MCP server integration and tool-call feasibility**, not as an AI-agent demonstration (SPEC §9).

## Observed results (26 October 2026, build environment)

| Scenario | Expected (SPEC §6) | Observed | Failed checks |
|---|---|---|---|
| S1 supported Uw (datasheet passage with reference size) | checked | **checked** | none |
| S1-note short quote from the report | flagged (scope) | **flagged** | scope |
| S2 glass-only Ug proposed as Uw | flagged (support, scope) | **flagged** | support, scope |
| S3a sash, supplier article PP-SA-100 | flagged (identity) | **flagged** | identity |
| S3b sash, reported product ID W-100 | checked (known limitation) | **checked** | none |

All observed results match the expectations written before the build. The frozen code was not changed.

## Known limitations (to report)

1. **No product/component rule.** A sash-only composition passes as the frame composition when the reported product ID is W-100 (S3b).
2. **The product ID comes from the proposer.** The identity check compares the product ID *reported in the candidate* with W-100. It is not verified against the source. The frozen message "source refers to 'PP-SA-100'" therefore describes the proposer's claim, not a check of the document.
3. **Only the checks run.** Review, approval, readiness assessment and release are not part of this demo.
4. **Fictional data only.** No real ERP, PLM or LCA system is connected.

## Rules this demo keeps

- The AI supplies only the candidate. The server loads the source itself and runs the frozen checks (D1).
- The vendor copy is read-only. No bytecode is written, and the diary runs in memory (D2). Test T8 confirms that the vendor copy and the dpp-prep repository are unchanged.
- Source IDs map to fixed files. Client input never becomes a path (D5).



