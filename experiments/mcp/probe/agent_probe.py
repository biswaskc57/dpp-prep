"""Agent probe (post hoc, illustrative; 29 Oct 2026).

A local language model (Ollama, tool calling) gets one task, e.g. "Prepare E06 for product
W-100", and may use only the four tools of the MCP server (list_sources, read_source,
get_product, run_candidate_checks). The frozen demonstrator controls decide "checked" or
"flagged". There is no tool for review, approval, readiness or release.

The server runs in pool mode (DPP_POOL): the agent sees documents only under neutral names.
Every step is logged to one JSON file per task; score.py compares the logs with
probe/pool_key.yaml.

Usage (on the Mac, Ollama running):
    python probe/agent_probe.py --model qwen3.5:9b                       # pilot: 16 tasks
    python probe/agent_probe.py --model qwen3.5:9b --only basic:E06:A    # one smoke-test task
    python probe/agent_probe.py --fake                                   # offline test of the loop
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
RUNS = ROOT / "probe" / "runs"

ELEMENTS = {  # descriptions as in the element profile of the frozen demonstrator
    "E06": "Declared thermal transmittance of the whole window (Uw)",
    "E03": "Frame material composition by mass share",
    "E04": "Glazing unit build-up",
    "E07": "Identifier of the thermal performance test report",
}
PILOT = [(p, e, s) for p in ("basic", "realistic", "stale", "sash") for e in ("E06", "E03") for s in ("A", "B")]

FINAL_FORMAT = ('When you are finished, reply with only a JSON object: {"status": "proposed" or "unresolved", '
                '"value": ..., "source_id": ..., "quote": ..., "reason": ...}.')
PROMPT_A = ("You prepare product information for a Digital Product Passport. You have tools to list and read "
            "the sources available for a product, to get its ERP record, and to submit a candidate value with "
            "its exact supporting quote for automated checks. Find the value of information element {eid} "
            "({desc}) for product W-100 and submit it for checks. " + FINAL_FORMAT)
PROMPT_B = PROMPT_A.replace(FINAL_FORMAT, "") + (
    "Rules: (1) Read the documents before deciding which ones to use; do not rely on document names. "
    "(2) Quote only text copied exactly from a document, including the unit and the size or scope the value "
    "refers to. (3) The value must describe the whole product (the whole window), not a component such as "
    "the glazing (Ug), the frame profile (Uf) or the sash. (4) Prefer current documents; check whether a "
    "document has been replaced or superseded. (5) If valid documents disagree, or no document supports the "
    "value, reply with status \"unresolved\" and explain why, instead of choosing. (6) If the checks fail, you "
    "may resubmit at most once, and only with new supporting evidence from a document; otherwise stop and "
    "report. " + FINAL_FORMAT)


# ------------------------------------------------------------------ language model back ends
class Ollama:
    def __init__(self, model: str, host: str, seed: int, num_ctx: int, timeout: int):
        self.model, self.host, self.seed, self.num_ctx, self.timeout = model, host.rstrip("/"), seed, num_ctx, timeout

    def info(self) -> dict:
        try:
            with urllib.request.urlopen(self.host + "/api/tags", timeout=10) as r:
                tags = json.load(r)
            m = next((m for m in tags.get("models", []) if m.get("name") == self.model), {})
            return {"model": self.model, "digest": m.get("digest"), "seed": self.seed, "temperature": 0,
                    "think": False, "num_ctx": self.num_ctx}
        except Exception as e:  # noqa: BLE001
            return {"model": self.model, "error": str(e)}

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        body = {"model": self.model, "messages": messages, "tools": tools, "stream": False, "think": False,
                "options": {"temperature": 0, "seed": self.seed, "num_ctx": self.num_ctx}}
        req = urllib.request.Request(self.host + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.load(r)["message"]


class Fake:
    """Scripted stand-in for offline testing of the loop, logging and scoring."""

    def __init__(self):
        self.step = 0

    def info(self) -> dict:
        return {"model": "fake (scripted)"}

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        self.step += 1
        script = [
            {"name": "list_sources", "arguments": {"product_id": "W-100"}},
            {"name": "read_source", "arguments": {"source_id": "doc_1"}},
            {"name": "run_candidate_checks", "arguments": {"element_id": "E06", "value": "1.2",
                                                           "quote": "Uw = 1.2 W/(m2K)", "source_id": "doc_1",
                                                           "unit": "W/(m2K)", "product_id": "W-100"}},
            {"name": "read_source", "arguments": {"source_id": "doc_3"}},
        ]
        if self.step <= len(script):
            return {"role": "assistant", "content": "", "tool_calls": [{"function": script[self.step - 1]}]}
        return {"role": "assistant", "content": json.dumps({"status": "unresolved", "value": None,
                                                            "source_id": None, "quote": None,
                                                            "reason": "fake run"})}


# ------------------------------------------------------------------ one task
def parse_final(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def run_task(llm, pool: str, eid: str, style: str, max_steps: int) -> dict:
    env = dict(os.environ, DPP_POOL=pool)
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)
    system = (PROMPT_A if style == "A" else PROMPT_B).replace("{eid}", eid).replace("{desc}", ELEMENTS[eid])
    messages = [{"role": "system", "content": system}, {"role": "user", "content": f"Prepare {eid} for product W-100."}]
    steps, final, stop = [], None, "final answer"
    t0 = time.time()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = (await session.list_tools()).tools
            tools = [{"type": "function", "function": {"name": t.name, "description": t.description or "",
                                                       "parameters": t.inputSchema}} for t in listed]
            calls = 0
            while True:
                try:
                    msg = llm.chat(messages, tools)
                except Exception as e:  # noqa: BLE001 - recorded, task ends
                    stop = f"model error: {e}"
                    break
                messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
                tcs = msg.get("tool_calls") or []
                if not tcs:
                    final = parse_final(msg.get("content", ""))
                    if final is None:
                        stop = "no parsable final answer"
                    steps.append({"type": "final", "content": msg.get("content", ""), "parsed": final})
                    break
                for tc in tcs:
                    fn = tc.get("function", {})
                    name, args = fn.get("name"), fn.get("arguments") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    calls += 1
                    try:
                        res = await session.call_tool(name, args)
                        text = "".join(getattr(c, "text", "") for c in res.content)
                    except Exception as e:  # noqa: BLE001
                        text = json.dumps({"error": str(e)})
                    try:
                        result = json.loads(text)
                    except json.JSONDecodeError:
                        result = {"raw": text}
                    steps.append({"type": "tool", "n": calls, "name": name, "arguments": args, "result": result})
                    messages.append({"role": "tool", "tool_name": name, "content": text})
                if calls >= max_steps:
                    stop = f"step limit ({max_steps}) reached"
                    break
    return {"pool": pool, "element": eid, "prompt": style, "system_prompt": system, "steps": steps,
            "final": final, "stop": stop, "seconds": round(time.time() - t0, 1)}


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.5:9b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--num-ctx", type=int, default=16384)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--max-steps", type=int, default=15)
    ap.add_argument("--only", action="append", help="pool:element:prompt, e.g. basic:E06:A (repeatable)")
    ap.add_argument("--repeat", type=int, default=1, help="run each task this many times")
    ap.add_argument("--fake", action="store_true", help="offline scripted model (tests the loop only)")
    a = ap.parse_args()

    tasks = [tuple(x.split(":")) for x in a.only] if a.only else PILOT
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RUNS / (("fake_" if a.fake else "") + stamp)
    out.mkdir(parents=True, exist_ok=True)
    meta = {"started": datetime.now(timezone.utc).isoformat(), "server": "dpp-sources v1.4 (pool mode)",
            "tasks": [":".join(t) for t in tasks], "repeat": a.repeat, "max_steps": a.max_steps}
    for t in tasks:
        for rep in range(1, a.repeat + 1):
            llm = Fake() if a.fake else Ollama(a.model, a.host, a.seed, a.num_ctx, a.timeout)
            meta.setdefault("llm", llm.info())
            pool, eid, style = t
            print(f"[{datetime.now():%H:%M:%S}] {pool} {eid} prompt {style} run {rep} ...", flush=True)
            res = asyncio.run(run_task(llm, pool, eid, style, a.max_steps))
            res["run"] = rep
            (out / f"{pool}_{eid}_{style}_run{rep}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False),
                                                                     encoding="utf-8")
            fin = res["final"] or {}
            print(f"    -> {res['stop']}; status={fin.get('status')} value={fin.get('value')!r} "
                  f"({len([s for s in res['steps'] if s['type'] == 'tool'])} tool calls, {res['seconds']} s)")
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"logs: {out}\nnext: python probe/score.py {out}")


if __name__ == "__main__":
    main()
