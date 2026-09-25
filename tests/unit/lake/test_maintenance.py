from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from typer.testing import CliRunner

from omnisus.cli.main import app
from omnisus.lake import Lake
from omnisus.lake.catalog import parse_target


def test_catalog_preserves_escaped_query():
    parsed = parse_target(
        "ducklake:postgresql://u:p%26q@h/db?sslmode=require&options=-c%20x%3Dy&storage=s3%3A%2F%2Fb%2Fa%3Fx%3D1"
    )
    assert parsed.catalog_uri == "postgresql://u:p%26q@h/db?sslmode=require&options=-c%20x%3Dy"
    assert parsed.storage_root == "s3://b/a?x=1"


def test_cloud_keeps_catalog_and_storage_separate(monkeypatch):
    from omnisus.lake.catalog import CatalogURI

    monkeypatch.setattr(Lake, "__init__", lambda self, *, target: setattr(self, "target", target))
    lake = Lake.cloud(catalog="postgresql://h/db?sslmode=require", storage="s3://b/a?x=1&y=2")
    assert lake.target == CatalogURI("postgresql://h/db?sslmode=require", "s3://b/a?x=1&y=2")


def test_quoted_paths_and_identifiers_roundtrip(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/D'Avila/lake.ducklake") as lake:
        lake.ingest(
            "select", pl.DataFrame({"from": [1], 'a"b': [2]}).lazy(), partition_by=("from",)
        )
        lake.ingest("select", pl.DataFrame({"from": [3], 'a"b': [4], "new column": ["x"]}).lazy())
        assert lake.connect().execute(
            'SELECT "from", "a""b", "new column" FROM lake."select" ORDER BY "from"'
        ).fetchall() == [(1, 2, None), (3, 4, "x")]


def test_compaction_and_dry_runs_preserve_rows_and_history(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/m.ducklake") as lake:
        for offset in (0, 5000):
            lake.ingest("t", pl.DataFrame({"x": range(offset, offset + 5000)}).lazy())
        before = lake.snapshots()
        old_snapshot = before[-1]["snapshot_id"]
        rows = lake.optimize("t")
        assert isinstance(rows, list)
        assert lake.connect().execute("SELECT count(*),sum(x) FROM lake.t").fetchone() == (
            10000,
            49995000,
        )
        assert (
            lake.connect()
            .execute(f"SELECT count(*) FROM lake.t AT (VERSION => {old_snapshot})")
            .fetchone()[0]
            == 10000
        )
        snapshots = lake.snapshots()
        paths = sorted(p.as_posix() for p in tmp_path.rglob("*.parquet"))
        future = datetime.now(UTC) + timedelta(days=1)
        assert isinstance(lake.expire_snapshots(older_than=future, dry_run=True), list)
        assert isinstance(lake.cleanup_files(older_than=future, dry_run=True), list)
        assert lake.snapshots() == snapshots
        assert sorted(p.as_posix() for p in tmp_path.rglob("*.parquet")) == paths


def test_naive_cutoff_rejected(tmp_path):
    with (
        Lake.local(f"ducklake:{tmp_path}/m.ducklake") as lake,
        pytest.raises(ValueError, match="timezone"),
    ):
        lake.cleanup_files(older_than=datetime(2020, 1, 1))


def test_optimize_failure_cli_is_nonzero(tmp_path):
    result = CliRunner().invoke(
        app, ["lake", "optimize", "missing", "--target", f"ducklake:{tmp_path}/m.ducklake"]
    )
    assert result.exit_code != 0


def test_invalid_uri_error_does_not_expose_credentials():
    with pytest.raises(ValueError) as error:
        parse_target("ducklake:postgresql://user:SENTINEL_PASSWORD@host\uff03/db?storage=s3://b")
    assert "SENTINEL_PASSWORD" not in str(error.value)
