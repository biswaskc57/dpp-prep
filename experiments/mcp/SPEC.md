# MCP demo for dpp-prep: specification

Version 1.3 (final) · 26 October 2026 · Status: **approved and frozen, not built** · No further revisions; next milestone is implementation.

Changes from 1.0: pinned SDK version (§7), fixed source mapping (D5), fallback host and its wording (§9). Changes in 1.2: results of the compatibility check against the frozen code (§4.5), corrected expected results for S1, S2 and S3b (§6), wording on version pinning (§7). Changes in 1.3: relation to the separate career track (§12); content of the thesis demo unchanged. No further design review unless implementation reveals a concrete technical incompatibility.

Build trigger: build only when (1) the numbers are verified on the Mac, (2) the refinement section is written and (3) the core Innsbruck slides are ready. Then implement the four tools, test the three scenarios, and stop. There are no further architecture rounds.

---

## 1. Purpose

Build one small MCP server that lets an AI client reach the W-100 sources through a standard interface and submit candidate values to the **unchanged** dpp-prep checks.

It has three aims:

- **Learn.** How an MCP server, its tools and an AI host work together.
- **Show.** Where AI autonomy ends and fixed business controls begin. The AI can read and propose. It cannot validate its own claims, review, approve or release.
- **Future.** A first building block for a DPP connector to real systems (portfolio, consulting).

### What it is not (non-goals)

- Not a new thesis experiment. It produces no new evaluation results.
- Not an execution of BPMN v0.6, and not a validation of it.
- Not evidence of industrial integration: it uses fictional data and no real ERP, PLM or LCA system.
- Not a new control. It adds no check that dpp-prep does not already have, including no product/component check.

### Place in the thesis

The demo goes in an appendix or a "future development" subsection, labelled **exploratory integration demonstration**. It is kept apart from the frozen evaluation results. The main text carries one paragraph: *MCP provides access to information, while independent preparation controls assess whether proposed values pass configured checks. Full readiness assessment and human approval remain outside this demonstration.* ("Checked" here is not "DPP-ready".)

---

## 2. Architecture

```
AI client (e.g. Claude Desktop)
    │  MCP (stdio)
    ▼
MCP server: dpp-sources
    ├── get_product(product_id)        → fictional ERP record
    ├── list_sources(product_id)       → allowed documents with identity
    ├── read_source(source_id)         → document text + fingerprint
    └── run_candidate_checks(...)      → frozen dpp-prep pipeline
                                              │
                                              ▼
                                  check results + reasons + resulting state
                                  (no review, approval, readiness or release)
```

---

## 3. Design rules

| # | Rule |
|---|---|
| D1 | **The AI never decides its own validation outcome.** The AI supplies only the candidate: element, value, quote, source ID, unit, scope and product ID. The server retrieves the source itself, applies the configured element definition and runs the existing checks. |
| D2 | **The frozen code is isolated.** The server runs on its own copy of dpp-prep commit 08d5840, unpacked with `git archive`. Source files are read-only. The diary uses an in-memory store, and any output goes to a separate folder. Nothing is ever written to the dpp-prep repository. |
| D3 | **Workflow states come only from the pipeline.** `checked`, `flagged` or `unresolved` are returned only as produced by the frozen pipeline. Nothing is inferred or invented by the server. |
| D4 | **No human-decision tools.** There are no tools for review, approval, release or readiness. Their absence is part of the design. |
| D5 | **An allowlist of sources, as a fixed mapping.** A fixed table in the server maps each source ID to one file in the vendor copy (e.g. `"D3_performance_report" → data/w100/baseline/D3_performance_report.md`). File paths are never built from the AI's input, so path tricks such as "../x" are impossible by design. Only the frozen W-100 files are in the table: baseline, variants, production-like and the ERP record. Any other ID is refused. |
| D6 | **Honest reporting.** Every check result states which checks ran, their outcome and reason, and which steps of the original workflow were not executed. |

---

## 4. Tools

### 4.1 `get_product(product_id)`

- **Input:** `product_id` (string, e.g. "W-100")
- **Output:** the fictional ERP record (`product_id`, `manufacturer`, `nominal_size`, `size_unit`), its fingerprint (SHA-256) and the source ID `erp_product_record`
- **Error:** unknown product → "no record for this product"

### 4.2 `list_sources(product_id)`

