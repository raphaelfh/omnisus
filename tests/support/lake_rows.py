"""Rows of a committed DATASUS fixture, read back through `odb.load` like a researcher does."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import omnisus as odb
from omnisus.sources._base import ScopeKey
from tests.support import fake_datasus

DBC = Path(__file__).resolve().parents[1] / "fixtures" / "dbc"


def load_fixture(dataset: str, fixture: str, scope: ScopeKey, lake_dir: Path) -> pl.DataFrame:
    """Serve ``fixture`` as ``scope`` of ``dataset`` and return ``odb.load``'s DataFrame."""
    payload = (DBC / f"{fixture}.dbc").read_bytes()
    with pytest.MonkeyPatch.context() as patch:
        fake_datasus.serve(patch, dataset, {scope: payload})
        return odb.load(
            dataset,
            years=[scope.ano],
            ufs=None if scope.uf is None else [scope.uf],
            months=None if scope.mes is None else [scope.mes],
            target=f"ducklake:{lake_dir}/lake.ducklake",
        )
