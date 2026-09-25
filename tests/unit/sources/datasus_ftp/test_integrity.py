"""Tests for the nrec integrity gate: DBF header count vs parsed records.

Failure mode being guarded (measured in the field, 2026-08): a truncated
download/decompress yields a structurally valid DBF that silently loses the
tail 1-2% of records. dbfread2 raises nothing in that case — it just stops.
The gate must turn silent loss into a hard error.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from omnisus.sources.datasus_ftp.parse import (
    DbfIntegrityError,
    dbc_bytes_to_lazyframe,
)
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from tests.support.dbf import make_dbf as build_dbf

FIXTURES = Path(__file__).parents[3] / "fixtures"


def make_dbf(nrec_declared: int, records: list[bytes], eof: bytes = b"\x1a") -> bytes:
    return build_dbf([("NOME", "C", 3, 0)], records, declared_rows=nrec_declared, eof=eof)


@pytest.fixture
def fake_decompress(monkeypatch):
    """Route dbc_bytes_to_lazyframe's decompression to return crafted DBF bytes."""

    def _install(dbf_bytes: bytes) -> None:
        monkeypatch.setattr(
            "omnisus.sources.datasus_ftp.dbc.decompress_bytes",
            lambda _: dbf_bytes,
        )

    return _install


def test_truncated_dbf_raises_integrity_error(fake_decompress) -> None:
    """Header declares 3 records, only 2 present: must raise, not lose data."""
    fake_decompress(make_dbf(3, [b" AAA", b" BBB"]))
    with pytest.raises(DbfIntegrityError) as exc_info:
        dbc_bytes_to_lazyframe(b"ignored", dataset="sim_obitos")
    msg = str(exc_info.value)
    assert "3" in msg
    assert "2" in msg


def test_early_eof_marker_raises_integrity_error(fake_decompress) -> None:
    """Byte length is right but an embedded 0x1A stops the parser early."""
    fake_decompress(make_dbf(3, [b" AAA", b"\x1aBBB", b" CCC"]))
    with pytest.raises(DbfIntegrityError):
        dbc_bytes_to_lazyframe(b"ignored", dataset="sim_obitos")


def test_deleted_records_are_tolerated(fake_decompress) -> None:
    """Deleted rows (flag ``*``) count toward nrec; no false positive."""
    fake_decompress(make_dbf(3, [b" AAA", b"*BBB", b" CCC"]))
    lf = dbc_bytes_to_lazyframe(b"ignored", dataset="sim_obitos")
    assert isinstance(lf, pl.LazyFrame)
    assert lf.collect().height == 2


def test_intact_dbf_passes_gate(fake_decompress) -> None:
    """Consistent header and body: gate is invisible."""
    fake_decompress(make_dbf(2, [b" AAA", b" BBB"]))
    lf = dbc_bytes_to_lazyframe(b"ignored", dataset="sim_obitos")
    assert lf.collect().height == 2


def test_real_fixture_passes_gate(dbc_fixture) -> None:
    """A genuine DATASUS file must sail through the gate untouched."""
    dbc_path = dbc_fixture("sim_rr_2023_mini")
    lf = dbc_bytes_to_lazyframe(dbc_path.read_bytes(), dataset="sim_obitos")
    assert lf.collect().height > 0


def test_zero_record_length_fails_before_staging(tmp_path) -> None:
    """Header declares 3 records and a record length of 0; the file holds 2.

    Synthetic bytes on purpose (AGENTS.md rule 2): malformed decoder input, see
    FIXTURES.md. Every real fixture declares a positive record length.
    """
    raw = (FIXTURES / "dbc" / "malformed" / "zero_record_length.dbc").read_bytes()
    with pytest.raises(DbfIntegrityError, match=r"^DBF header declares a record length of 0$"):
        dbc_bytes_to_parquet(raw, tmp_path / "out.parquet", dataset="sim_obitos")
    assert not list(tmp_path.iterdir())
