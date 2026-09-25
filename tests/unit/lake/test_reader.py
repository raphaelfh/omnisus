"""Tests for LakeReader — the read-only session (U3)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl
import pytest

from omnisus.lake import CatalogAttachError, Lake, LakeReader
from omnisus.sources._base import ScopeKey

ROW_1 = pl.DataFrame({"ano": [2024], "uf": ["SP"], "v": [1]})
ROW_2 = pl.DataFrame({"ano": [2025], "uf": ["RJ"], "v": [2]})


def _commit_rows(target: str, *frames: pl.DataFrame) -> list[int]:
    """Append each frame to ``t`` as its own commit; return the snapshot id after each."""
    snapshots = []
    with Lake.local(target) as lake:
        for frame in frames:
            lake.ingest("t", frame.lazy())
            snapshots.append(lake.snapshots()[-1]["snapshot_id"])
    return snapshots


def _count(reader: LakeReader) -> int:
    (n,) = reader.connect().execute("SELECT count(*) FROM lake.t").fetchone()
    return n


def test_reader_opens_an_existing_lake(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/x.ducklake"
    _commit_rows(target, ROW_1)

    with LakeReader(target) as reader:
        assert reader.tables() == ["t"]
        assert reader.connect().execute("SELECT v FROM lake.t").fetchall() == [(1,)]
        assert reader.snapshot_id is None


def test_reader_takes_no_writer_lock(tmp_path: Path) -> None:
    """Opening a writer while a reader is open would raise WriterBusyError if the
    reader held the lock. An unpinned reader then sees the writer's commit."""
    target = f"ducklake:{tmp_path}/x.ducklake"
    _commit_rows(target, ROW_1)

    with LakeReader(target) as reader:
        with Lake.local(target) as writer:
            writer.ingest("t", ROW_2.lazy())
        assert _count(reader) == 2


def test_pinned_reader_ignores_later_commits(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/x.ducklake"
    (first,) = _commit_rows(target, ROW_1)

    with LakeReader(target, snapshot_id=first) as pinned, LakeReader(target) as live:
        _commit_rows(target, ROW_2)
        assert pinned.snapshot_id == first
        assert _count(pinned) == 1
        assert _count(live) == 2
        # History stays visible from a pinned session, so a caller can find newer snapshots.
        assert pinned.snapshots()[-1]["snapshot_id"] > first


def test_pin_to_a_missing_snapshot_is_an_attach_error(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/x.ducklake"
    _commit_rows(target, ROW_1)

    with pytest.raises(CatalogAttachError) as caught:
        LakeReader(target, snapshot_id=99)
    assert caught.value.stage == "attach"


def test_reader_never_creates_a_catalog(tmp_path: Path) -> None:
    with pytest.raises(CatalogAttachError) as caught:
        LakeReader(f"ducklake:{tmp_path}/missing.ducklake")
    assert caught.value.stage == "attach"
    assert not (tmp_path / "missing-catalog.sqlite").exists()
    assert not (tmp_path / "missing.ducklake").exists()


@pytest.mark.parametrize("bad", [-1, True, "1", 1.0])
def test_reader_rejects_invalid_snapshot_ids_before_connecting(tmp_path: Path, bad) -> None:
    with pytest.raises(ValueError, match="snapshot_id"):
        LakeReader(f"ducklake:{tmp_path}/missing.ducklake", snapshot_id=bad)


def test_reader_connection_refuses_writes_and_options(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/x.ducklake"
    _commit_rows(target, ROW_1)

    with LakeReader(target) as reader:
        with pytest.raises(duckdb.Error):
            reader.connect().execute("INSERT INTO lake.t VALUES (2030, 'XX', 9)")
        with pytest.raises(duckdb.Error):
            reader.connect().execute("CALL lake.set_option('parquet_compression', 'zstd')")


def test_reader_reads_the_publication_manifest(tmp_path: Path) -> None:
    """The app opened a writer just to read publications; a reader is enough."""
    target = f"ducklake:{tmp_path}/x.ducklake"
    staging = tmp_path / "staging.parquet"
    ROW_1.write_parquet(staging)
    with Lake.local(target) as lake:
        lake.publish_scope(
            "t",
            staging,
            scope=ScopeKey(uf="SP", ano=2024),
            source_sha256="0" * 64,
            parser_version="v1",
            run_id="run-1",
        )

    with LakeReader(target) as reader:
        assert [p["run_id"] for p in reader.publications(run_id="run-1")] == ["run-1"]
        assert reader.attempts() == []


def test_reader_close_is_idempotent_and_final(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/x.ducklake"
    _commit_rows(target, ROW_1)

    reader = LakeReader(target)
    reader.close()
    reader.close()
    with pytest.raises(RuntimeError, match="closed"):
        reader.connect()
