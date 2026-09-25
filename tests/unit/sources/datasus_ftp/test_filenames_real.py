"""The codec against real DATASUS listings (tests/fixtures/listings)."""

from __future__ import annotations

from omnisus.sources._base import ALL_UFS, ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.filenames import SourceName, decode_for, parse_name
from tests.support.listings import listing_lines

BI = REGISTRY["sia_bpa_individualizado"]
SIM = REGISTRY["sim_obitos"]
SINASC = REGISTRY["sinasc_nascidos_vivos"]


def _names(fixture: str) -> list[str]:
    return [" ".join(line.split()[3:]) for line in listing_lines(fixture)]


def test_numeric_parts_decode_to_the_same_scope_with_their_part() -> None:
    names = _names("siasus_200801_dados")
    assert "BIMG2412_1.dbc" in names and "BIMG2412_2.dbc" in names
    scope = ScopeKey(uf="MG", ano=2024, mes=12)
    assert parse_name(BI, "BIMG2412_1.dbc") == SourceName(scope=scope, part="1")
    assert parse_name(BI, "BIMG2412_2.dbc") == SourceName(scope=scope, part="2")
    assert parse_name(BI, "BIMG2401.dbc") == SourceName(scope=ScopeKey("MG", 2024, 1), part=None)


def test_letter_parts_decode_with_a_lowercase_part() -> None:
    from dataclasses import replace

    assert "PASP2401a.dbc" in _names("siasus_200801_dados")
    pa = replace(BI, name="sia_pa_probe", prefix="PA")
    assert parse_name(pa, "PASP2401a.dbc") == SourceName(ScopeKey("SP", 2024, 1), part="a")
    assert parse_name(pa, "PASP2401A.dbc") is None  # one lowercase letter


def test_decode_for_keeps_returning_the_scope_for_whole_files_and_parts() -> None:
    assert decode_for(BI, "BIMG2412_2.dbc") == ScopeKey("MG", 2024, 12)
    assert decode_for(BI, "BIMG2401.dbc") == ScopeKey("MG", 2024, 1)


def test_national_files_are_not_states() -> None:
    assert "DOBR2022.dbc" in _names("sim_cid10_dores")
    assert parse_name(SIM, "DOBR2022.dbc") is None
    assert "DNEX2025.dbc" in _names("sinasc_prelim_dnres")
    assert parse_name(SINASC, "DNEX2025.dbc") is None
    assert parse_name(SINASC, "DNBR2023.dbc") is None


def test_every_decoded_state_is_a_uf_in_every_real_listing() -> None:
    for fixture, row in [
        ("siasus_200801_dados", BI),
        ("sim_cid10_dores", SIM),
        ("sinasc_1996_dados_dnres", SINASC),
        ("sinasc_prelim_dnres", SINASC),
    ]:
        decoded = [parse_name(row, name) for name in _names(fixture)]
        assert {n.scope.uf for n in decoded if n is not None} <= set(ALL_UFS), fixture


def test_shorter_prefixes_do_not_swallow_longer_families() -> None:
    am = REGISTRY["sia_apac_medicamentos"]
    atd = REGISTRY["sia_apac_tratamento_dialitico"]
    for name in _names("siasus_200801_dados"):
        if name.upper().startswith("ATD"):
            assert parse_name(am, name) is None, name
            assert parse_name(atd, name) is not None, name


def _row(**kw):
    from omnisus.sources.datasus_ftp.datasets import Dataset

    base = {"cadence": "yearly", "partition_by": ("ano", "uf"), "coverage": ((1979, 1), None)}
    return Dataset(**(base | kw))


def test_sim_subsets_are_national_files_without_a_code() -> None:
    """SIM/CID10/DOFET: DOEXT96.dbc … DOEXT25.dbc, PREFIX + YY with no BR."""
    names = _names("sim_cid10_dofet")
    ext = _row(
        name="probe_ext",
        prefix="DOEXT",
        ftp_dir="/dissemin/publicos/SIM/CID10/DOFET",
        partition_by=("_source_ano",),
        geography="national",
        national_code="",
    )
    decoded = sorted(s.ano for n in names if (s := decode_for(ext, n)) is not None)
    assert decoded == list(range(1996, 2026))
    assert any(n.upper().startswith("DOREXT") for n in names)  # another family


def test_two_digit_years_decode_for_yearly_state_rows() -> None:
    """SIM/CID9/DORES: DORRR79.DBC … (DOR + UF + YY); DORBR79 is Brazil, not a state."""
    names = _names("sim_cid9_dores")
    cid9 = _row(
        name="probe_cid9", prefix="DOR", ftp_dir="/dissemin/publicos/SIM/CID9/DORES", year_digits=2
    )
    decoded = [s for n in names if (s := decode_for(cid9, n)) is not None]
    assert len(decoded) == 466 - 17
    assert {s.ano for s in decoded} == set(range(1979, 1996))
    assert decode_for(cid9, "DORRR79.DBC") == ScopeKey("RR", 1979)
    assert decode_for(cid9, "DORBR79.dbc") is None


def test_four_digit_years_still_decode_beside_national_files() -> None:
    """SINASC/1994_1995/Dados/DNRES: DNRRR1994.dbc; DNBR1994.dbc is another prefix."""
    names = _names("sinasc_1994_1995_dnres")
    dnr = _row(
        name="probe_dnr", prefix="DNR", ftp_dir="/dissemin/publicos/SINASC/1994_1995/Dados/DNRES"
    )
    decoded = [s for n in names if (s := decode_for(dnr, n)) is not None]
    assert len(decoded) == 54 and {s.ano for s in decoded} == {1994, 1995}


def test_the_six_sia_families_decode_every_listed_name() -> None:
    """SIASUS/200801_/Dados on 2026-09-23: every AB, ACF, AMP, AN, AR and SAD name is read
    by exactly one row, and each row's coverage is its first and last listed month."""
    rows = [  # AB, ACF, AMP, AN, AR, SAD
        ("sia_apac_acompanhamento_bariatrica", 635, (2008, 1), (2025, 7)),
        ("sia_apac_fistula_arteriovenosa", 3768, (2014, 8), (2026, 7)),
        ("sia_apac_acompanhamento_multiprofissional", 891, (2016, 3), (2026, 7)),
        ("sia_apac_nefrologia", 2145, (2008, 1), (2014, 10)),
        ("sia_apac_radioterapia", 5465, (2008, 1), (2026, 7)),
        ("sia_atencao_domiciliar", 1088, (2012, 4), (2018, 10)),
    ]
    names = _names("siasus_200801_dados_apac_sad")
    assert len(names) == sum(count for _, count, _, _ in rows)
    sia = [r for r in REGISTRY.values() if r.ftp_dir == BI.ftp_dir]
    for name, count, first, last in rows:
        row = REGISTRY[name]
        scopes = [s for n in names if (s := decode_for(row, n)) is not None]
        assert len(scopes) == count, name
        months = sorted((s.ano, s.mes) for s in scopes)
        assert (months[0], months[-1]) == (first, last), name
        assert row.coverage == (first, None if last == (2026, 7) else last), name
    for n in names:
        assert sum(decode_for(r, n) is not None for r in sia) == 1, n
