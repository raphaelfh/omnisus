"""DBC bytes → Polars LazyFrame pipeline.

The compatibility LazyFrame materializes validated Parquet before its temporary
file is removed. Bulk ingestion uses staging.dbc_bytes_to_parquet directly.
DBC decompression still materializes the entire DBF payload.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import polars as pl
from dbfread2 import DBF

from omnisus.sources.datasus_ftp.dbf_contract import (
    DbfIntegrityError as DbfIntegrityError,
)
from omnisus.sources.datasus_ftp.dbf_contract import (
    _check_dbf_length as _check_dbf_length,
)
from omnisus.sources.datasus_ftp.dbf_contract import (
    _check_record_count as _check_record_count,
)
from omnisus.sources.datasus_ftp.dbf_contract import (
    _ensure_dbf_terminator as _ensure_dbf_terminator,
)
from omnisus.sources.datasus_ftp.dbf_contract import (
    _read_dbf_geometry as _read_dbf_geometry,
)

BATCH_ROWS = 100_000


def _stream_records(dbf_bytes: bytes, encoding: str) -> Iterator[dict[str, Any]]:
    """Stream records from DBF bytes via a temp file (dbfread2 needs a path)."""
    dbf_bytes = _ensure_dbf_terminator(dbf_bytes)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(dbf_bytes)
        for record in DBF(tmp_path, encoding=encoding, preload=False):
            yield dict(record)
    finally:
        if tmp_path is not None:
            os.unlink(tmp_path)


def dbc_bytes_to_lazyframe(
    dbc_bytes: bytes,
    *,
    dataset: str,
    ano: int | None = None,
    uf: str | None = None,
    dictionary: Path | None = None,
) -> pl.LazyFrame:
    """Decode DBC bytes and return a Polars LazyFrame.

    Args:
        dbc_bytes: raw DBC payload from FTP.
        dataset: dataset name (e.g. "sim_obitos") — used for log/error messages
            and, when ``dictionary`` is None, to look up the packaged YAML.
        ano, uf: optionally injected as canonical partition columns.
        dictionary: explicit Frictionless YAML path. Bypasses the packaged
            lookup so an unregistered dataset can be parsed.

    Raises:
        FileNotFoundError: if no dictionary can be loaded.
        DbfIntegrityError: if the decompressed DBF is truncated or the parsed
            record count diverges from the header's declared count.
        InvalidDbcError: if the DBC payload is malformed or truncated.
        Exception: bubbles from dbfread2 on a malformed DBF.
    """
    from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet

    # Materialize before cleanup so the compatibility LazyFrame owns its data.
    # Bulk ingestion uses dbc_bytes_to_parquet directly instead.
    with tempfile.TemporaryDirectory(prefix="dbc-lazyframe-") as directory:
        path = Path(directory) / "data.parquet"
        dbc_bytes_to_parquet(
            dbc_bytes, path, dataset=dataset, ano=ano, uf=uf, dictionary=dictionary
        )
        return pl.read_parquet(path).lazy()
