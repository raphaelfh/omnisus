"""Optional native DBF to Arrow reader and DBC decompressor."""

from ._native import (
    API_VERSION,
    DbfBatchReader,
    InvalidDbcError,
    InvalidDbfError,
    UnsupportedDbfError,
    __version__,
    decompress_dbc,
    open_reader,
)

__all__ = [
    "API_VERSION",
    "DbfBatchReader",
    "InvalidDbcError",
    "InvalidDbfError",
    "UnsupportedDbfError",
    "__version__",
    "decompress_dbc",
    "open_reader",
]
