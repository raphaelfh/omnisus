"""Tests for datasus_ftp.parse — DBC → Polars."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from omnisus.sources.datasus_ftp.dbc import InvalidDbcError
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe


def test_parse_sim_fixture_returns_lazyframe(dbc_fixture) -> None:
    dbc_path: Path = dbc_fixture("sim_rr_2023_mini")
    lf = dbc_bytes_to_lazyframe(dbc_path.read_bytes(), dataset="sim_obitos")
    assert isinstance(lf, pl.LazyFrame)
    df = lf.collect()
    assert df.height > 0
    # SIM should have at least the canonical columns (lower-cased).
    # NOTE: the raw DATASUS DO* DBC does not contain `numerodo` (that key is
    # synthesized downstream); use a column that is actually present.
    assert any(c.lower() == "dtobito" for c in df.columns)
    assert all(c == c.lower() for c in df.columns)


def test_parse_sim_applies_canonical_partition_cols(dbc_fixture) -> None:
    dbc_path: Path = dbc_fixture("sim_rr_2023_mini")
    lf = dbc_bytes_to_lazyframe(
        dbc_path.read_bytes(),
        dataset="sim_obitos",
        ano=2023,
        uf="RR",
    )
    df = lf.collect()
    assert df["ano"].dtype == pl.UInt16
    assert df["ano"].unique().to_list() == [2023]
    assert df["uf"].unique().to_list() == ["RR"]


def test_parse_unknown_dataset_raises() -> None:
    with pytest.raises(FileNotFoundError):
        dbc_bytes_to_lazyframe(b"x", dataset="bogus")


def test_parse_empty_bytes_raises_invalid_dbc() -> None:
    with pytest.raises(InvalidDbcError, match="missing DBC header"):
        dbc_bytes_to_lazyframe(b"", dataset="sim_obitos")


def test_parse_with_explicit_dictionary_path(dbc_fixture, tmp_path: Path) -> None:
    """The dictionary argument bypasses the packaged lookup entirely, so the
    dataset name need not be registered."""
    from importlib.resources import files

    custom = tmp_path / "mine.yaml"
    custom.write_text(
        (files("omnisus.data.dicionarios") / "sim_obitos.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    lf = dbc_bytes_to_lazyframe(raw, dataset="not_in_registry", dictionary=custom)
    assert lf.collect().height > 0
