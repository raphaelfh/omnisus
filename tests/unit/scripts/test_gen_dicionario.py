"""The dictionary generator reads the DBF header, not a hand-copied layout.

A wrong DBF type mapping would publish a dictionary that disagrees with the
file it describes, so the mapping is asserted against bytes this test wrote
itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.dbf import make_dbf


def _load(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import scripts/gen_dicionario.py with decompression stubbed to identity."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "gen_dicionario.py"
    spec = importlib.util.spec_from_file_location("gen_dicionario", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "gen_dicionario", module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.dbc, "decompress_bytes", lambda raw: raw)
    return module


def test_fields_of_maps_every_dbf_type_the_generator_claims_to_know(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load(monkeypatch)
    dbf = make_dbf(
        [("NU_ANO", "C", 4, 0), ("QT", "N", 5, 0), ("VL", "N", 6, 2), ("DT", "D", 8, 0)],
        [b" 2026" + b"    1" + b"  1.50" + b"20260101"],
    )

    assert module.fields_of(module.dbc.decompress_bytes(dbf)) == [
        {"name": "nu_ano", "type": "string"},
        {"name": "qt", "type": "integer"},
        {"name": "vl", "type": "number"},
        {"name": "dt", "type": "date"},
    ]
