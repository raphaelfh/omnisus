"""dbc_excerpt keeps real records and produces a DBC both decoders read."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.dbc_excerpt import (
    _columns,
    blank_dbf,
    dbc_from_dbf,
    excerpt_dbc,
    excerpt_dbf,
    implode,
)

from omnisus.sources.datasus_ftp.dbc import _python_decompress, decompress_bytes

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
REAL = FIXTURES / "dbc" / "sim_rr_2023_mini.dbc"


def _geometry(dbf: bytes) -> tuple[int, int, int]:
    return (
        int.from_bytes(dbf[4:8], "little"),
        int.from_bytes(dbf[8:10], "little"),
        int.from_bytes(dbf[10:12], "little"),
    )


def test_implode_round_trips_every_byte_value_through_our_decoder() -> None:
    """Synthetic bytes on purpose: every byte value 0-255, alone and repeated, must
    survive the implode stream, which no real DBF guarantees to contain."""
    payload = bytes(range(256)) * 3 + bytes(600)
    stream = implode(payload)
    assert stream[:2] == b"\x00\x06"
    header = b"\x03" + b"\x00" * 7 + (33).to_bytes(2, "little") + b"\x00" * 22 + b"\x0d"
    dbc = header + b"\x00\x00\x00\x00" + stream
    assert _python_decompress(dbc) == header + payload


def test_a_rewrapped_real_file_stays_near_the_datasus_size() -> None:
    raw = REAL.read_bytes()
    original = decompress_bytes(raw)
    wrapped = dbc_from_dbf(original)
    assert decompress_bytes(wrapped) == original
    assert len(wrapped) < 1.2 * len(raw)


def test_excerpt_keeps_the_first_records_of_a_real_file() -> None:
    original = decompress_bytes(REAL.read_bytes())
    nrec, header_length, record_length = _geometry(original)
    assert nrec > 50
    excerpt = decompress_bytes(excerpt_dbc(REAL.read_bytes(), records=50))
    assert _geometry(excerpt) == (50, header_length, record_length)
    body = original[header_length : header_length + 50 * record_length]
    assert excerpt[header_length:] == body + b"\x1a"
    assert excerpt[12:header_length] == original[12:header_length]


def test_excerpt_can_start_after_the_first_record() -> None:
    """An excerpt can hold the one record a test needs from deep inside a file."""
    original = decompress_bytes(REAL.read_bytes())
    _, header_length, record_length = _geometry(original)
    excerpt = decompress_bytes(excerpt_dbc(REAL.read_bytes(), records=5, first=40))
    assert _geometry(excerpt) == (5, header_length, record_length)
    start = header_length + 40 * record_length
    assert excerpt[header_length:] == original[start : start + 5 * record_length] + b"\x1a"


def test_excerpt_is_readable_by_the_staging_pipeline(tmp_path: Path) -> None:
    from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet

    raw = excerpt_dbc(REAL.read_bytes(), records=20)
    result = dbc_bytes_to_parquet(
        raw, tmp_path / "out.parquet", dataset="sim_obitos", ano=2023, uf="RR"
    )
    assert result.rows == 20


def test_asking_for_more_records_than_exist_fails() -> None:
    original = decompress_bytes(REAL.read_bytes())
    with pytest.raises(ValueError, match="only"):
        excerpt_dbf(original, records=_geometry(original)[0] + 1)
    with pytest.raises(ValueError, match="only"):
        excerpt_dbf(original, records=2, first=_geometry(original)[0] - 1)


def test_dbc_from_dbf_keeps_the_header_uncompressed() -> None:
    original = decompress_bytes(REAL.read_bytes())
    header_length = _geometry(original)[1]
    wrapped = dbc_from_dbf(original)
    assert wrapped[:header_length] == original[:header_length]
    assert decompress_bytes(wrapped) == original


@pytest.mark.rust_dbf
def test_rust_decoder_reads_the_excerpt_identically() -> None:
    raw = excerpt_dbc(REAL.read_bytes(), records=30)
    assert decompress_bytes(raw, backend="rust") == decompress_bytes(raw, backend="python")


def _cells(dbf: bytes, column: str) -> list[bytes]:
    offset, width = _columns(dbf)[column]
    header_length = int.from_bytes(dbf[8:10], "little")
    record_length = int.from_bytes(dbf[10:12], "little")
    records = int.from_bytes(dbf[4:8], "little")
    return [
        dbf[start + offset : start + offset + width]
        for start in range(header_length, header_length + records * record_length, record_length)
    ]


def test_blank_fills_only_the_named_column() -> None:
    original = decompress_bytes(REAL.read_bytes())
    blanked = blank_dbf(original, ["CODMUNRES"])
    assert len(blanked) == len(original)
    assert all(cell.strip() == b"" for cell in _cells(blanked, "CODMUNRES"))
    assert any(cell.strip() for cell in _cells(original, "CODMUNRES"))
    for column in _columns(original):
        if column != "CODMUNRES":
            assert _cells(blanked, column) == _cells(original, column), column


def test_blank_with_a_condition_keeps_the_other_records() -> None:
    original = decompress_bytes(REAL.read_bytes())
    blanked = blank_dbf(original, ["CODMUNRES:SEXO=1"])
    pairs = zip(
        _cells(original, "SEXO"),
        _cells(original, "CODMUNRES"),
        _cells(blanked, "CODMUNRES"),
        strict=True,
    )
    for sexo, before, after in pairs:
        assert after == (b" " * len(before) if sexo.strip() == b"1" else before)
