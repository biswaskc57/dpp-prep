"""Load the wish list (information profile)."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import ElementDefinition


def load_profile(path: str | Path) -> tuple[dict, dict[str, ElementDefinition]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    product = dict(data["product"])
    product["profile_version"] = str(data.get("profile_version", "unversioned"))
    defs = {e["id"]: ElementDefinition(**e) for e in data["elements"]}
    return product, defs
