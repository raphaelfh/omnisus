"""Controlled official HTTP -> publication + atomic DuckLake provenance."""

import json
from pathlib import Path

import polars as pl
import pytest
import respx

from omnisus.lake import Lake
from omnisus.sources.ibge.importers.pop import import_pop_year

FIXTURES = Path(__file__).parents[1] / "unit/sources/ibge/fixtures"
BASE = "https://servicodados.ibge.gov.br/api/v3/agregados/4714"


def mock_source():
    body = json.loads((FIXTURES / "4714-population.json").read_text(encoding="utf-8"))
    for name in ("metadados", "periodos"):
        respx.get(f"{BASE}/{name}").respond(
            200, content=(FIXTURES / f"4714-{name}.json").read_bytes()
        )
    respx.get(f"{BASE}/localidades/N6").respond(
        200, json=[s["localidade"] for s in body[0]["resultados"][0]["series"]]
    )
    return respx.get(f"{BASE}/periodos/2022/variaveis/93", params={"localidades": "N6"}).respond(
        200, json=body
    )


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_import_ibge_pop_e2e(tmp_path):
    mock_source()
    lake = Lake.local(f"ducklake:{tmp_path}/test.ducklake")
    try:
        result = await import_pop_year(year=2022, product="census", lake=lake)
        assert result.rows == 2 and result.snapshot_id is not None
        con = lake.connect()
        assert (
            con.execute("SELECT sum(populacao) FROM lake.ibge_populacao").fetchone()[0] == 118327
        )
        records = con.execute(
            "SELECT p.publication_id, m.product, m.sha256, m.revision, m.expected_rows, m.accepted_rows, m.evidence_json FROM lake.ibge_population p JOIN lake.ibge_population_manifest m USING(publication_id)"
        ).fetchall()
        assert len(records) == 2 and records[0][1] == "census"
        assert result.publication_id == records[0][0]
        assert len(records[0][2]) == 64 and records[0][3] == "07/05/2026"
        assert records[0][4:6] == (2, 2)
        assert json.loads(records[0][6])["universe"]["codes"] == ["1100015", "1100023"]
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_manifest_failure_rolls_back_data_and_keeps_prior_publication(tmp_path, monkeypatch):
    mock_source()
    lake = Lake.local(f"ducklake:{tmp_path}/atomic.ducklake")
    try:
        await import_pop_year(year=2022, product="census", lake=lake)
        original = lake.ingest

        def fail(table, *args, **kwargs):
            if table == "ibge_population_manifest":
                raise RuntimeError("manifest fault")
            return original(table, *args, **kwargs)

        monkeypatch.setattr(lake, "ingest", fail)
        with pytest.raises(RuntimeError, match="manifest fault"):
            await import_pop_year(year=2022, product="census", lake=lake)
        assert (
            lake.connect().execute("SELECT count(*) FROM lake.ibge_population").fetchone()[0] == 2
        )
        assert (
            lake.connect()
            .execute("SELECT count(*) FROM lake.ibge_population_manifest")
            .fetchone()[0]
            == 1
        )
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_legacy_table_is_preserved_and_requires_migration(tmp_path):
    mock_source()
    lake = Lake.local(f"ducklake:{tmp_path}/legacy.ducklake")
    try:
        lake.ingest("ibge_populacao", pl.DataFrame({"sentinel": [42]}).lazy())
        with pytest.raises(ValueError, match=r"legacy|migration"):
            await import_pop_year(year=2022, product="census", lake=lake)
        assert (
            lake.connect().execute("SELECT sentinel FROM lake.ibge_populacao").fetchone()[0] == 42
        )
        assert "ibge_population" not in lake.tables()
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_append_preserves_publications_and_compatibility_view_refuses_ambiguity(tmp_path):
    mock_source()
    lake = Lake.local(f"ducklake:{tmp_path}/append.ducklake")
    try:
        for _ in range(2):
            await import_pop_year(year=2022, product="census", lake=lake)
        assert (
            lake.connect()
            .execute("SELECT count(DISTINCT publication_id) FROM lake.ibge_population")
            .fetchone()[0]
            == 2
        )
        with pytest.raises(Exception, match="ambiguous"):
            lake.connect().execute("SELECT populacao FROM lake.ibge_populacao").fetchall()
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_empty_http_payload_never_writes(tmp_path):
    route = mock_source()
    route.respond(200, json=[])
    lake = Lake.local(f"ducklake:{tmp_path}/empty.ducklake")
    try:
        with pytest.raises(ValueError):
            await import_pop_year(year=2022, product="census", lake=lake)
        assert not lake.tables()
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
async def test_cancellation_during_manifest_rolls_back(tmp_path, monkeypatch):
    import asyncio

    mock_source()
    lake = Lake.local(f"ducklake:{tmp_path}/cancel.ducklake")
    original = lake.ingest

    def cancel(table, *args, **kwargs):
        if table == "ibge_population_manifest":
            raise asyncio.CancelledError()
        return original(table, *args, **kwargs)

    monkeypatch.setattr(lake, "ingest", cancel)
    try:
        with pytest.raises(asyncio.CancelledError):
            await import_pop_year(year=2022, product="census", lake=lake)
        assert lake.tables() == []
    finally:
        lake.close()


@pytest.mark.integration
@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    "table,year,product,reference,revision",
    [
        (202, 2010, "census", "2010-08-01", "01/02/2019"),
        (4714, 2022, "census", "2022-08-01", "07/05/2026"),
        (6579, 2026, "estimate", "2026-07-01", "28/08/2026"),
    ],
)
async def test_manifest_separates_population_reference_from_revision_and_unknown_dates(
    tmp_path, table, year, product, reference, revision
):
    from tests.unit.sources.ibge.test_fetch import setup_source

    setup_source(table, year)
    lake = Lake.local(f"ducklake:{tmp_path}/dates.ducklake")
    try:
        await import_pop_year(year=year, product=product, lake=lake)
        row = (
            lake.connect()
            .execute(
                "SELECT population_reference_date::VARCHAR, "
                "population_reference_source_url, population_reference_note, "
                "territorial_reference_date, publication_date, temporal_metadata_note, "
                "source_revision, collected_at, period "
                "FROM lake.ibge_population_manifest"
            )
            .fetchone()
        )
        assert row[0] == reference
        assert "ibge.gov.br/" in row[1] and row[1].startswith("https://")
        assert ("noite" in row[2]) if product == "census" else ("julho" in row[2])
        assert row[3:5] == (None, None)
        assert "unknown" in row[5]
        assert row[6] == revision and row[8] == str(year)
        assert row[7] != row[0] and row[7] != row[6]
        types = dict(
            lake.connect()
            .execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_catalog = 'lake' AND table_name = 'ibge_population_manifest'"
            )
            .fetchall()
        )
        for field in [
            "population_reference_date",
            "territorial_reference_date",
            "publication_date",
        ]:
            assert types[field] == "DATE"
    finally:
        lake.close()
