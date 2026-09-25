"""DBC decompression: byte-exact with datasus-dbc output, never silent on bad input."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from omnisus.sources.datasus_ftp import dbc, native
from omnisus.sources.datasus_ftp.dbf_batches import open_dbf_batches
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from tests.support.native import missing_module

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"
GOLDEN = json.loads((FIXTURES / "dbc" / "golden.json").read_text(encoding="utf-8"))
MUTATION_SEED = (FIXTURES / "dbc" / "sia_aq_rr_2024_01_mini.dbc").read_bytes()
VECTOR = (FIXTURES / "blast" / "test.pk").read_bytes()
MALFORMED = FIXTURES / "dbc" / "malformed"
MICRODATASUS = (FIXTURES / "dbc" / "vectors" / "microdatasus_three_fields.dbc").read_bytes()
BACKENDS = ["python", pytest.param("rust", marks=pytest.mark.rust_dbf)]
HEADER = 33


def framed(body: bytes) -> bytes:
    """A minimal DBC: a 33-byte DBF header declaring its own size, a CRC32, the body."""
    return bytes(8) + HEADER.to_bytes(2, "little") + bytes(HEADER - 10) + bytes(4) + body


def outcome(raw: bytes, backend: str) -> bytes | str:
    try:
        return dbc.decompress_bytes(raw, backend=backend)
    except dbc.InvalidDbcError as exc:
        return str(exc)


def test_golden_covers_every_fixture():
    assert sorted(GOLDEN) == sorted(path.name for path in (FIXTURES / "dbc").glob("*.dbc"))


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("name", sorted(GOLDEN))
def test_matches_datasus_dbc_output(backend, name):
    out = dbc.decompress_bytes((FIXTURES / "dbc" / name).read_bytes(), backend=backend)
    assert len(out) == GOLDEN[name]["length"]
    assert hashlib.sha256(out).hexdigest() == GOLDEN[name]["sha256"]


@pytest.mark.parametrize("backend", BACKENDS)
def test_zlib_blast_vector(backend):
    expected = (FIXTURES / "blast" / "test.txt").read_bytes()
    assert dbc.decompress_bytes(framed(VECTOR), backend=backend) == framed(b"")[:HEADER] + expected


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"", "missing DBC header"),
        (bytes(9), "missing DBC header"),
        (bytes(8) + (32).to_bytes(2, "little"), "DBF header size 32 is below the 33-byte minimum"),
        (bytes(8) + (100).to_bytes(2, "little"), "DBC header size exceeds file size"),
        (framed(b"\x02\x04"), "corrupt DBC stream at byte 38"),
        (framed(b"\x00\x07"), "corrupt DBC stream at byte 39"),
    ],
)
def test_malformed_input_names_the_problem(backend, raw, message):
    assert outcome(raw, backend) == message


@pytest.mark.parametrize("backend", BACKENDS)
def test_every_truncation_is_reported_where_input_ends(backend):
    raw = framed(VECTOR)
    for end in range(HEADER + 4, len(raw)):
        assert outcome(raw[:end], backend) == f"truncated DBC stream at byte {end}"


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("short_header.dbc", "DBF header size 32 is below the 33-byte minimum"),
        ("dict_size_3.dbc", "corrupt DBC stream at byte 39"),
    ],
)
def test_malformed_fixture_is_rejected(backend, name, message):
    """Synthetic bytes on purpose (AGENTS.md rule 2): malformed decoder input, see FIXTURES.md."""
    with pytest.raises(dbc.InvalidDbcError, match=f"^{re.escape(message)}$"):
        dbc.decompress_bytes((MALFORMED / name).read_bytes(), backend=backend)


def test_short_header_fails_before_staging(tmp_path):
    """The header claims 5 records and holds none; before the guard it staged 0 rows."""
    raw = (MALFORMED / "short_header.dbc").read_bytes()
    with pytest.raises(dbc.InvalidDbcError, match=r"^DBF header size 32 "):
        dbc_bytes_to_parquet(raw, tmp_path / "out.parquet", dataset="sim_obitos")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("backend", BACKENDS)
def test_microdatasus_vector_decodes_to_the_same_dbf(backend):
    out = dbc.decompress_bytes(MICRODATASUS, backend=backend)
    assert len(out) == 193
    assert hashlib.sha256(out).hexdigest() == (
        "7dcb84cd8e058ddd6a8e119f8094c75f14223105ade8e9b4117479fcf8a44eeb"
    )


def test_microdatasus_vector_keeps_blank_numbers_dates_and_leading_zeros():
    """microdatasus's own expectations (test-read_dbc.R at 7109ec2): CODE "001"/"010",
    VALUE 1.5/NA, WHEN 2020-01-02/NA. The second record stores VALUE as 19 ``*`` and
    WHEN as ``00000000``; both read as null. DBF read in Python: the native reader
    does not support ``D`` fields (UnsupportedDbfError)."""
    dbf = dbc.decompress_bytes(MICRODATASUS, backend="python")
    assert dbf[129 + 32 :] == b" 010 " + b"*" * 19 + b"0" * 8
    with open_dbf_batches(dbf, encoding="latin-1", batch_rows=10, backend="python") as stream:
        rows = [row for batch in stream for row in batch.to_pylist()]
    assert rows == [
        {"CODE": "001", "VALUE": 1.5, "WHEN": dt.date(2020, 1, 2)},
        {"CODE": "010", "VALUE": None, "WHEN": None},
    ]


@settings(max_examples=300, deadline=None)
@given(body=st.binary(max_size=2048), frame=st.booleans())
def test_arbitrary_bytes_decode_or_raise_invalid(body, frame):
    raw = framed(body) if frame else body
    assert isinstance(outcome(raw, "python"), bytes | str)


@pytest.mark.rust_dbf
@settings(max_examples=500, deadline=None)
@given(
    body=st.one_of(
        st.binary(max_size=2048),
        st.tuples(st.integers(0, 1), st.integers(4, 6), st.binary(max_size=2048)).map(
            lambda t: bytes([t[0], t[1]]) + t[2]
        ),
    ),
    frame=st.booleans(),
)
def test_backends_agree_on_bytes_and_messages(body, frame):
    raw = framed(body) if frame else body
    assert outcome(raw, "rust") == outcome(raw, "python")


@pytest.mark.rust_dbf
@settings(max_examples=200, deadline=None)
@given(index=st.integers(0, len(MUTATION_SEED) - 1), value=st.integers(0, 255))
def test_backends_agree_on_mutated_fixture(index, value):
    mutated = bytearray(MUTATION_SEED)
    mutated[index] = value
    assert outcome(bytes(mutated), "rust") == outcome(bytes(mutated), "python")


class Recorder:
    def __init__(self):
        self.events = []

    def debug(self, event, **fields):
        self.events.append(("debug", event, fields))

    def info(self, event, **fields):
        self.events.append(("info", event, fields))


class FakeInvalidDbcError(ValueError):
    pass


def fake_native(decompress):
    return SimpleNamespace(
        API_VERSION=native.API_VERSION,
        __version__="9.9.9",
        decompress_dbc=decompress,
        InvalidDbcError=FakeInvalidDbcError,
    )


def test_unknown_backend_is_rejected(monkeypatch):
    monkeypatch.setenv("OMNISUS_DBC_BACKEND", "typo")
    with pytest.raises(ValueError, match=r"^DBC backend must be python, rust or auto$"):
        dbc.decompress_bytes(framed(VECTOR))


def test_auto_prefers_native_and_logs_it(monkeypatch):
    monkeypatch.delenv("OMNISUS_DBC_BACKEND", raising=False)
    monkeypatch.setattr(native, "import_module", lambda _: fake_native(lambda raw: b"native"))
    log = Recorder()
    monkeypatch.setattr(dbc, "logger", log)
    assert dbc.decompress_bytes(framed(VECTOR)) == b"native"
    assert log.events == [
        (
            "debug",
            "datasus_ftp.dbc_backend",
            {"backend": "rust", "requested": "auto", "version": "9.9.9", "fallback": None},
        )
    ]


def test_native_error_is_raised_as_invalid_dbc_error_without_python_retry(monkeypatch):
    def broken(raw):
        raise FakeInvalidDbcError("corrupt DBC stream at byte 3")

    monkeypatch.setattr(native, "import_module", lambda _: fake_native(broken))
    with pytest.raises(dbc.InvalidDbcError, match=r"^corrupt DBC stream at byte 3$"):
        dbc.decompress_bytes(b"", backend="rust")


def test_auto_without_package_decodes_in_python_and_says_why(monkeypatch):
    monkeypatch.setattr(native, "import_module", lambda _: missing_module("omnisus_dbf"))
    log = Recorder()
    monkeypatch.setattr(dbc, "logger", log)
    assert dbc.decompress_bytes(framed(VECTOR), backend="auto").endswith(b"AIAIAIAIAIAIA")
    assert log.events == [
        (
            "debug",
            "datasus_ftp.dbc_backend",
            {
                "backend": "python",
                "requested": "auto",
                "version": None,
                "fallback": "extension_not_installed",
            },
        )
    ]


@pytest.mark.parametrize(("backend", "hinted"), [("auto", True), ("python", False)])
def test_speed_hint_only_when_python_was_not_chosen(monkeypatch, backend, hinted):
    monkeypatch.setattr(native, "import_module", lambda _: missing_module("omnisus_dbf"))
    monkeypatch.setattr(dbc, "HINT_BYTES", 10)
    log = Recorder()
    monkeypatch.setattr(dbc, "logger", log)
    raw = framed(VECTOR)
    dbc.decompress_bytes(raw, backend=backend)
    hints = [fields for level, event, fields in log.events if level == "info"]
    assert hints == ([{"compressed_bytes": len(raw)}] if hinted else [])
