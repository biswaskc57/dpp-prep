"""Fact-checker part 2, and the rule checker (R05, R06). Ordinary code, not AI.

support()      the quote really supports the value: same value, right label,
               no wrong label (Ug is not Uw), unit stated
identity()     the source is about the right product
unit()         the value has the expected unit
scope()        the value applies to the required scope (e.g. reference size),
               and the evidence says so
value_type()   numbers are numbers
composition()  material shares add up to 100 %
conflict()     all candidate values agree; otherwise all are shown, none merged
"""
from __future__ import annotations

import re
from typing import Optional

from .models import CheckResult, ElementDefinition, Method, Proposal

_NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower().rstrip(".")


def _numbers(text: str) -> set[float]:
    return {float(n.replace(",", ".")) for n in _NUM.findall(text)}


def _as_number(value: str) -> Optional[float]:
    try:
        return float(value.strip().replace(",", "."))
    except ValueError:
        return None


def _term_present(term: str, text: str) -> bool:
    pattern = re.escape(term)
    if term[:1].isalnum():
        pattern = r"\b" + pattern
    if term[-1:].isalnum():
        pattern = pattern + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _result(name: str, ok: bool, msg: str, p: Optional[Proposal] = None) -> CheckResult:
    return CheckResult(name=name, passed=ok, message="" if ok else msg,
                       proposal_id=p.id if p else None)


def support(p: Proposal, d: ElementDefinition) -> CheckResult:
    """Does the quote support this value for this element?"""
    if p.method == Method.IMPORT:
        return _result("support", True, "", p)       # verified field-by-field in verify.py
    quote = p.evidence.quote or ""
    problems = []
    if not quote.strip():
        problems.append("no quote")
    if d.value_type == "number":
        v = _as_number(p.value)
        if v is None or v not in _numbers(quote):
            problems.append(f"value {p.value!r} does not appear in the quote")
    elif _norm(p.value) not in _norm(quote):
        problems.append(f"value {p.value!r} does not appear in the quote")
    for term in d.must_contain:
        if not _term_present(term, quote):
            problems.append(f"quote does not mention {term!r}")
    for term in d.must_not_contain:
        if _term_present(term, quote):
            problems.append(f"quote is about {term!r}, not this element")
    if d.unit and d.unit.replace(" ", "") not in quote.replace(" ", ""):
        problems.append(f"quote does not state the unit {d.unit!r}")
    return _result("support", not problems, "; ".join(problems), p)


def identity(p: Proposal, expected_product_id: str) -> CheckResult:
    return _result("identity", p.product_id == expected_product_id,
                   f"source refers to {p.product_id!r}, expected {expected_product_id!r}", p)


def unit(p: Proposal, d: ElementDefinition) -> CheckResult:
    ok = d.unit is None or (p.unit or "").replace(" ", "") == d.unit.replace(" ", "")
    return _result("unit", ok, f"unit {p.unit!r}, expected {d.unit!r}", p)


def scope(p: Proposal, d: ElementDefinition, expected_scope: str) -> CheckResult:
    if d.required_scope == "product":
        return _result("scope", True, "", p)
    if (p.scope or "") != expected_scope:
        return _result("scope", False, f"value applies to {p.scope!r}, required {expected_scope!r}", p)
    stated = " ".join(filter(None, [p.evidence.quote, p.evidence.context_quote]))
    return _result("scope", _norm(expected_scope) in _norm(stated),
                   "the evidence does not state the scope the value applies to", p)


def value_type(p: Proposal, d: ElementDefinition) -> CheckResult:
    ok = d.value_type != "number" or _as_number(p.value) is not None
    return _result("value_type", ok, f"{p.value!r} is not a number", p)


def composition_sum(p: Proposal, tolerance: float = 0.5) -> CheckResult:
    shares = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", p.value)]
    total = sum(shares)
    return _result("composition_sum", bool(shares) and abs(total - 100.0) <= tolerance,
                   f"shares add up to {total:g} %", p)


def _comparable(p: Proposal, d: ElementDefinition):
    if d.value_type == "number":
        return _as_number(p.value)
    return _norm(p.value)


def conflict(proposals: list[Proposal], d: ElementDefinition) -> CheckResult:
    values = {_comparable(p, d) for p in proposals}
    detail = "; ".join(f"{p.value} ({p.evidence.source})" for p in proposals)
    return _result("conflict", len(values) <= 1, f"sources disagree: {detail}")


def run_checks(d: ElementDefinition, proposals: list[Proposal],
               expected_product_id: str, expected_scope: str = "product") -> list[CheckResult]:
    """Run every applicable check. Support and value type are always checked."""
    results: list[CheckResult] = []
    for p in proposals:
        results.append(support(p, d))
        results.append(value_type(p, d))
        if "identity" in d.controls:
            results.append(identity(p, expected_product_id))
        if "unit" in d.controls:
            results.append(unit(p, d))
        if "scope" in d.controls:
            results.append(scope(p, d, expected_scope))
        if "composition_sum" in d.controls:
            results.append(composition_sum(p))
    if "conflict" in d.controls and len(proposals) > 1:
        results.append(conflict(proposals, d))
    return results


def all_passed(results: list[CheckResult]) -> bool:
    return bool(results) and all(r.passed for r in results if r.mandatory)
