"""Fixtures shared by the DBF reader tests."""

import pytest

from tests.support.dbf import make_dbf


@pytest.fixture
def native_reads_date(request):
    """omnisus-dbf 0.2.0 (on PyPI, pinned in uv.lock) rejects D fields; native.yml builds
    the wheel from this checkout and runs with --require-rust-dbf, so there it must pass."""
    import omnisus_dbf

    try:
        omnisus_dbf.open_reader(
            make_dbf([("X", "D", 8, 0)], [b" 20240101"]), encoding="latin-1", batch_rows=1
        ).close()
    except omnisus_dbf.UnsupportedDbfError:
        if request.config.getoption("--require-rust-dbf"):
            pytest.fail("--require-rust-dbf: the installed omnisus-dbf rejects D fields")
        pytest.skip("installed omnisus-dbf predates D fields")
