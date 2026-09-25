"""Official contracts with controlled HTTP responses; no live network in tests."""

import json
from pathlib import Path

import httpx
import pytest
import respx

from omnisus.sources.ibge.fetch import fetch_pop_by_year

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"


def setup_source(table=4714, year=2022):
    metadata = json.loads((FIXTURES / f"{table}-metadados.json").read_text(encoding="utf-8"))
    periods = json.loads((FIXTURES / f"{table}-periodos.json").read_text(encoding="utf-8"))
    body = json.loads((FIXTURES / f"{table}-population.json").read_text(encoding="utf-8"))
    localities = [s["localidade"] for s in body[0]["resultados"][0]["series"]]
    routes = {}
    for name, data in [
        ("metadados", metadata),
        ("periodos", periods),
        ("localidades/N6", localities),
    ]:
        routes[name] = respx.get(f"{BASE}/{table}/{name}").mock(
            return_value=httpx.Response(200, json=data)
        )
    variable = 9324 if table == 6579 else 93
    params = {"localidades": "N6"}
    if table == 202:
        params["classificacao"] = "2[0]|1[0]"
    routes["population"] = respx.get(
        f"{BASE}/{table}/periodos/{year}/variaveis/{variable}", params=params
    ).mock(return_value=httpx.Response(200, json=body))
    return routes


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    "table,year,product", [(202, 2010, "census"), (4714, 2022, "census"), (6579, 2026, "estimate")]
)
async def test_validated_fetch(table, year, product):
    setup_source(table, year)
    publication = await fetch_pop_by_year(year, product=product)
    assert publication.expected_codes == frozenset({"1100015", "1100023"})
    assert len(publication.sha256) == 64
    assert publication.revision
    assert publication.payload[0]["id"] == str(9324 if table == 6579 else 93)


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    "kind", ["metadata", "period", "universe", "duplicate_universe", "revision", "http"]
)
async def test_invalid_control_documents(kind):
    routes = setup_source()
    if kind == "metadata":
        routes["metadados"].respond(200, json={"id": 4714})
    if kind == "period":
        routes["periodos"].respond(200, json=[])
    if kind == "universe":
        routes["localidades/N6"].respond(200, json=[])
    if kind == "duplicate_universe":
        routes["localidades/N6"].respond(200, json=[{"id": "1100015", "nivel": {"id": "N6"}}] * 2)
    if kind == "revision":
        routes["periodos"].respond(200, json=[{"id": "2022"}])
    if kind == "http":
        routes["metadados"].respond(503)
    with pytest.raises((ValueError, httpx.HTTPStatusError)):
        await fetch_pop_by_year(2022, product="census")


@pytest.mark.asyncio
@respx.mock
async def test_estimate_unavailable_year_does_not_switch_to_census():
    setup_source(6579, 2022)
    with pytest.raises(ValueError, match=r"available|unavailable"):
        await fetch_pop_by_year(2022, product="estimate")


@pytest.mark.asyncio
@respx.mock
async def test_estimate_old_edition_requires_vetted_universe():
    setup_source(6579, 2024)
    with pytest.raises(ValueError, match="universe"):
        await fetch_pop_by_year(2024, product="estimate")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "year,product", [(2007, "census"), (2023, "estimate"), (2024, "bad"), (True, "estimate")]
)
async def test_unsupported_product_year(year, product):
    with pytest.raises(ValueError):
        await fetch_pop_by_year(year, product=product)


@pytest.mark.asyncio
@respx.mock
async def test_revision_change_during_collection_is_rejected():
    routes = setup_source()
    routes["periodos"].mock(
        side_effect=[
            httpx.Response(200, json=[{"id": "2022", "modificacao": "07/05/2026"}]),
            httpx.Response(200, json=[{"id": "2022", "modificacao": "08/05/2026"}]),
        ]
    )
    with pytest.raises(ValueError, match="revision changed"):
        await fetch_pop_by_year(2022, product="census")


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("kind", ["variable", "unit", "level", "categories", "total"])
async def test_metadata_contract_is_enforced(kind):
    routes = setup_source(202, 2010)
    metadata = json.loads((FIXTURES / "202-metadados.json").read_text(encoding="utf-8"))
    if kind == "variable":
        metadata["variaveis"][0]["id"] = 999
    if kind == "unit":
        metadata["variaveis"][0]["unidade"] = "%"
    if kind == "level":
        metadata["nivelTerritorial"]["Administrativo"] = ["N1"]
    if kind == "categories":
        metadata["classificacoes"] = []
    if kind == "total":
        metadata["classificacoes"][0]["categorias"][0]["nome"] = "Homens"
    routes["metadados"].respond(200, json=metadata)
    with pytest.raises(ValueError):
        await fetch_pop_by_year(2010, product="census")
