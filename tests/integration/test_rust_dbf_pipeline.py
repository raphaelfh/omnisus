"""Native parser exercised through real scope publication and transaction rollback."""

import pytest

from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp import parse
from omnisus.sources.datasus_ftp._runner import ingest_raw
from omnisus.sources.datasus_ftp.datasets import resolve
from tests.support.dbf import make_dbf
from tests.support.listings import listed

pytestmark = [pytest.mark.integration, pytest.mark.rust_dbf]


def test_backend_change_keeps_skip_same_and_replace_is_atomic(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    dataset = resolve("sim_obitos")
    rr = ScopeKey(uf="RR", ano=2023)
    sp = ScopeKey(uf="SP", ano=2023)
    with Lake.local(f"ducklake:{tmp_path}/native.ducklake") as lake:
        monkeypatch.setenv("OMNISUS_DBF_BACKEND", "python")
        first = ingest_raw(dataset, rr, listed(dataset, rr, raw), lake, run_id="first")
        monkeypatch.setenv("OMNISUS_DBF_BACKEND", "rust")
        assert ingest_raw(dataset, rr, listed(dataset, rr, raw), lake, policy="skip_same") is None
        assert len(lake.publications()) == 1
        other = ingest_raw(dataset, sp, listed(dataset, sp, raw), lake)
        replaced = ingest_raw(dataset, rr, listed(dataset, rr, raw), lake, policy="replace")
        assert first.rows == other.rows == replaced.rows == 3311
        assert lake.connect().execute(
            "SELECT uf,count(*) FROM lake.sim_obitos GROUP BY uf ORDER BY uf"
        ).fetchall() == [("RR", 3311), ("SP", 3311)]
        before = lake.publications()
        with pytest.raises(RuntimeError), lake.transaction():
            ingest_raw(
                dataset, rr, listed(dataset, rr, raw), lake, policy="replace", run_id="rolled-back"
            )
            raise RuntimeError("abort")
        assert lake.publications() == before
        assert lake.publications(run_id="rolled-back") == []


def test_late_native_parse_error_preserves_prior_publication(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    dataset = resolve("sim_obitos")
    scope = ScopeKey(uf="RR", ano=2023)
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "rust")
    with Lake.local(f"ducklake:{tmp_path}/native.ducklake") as lake:
        ingest_raw(dataset, scope, listed(dataset, scope, raw), lake)
        before = lake.publications()
        broken = make_dbf([("X", "N", 3, 0)], [b" 123", b" bad"])
        monkeypatch.setattr(parse, "BATCH_ROWS", 1)
        monkeypatch.setattr("omnisus.sources.datasus_ftp.dbc.decompress_bytes", lambda _: broken)
        with pytest.raises(ValueError):
            ingest_raw(dataset, scope, listed(dataset, scope, b"changed"), lake, policy="replace")
        assert lake.connect().execute("SELECT count(*) FROM lake.sim_obitos").fetchone() == (3311,)
        assert lake.publications() == before
