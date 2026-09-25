"""The optional native package is found, rejected or skipped, never silently misused."""

from types import SimpleNamespace

import pytest

from omnisus.sources.datasus_ftp import dbc, dbf_batches, native
from tests.support.native import missing_module


@pytest.mark.parametrize("value", ["python", "rust", "auto"])
def test_explicit_backend_wins_over_environment(monkeypatch, value):
    monkeypatch.setenv("OMNISUS_X_BACKEND", "typo")
    assert native.requested_backend(value, variable="OMNISUS_X_BACKEND", label="X") == value


def test_environment_then_auto(monkeypatch):
    monkeypatch.delenv("OMNISUS_X_BACKEND", raising=False)
    assert native.requested_backend(None, variable="OMNISUS_X_BACKEND", label="X") == "auto"
    monkeypatch.setenv("OMNISUS_X_BACKEND", "python")
    assert native.requested_backend(None, variable="OMNISUS_X_BACKEND", label="X") == "python"


def test_unknown_backend_names_the_capability(monkeypatch):
    monkeypatch.setenv("OMNISUS_X_BACKEND", "typo")
    with pytest.raises(ValueError, match=r"^X backend must be python, rust or auto$"):
        native.requested_backend(None, variable="OMNISUS_X_BACKEND", label="X")


def test_python_never_imports(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: pytest.fail("imported"))
    assert native.load_native("python") is None


def test_auto_without_package_is_none(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: missing_module("omnisus_dbf"))
    assert native.load_native("auto") is None


def test_rust_without_package_raises(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: missing_module("omnisus_dbf"))
    with pytest.raises(ImportError, match="omnisus-dbf"):
        native.load_native("rust")


def test_missing_transitive_dependency_is_not_hidden(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: missing_module("pyarrow"))
    with pytest.raises(ModuleNotFoundError):
        native.load_native("auto")


def test_incompatible_api_is_an_error_even_for_auto(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: SimpleNamespace(API_VERSION=99))
    with pytest.raises(ImportError, match=f"API_VERSION={native.API_VERSION}"):
        native.load_native("auto")


def test_compatible_module_is_returned(monkeypatch):
    module = SimpleNamespace(API_VERSION=native.API_VERSION)
    monkeypatch.setattr(native, "import_module", lambda _: module)
    assert native.load_native("rust") is module


def _dbc_selector():
    dbc.decompress_bytes(b"", backend="auto")


def _dbf_selector():
    with dbf_batches.open_dbf_batches(
        b"", encoding="latin-1", batch_rows=1, backend="auto"
    ) as batches:
        list(batches)


@pytest.mark.parametrize("selector", [_dbc_selector, _dbf_selector])
@pytest.mark.parametrize(
    ("import_module", "match", "expected_error"),
    [
        (lambda _: SimpleNamespace(API_VERSION=99), "API", ImportError),
        (lambda _: missing_module("pyarrow"), None, ModuleNotFoundError),
    ],
)
def test_selectors_do_not_hide_loader_errors_under_auto(
    monkeypatch, selector, import_module, match, expected_error
):
    """A selector must let load_native's errors propagate, never swallow them into Python."""
    monkeypatch.setattr(native, "import_module", import_module)
    if match is not None:
        with pytest.raises(expected_error, match=match):
            selector()
    else:
        with pytest.raises(expected_error):
            selector()
