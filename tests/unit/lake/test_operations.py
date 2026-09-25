"""Tests for the Lake class."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from omnisus.lake import Lake


def test_lake_local_creates_catalog_and_storage(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/omnisus.ducklake"
    lake = Lake.local(target)

    catalog_file = tmp_path / "omnisus-catalog.sqlite"
    assert catalog_file.exists()
    assert (tmp_path / "omnisus.ducklake").is_dir()

    lake.close()


def test_lake_tables_returns_empty_initially(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    assert lake.tables() == []
    lake.close()


def test_lake_connect_returns_duckdb_connection(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    con = lake.connect()
    assert isinstance(con, duckdb.DuckDBPyConnection)
    lake.close()


def test_lake_query_runs_sql(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    con = lake.connect()
    rows = con.execute("SELECT 1 AS x").fetchall()
    assert rows == [(1,)]
    lake.close()


def test_lake_cloud_failure_names_the_stage_without_the_dsn(tmp_path: Path) -> None:
    """A real attach against a closed port: the error says which statement
    failed and never carries the connection string."""
    import traceback

    from omnisus.lake import CatalogAttachError

    secret = "synthetic-secret"
    with pytest.raises(CatalogAttachError) as caught:
        Lake.cloud(catalog=f"postgresql://user:{secret}@127.0.0.1:1/none", storage=str(tmp_path))
    assert caught.value.stage == "attach"
    assert secret not in "".join(traceback.format_exception(caught.value))


def test_lake_context_manager(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/cm.ducklake"
    with Lake.local(target) as lake:
        assert lake.tables() == []


# ---------------------------------------------------------------------------
# ensure_aux_cnes_view — derived view over cnes_estabelecimentos
# ---------------------------------------------------------------------------


def _seed_cnes_estabelecimentos(lake: Lake) -> None:
    """Seed ``lake.cnes_estabelecimentos`` with two snapshots for the same CNES so that
    the view's ARG_MAX picks the latest tp_unid/codufmun.

    Reflects the real DATASUS CNES-ST schema: no name fields — establishment
    metadata is limited to type (``tp_unid``) and município (``codufmun``).
    """
    con = lake.connect()
    con.execute(
        f"""
        CREATE TABLE {lake.alias}.cnes_estabelecimentos (
            cnes VARCHAR,
            tp_unid VARCHAR,
            codufmun VARCHAR,
            ano INTEGER,
            mes INTEGER
        )
        """
    )
    con.execute(
        f"""
        INSERT INTO {lake.alias}.cnes_estabelecimentos VALUES
            ('1234567', '05', '355030', 2024, 1),
            ('1234567', '07', '355030', 2024, 3),
            ('7654321', '02', '354780', 2024, 1)
        """
    )


def test_ensure_aux_cnes_view_skips_when_cnes_estabelecimentos_missing(tmp_path: Path) -> None:
    with Lake.local(f"ducklake:{tmp_path}/v.ducklake") as lake:
        assert lake.ensure_aux_cnes_view() is False
        assert "aux_cnes" not in lake.tables()


def test_ensure_aux_cnes_view_picks_latest_snapshot_per_cnes(tmp_path: Path) -> None:
    with Lake.local(f"ducklake:{tmp_path}/v.ducklake") as lake:
        _seed_cnes_estabelecimentos(lake)
        assert lake.ensure_aux_cnes_view() is True

        rows = (
            lake.connect()
            .execute(
                f"SELECT cnes, tp_unid, codufmun, yyyymm_max "
                f"FROM {lake.alias}.aux_cnes ORDER BY cnes"
            )
            .fetchall()
        )
        assert rows == [
            ("1234567", "07", "355030", 202403),
            ("7654321", "02", "354780", 202401),
        ]


def test_ensure_aux_cnes_view_is_idempotent(tmp_path: Path) -> None:
    with Lake.local(f"ducklake:{tmp_path}/v.ducklake") as lake:
        _seed_cnes_estabelecimentos(lake)
        assert lake.ensure_aux_cnes_view() is True
        # Refreshing twice must not raise (CREATE OR REPLACE).
        assert lake.ensure_aux_cnes_view() is True
        n = lake.connect().execute(f"SELECT COUNT(*) FROM {lake.alias}.aux_cnes").fetchone()[0]
        assert n == 2  # one row per distinct CNES, regardless of how many calls


def test_ensure_aux_cnes_view_reflects_new_snapshots(tmp_path: Path) -> None:
    """The view is a thin SQL projection — re-creating the view (or simply
    re-querying it) must surface rows added to ``cnes_estabelecimentos`` afterwards.
    """
    with Lake.local(f"ducklake:{tmp_path}/v.ducklake") as lake:
        _seed_cnes_estabelecimentos(lake)
        lake.ensure_aux_cnes_view()

        con = lake.connect()
        con.execute(
            f"INSERT INTO {lake.alias}.cnes_estabelecimentos VALUES ('1234567', '15', '355030', 2024, 7)"
        )
        # No need to call ensure_* again — view re-reads cnes_estabelecimentos.
        tp_unid = con.execute(
            f"SELECT tp_unid FROM {lake.alias}.aux_cnes WHERE cnes = '1234567'"
        ).fetchone()[0]
        assert tp_unid == "15"
