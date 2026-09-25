"""Direct optional-package contract; requires a built, installed wheel."""

import gc
from pathlib import Path

import pyarrow as pa
import pytest

SEEDS = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "dbf"


def test_batch_lifetime_and_close():
    import omnisus_dbf as native

    reader = native.open_reader(
        (SEEDS / "numeric-exact.dbf").read_bytes(), encoding="cp1252", batch_rows=1
    )
    assert iter(reader) is reader
    batch = next(reader)
    assert isinstance(batch, pa.RecordBatch)
    expected = batch.to_pylist()
    reader.close()
    reader.close()
    assert list(reader) == []
    del reader
    gc.collect()
    assert batch.to_pylist() == expected


def test_strict_decode_and_preflight_errors():
    import omnisus_dbf as native

    raw = (SEEDS / "text-latin1.dbf").read_bytes()
    assert native.API_VERSION == 2
    assert native.__version__
    for alias in ["latin-1", "latin1", "iso-8859-1", "L1"]:
        assert list(native.open_reader(raw, encoding=alias, batch_rows=2))
    with pytest.raises(UnicodeDecodeError):
        list(native.open_reader(raw, encoding="cp1252", batch_rows=2))
    with pytest.raises(native.UnsupportedDbfError):
        native.open_reader(raw, encoding="utf-16", batch_rows=2)
    with pytest.raises(native.InvalidDbfError):
        native.open_reader(raw[:16], encoding="cp1252", batch_rows=2)
    for rows in [0, -1]:
        with pytest.raises(ValueError):
            native.open_reader(raw, encoding="cp1252", batch_rows=rows)
    with pytest.raises(TypeError):
        native.open_reader(bytearray(raw), encoding="cp1252", batch_rows=2)


def test_decompress_dbc_contract():
    import omnisus_dbf as native

    blast = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "blast"
    raw = bytes(8) + (33).to_bytes(2, "little") + bytes(27) + (blast / "test.pk").read_bytes()
    assert native.decompress_dbc(raw) == raw[:33] + (blast / "test.txt").read_bytes()
    with pytest.raises(native.InvalidDbcError, match=r"^missing DBC header$"):
        native.decompress_dbc(b"")
    assert issubclass(native.InvalidDbcError, ValueError)
    with pytest.raises(TypeError):
        native.decompress_dbc(bytearray(raw))
