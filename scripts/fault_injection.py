"""Fault-injection check: does the test suite notice when a safeguard is removed?

For each safeguard, this script copies the project to a temporary folder,
disables that one safeguard in the copy, runs the tests there, and reports
whether at least one test failed. The real project is never modified.

Run from the project root:  python scripts/fault_injection.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAULTS = [
    ("value must appear in its quote",
     "src/dpp_prep/checks.py",
     "if v is None or v not in _numbers(quote):", "if v is None:"),
    ("quote must not be about a different attribute (Ug is not Uw)",
     "src/dpp_prep/checks.py",
     "for term in d.must_not_contain:", "for term in []:"),
    ("quote must be found in the source",
     "src/dpp_prep/verify.py",
     'return False, "quote not found in source"', "pass"),
    ("approval requires passed checks on the current version",
     "src/dpp_prep/states.py",
     "    elif not all_passed(r.checks):", "    elif False:"),
    ("approval requires a recorded reviewer decision",
     "src/dpp_prep/states.py",
     '        problems.append("no reviewer decision recorded")', "        pass"),
    ("the same person may not review and approve",
     "src/dpp_prep/states.py",
     "elif actor_id == r.review.reviewer_id:", "elif False:"),
    ("approval is bound to the exact version",
     "src/dpp_prep/states.py",
     "elif r.approval.record_version != r.version:", "elif False:"),
    ("only the approver role may approve",
     "src/dpp_prep/states.py",
     "(S.REVIEWED, S.APPROVED): {R.APPROVER},", "(S.REVIEWED, S.APPROVED): {R.APPROVER, R.AI},"),
    ("reviewer must confirm inspecting the evidence",
     "src/dpp_prep/service.py",
     "        if not evidence_inspected:", "        if False:"),
    ("unsupported proposals are kept, not deleted",
     "src/dpp_prep/service.py",
     "                r.rejected.append(p)\n                r.note(", "                r.note("),
    ("AI output not anchored in the document is discarded",
     "src/dpp_prep/extract.py",
     "if e.extraction_class != d.name or not self._grounded(e):", "if e.extraction_class != d.name:"),
    ("an empty AI extraction does not count as anchored",
     "src/dpp_prep/extract.py",
     'and ci.end_pos > ci.start_pos and bool((e.extraction_text or "").strip()))', ")"),
]


def run_one(name: str, rel: str, old: str, new: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "proj"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.sqlite", "out"))
        target = copy / rel
        text = target.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"fault {name!r}: pattern not found in {rel}; update this script")
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x"], cwd=copy,
                                capture_output=True, text=True)
        return result.returncode != 0


def main() -> int:
    print(f"{'Safeguard removed':<62} Detected")
    print("-" * 72)
    missed = 0
    for fault in FAULTS:
        detected = run_one(*fault)
        missed += not detected
        print(f"{fault[0]:<62} {'yes' if detected else 'NO'}")
    print("-" * 72)
    print(f"{len(FAULTS) - missed} of {len(FAULTS)} removed safeguards detected by the test suite")
    return 1 if missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
