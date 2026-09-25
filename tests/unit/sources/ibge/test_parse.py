"""Strict edition validation: malformed data must never become a successful load."""

import copy
import json
from pathlib import Path

import polars as pl
import pytest

from omnisus.sources.ibge.parse import pop_json_to_lazyframe

FIXTURES = Path(__file__).parent / "fixtures"


def payload(table=4714):
    return json.loads((FIXTURES / f"{table}-population.json").read_text(encoding="utf-8"))


def parse(body, year=2022, product="census"):
    return pop_json_to_lazyframe(
        body, year=year, product=product, expected_codes={"1100015", "1100023"}
    ).collect()


def test_empty_rejected():
    with pytest.raises(ValueError):
        pop_json_to_lazyframe([], year=2022)


@pytest.mark.parametrize(
    "table,year,product", [(202, 2010, "census"), (4714, 2022, "census"), (6579, 2026, "estimate")]
)
def test_official_products(table, year, product):
    frame = parse(payload(table), year, product)
    assert frame.height == 2
    assert frame["ano"].dtype == pl.UInt16
    assert frame["populacao"].sum() > 0


@pytest.mark.parametrize(
    "kind",
    [
        "variable",
        "unit",
        "level",
        "year",
        "code",
        "duplicate",
        "missing",
        "extra_result",
        "category",
        "symbol",
        "negative",
        "decimal",
        "overflow",
        "empty_series",
    ],
)
def test_rejects_invalid_source(kind):
    body = payload()
    result = body[0]["resultados"][0]
    series = result["series"]
    if kind == "variable":
        body[0]["id"] = "9324"
    if kind == "unit":
        body[0]["unidade"] = "%"
    if kind == "level":
        series[0]["localidade"]["nivel"]["id"] = "N3"
    if kind == "year":
        series[0]["serie"] = {"2021": "100"}
    if kind == "code":
        series[0]["localidade"]["id"] = "110001"
    if kind == "duplicate":
        series.append(copy.deepcopy(series[0]))
    if kind == "missing":
        series.pop()
    if kind == "extra_result":
        body[0]["resultados"].append(copy.deepcopy(result))
    if kind == "category":
        result["classificacoes"] = [{"id": "2", "categoria": {"4": "Homens"}}]
    if kind in ["symbol", "negative", "decimal", "overflow"]:
        series[0]["serie"]["2022"] = {
            "symbol": "...",
            "negative": "-1",
            "decimal": "1.5",
            "overflow": str(2**64),
        }[kind]
    if kind == "empty_series":
        result["series"] = []
    with pytest.raises(ValueError):
        parse(body)


def test_census_requires_total_categories():
    body = payload(202)
    body[0]["resultados"][0]["classificacoes"][0]["categoria"] = {"4": "Homens"}
    with pytest.raises(ValueError):
        parse(body, 2010)
