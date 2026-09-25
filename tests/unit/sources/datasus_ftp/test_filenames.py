"""Tests for DATASUS FTP filename / ScopeKey conversion."""

from __future__ import annotations

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY, resolve
from omnisus.sources.datasus_ftp.filenames import decode_for
from tests.support.datasus_names import filename_for


def test_decode_for_sim_obitos() -> None:
    scope = decode_for(REGISTRY["sim_obitos"], "DOSP2024.dbc")
    assert scope == ScopeKey(uf="SP", ano=2024)


def test_decode_for_sih_aih_reduzida_monthly() -> None:
    scope = decode_for(REGISTRY["sih_aih_reduzida"], "RDSP2401.dbc")
    assert scope == ScopeKey(uf="SP", ano=2024, mes=1)


def test_filename_for_sim() -> None:
    name = filename_for(resolve("sim_obitos"), ScopeKey(uf="SP", ano=2024))
    assert name == "DOSP2024.dbc"


def test_filename_for_sih_monthly() -> None:
    name = filename_for(resolve("sih_aih_reduzida"), ScopeKey(uf="SP", ano=2024, mes=1))
    assert name == "RDSP2401.dbc"


def test_decode_for_returns_scope_for_known_names() -> None:
    assert decode_for(REGISTRY["sim_obitos"], "DOSP2024.dbc") == ScopeKey(uf="SP", ano=2024)
    assert decode_for(REGISTRY["sia_apac_tratamento_dialitico"], "ATDRR2401.dbc") == ScopeKey(
        uf="RR", ano=2024, mes=1
    )


def test_decode_for_returns_none_for_unmodelled_prefixes() -> None:
    """SIASUS/200801_/Dados also holds PA*, SAD* and others we do not model —
    available() must skip them, not raise."""
    assert decode_for(REGISTRY["sia_apac_medicamentos"], "PARR2401.dbc") is None
    assert decode_for(REGISTRY["sia_apac_medicamentos"], "SADRR2401.dbc") is None


def test_decode_for_returns_none_for_non_dbc_and_junk() -> None:
    d = REGISTRY["sim_obitos"]
    for name in ("readme.txt", "base_aih1.duck", "", "DO.dbc", "199407_200712"):
        assert decode_for(d, name) is None, name


def test_decode_for_agrees_with_filename_for_round_trip() -> None:
    d = REGISTRY["sih_aih_reduzida"]
    scope = ScopeKey(uf="SP", ano=2024, mes=1)
    assert decode_for(d, filename_for(d, scope)) == scope
