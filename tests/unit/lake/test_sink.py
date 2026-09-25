"""Tests for Lake.ingest()."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from omnisus.lake import Lake


def test_ingest_creates_table_and_inserts(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    lf = pl.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]}).lazy()

    result = lake.ingest("foo", lf, partition_by=())

    assert result.rows == 3
    assert result.bytes_written > 0
    assert result.duration_seconds >= 0

    rows = lake.connect().execute("SELECT count(*) FROM lake.foo").fetchone()[0]
    assert rows == 3
    lake.close()


def test_ingest_appends_on_second_call(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    lf = pl.DataFrame({"id": [1]}).lazy()
    lake.ingest("foo", lf, partition_by=())
    lake.ingest("foo", lf, partition_by=())
    n = lake.connect().execute("SELECT count(*) FROM lake.foo").fetchone()[0]
    assert n == 2
    lake.close()


def test_ingest_returns_snapshot_id_when_available(tmp_path: Path) -> None:
    """Snapshot id may be None on first DuckLake versions; if non-None, must be int."""
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    lf = pl.DataFrame({"id": [1]}).lazy()
    result = lake.ingest("foo", lf, partition_by=())
    if result.snapshot_id is not None:
        assert isinstance(result.snapshot_id, int)
    lake.close()
