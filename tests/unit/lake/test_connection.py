"""Tests for lake.connection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from omnisus.lake.connection import (
    CatalogAttachError,
    make_connection,
    make_reader_connection,
)


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "sqlite", "duckdb"])
def test_catalog_backend_selector(scheme, tmp_path, monkeypatch):
    con = Mock()
    monkeypatch.setattr("omnisus.lake.connection.duckdb.connect", lambda _: con)
    uri = (
        f"{scheme}://user:p'ass@localhost/test"
        if scheme in ("postgres", "postgresql")
        else f"{scheme}:{tmp_path}/cat"
    )
    make_connection(catalog_uri=uri, storage_root=str(tmp_path), alias='a"b')
    backend = "postgres:" if scheme in ("postgres", "postgresql") else ""
    escaped_uri = uri.replace("'", "''")
    con.execute.assert_any_call(
        f'ATTACH \'ducklake:{backend}{escaped_uri}\' AS "a""b" '
        f"(DATA_PATH '{str(tmp_path).replace(chr(39), chr(39) * 2)}')"
    )


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "sqlite"])
@pytest.mark.parametrize("snapshot_id", [None, 7])
def test_reader_attach_is_read_only_and_sets_nothing(scheme, snapshot_id, tmp_path, monkeypatch):
    """A reader attaches READ_ONLY without DATA_PATH — the catalog knows its own —
    never creates a catalog, and never runs set_option."""
    con = Mock()
    monkeypatch.setattr("omnisus.lake.connection.duckdb.connect", lambda _: con)
    remote = scheme != "sqlite"
    uri = f"{scheme}://user:pw@localhost/test" if remote else f"sqlite:{tmp_path}/cat"
    make_reader_connection(catalog_uri=uri, alias="lake", snapshot_id=snapshot_id)
    pin = f", SNAPSHOT_VERSION {snapshot_id}" if snapshot_id is not None else ""
    con.execute.assert_any_call(
        f"ATTACH 'ducklake:{'postgres:' if remote else ''}{uri}' AS \"lake\" "
        f"(READ_ONLY, CREATE_IF_NOT_EXISTS false{pin})"
    )
    statements = [call.args[0] for call in con.execute.call_args_list]
    assert not any("set_option" in s or "DATA_PATH" in s for s in statements)


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
@pytest.mark.parametrize(
    ("failing_statement", "stage"), [(0, "install"), (1, "attach"), (2, "set_option")]
)
def test_remote_failure_names_the_stage_and_withholds_credentials(
    scheme, failing_statement, stage, tmp_path, monkeypatch
):
    """DuckDB's error text can echo the connection string, so a remote failure
    reports which statement failed and the DuckDB error class — never the cause."""
    import traceback

    import duckdb

    con = Mock()
    secret = "synthetic-secret"
    con.execute.side_effect = [None] * failing_statement + [
        duckdb.IOException(f"connection failed: {secret}")
    ]
    monkeypatch.setattr("omnisus.lake.connection.duckdb.connect", lambda _: con)
    with pytest.raises(CatalogAttachError) as caught:
        make_connection(
            catalog_uri=f"{scheme}://user:{secret}@localhost/test",
            storage_root=str(tmp_path),
        )
    assert caught.value.stage == stage
    assert "IOException" in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
    assert secret not in "".join(traceback.format_exception(caught.value))
    con.close.assert_called_once()


def test_local_failure_keeps_the_duckdb_cause(tmp_path: Path) -> None:
    """A local catalog path names a file, not a credential: the DuckDB error
    stays chained so the researcher sees why the file could not be opened."""
    import duckdb

    with pytest.raises(CatalogAttachError) as caught:
        make_connection(catalog_uri=f"sqlite:{tmp_path}", storage_root=str(tmp_path / "data"))
    assert caught.value.stage == "attach"
    assert isinstance(caught.value.__cause__, duckdb.Error)


def test_make_connection_returns_duckdb_with_ducklake_loaded(tmp_path: Path) -> None:
    catalog = f"sqlite:{tmp_path / 'cat.sqlite'}"
    storage = str(tmp_path / "data")

    con = make_connection(catalog_uri=catalog, storage_root=storage, alias="lake")

    extensions = con.execute(
        "SELECT extension_name FROM duckdb_extensions() WHERE loaded"
    ).fetchall()
    assert any(name == "ducklake" for (name,) in extensions)

    # DuckLake attaches as a catalog (database) named after the alias;
    # its default schema is "main".
    catalogs = con.execute(
        "SELECT DISTINCT catalog_name FROM information_schema.schemata"
    ).fetchall()
    assert any(name == "lake" for (name,) in catalogs)


def test_make_connection_creates_storage_dir_if_missing(tmp_path: Path) -> None:
    storage = tmp_path / "lake-data"
    assert not storage.exists()

    make_connection(
        catalog_uri=f"sqlite:{tmp_path / 'cat.sqlite'}",
        storage_root=str(storage),
        alias="lake",
    )

    assert storage.is_dir()


def test_make_connection_rejects_unsupported_catalog_scheme(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported catalog scheme"):
        make_connection(
            catalog_uri="mongodb://nope",
            storage_root=str(tmp_path),
            alias="lake",
        )


def test_lake_files_are_zstd_not_3x_larger_than_staging(tmp_path: Path) -> None:
    """DuckLake rewrites every ingested Parquet with its own writer settings
    and does not inherit the staging file's compression. Probed on DuckLake
    415a9ebd: 801,067 B without the option vs 241,497 B with it, for a
    241,491 B zstd reference. The connection must set
    parquet_compression=zstd so lake files match a zstd reference written by
    the same engine."""
    import polars as pl

    from omnisus.lake import Lake

    with Lake.local(f"ducklake:{tmp_path}/z.ducklake") as lake:
        con = lake.connect()
        ref = tmp_path / "ref.parquet"
        con.execute(
            "COPY (SELECT 2022 AS ano, 'BA' AS uf, i AS v FROM range(200000) t(i)) "
            f"TO '{ref}' (FORMAT PARQUET, COMPRESSION zstd)"
        )
        lake.ingest("t", pl.scan_parquet(ref))
        (lake_bytes,) = con.execute(
            "SELECT sum(file_size_bytes) FROM __ducklake_metadata_lake.ducklake_data_file"
        ).fetchone()

    assert lake_bytes <= 1.2 * ref.stat().st_size, (
        f"lake wrote {lake_bytes:,} B for a {ref.stat().st_size:,} B zstd reference"
    )
