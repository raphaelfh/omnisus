"""Tests for the generic DATASUS-FTP runner."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp._runner import import_scope
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from tests.support import fake_datasus


@pytest.mark.asyncio
async def test_import_scope_sim_uses_fixture(monkeypatch, tmp_path, dbc_fixture) -> None:
    fixture_bytes = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {ScopeKey(uf="RR", ano=2023): fixture_bytes})

    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    result = await import_scope(
        dataset="sim_obitos",
        scope=ScopeKey(uf="RR", ano=2023),
        lake=lake,
    )
    assert result.rows > 0
    assert "sim_obitos" in lake.tables()
    lake.close()


@pytest.mark.asyncio
async def test_import_scope_sih_requires_mes(tmp_path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    with pytest.raises(ValueError, match="monthly"):
        await import_scope(
            dataset="sih_aih_reduzida",
            scope=ScopeKey(uf="SP", ano=2024, mes=None),
            lake=lake,
        )
    lake.close()


def test_resolve_returns_partition_by() -> None:
    from omnisus.sources.datasus_ftp.datasets import resolve

    cfg = resolve("sim_obitos")
    assert cfg.partition_by == ("ano", "uf")
    assert cfg.monthly is False

    sih = resolve("sih_aih_reduzida")
    assert sih.partition_by == ("ano", "uf", "mes")
    assert sih.monthly is True


def test_resolve_unknown_raises() -> None:
    import pytest as _pt

    from omnisus.sources.datasus_ftp.datasets import resolve

    with _pt.raises(ValueError):
        resolve("bogus")


def _custom_sim_yaml(tmp_path: Path) -> Path:
    from importlib.resources import files

    dest = tmp_path / "sim_custom.yaml"
    dest.write_text(
        (files("omnisus.data.dicionarios") / "sim_obitos.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return dest


@pytest.mark.asyncio
async def test_import_scope_accepts_an_adhoc_dataset_value(
    monkeypatch, tmp_path, dbc_fixture
) -> None:
    """A Dataset built by the caller, with its own YAML, ingests through the
    same path as a registered one — no second untyped mode."""
    from omnisus.sources.datasus_ftp.datasets import Dataset

    fixture_bytes = dbc_fixture("sim_rr_2023_mini").read_bytes()
    ds = Dataset(
        name="sim_custom",
        prefix="DO",
        ftp_dir="/dissemin/publicos/SIM/CID9/DORES",
        cadence="yearly",
        partition_by=("ano", "uf"),
        coverage=((1979, 1), (1995, 12)),
        dictionary=_custom_sim_yaml(tmp_path),
    )
    fetched = fake_datasus.serve(monkeypatch, ds, {ScopeKey(uf="RR", ano=2023): fixture_bytes})

    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake:
        result = await import_scope(dataset=ds, scope=ScopeKey(uf="RR", ano=2023), lake=lake)
        assert result.rows > 0
        assert "sim_custom" in lake.tables()
        (publication,) = lake.publications()
    assert fetched == ["/dissemin/publicos/SIM/CID9/DORES/DORR2023.dbc"]
    assert publication["source_uri"].endswith("/SIM/CID9/DORES/DORR2023.dbc")


@pytest.mark.asyncio
async def test_import_scope_adhoc_without_yaml_fails_fast(monkeypatch, tmp_path) -> None:
    """Uncurated is not schemaless: no YAML -> FileNotFoundError before any
    bytes are decoded, never a silent all-strings fallback."""
    from omnisus.sources.datasus_ftp.datasets import Dataset

    ds = Dataset(
        name="no_such_yaml",
        prefix="ZZ",
        ftp_dir="/x",
        cadence="yearly",
        partition_by=("ano", "uf"),
        coverage=((2000, 1), None),
    )

    fake_datasus.serve(monkeypatch, ds, {ScopeKey(uf="RR", ano=2023): b"never decoded"})

    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake, pytest.raises(FileNotFoundError):
        await import_scope(dataset=ds, scope=ScopeKey(uf="RR", ano=2023), lake=lake)


def test_run_scopes_publishes_a_prelim_listing_as_prelim(
    monkeypatch, tmp_path, dbc_fixture
) -> None:
    """The release is where the listing found the file, never a guess."""
    from omnisus.sources.datasus_ftp import _runner

    d = REGISTRY["sim_obitos"]
    scope = ScopeKey("RR", 2023)
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, d, {scope: raw}, release="prelim")
    with Lake.local(f"ducklake:{tmp_path}/l.ducklake") as lake:
        report = asyncio.run(_runner.run_scopes("sim_obitos", scopes=[scope], lake=lake))
        assert [o.status for o in report.outcomes] == ["ok"]
        (publication,) = [p for p in lake.publications() if p["active"]]
        stored = (
            lake.connect()
            .execute("SELECT DISTINCT _source_release FROM lake.sim_obitos")
            .fetchall()
        )
    assert publication["release"] == "prelim"
    assert publication["source_uri"].endswith(f"{d.prelim_dir}/DORR2023.dbc")
    assert stored == [("prelim",)]


@pytest.mark.asyncio
async def test_import_scope_refuses_a_scope_the_listing_lacks(monkeypatch, tmp_path) -> None:
    from omnisus.sources.datasus_ftp.fetch import FtpFileNotFound

    fetched = fake_datasus.serve(monkeypatch, "sim_obitos", {})
    with (
        Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake,
        pytest.raises(FtpFileNotFound, match="not in the server listing"),
    ):
        await import_scope(dataset="sim_obitos", scope=ScopeKey(uf="RR", ano=2023), lake=lake)
    assert fetched == []
