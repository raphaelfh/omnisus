"""`sus.read`: a lake table or view as a polars DataFrame, without SQL.

Real data: the packaged vocabularies of `auxiliares-bootstrap.zip` (each file hashed in
the source registry) and `sim_rr_2023_mini.dbc`, DORR2023.dbc (3 311 rows), served by
the fake DATASUS listing in `tests/support/fake_datasus.py`.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import omnisus as sus
from omnisus.sources._base import ScopeKey
from tests.support import fake_datasus


@pytest.fixture
def target(tmp_path: Path) -> str:
    target = f"ducklake:{tmp_path}/lake.ducklake"
    with sus.Lake.local(target) as lake:
        lake.bootstrap_auxiliares()
    return target


def test_read_returns_a_vocabulary_as_polars(target: str) -> None:
    cid10 = sus.read("aux_cid10", target=target)

    with sus.LakeReader(target) as lake:
        expected = lake.connect().sql("FROM lake.aux_cid10").pl()
    assert isinstance(cid10, pl.DataFrame)
    assert cid10.sort("codigo").equals(expected.sort("codigo"))


def test_read_returns_the_rows_load_imported(target: str, monkeypatch, dbc_fixture) -> None:
    payload = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {ScopeKey(uf="RR", ano=2023): payload})
    sus.load("sim_obitos", years=[2023], ufs=["RR"], target=target)

    obitos = sus.read("sim_obitos", target=target)

    assert obitos.height == 3311
    assert set(obitos["uf"]) == {"RR"}


def test_read_returns_a_view(target: str) -> None:
    """`ibge_populacao` is a view; DuckDB's `.table()` does not resolve DuckLake views."""
    with sus.Lake.local(target) as lake:
        lake.connect().execute(
            "CREATE VIEW lake.uf_norte AS FROM lake.aux_uf WHERE codigo_ibge < '20'"
        )

    assert sorted(sus.read("uf_norte", target=target)["sigla"]) == [
        "AC", "AM", "AP", "PA", "RO", "RR", "TO",
    ]  # fmt: skip


def test_read_names_what_to_run_for_a_missing_table(target: str) -> None:
    with pytest.raises(LookupError, match=r"ibge_populacao.*import_ibge_populacao"):
        sus.read("ibge_populacao", target=target)
