"""Local language model through Ollama: the AI step without a cloud provider.

Added in v0.3.1 (11 Oct 2026). Same role as the LangExtract adapter: it fills
the replaceable proposal slot. Nothing it returns is trusted; every proposal
still passes verify.keep_grounded(), checks.support() and the rule checks.

Design decisions
  * One call per document, cached by the document fingerprint.
  * Ollama's structured output: the answer must follow a JSON schema built
    from the element profile, so formatting failures are rare and visible.
  * Fixed settings for reproducibility: temperature 0, fixed seed, thinking
    off where the model supports it. The model digest is recorded.
  * The model's quote is passed on as evidence. If it is found in the
    document, it is widened to the full source line(s), so later checks see
    the label and unit. If it is NOT found, it is passed on unchanged, so the
    ordinary evidence check drops it and the diary records why.
  * Every raw answer is written to the diary and, optionally, to a JSONL
    file. ReplayResponses feeds a saved file back in, so a run can be
    repeated exactly without the model.
  * The worked example is the fictitious door D-200, never W-100.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional

import yaml

from .models import ElementDefinition, Evidence, Method, Proposal, SourceDocument

DEFAULT_HOST = "http://localhost:11434"
PRODUCT_FIELD = "product_id"


class OllamaError(RuntimeError):
    pass


# ----------------------------------------------------------------- helpers
def _span(text: str, quote: str) -> Optional[tuple[int, int]]:
    """Position of a quote in the original text, tolerant of whitespace and case."""
    words = quote.split()
    if not words:
        return None
    pattern = r"\s+".join(re.escape(w) for w in words)
    m = re.search(pattern, text, re.IGNORECASE)
    return (m.start(), m.end()) if m else None


def _lines_around(text: str, start: int, end: int) -> str:
    a = text.rfind("\n", 0, start) + 1
    b = text.find("\n", end)
    return text[a:b if b >= 0 else len(text)].strip()


def _blank_to_none(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


# ------------------------------------------------------- recording/replay
class ResponseRecorder:
    """Appends every raw model answer to a JSONL file, in call order."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, entry: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class ReplayResponses:
    """Serves saved answers back in the order they were recorded.

    Each answer must belong to the same document (same fingerprint) as the
    call it replaces; otherwise replay stops, because the run would no longer
    be the same run."""

    def __init__(self, path: str | Path):
        self.entries = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
        self.i = 0
        self.model = self.entries[0].get("model") if self.entries else None
        self.digest = self.entries[0].get("digest") if self.entries else None

    def __call__(self, payload: dict, doc_sha256: str) -> str:
        if self.i >= len(self.entries):
            raise OllamaError("replay file has fewer answers than the run needs")
        e = self.entries[self.i]
        self.i += 1
        if e["doc_sha256"] != doc_sha256:
            raise OllamaError(f"replay mismatch at answer {self.i}: recorded for another document")
        return e["raw"]


