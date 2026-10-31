"""Public research helpers: citation, skip_same import, municipality join key."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pytest

import omnisus as sus
from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from tests.support import fake_datasus


def _serve_sim_rr_2023(monkeypatch, payload: bytes) -> None:
    fake_datasus.serve(monkeypatch, "sim_obitos", {ScopeKey(uf="RR", ano=2023): payload})


def test_research_helpers_are_exported() -> None:
    for name in (
        "Citation",
        "citation_from_publications",
        "cite",
        "import_research",
        "latest_snapshot_id",
        "municipality_join_key",
        "municipality_join_key_sql",
    ):
        assert name in sus.__all__
        assert hasattr(sus, name)


def test_import_research_requires_run_id_and_refuses_append(
    monkeypatch, tmp_path: Path, dbc_fixture
) -> None:
    _serve_sim_rr_2023(monkeypatch, dbc_fixture("sim_rr_2023_mini").read_bytes())
    target = f"ducklake:{tmp_path}/research.ducklake"
    scopes = [ScopeKey(uf="RR", ano=2023)]

    with pytest.raises(TypeError):
        sus.import_research("sim_obitos", scopes=scopes, target=target)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="append"):
        sus.import_research(
            "sim_obitos",
            scopes=scopes,
            target=target,
            run_id="r1",
            policy="append",
        )

    with pytest.raises(ValueError, match="run_id"):
        sus.import_research("sim_obitos", scopes=scopes, target=target, run_id="  ")


def test_import_research_skip_same_does_not_duplicate(
    monkeypatch, tmp_path: Path, dbc_fixture
) -> None:
    _serve_sim_rr_2023(monkeypatch, dbc_fixture("sim_rr_2023_mini").read_bytes())
    target = f"ducklake:{tmp_path}/research.ducklake"
    scopes = [ScopeKey(uf="RR", ano=2023)]

    first = sus.import_research("sim_obitos", scopes=scopes, target=target, run_id="r1")
    second = sus.import_research("sim_obitos", scopes=scopes, target=target, run_id="r2")

    assert first.rows > 0
    assert second.rows == 0
    assert second.skipped
    with Lake.local(target) as lake:
        (n,) = lake.connect().execute("SELECT count(*) FROM lake.sim_obitos").fetchone()
    assert n == first.rows


def test_latest_snapshot_id_and_cite_name_the_file(
    monkeypatch, tmp_path: Path, dbc_fixture
) -> None:
    _serve_sim_rr_2023(monkeypatch, dbc_fixture("sim_rr_2023_mini").read_bytes())
    target = f"ducklake:{tmp_path}/cite.ducklake"
    sus.import_research(
        "sim_obitos",
        scopes=[ScopeKey(uf="RR", ano=2023)],
        target=target,
        run_id="sim-rr-2023-01",
    )

    with sus.LakeReader(target) as leitor:
        snapshot_id = sus.latest_snapshot_id(leitor)
        citacao = sus.cite(
            leitor,
            dataset="sim_obitos",
            snapshot_id=snapshot_id,
            run_id="sim-rr-2023-01",
            accessed=date(2026, 9, 18),
        )

    assert snapshot_id == citacao.snapshot_id
    assert citacao.dataset == "sim_obitos"
    assert citacao.run_id == "sim-rr-2023-01"
    assert citacao.omnisus == sus.__version__
    assert len(citacao.publications) == 1
    pub = citacao.publications[0]
    assert pub["source_sha256"]
    assert "sim_obitos" in citacao.text
    assert pub["source_sha256"] in citacao.text
    assert "sim-rr-2023-01" in citacao.text
    assert str(snapshot_id) in citacao.text
    assert "2026-09-18" in citacao.text
    assert sus.__version__ in citacao.text


def test_cite_without_snapshot_pins_the_latest(monkeypatch, tmp_path: Path, dbc_fixture) -> None:
    _serve_sim_rr_2023(monkeypatch, dbc_fixture("sim_rr_2023_mini").read_bytes())
    target = f"ducklake:{tmp_path}/pin.ducklake"
    sus.import_research(
        "sim_obitos",
        scopes=[ScopeKey(uf="RR", ano=2023)],
        target=target,
        run_id="r1",
    )
    with sus.LakeReader(target) as leitor:
        expected = sus.latest_snapshot_id(leitor)
        citacao = sus.cite(leitor, dataset="sim_obitos")
    assert citacao.snapshot_id == expected


def _freeze_publication_clock(monkeypatch, stamp: str) -> None:
    """Make the lake record ``published_at`` as ``stamp`` (UTC)."""
    frozen = datetime.fromisoformat(stamp)

    class _Clock(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return frozen

    monkeypatch.setattr("omnisus.lake.publication.datetime", _Clock)


def test_cite_of_an_old_snapshot_keeps_its_date_and_run_after_a_replace(
    monkeypatch, tmp_path: Path, dbc_fixture
) -> None:
    """A citation of snapshot N reads the publications as they were at N: a later
    ``replace`` changes neither the access date nor the run it prints."""
    _serve_sim_rr_2023(monkeypatch, dbc_fixture("sim_rr_2023_mini").read_bytes())
    target = f"ducklake:{tmp_path}/replace.ducklake"
    scopes = [ScopeKey(uf="RR", ano=2023)]

    _freeze_publication_clock(monkeypatch, "2026-10-18T12:00:00+00:00")
    sus.import_research("sim_obitos", scopes=scopes, target=target, run_id="r1")
    with sus.LakeReader(target) as leitor:
        antigo = sus.latest_snapshot_id(leitor)

    _freeze_publication_clock(monkeypatch, "2026-10-25T12:00:00+00:00")
    sus.import_research("sim_obitos", scopes=scopes, target=target, run_id="r2", policy="replace")

    with sus.LakeReader(target) as leitor:
        velha = sus.cite(leitor, dataset="sim_obitos", snapshot_id=antigo)
        nova = sus.cite(leitor, dataset="sim_obitos")

    assert "acessado em 2026-10-18 " in velha.text
    assert "execução r1." in velha.text
    assert "acessado em 2026-10-25 " in nova.text
    assert "execução r2." in nova.text


def test_latest_snapshot_id_without_history() -> None:
    class _Vazio:
        def snapshots(self):
            return []

    with pytest.raises(LookupError, match="snapshot"):
        sus.latest_snapshot_id(_Vazio())  # type: ignore[arg-type]


def test_cite_ibge_uses_population_manifest(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/ibge.ducklake"
    with Lake.local(target) as lake:
        lake.ingest(
            "ibge_population_manifest",
            __import__("polars")
            .DataFrame(
                {
                    "publication_id": ["pub-1"],
                    "product": ["census"],
                    "ano": [2022],
                    "sha256": ["abc123"],
                    "url": ["https://example.test/sidra"],
                    "collected_at": ["2026-01-01T00:00:00+00:00"],
                }
            )
            .lazy(),
        )
        snapshot_id = sus.latest_snapshot_id(lake)
        citacao = sus.cite(
            lake,
            dataset="ibge_populacao",
            snapshot_id=snapshot_id,
            accessed=date(2026, 9, 18),
        )
    assert citacao.publications[0]["sha256"] == "abc123"
    assert "abc123" in citacao.text
    assert "https://example.test/sidra" in citacao.text
    assert "pub-1" in citacao.text


def test_the_citation_names_every_part_of_a_split_month() -> None:
    row = {
        "dataset": "sia_bpa_individualizado",
        "source_uri": "ftp://ftp.datasus.gov.br/d/BIMG2412_1.dbc",
        "source_sha256": "0" * 64,
        "run_id": "r1",
        "sources": [
            {
                "ordinal": 0,
                "source_uri": "ftp://ftp.datasus.gov.br/d/BIMG2412_1.dbc",
                "source_sha256": "1" * 64,
                "source_bytes": 1,
                "source_modified": None,
            },
            {
                "ordinal": 1,
                "source_uri": "ftp://ftp.datasus.gov.br/d/BIMG2412_2.dbc",
                "source_sha256": "2" * 64,
                "source_bytes": 1,
                "source_modified": None,
            },
        ],
    }
    text = sus.citation_from_publications([row], snapshot_id=3).text
    assert "BIMG2412_1.dbc" in text and "BIMG2412_2.dbc" in text
    assert "1" * 64 in text and "2" * 64 in text


def test_the_access_date_is_the_import_date_of_each_publication() -> None:
    """Without ``accessed``, a file imported on 2026-10-18 is cited as accessed that day,
    not on the day the citation is printed."""
    row = {
        "dataset": "sim_obitos",
        "source_uri": "ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DORR2023.dbc",
        "source_sha256": "15b5203507161b7c35f9c69a52c955bdac133629549099b85a88e03a9a45baf0",
        "run_id": "r1",
        "published_at": "2026-10-18T23:40:00+00:00",
    }
    assert "acessado em 2026-10-18 " in sus.citation_from_publications([row], snapshot_id=3).text
    explicit = sus.citation_from_publications([row], snapshot_id=3, accessed=date(2026, 9, 1))
    assert "acessado em 2026-09-01 " in explicit.text


def test_the_ibge_access_date_is_its_collection_date() -> None:
    row = {
        "publication_id": "pub-1",
        "sha256": "abc123",
        "url": "https://example.test/sidra",
        "collected_at": "2026-01-01T00:00:00+00:00",
    }
    text = sus.citation_from_publications([row], snapshot_id=3, dataset="ibge_populacao").text
    assert "acessado em 2026-01-01." in text


def test_municipality_join_key_takes_the_left_digits() -> None:
    assert sus.municipality_join_key("1400100") == "140010"
    assert sus.municipality_join_key("140010", digits=6) == "140010"
    assert sus.municipality_join_key(1400100) == "140010"
    assert sus.municipality_join_key(" 1400100 ", digits=7) == "1400100"
    assert sus.municipality_join_key(None) is None
    assert sus.municipality_join_key("  ") is None
    with pytest.raises(ValueError, match="digits"):
        sus.municipality_join_key("1400100", digits=5)


def test_municipality_join_key_sql_matches_the_guide() -> None:
    sql = sus.municipality_join_key_sql("codmunres")
    assert sql == 'left(trim(CAST("codmunres" AS VARCHAR)), 6)'
    ibge = sus.municipality_join_key_sql("codigo_ibge", digits=6)
    con = duckdb.connect()
    assert con.execute(f"SELECT {sql} FROM (SELECT '1400100' AS codmunres)").fetchone() == (
        "140010",
    )
    assert con.execute(f"SELECT {ibge} FROM (SELECT '1400100' AS codigo_ibge)").fetchone() == (
        "140010",
    )
    with pytest.raises(ValueError):
        sus.municipality_join_key_sql("codmunres", digits=8)


def test_a_row_without_an_import_date_has_an_unknown_access_date() -> None:
    """No ``published_at`` nor ``collected_at``: the citation says the date is unknown
    instead of printing today."""
    row = {
        "dataset": "sim_obitos",
        "source_uri": "ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DORR2023.dbc",
        "source_sha256": "15b5203507161b7c35f9c69a52c955bdac133629549099b85a88e03a9a45baf0",
        "run_id": "r1",
    }
    text = sus.citation_from_publications([row], snapshot_id=3).text
    assert "acessado em (data de acesso desconhecida) pelo DATASUS." in text


@pytest.mark.parametrize("stamp", ["None", "18/10/2026", "ontem"])
def test_an_import_date_that_is_not_iso_raises_a_clear_error(stamp: str) -> None:
    row = {"dataset": "sim_obitos", "source_uri": "x/DORR2023.dbc", "published_at": stamp}
    with pytest.raises(ValueError, match=r"published_at.*ISO"):
        sus.citation_from_publications([row], snapshot_id=3)


@pytest.mark.parametrize("stamp", [datetime(2026, 10, 18, 23, 40, tzinfo=UTC), date(2026, 10, 18)])
def test_an_import_date_may_be_a_datetime_or_a_date(stamp: date) -> None:
    row = {"dataset": "sim_obitos", "source_uri": "x/DORR2023.dbc", "published_at": stamp}
    assert "acessado em 2026-10-18 " in sus.citation_from_publications([row], snapshot_id=3).text


@pytest.mark.parametrize(
    "stamp",
    [
        "2026-10-18T22:30:00-03:00",
        datetime(2026, 10, 18, 22, 30, tzinfo=timezone(timedelta(hours=-3))),
    ],
)
def test_an_import_date_with_an_offset_prints_its_utc_day(stamp: object) -> None:
    """22:30 at -03:00 is already 2026-10-19 in UTC, the day the docs promise."""
    row = {"dataset": "sim_obitos", "source_uri": "x/DORR2023.dbc", "published_at": stamp}
    assert "acessado em 2026-10-19 " in sus.citation_from_publications([row], snapshot_id=3).text


def test_cite_ibge_reads_the_manifest_at_the_snapshot(tmp_path: Path) -> None:
    """A second manifest row written after snapshot N stays out of ``cite(snapshot_id=N)``."""
    pl = __import__("polars")
    target = f"ducklake:{tmp_path}/ibge-pin.ducklake"

    def _manifest(publication_id: str, sha256: str, collected_at: str):
        return pl.DataFrame(
            {
                "publication_id": [publication_id],
                "product": ["census"],
                "ano": [2022],
                "sha256": [sha256],
                "url": ["https://example.test/sidra"],
                "collected_at": [collected_at],
            }
        ).lazy()

    with Lake.local(target) as lake:
        lake.ingest(
            "ibge_population_manifest", _manifest("pub-1", "a" * 64, "2026-01-01T00:00:00+00:00")
        )
        antigo = sus.latest_snapshot_id(lake)
        lake.ingest(
            "ibge_population_manifest", _manifest("pub-2", "b" * 64, "2026-02-01T00:00:00+00:00")
        )
        velha = sus.cite(lake, dataset="ibge_populacao", snapshot_id=antigo)

    assert "a" * 64 in velha.text and "acessado em 2026-01-01." in velha.text
    assert "b" * 64 not in velha.text and "2026-02-01" not in velha.text