- **Input:** `product_id`
- **Output:** a list of allowed sources, each with `source_id`, `kind` (document or structured record), `set` (baseline, variant, production-like), a short title and its fingerprint

### 4.3 `read_source(source_id)`

- **Input:** `source_id` from the list
- **Output:** the full text (Markdown version of the document), the fingerprint and the source ID
- **Error:** an ID not in the allowlist → refused

### 4.4 `run_candidate_checks(element_id, value, quote, source_id, unit, scope, product_id)`

**Input**, all from the AI:

| Field | Example |
|---|---|
| `element_id` | "E06" |
| `value` | "1.1" |
| `quote` | "Uw = 1.1 W/(m2K)" |
| `source_id` | "D3_performance_report" |
| `unit` (optional) | "W/(m2K)" |
| `scope` (optional) | "1230 x 1480 mm" |
| `product_id` (optional) | "W-100" |

**What the server does.** It uses only frozen code, with no new logic.

1. It loads the source by `source_id` from its own copy. The AI's text is not used.
2. It builds one proposal from the candidate. The proposal enters the frozen preparation flow through the existing extractor slot (the same slot the evaluation used for the oracle and the language models).
3. It runs the frozen flow for this element:
   - locate the quote in the source (unsupported proposals are dropped);
   - the configured rule checks for the element (support, value type, identity, unit, scope, composition sum, conflict as configured);
   - the resulting state.
4. It returns the result for this element only.

### 4.5 Compatibility check against the frozen code (done before building)

Read from `service.py`, `verify.py` and `checks.py` (commit 08d5840):

- **One outside proposal can enter the pipeline** through the extractor slot (`propose(element, document)`). The other elements end as unresolved, which does not affect the result for the element tested.
- **A quote not found in the source** is dropped by the evidence check. With no proposal left, the state is **unresolved**, not flagged.
- **The scope check** requires the proposal's scope to equal the required scope ("1230 x 1480 mm") **and** that text to appear in the quote or its context quote. A short quote without the reference size therefore fails the scope check (cause C2 in the evaluation).
- **The identity check** compares the product ID **as reported in the proposal** with W-100. It does not verify the ID against the source document. In this demo the product ID therefore comes from the AI. This is a limitation of the frozen checks (it applied to the language models in the evaluation as well), and it is reported, not fixed.

**Output:**

```json
{
  "element_id": "E06",
  "quote_found": true,
  "checks": [
    {"name": "support", "passed": true, "reason": ""},
    {"name": "unit", "passed": true, "reason": ""}
  ],
  "state": "checked",
  "state_source": "frozen dpp-prep v0.3.2 pipeline",
  "not_executed": ["review", "approval", "readiness assessment", "package release"]
}
```

---

## 5. Corresponding BPMN activities (element level, Figure 9b)

MCP exposes functions. It does not execute the BPMN diagram.

| Tool | Corresponding BPMN activity |
|---|---|
| `list_sources` | Select source documents and records |
| `get_product` | Import value from structured record |
| `read_source` + the AI's own reasoning | Propose value with supporting evidence |
| `run_candidate_checks` | Locate evidence; Run rule checks |
| *(no tool)* | Assess readiness; Review; Approve; Release (human or not implemented) |

---

## 6. Scenarios and expected results

The expected results are stated **before** building, from the frozen code and the probe result of 18 October. The tests check them.

| # | Candidate from the AI | Expected (frozen pipeline) | What it shows |
|---|---|---|---|
| S1 | E06 Uw = 1.1, actual datasheet passage "Uw = 1.1 W/(m2K) for reference size 1230 x 1480 mm." from D1, unit W/(m2K), scope 1230 x 1480 mm, product W-100 | quote found; support, value type, identity, unit and scope pass → **checked** | a supported value passes |
| S1-note | as S1, but the short quote "Uw = 1.1 W/(m2K)" from the report D3 | **scope fails** (reference size not in the quote) → **flagged** | the over-flag seen in the evaluation (C2); reported, not a scenario of its own |
| S2 | E06 Uw = 0.5, quote "Ug = 0.5 W/(m2K) (glazing only, centre of pane)." from variant V6, product W-100 | quote found; **support fails** (quote does not mention "Uw"; excluded term "Ug"); scope also fails (no reference size) → **flagged** | glass-only value refused by existing rules |
| S3a | E03 sash composition, quote from R2b sash-only declaration, product ID **PP-SA-100** (as in the document) | **identity fails** → **flagged** | stopped, but only incidentally (as in the evaluation) |
| S3b | **same source, same quote and same value** as S3a; only the product ID reported in the proposal is W-100 | all checks pass → **checked** | **two known limitations:** no product/component rule (sash case, §6.4), and the product ID is taken from the proposer, not verified against the source (§4.5) |

