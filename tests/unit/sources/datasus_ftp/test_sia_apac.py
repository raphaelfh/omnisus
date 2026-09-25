"""Tests for the APAC family datasets (AM, AQ, ATD, AD, ABO) + RAAS-PS.

Stress scenarios these tests encode (all field-measured, 2026-08):

- prefix ambiguity: AM/AQ/AD are 2-letter, ATD/ABO are 3-letter; the
  monthly filename regex must backtrack correctly (AMRR2401 is AM+RR,
  ATDRR2401 is ATD+RR, ABOSP2401 is ABO+SP — never AB+OS).
- ABO schema drift: 86 header fields of which 8 are UNNAMED trailers that
  dbfread2 silently drops (78 parsed columns), and the AP_* core uses
  variant names (AP_TPPRE, AP_APACAN, AP_DTOOCOR, CO_CIDPRIM).
- expected record counts come from each fixture's DBF header (nrec),
  independently verified against parsed rows by the integrity gate.
"""

from __future__ import annotations

import pytest

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY, resolve
from omnisus.sources.datasus_ftp.filenames import decode_for
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario
from tests.support.datasus_names import filename_for

# dataset -> (fixture name, measured nrec, measured parsed column floor)
FIXTURES = {
    "sia_apac_medicamentos": ("sia_am_rr_2024_01_mini", 2_083, 51),
    "sia_apac_quimioterapia": ("sia_aq_rr_2024_01_mini", 17, 74),
    "sia_apac_tratamento_dialitico": ("sia_atd_rr_2024_01_mini", 358, 65),
    "sia_apac_laudos_diversos": ("sia_ad_rr_2024_01_mini", 678, 46),
    "sia_apac_cirurgia_bariatrica": ("sia_abo_sp_2024_01_mini", 844, 78),
    "sia_psicossocial": ("sia_ps_rr_2024_01_mini", 1_670, 45),
}


# ---------------------------------------------------------------------------
# inventory: prefix ambiguity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "dataset", "uf"),
    [
        ("AMRR2401.dbc", "sia_apac_medicamentos", "RR"),
        ("AQRR2401.dbc", "sia_apac_quimioterapia", "RR"),
        ("ADRR2401.dbc", "sia_apac_laudos_diversos", "RR"),
        ("ATDRR2401.dbc", "sia_apac_tratamento_dialitico", "RR"),  # 3-letter, backtrack from ATDR
        ("ABOSP2401.dbc", "sia_apac_cirurgia_bariatrica", "SP"),  # 3-letter, never AB+OS
        ("PSRR2401.dbc", "sia_psicossocial", "RR"),
        ("BIRR2401.dbc", "sia_bpa_individualizado", "RR"),  # regression: BI still parses
        ("RDRR2401.dbc", "sih_aih_reduzida", "RR"),  # regression: SIH untouched
    ],
)
def test_decode_for_disambiguates_prefixes(filename: str, dataset: str, uf: str) -> None:
    scope = decode_for(REGISTRY[dataset], filename)
    assert scope == ScopeKey(uf=uf, ano=2024, mes=1)


@pytest.mark.parametrize("dataset", list(FIXTURES))
def test_scope_roundtrip(dataset: str) -> None:
    scope = ScopeKey(uf="RR", ano=2024, mes=1)
    filename = filename_for(resolve(dataset), scope)
    back_scope = decode_for(REGISTRY[dataset], filename)
    assert back_scope == scope


# ---------------------------------------------------------------------------
# registry + dicionários
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dataset", list(FIXTURES))
def test_registry_monthly_uf_partition(dataset: str) -> None:
    cfg = resolve(dataset)
    assert cfg.monthly is True
    assert cfg.partition_by == ("ano", "uf", "mes")


@pytest.mark.parametrize("dataset", list(FIXTURES))
def test_dicionario_latin1_and_cns_marker(dataset: str) -> None:
    dic = load_dicionario(dataset)
    assert dic.encoding == "latin-1"
    crypto = [f["name"] for f in dic.fields if f.get("x-crypto") == "datasus-cns"]
    assert crypto, f"{dataset}: no field marked x-crypto datasus-cns"


def test_apac_core_shares_linkage_fields() -> None:
    """Every APAC dicionário exposes the person/clinical core (variant-aware)."""
    for dataset in (
        "sia_apac_medicamentos",
        "sia_apac_quimioterapia",
        "sia_apac_tratamento_dialitico",
        "sia_apac_laudos_diversos",
    ):
        names = {f["name"] for f in load_dicionario(dataset).fields}
        assert {"ap_cnspcn", "ap_cidpri", "ap_pripal", "ap_obito", "ap_ceppcn"} <= names
    # ABO variant core
    abo = {f["name"] for f in load_dicionario("sia_apac_cirurgia_bariatrica").fields}
    assert {"ap_cnspcn", "co_cidprim", "ab_numaih"} <= abo


# ---------------------------------------------------------------------------
# parse: real fixtures, exact header counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("dataset", "spec"), FIXTURES.items())
def test_parse_fixture_exact_counts(dataset: str, spec, dbc_fixture) -> None:
    fixture, nrec, min_cols = spec
    uf = "SP" if "sp" in fixture else "RR"
    df = dbc_bytes_to_lazyframe(
        dbc_fixture(fixture).read_bytes(), dataset=dataset, ano=2024, uf=uf
    ).collect()
    assert df.height == nrec
    assert len(df.columns) >= min_cols + 2  # +ano +uf
    assert df["uf"].unique().to_list() == [uf]


def test_abo_unnamed_trailer_fields_are_dropped(dbc_fixture) -> None:
    """86 header fields, 8 unnamed -> exactly 78 data columns (+ano/uf)."""
    df = dbc_bytes_to_lazyframe(
        dbc_fixture("sia_abo_sp_2024_01_mini").read_bytes(),
        dataset="sia_apac_cirurgia_bariatrica",
        ano=2024,
        uf="SP",
    ).collect()
    assert len(df.columns) == 78 + 2
    assert "ab_numaih" in df.columns
    # gold-standard bridge: every row carries a 13-digit AIH number
    aihs = [v for v in df["ab_numaih"].to_list() if v and v.strip()]
    assert len(aihs) == df.height
    assert all(len(v.strip()) == 13 for v in aihs)


def test_am_dates_and_competencia_formats(dbc_fixture) -> None:
    df = dbc_bytes_to_lazyframe(
        dbc_fixture("sia_am_rr_2024_01_mini").read_bytes(), dataset="sia_apac_medicamentos"
    ).collect()
    assert df["ap_cmp"].head(50).str.len_chars().unique().to_list() == [6]  # AAAAMM
    inic = [v for v in df["ap_dtinic"].head(100).to_list() if v and v.strip()]
    assert all(len(v) == 8 and v[:2] in ("19", "20") for v in inic)  # AAAAMMDD
