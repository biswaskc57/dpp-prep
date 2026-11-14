"""Demo client: talks to server.py over the real MCP protocol (stdio), like an AI host would.

It discovers the tools and runs the scenarios of SPEC.md §6. Here a script calls the tools,
so this shows MCP integration and tool-call feasibility, NOT an AI agent choosing tools (SPEC §9).

Run:  python demo_client.py
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "server.py"
SASH_VALUE = "pine wood 74 %, aluminium 21 %, EPDM seals 4 %, steel fittings 1 %."
SASH_QUOTE = ("Sash profile set, share of sash mass: pine wood 74 %, aluminium 21 %, "
              "EPDM seals 4 %, steel fittings 1 %.")
UW = dict(element_id="E06", unit="W/(m2K)", scope="1230 x 1480 mm", product_id="W-100")

SCENARIOS = [
    ("S1  supported Uw", dict(UW, value="1.1", source_id="D1_datasheet",
                              quote="Uw = 1.1 W/(m2K) for reference size 1230 x 1480 mm.")),
    ("S1-note  short quote", dict(UW, value="1.1", source_id="D3_performance_report", quote="Uw = 1.1 W/(m2K)")),
    ("S2  glass-only Ug as Uw", dict(UW, value="0.5", source_id="V6_D1_ug_only",
                                     quote="Ug = 0.5 W/(m2K) (glazing only, centre of pane).")),
    ("S3a sash, supplier article", dict(element_id="E03", value=SASH_VALUE, quote=SASH_QUOTE, unit="%",
                                        source_id="R2b_supplier_declaration_sash_only", product_id="PP-SA-100")),
    ("S3b sash, reported W-100", dict(element_id="E03", value=SASH_VALUE, quote=SASH_QUOTE, unit="%",
                                      source_id="R2b_supplier_declaration_sash_only", product_id="W-100")),
]


def payload(result) -> dict:
    return json.loads(result.content[0].text)


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools offered by the server:", ", ".join(t.name for t in tools.tools))

            erp = payload(await session.call_tool("get_product", {"product_id": "W-100"}))
            print("\nERP record:", erp["record"])
            srcs = payload(await session.call_tool("list_sources", {"product_id": "W-100"}))
            print(f"Sources available: {len(srcs['sources'])}")
            bad = payload(await session.call_tool("read_source", {"source_id": "../config/elements_w100.yaml"}))
            print("Path trick refused:", "error" in bad)

            print("\nScenario                     state       failed checks")
            for label, args in SCENARIOS:
                r = payload(await session.call_tool("run_candidate_checks", args))
                failed = [f"{c['name']} ({c['reason']})" for c in r["checks"] if not c["passed"]]
                print(f"{label:<28} {r['state']:<11} {'; '.join(failed) or '-'}")
            print("\nNot executed by the server:", ", ".join(r["not_executed"]))


if __name__ == "__main__":
    asyncio.run(main())