# ------------------------------------------------------------- extractor
class OllamaExtractor:
    def __init__(self, model: str, defs: dict, examples_path: str | Path,
                 host: str = DEFAULT_HOST, seed: int = 42, temperature: float = 0.0,
                 think: bool = False, num_ctx: int = 8192, timeout: int = 600, retries: int = 3,
                 recorder: Optional[ResponseRecorder] = None,
                 transport: Optional[Callable[[dict, str], str]] = None,
                 run_label: str = ""):
        self.model = model
        self.name = f"ollama:{model}"
        self.defs = {d.name: d for d in defs.values() if d.route == "extract"}
        self.examples_path = Path(examples_path)
        self.host = host.rstrip("/")
        self.options = {"temperature": temperature, "seed": seed, "num_ctx": num_ctx}
        self.think = think
        self.timeout = timeout
        self.retries = retries
        self.recorder = recorder
        self.transport = transport              # replaces the HTTP call (tests, replay)
        self.run_label = run_label
        self.raw_log: list[dict] = []
        self._cache: dict[str, dict] = {}
        self._digest: Optional[str] = getattr(transport, "digest", None)

    # ---- the request -------------------------------------------------
    def schema(self) -> dict:
        names = list(self.defs)
        return {
            "type": "object",
            "properties": {
                PRODUCT_FIELD: {"type": "string"},
                "extractions": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "element": {"type": "string", "enum": names},
                        "quote": {"type": "string"},
                        "value": {"type": "string"},
                        "unit": {"type": "string"},
                        "scope": {"type": "string"},
                    },
                    "required": ["element", "quote", "value", "unit", "scope"],
                }},
            },
            "required": [PRODUCT_FIELD, "extractions"],
        }

    def instruction(self) -> str:
        lines = [
            "Extract the following product information from the document.",
            "For every item, copy the exact sentence or phrase from the document into 'quote'.",
            "Use exact text from the document. Do not infer, calculate or use outside knowledge.",
            "If an item is not stated in the document, do not extract it.",
            "A value for a part (for example a glazing-only Ug value) is not a value for the whole product.",
            "Put the value only in 'value'. Put the unit and the reference size in 'unit' and 'scope' "
            "when the document states them, otherwise use an empty string.",
            f"Put the identifier of the product the document is about in '{PRODUCT_FIELD}', "
            "or an empty string if none is stated.",
            "Items:",
        ]
        lines += [f"- {n}: {d.description}" for n, d in self.defs.items()]
        return "\n".join(lines)

    def example(self) -> tuple[str, str]:
        cfg = yaml.safe_load(self.examples_path.read_text(encoding="utf-8"))
        pid, items = "", []
        for e in cfg["extractions"]:
            a = e.get("attributes") or {}
            if e["class"] == "document_product_id":
                pid = a.get("value", e["text"])
                continue
            items.append({"element": e["class"], "quote": e["text"], "value": a.get("value", e["text"]),
                          "unit": a.get("unit", ""), "scope": a.get("scope", "")})
        return cfg["text"], json.dumps({PRODUCT_FIELD: pid, "extractions": items}, ensure_ascii=False)

    def payload(self, doc: SourceDocument) -> dict:
        ex_text, ex_answer = self.example()
        user = ("Example document:\n" + ex_text + "\nExample answer:\n" + ex_answer +
                "\n\nNow extract from this document:\n" + doc.text)
        p = {"model": self.model, "stream": False, "format": self.schema(), "options": dict(self.options),
             "messages": [{"role": "system", "content": self.instruction()},
                          {"role": "user", "content": user}]}
        if self.think is not None:
            p["think"] = self.think
        return p

    # ---- the call ----------------------------------------------------
    def _post(self, path: str, body: Optional[dict] = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.host + path, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST" if body is not None else "GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def digest(self) -> Optional[str]:
        if self._digest is None and self.transport is None:
            try:
                tags = self._post("/api/tags")
                for m in tags.get("models", []):
                    if m.get("name") == self.model or m.get("model") == self.model:
                        self._digest = m.get("digest")
            except Exception:  # noqa: BLE001 - the digest is recorded when available
                self._digest = None
        return self._digest

    def _chat(self, payload: dict, doc_sha256: str) -> str:
        if self.transport is not None:
            return self.transport(payload, doc_sha256)
        last = None
        for attempt in range(self.retries + 1):
            try:
                out = self._post("/api/chat", payload)
                return out.get("message", {}).get("content", "")
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                if e.code == 400 and "think" in body and "think" in payload:
                    payload = {k: v for k, v in payload.items() if k != "think"}   # model has no thinking switch
                    continue
                if e.code == 404:
                    raise OllamaError(f"model {self.model!r} not found in Ollama; run: ollama pull {self.model}") from e
                last = OllamaError(f"Ollama HTTP {e.code}: {body[:300]}")
            except urllib.error.URLError as e:
                last = OllamaError(f"cannot reach Ollama at {self.host} ({e.reason}); is the Ollama app running?")
            if attempt < self.retries:
                time.sleep(5 * 3 ** attempt)
        raise last

    def _annotate(self, doc: SourceDocument) -> dict:
        if doc.sha256 in self._cache:
            return self._cache[doc.sha256]
        payload = self.payload(doc)
        t0 = time.time()
        raw = self._chat(payload, doc.sha256)
        seconds = round(time.time() - t0, 2)
        parse_error = None
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("answer is not a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            parsed, parse_error = {PRODUCT_FIELD: "", "extractions": []}, str(e)
        entry = {"source": doc.name, "doc_sha256": doc.sha256, "model": self.model, "digest": self.digest(),
                 "options": self.options, "think": self.think, "run": self.run_label,
                 "seconds": seconds, "raw": raw, "parse_error": parse_error}
        self.raw_log.append(entry)
        if self.recorder:
            self.recorder.write(entry)
        self._cache[doc.sha256] = parsed
        return parsed

    # ---- proposals ---------------------------------------------------
    def propose(self, d: ElementDefinition, doc: SourceDocument) -> list[Proposal]:
        if doc.kind != "document" or d.name not in self.defs:
            return []
        parsed = self._annotate(doc)
        pid = _blank_to_none(parsed.get(PRODUCT_FIELD))
        if pid and not _span(doc.text, pid):
            pid = None                                   # an identifier not in the document is not used
        proposals = []
        for e in parsed.get("extractions") or []:
            if not isinstance(e, dict) or e.get("element") != d.name:
                continue
            quote = _blank_to_none(e.get("quote")) or ""
            value = _blank_to_none(e.get("value")) or ""
            if not value:
                continue
            if d.value_type == "number":
                value = value.replace(",", ".")
            span = _span(doc.text, quote) if quote else None
            if span:
                quote = _lines_around(doc.text, *span)   # widen to the full source line(s)
            scope = _blank_to_none(e.get("scope"))
            context = None
            if scope:
                s = _span(doc.text, scope)
                context = _lines_around(doc.text, *s) if s else None
            proposals.append(Proposal(
                element_id=d.id, value=value, unit=_blank_to_none(e.get("unit")) or d.unit,
                scope=scope, product_id=pid, method=Method.AI, produced_by=self.name,
                evidence=Evidence(source=doc.name, quote=quote, context_quote=context)))
        return proposals
