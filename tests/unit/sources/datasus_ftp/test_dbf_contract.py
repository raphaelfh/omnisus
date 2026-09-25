"""Literal expectations protect decoding independently of backend parity."""

import pytest

from omnisus.sources.datasus_ftp.parse import _stream_records
from tests.support.dbf import make_dbf


def read_value(kind, value, encoding="latin-1"):
    data = make_dbf([("X", kind, len(value), 0)], [b" " + value])
    stream = _stream_records(data, encoding=encoding)
    try:
        return next(stream)["X"]
    finally:
        stream.close()


@pytest.mark.parametrize(
    "raw,expected",
    [(b"   ", ""), (b"  a  ", "  a"), (b"0012", "0012"), (b"\x81 ", "\x81")],
)
def test_character_semantics(raw, expected):
    assert read_value("C", raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        (str(2**60 + 1).encode(), 2**60 + 1),
        (b"1,25", 1.25),
        (b"1e2", 100.0),
        (b" ** ", None),
        (b"\x00", None),
        (b" -12", -12),
    ],
)
def test_numeric_semantics(raw, expected):
    actual = read_value("N", raw)
    assert actual == expected
    assert type(actual) is type(expected)


def test_cp1252_undefined_byte_rejected():
    with pytest.raises(UnicodeDecodeError):
        read_value("C", b"\x81", encoding="cp1252")