If a test shows a different result, the result is reported as it is, and the frozen code is not changed.

---

## 7. Folder layout and technology

```
dpp-prep-mcp/                     (separate folder, NOT inside the dpp-prep repo)
├── SPEC.md                       (this document)
├── README.md                     (setup, Claude Desktop configuration, demo script)
├── vendor/dpp-prep-08d5840/      (git archive copy; read-only)
├── requirements.txt              (pinned versions, e.g. mcp==1.27.0)
├── server.py                     (the MCP server: four tools, ~150 lines)
└── tests/test_server.py          (tools, scenarios S1–S3b, allowlist, no-writes check)
```

- **Language:** Python 3.11.
- **Library:** the official MCP Python SDK (`mcp`, FastMCP), **version pinned** in `requirements.txt` (1.27.0 in the build environment), to reduce dependency-related differences between the Mac and the test environment.
- **Transport:** stdio, which is what Claude Desktop uses for local servers.
- **Host:** Claude Desktop on the Mac, configured via its MCP server settings. Steps go in README.md.
- **No network access, and no language model inside the server.**

---

## 8. Tests (written before the server code)

| Test | Checks |
|---|---|
| T1 | `get_product("W-100")` returns the ERP record with the correct fingerprint |
| T2 | `list_sources` lists only allowlisted files |
| T3 | `read_source` refuses an unknown ID and a path such as "../x" |
| T4–T7 | scenarios S1, S2, S3a, S3b give the expected results (§6) |
| T8 | after all tests, the dpp-prep repository is unchanged (`git status` clean) and the vendor copy is unchanged |

---

## 9. Time and stop rule

- **Estimate:** 2–3 hours, plus about 30 minutes to set up Claude Desktop on the Mac.
- **Stop when:** the four tools work, tests T1–T8 pass and the demo runs once in **either Claude Desktop or the MCP Inspector**.
- **Fallback host.** If Claude Desktop setup does not work within about 30 minutes, use the MCP Inspector (the official tool for calling an MCP server's tools by hand) or a short test client script.
- **Wording depends on the host.** With Claude Desktop, the AI chooses and calls the tools itself, so the result can be described as an AI-agent demonstration. With the Inspector or a script, a person or script calls the tools, so it must be described only as **MCP server integration and tool-invocation feasibility**, not as an AI-agent demonstration.
- **Not added later without a new decision:** more tools, real systems, a language model inside the server, review or approval tools.

---

## 10. Learning goals

1. How an MCP server exposes tools, and how an AI host discovers and calls them.
2. Designing tool inputs and outputs so that the AI cannot overstep: it proposes, the server verifies.
3. Separating access (MCP) from control (your BPMN and readiness framework) in working code.
4. Reusing frozen research code safely: isolation, read-only data, no writes.

---

## 11. Open points

- Whether Claude Desktop is installed on the Mac (otherwise the MCP Inspector is the host, see §9).
- The exact wording of the thesis paragraph and the appendix entry, to be written after the demo runs.

---

## 12. Relation to the career track

This specification covers **only the thesis demo** (track 1). It stays at this scope after the appendix is written.

A separate career project (track 2) may extend the same idea in its own repository after submission. These are **ideas for a roadmap, not demonstrated capabilities**; their practicality, security and benefits remain to be tested. Examples: a tool-call audit log, separate source servers, product-ID verification at the access layer, a DMN readiness tool, role-based tool sets or a BPMN engine. Those extensions:

- are not part of the thesis and are not reported as thesis evidence;
- never change the frozen dpp-prep code or the thesis demo described here.

In the thesis, the product-ID finding (§4.5) is reported as a limitation and a design insight, not as demo code. The insight has two parts: identifiers should be taken from the source, not from the proposer; and an identity match alone cannot establish granularity, so it must be combined with explicit product–component relationships and alignment checks (the Aligned condition).

