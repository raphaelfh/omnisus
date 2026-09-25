"""End-to-end: BPA-I fixture -> generic runner -> lake -> query.

Uses the runner directly (not a public ``import_sia_bpa_individualizado`` wrapper) because
``omnisus/__init__.py`` currently carries unrelated uncommitted work;
the public wrapper lands separately.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp._runner import import_scope
from tests.support import fake_datasus


@pytest.mark.integration
def test_import_sia_bpa_individualizado_monthly(monkeypatch, tmp_path: Path, dbc_fixture) -> None:
    fixture_bytes = dbc_fixture("sia_bi_rr_2024_01_mini").read_bytes()
    fake_datasus.serve(
        monkeypatch, "sia_bpa_individualizado", {ScopeKey(uf="RR", ano=2024, mes=1): fixture_bytes}
    )

    target = f"ducklake:{tmp_path}/test.ducklake"
    lake = Lake.local(target)
    result = asyncio.run(
        import_scope(
            dataset="sia_bpa_individualizado", scope=ScopeKey(uf="RR", ano=2024, mes=1), lake=lake
        )
    )
    assert result.rows == 12_099

    con = lake.connect()
    rows = con.execute(
        "SELECT count(*) FROM lake.sia_bpa_individualizado WHERE ano=2024 AND uf='RR' AND mes=1"
    ).fetchone()[0]
    assert rows == 12_099
    # linkage key survived the trip into the lake
    non_blank = con.execute(
        "SELECT count(*) FROM lake.sia_bpa_individualizado WHERE trim(cns_pac) != ''"
    ).fetchone()[0]
    assert non_blank > 11_000
    lake.close()
