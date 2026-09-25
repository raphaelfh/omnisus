"""DuckDB connection factory with ducklake extension loaded."""

from __future__ import annotations

import contextlib
from pathlib import Path

import duckdb

from omnisus.lake.sql import quote_identifier, quote_literal

SUPPORTED_CATALOG_SCHEMES = ("sqlite", "postgresql", "postgres", "duckdb")


class CatalogAttachError(RuntimeError):
    """The DuckLake catalog could not be opened, so there is no lake to use.

    ``stage`` names the statement that failed: ``"install"`` (the ducklake
    extension), ``"attach"`` (the catalog itself) or ``"set_option"``; the
    message adds the DuckDB error class. For a remote catalog the DuckDB error
    is not chained — its text can echo the connection string — so stage and
    class are the whole diagnostic. For a local catalog it is chained, so the
    file-level reason stays visible.
    """

    def __init__(self, stage: str, duckdb_error: str) -> None:
        self.stage = stage
        super().__init__(f"could not open DuckLake catalog: {duckdb_error} during {stage}")


def make_connection(
    *,
    catalog_uri: str,
    storage_root: str,
    alias: str = "lake",
) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection with ducklake attached for writing.

    Args:
        catalog_uri: ``sqlite:/path/to/catalog.sqlite`` or ``postgresql://...``.
        storage_root: filesystem path or s3:// URI for Parquet storage.
        alias: schema alias for the attached ducklake (default ``lake``).

    Returns:
        Connected ``DuckDBPyConnection`` with ducklake loaded and attached.

    Raises:
        CatalogAttachError: any of the three setup statements failed; the
            connection is closed before raising.
    """
    remote = _is_remote(catalog_uri)
    if not storage_root.startswith(("s3://", "gs://", "az://", "azure://")):
        Path(storage_root).mkdir(parents=True, exist_ok=True)
    return _attach(
        catalog_uri,
        alias,
        remote=remote,
        options=(f"DATA_PATH {quote_literal(storage_root)}",),
        set_compression=True,
    )


def make_reader_connection(
    *,
    catalog_uri: str,
    alias: str = "lake",
    snapshot_id: int | None = None,
) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection with an *existing* ducklake attached read-only.

    No ``DATA_PATH`` is passed — the catalog records its own and rejects a
    different one — no catalog is created when none exists, and no option is
    set, so nothing here needs the writer lock. ``snapshot_id`` pins the whole
    session to one snapshot; without it every statement reads the latest
    committed one.
    """
    options = ["READ_ONLY", "CREATE_IF_NOT_EXISTS false"]
    if snapshot_id is not None:
        options.append(f"SNAPSHOT_VERSION {snapshot_id}")
    return _attach(
        catalog_uri,
        alias,
        remote=_is_remote(catalog_uri),
        options=tuple(options),
        set_compression=False,
    )


def _is_remote(catalog_uri: str) -> bool:
    """Whether the catalog is PostgreSQL-backed; rejects unsupported schemes first."""
    scheme = catalog_uri.split(":", 1)[0].lower()
    if scheme not in SUPPORTED_CATALOG_SCHEMES:
        raise ValueError(f"unsupported catalog scheme: {scheme!r}")
    return scheme in ("postgres", "postgresql")


def _attach(
    catalog_uri: str,
    alias: str,
    *,
    remote: bool,
    options: tuple[str, ...],
    set_compression: bool,
) -> duckdb.DuckDBPyConnection:
    # DuckLake requires an explicit backend selector before a PostgreSQL URI.
    metadata_path = "postgres:" + catalog_uri if remote else catalog_uri
    quoted_alias = quote_identifier(alias)
    statements = [
        ("install", "INSTALL ducklake; LOAD ducklake;"),
        (
            "attach",
            f"ATTACH {quote_literal('ducklake:' + metadata_path)} AS {quoted_alias} "
            f"({', '.join(options)})",
        ),
    ]
    if set_compression:
        statements.append(
            ("set_option", f"CALL {quoted_alias}.set_option('parquet_compression', 'zstd')")
        )
    con = duckdb.connect(":memory:")
    for stage, sql in statements:
        try:
            con.execute(sql)
        except BaseException as exc:
            con.close()
            if not isinstance(exc, Exception):
                raise
            cause = None if remote else exc  # a remote error can echo the connection string
            raise CatalogAttachError(stage, type(exc).__name__) from cause
    return con


def close_connection(con: duckdb.DuckDBPyConnection, alias: str = "lake") -> None:
    """Detach + close cleanly."""
    with contextlib.suppress(duckdb.Error):
        con.execute(f"DETACH {quote_identifier(alias)}")
    con.close()
