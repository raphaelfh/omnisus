"""`describe_datasets()`: the registry and the packaged dictionaries as one table.

Every expected value is read from the registry rows (`datasus_ftp/datasets.py`) and
the packaged dictionaries, the same artifacts the importers use (AGENTS.md rule 2).
"""

from __future__ import annotations

import polars as pl
import pytest

import omnisus as sus
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.transforms.dictionaries import load_dicionario

COLUMNS = [
    "name",
    "category",
    "title",
    "geography",
    "cadence",
    "coverage_start",
    "coverage_end",
    "prefix",
    "ftp_dir",
    "prelim_dir",
    "fields",
    "labelled_fields",
    "validated_scopes",
]


@pytest.fixture(scope="module")
def table() -> pl.DataFrame:
    return sus.describe_datasets()


def _row(table: pl.DataFrame, name: str) -> dict:
    return table.filter(pl.col("name") == name).to_dicts()[0]


def test_one_row_per_registry_dataset_sorted_by_name(table: pl.DataFrame) -> None:
    assert table.columns == COLUMNS
    assert table["name"].to_list() == sorted(REGISTRY)


def test_monthly_coverage_keeps_the_month_and_an_open_end(table: pl.DataFrame) -> None:
    atd = _row(table, "sia_apac_tratamento_dialitico")
    assert (atd["category"], atd["coverage_start"], atd["coverage_end"]) == (
        "SIA",
        "2014-08",
        None,
    )
    ee = _row(table, "cnes_estabelecimentos_ensino")
    assert (ee["coverage_start"], ee["coverage_end"]) == ("2007-03", "2021-07")


def test_yearly_coverage_is_the_year(table: pl.DataFrame) -> None:
    cid9 = _row(table, "sim_obitos_cid9")
    assert (cid9["cadence"], cid9["coverage_start"], cid9["coverage_end"]) == (
        "yearly",
        "1979",
        "1995",
    )


def test_location_comes_from_the_registry(table: pl.DataFrame) -> None:
    for name in ("sim_obitos", "sinan_chagas", "sih_aih_reduzida"):
        row, d = _row(table, name), REGISTRY[name]
        assert (row["geography"], row["cadence"], row["prefix"]) == (
            d.geography,
            d.cadence,
            d.prefix,
        )
        assert (row["ftp_dir"], row["prelim_dir"]) == (d.ftp_dir, d.prelim_dir)
    assert _row(table, "sih_aih_reduzida")["prelim_dir"] is None


def test_fields_and_labelled_fields_count_the_dictionary(table: pl.DataFrame) -> None:
    dictionary = load_dicionario("sim_obitos")
    row = _row(table, "sim_obitos")
    assert row["title"] == dictionary.title
    assert row["fields"] == len(dictionary.fields)
    assert row["labelled_fields"] == sum(1 for f in dictionary.fields if f.get("x-decode"))


def test_validated_scopes_list_the_validated_sources(table: pl.DataFrame) -> None:
    """A list of scopes, never a yes/no: the categories exist only there (ADR 0003)."""
    sources = load_dicionario("sim_obitos").raw["x-analytics"]["validated_sources"]
    expected = [str(ScopeKey(s.get("uf"), s["ano"], s.get("mes"))) for s in sources]
    assert _row(table, "sim_obitos")["validated_scopes"] == expected
    assert "SP_2024" in expected
    assert _row(table, "sia_apac_nefrologia")["validated_scopes"] == []


def test_category_is_what_describe_dataset_reports(table: pl.DataFrame) -> None:
    for name, category in table.select("name", "category").iter_rows():
        fields = sus.describe_dataset(name)["fields"]
        assert {f["dataset"]["category"] for f in fields} == {category}, name
    assert set(table["category"]) == {"CNES", "SIA", "SIH", "SIM", "SINAN", "SINASC"}
