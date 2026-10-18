"""Post-hoc probe of the sash-only case (not part of the pre-registered evaluation)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("probe_sash", ROOT / "scripts/probe_sash.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_PR01_recorded_sash_proposal_is_stopped_only_by_identity():
    r = probe.run("PP-SA-100")
    assert r["quote_found"] is True
    assert r["failed_checks"] == ["identity"]
    assert r["state"] == "flagged"


def test_PR02_same_proposal_with_product_id_W100_passes_every_check():
    r = probe.run("W-100")
    assert r["quote_found"] is True
    assert r["failed_checks"] == []
    assert r["state"] == "checked"
