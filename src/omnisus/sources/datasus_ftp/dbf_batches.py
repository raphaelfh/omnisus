"""Closable DBF → Arrow adapters; staging owns all publication and schema policy."""

from __future__ import annotations

import datetime as dt
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

import pyarrow as pa
import structlog

from omnisus.sources.datasus_ftp.dbf_contract import (
    DbfFieldDescriptor,
    DbfIntegrityError,
    _read_field_descriptors,
)
from omnisus.sources.datasus_ftp.native import Backend, load_native, requested_backend

logger = structlog.get_logger(__name__)

_PHYSICAL_TYPES: dict[str, pa.DataType] = {
    "C": pa.string(),
    "V": pa.string(),
    "M": pa.string(),
    "D": pa.date32(),
    "L": pa.bool_(),
    "F": pa.float64(),
    "O": pa.float64(),
    "I": pa.int64(),
    "+": pa.int64(),
    "T": pa.timestamp("us"),
    "@": pa.timestamp("us"),
}
"""Arrow type each DBF field type yields once a record carries a value.

This mirrors what the readers actually emit — the Python backend infers from
dbfread2's Python objects (``D`` -> ``datetime.date`` -> ``date32``, ``L`` ->
``bool``, text -> ``string``), the Rust backend builds ``StringBuilder`` for
``C`` and integer/float builders for ``N`` — not what a dictionary declares.
``N`` is resolved from the descriptor's decimal count, see :func:`_arrow_type`.
"""


def _arrow_type(field: DbfFieldDescriptor) -> pa.DataType | None:
    """The type a populated batch of this field would have; None if unknown."""
    if field.kind == "N":
        return pa.float64() if field.decimals else pa.int64()
    return _PHYSICAL_TYPES.get(field.kind)


def physical_arrow_types(dbf_bytes: bytes) -> dict[str, pa.DataType]:
    """Type per header field (lowercased), skipping field types we cannot map."""
    types = {}
    for field in _read_field_descriptors(dbf_bytes):
        arrow = _arrow_type(field)
        if arrow is not None:
            types[field.name.lower()] = arrow
    return types


def physical_arrow_schema(dbf_bytes: bytes) -> pa.Schema:
    """Every header field, in file order — the schema of a zero-record file.

    Unmappable field types fall back to ``string``: with no records there is
    nothing to disagree with, and string is what such a column staged as before.
    """
    return pa.schema(
        [
            pa.field(field.name.lower(), _arrow_type(field) or pa.string())
            for field in _read_field_descriptors(dbf_bytes)
        ]
    )


def _family(value: Any) -> type:
    # bool is an int subclass; datetime is a date subclass.
    for cls in (bool, int, float, str, bytes, Decimal, dt.datetime, dt.date, dt.time):
        if isinstance(value, cls):
            return cls
    raise TypeError(f"Unsupported DBF value type: {type(value).__name__}")


def _table(records: list[dict[str, Any]]) -> pa.Table:
    names = dict.fromkeys(name for record in records for name in record)
    columns = {}
    for name in names:
        values = [record.get(name) for record in records]
        families = {_family(value) for value in values if value is not None}
        if len(families) > 1:
            raise TypeError(f"Incompatible value families in DBF column {name}")
        columns[name] = pa.array(values, safe=True)
    return pa.table(columns)


def _python_batches(
    data: bytes, encoding: str, batch_rows: int
) -> Generator[pa.RecordBatch, None, None]:
    from omnisus.sources.datasus_ftp import parse

    records = parse._stream_records(data, encoding=encoding)
    buffer = []
    try:
        for record in records:
            buffer.append(record)
            if len(buffer) >= batch_rows:
                yield from _table(buffer).to_batches()
                buffer.clear()
        if buffer:
            yield from _table(buffer).to_batches()
    finally:
        close = getattr(records, "close", None)
        if close is not None:
            close()


@contextmanager
def open_dbf_batches(
    dbf_bytes: bytes, *, encoding: str, batch_rows: int, backend: Backend | None = None
) -> Iterator[Iterator[pa.RecordBatch]]:
    """Resolve once, then consume without retrying errors through a different parser.

    Both readers own their resources until context exit. Native preflight may
    reject unsupported metadata before iteration, the only capability fallback.
    """
    if batch_rows <= 0:
        raise ValueError("batch_rows must be positive")
    requested = requested_backend(backend, variable="OMNISUS_DBF_BACKEND", label="DBF")
    native = load_native(requested)
    reader = None
    reason = "extension_not_installed" if native is None and requested == "auto" else None
    if native is not None:
        from omnisus.sources.datasus_ftp import parse

        try:
            reader = native.open_reader(
                parse._ensure_dbf_terminator(dbf_bytes),
                encoding=encoding,
                batch_rows=batch_rows,
            )
        except native.UnsupportedDbfError:
            if requested == "rust":
                raise
            reason = "unsupported_metadata"
        except native.InvalidDbfError as exc:
            raise DbfIntegrityError(str(exc)) from exc
    actual = "rust" if reader is not None else "python"
    logger.debug(
        "datasus_ftp.dbf_backend",
        backend=actual,
        requested=requested,
        version=getattr(native, "__version__", None) if actual == "rust" else None,
        fallback=reason,
    )
    if reader is None:
        reader = _python_batches(dbf_bytes, encoding, batch_rows)

    def batches():
        try:
            yield from reader
        except Exception as exc:
            if actual == "rust" and isinstance(exc, native.InvalidDbfError):
                raise DbfIntegrityError(str(exc)) from exc
            raise

    stream = batches()
    try:
        yield stream
    finally:
        stream.close()
        reader.close()
