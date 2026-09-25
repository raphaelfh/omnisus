"""Backend selection must not hide corruption or leak readers."""

import importlib
from types import SimpleNamespace

import pyarrow as pa
import pytest

from omnisus.sources.datasus_ftp import native as native_loader
from tests.support.dbf import make_dbf
from tests.support.native import missing_module


def batches_module():
    return importlib.import_module("omnisus.sources.datasus_ftp.dbf_batches")


def test_python_batches_keep_order_and_boundaries():
    module = batches_module()
    data = make_dbf([("X", "C", 1, 0)], [b" a", b" b", b" c"])
    with module.open_dbf_batches(
        data, encoding="latin-1", batch_rows=2, backend="python"
    ) as stream:
        batches = list(stream)
    assert [batch.num_rows for batch in batches] == [2, 1]
    assert [row["X"] for batch in batches for row in batch.to_pylist()] == ["a", "b", "c"]


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_batch_size(size):
    module = batches_module()
    with (
        pytest.raises(ValueError),
        module.open_dbf_batches(b"", encoding="latin-1", batch_rows=size, backend="python"),
    ):
        pass


def test_python_reader_closed_when_consumer_stops(monkeypatch):
    from omnisus.sources.datasus_ftp import parse

    closed = []

    def records(*args, **kwargs):
        try:
            yield {"X": 1}
            yield {"X": 2}
        finally:
            closed.append(True)

    monkeypatch.setattr(parse, "_stream_records", records)
    with batches_module().open_dbf_batches(
        b"fake", encoding="latin-1", batch_rows=1, backend="python"
    ) as reader:
        assert next(reader).to_pylist() == [{"X": 1}]
    assert closed == [True]


def test_invalid_backend_is_not_silently_python(monkeypatch):
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "typo")
    with (
        pytest.raises(ValueError, match="backend"),
        batches_module().open_dbf_batches(b"", encoding="latin-1", batch_rows=1),
    ):
        pass


@pytest.mark.parametrize("backend", [None, "auto", "rust"])
def test_missing_optional_module(monkeypatch, backend):
    monkeypatch.delenv("OMNISUS_DBF_BACKEND", raising=False)
    module = batches_module()
    monkeypatch.setattr(native_loader, "import_module", missing_module)
    data = make_dbf([("X", "C", 1, 0)], [b" a"])
    if backend == "rust":
        with (
            pytest.raises(ImportError, match="omnisus-dbf"),
            module.open_dbf_batches(data, encoding="latin-1", batch_rows=1, backend=backend),
        ):
            pass
    else:
        with module.open_dbf_batches(
            data, encoding="latin-1", batch_rows=1, backend=backend
        ) as stream:
            assert next(stream).to_pylist() == [{"X": "a"}]


class UnsupportedDbfError(ValueError):
    pass


class InvalidDbfError(ValueError):
    pass


def fake_native(open_reader):
    return SimpleNamespace(
        API_VERSION=native_loader.API_VERSION,
        __version__="0.1.0",
        open_reader=open_reader,
        UnsupportedDbfError=UnsupportedDbfError,
        InvalidDbfError=InvalidDbfError,
    )


def test_default_uses_native_when_installed(monkeypatch):
    module = batches_module()
    monkeypatch.delenv("OMNISUS_DBF_BACKEND", raising=False)

    def reader(*args, **kwargs):
        yield pa.record_batch({"X": ["native"]})

    monkeypatch.setattr(native_loader, "import_module", lambda _: fake_native(reader))
    data = make_dbf([("X", "C", 1, 0)], [b" a"])
    with module.open_dbf_batches(data, encoding="latin-1", batch_rows=1) as stream:
        assert next(stream).to_pylist() == [{"X": "native"}]


def test_only_preflight_unsupported_can_fallback(monkeypatch):
    module = batches_module()

    def unsupported(*args, **kwargs):
        raise UnsupportedDbfError("field D")

    monkeypatch.setattr(native_loader, "import_module", lambda _: fake_native(unsupported))
    data = make_dbf([("X", "D", 8, 0)], [b" 20240101"])
    with module.open_dbf_batches(data, encoding="latin-1", batch_rows=1, backend="auto") as stream:
        assert str(next(stream).to_pylist()[0]["X"]) == "2024-01-01"


@pytest.mark.parametrize(
    "error", [UnsupportedDbfError, InvalidDbfError, ValueError, KeyboardInterrupt]
)
def test_late_native_error_cleans_and_never_restarts(monkeypatch, error):
    from omnisus.sources.datasus_ftp import parse

    module = batches_module()
    closed = []

    def reader():
        try:
            yield pa.record_batch({"X": ["a"]})
            raise error("late")
        finally:
            closed.append(True)

    monkeypatch.setattr(
        native_loader, "import_module", lambda _: fake_native(lambda *a, **kw: reader())
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Python fallback after native iteration")

    monkeypatch.setattr(parse, "_stream_records", forbidden)
    expected = parse.DbfIntegrityError if error is InvalidDbfError else error
    with (
        pytest.raises(expected),
        module.open_dbf_batches(b"", encoding="latin-1", batch_rows=1, backend="auto") as stream,
    ):
        assert next(stream).num_rows == 1
        next(stream)
    assert closed == [True]
