"""An independent reading of the same server agrees with our directories."""

from __future__ import annotations

import json
from pathlib import Path

from omnisus.sources.datasus_ftp.datasets import REGISTRY

CROSSCHECK = Path(__file__).resolve().parents[3] / "support" / "microdatasus_registry.json"


def test_overlapping_rows_read_the_same_directories() -> None:
    rows = json.loads(CROSSCHECK.read_text(encoding="utf-8"))["rows"]
    assert rows, "cross-check file lists no rows"
    for name, directories in rows.items():
        assert set(REGISTRY[name].directories().values()) == set(directories), name
