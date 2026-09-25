"""Names that start with a row's prefix but are national aggregates, from real listings."""

from __future__ import annotations

from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.filenames import national_variant, parse_name
from tests.support.listings import listing_lines


def _names(fixture: str) -> list[str]:
    return [" ".join(line.split()[3:]) for line in listing_lines(fixture)]


def test_every_prefix_name_that_does_not_decode_is_a_national_variant() -> None:
    for fixture, row in [
        ("sim_cid10_dores", REGISTRY["sim_obitos"]),
        ("sinasc_1996_dados_dnres", REGISTRY["sinasc_nascidos_vivos"]),
        ("sinasc_prelim_dnres", REGISTRY["sinasc_nascidos_vivos"]),
    ]:
        unexplained = [
            name
            for name in _names(fixture)
            if name.upper().startswith(row.prefix)
            and parse_name(row, name) is None
            and not national_variant(row, name)
        ]
        assert unexplained == [], (fixture, unexplained[:5])


def test_known_national_names() -> None:
    sinasc = REGISTRY["sinasc_nascidos_vivos"]
    assert national_variant(REGISTRY["sim_obitos"], "DOBR2022.dbc")
    assert national_variant(sinasc, "DNEX2025.dbc")
    assert not national_variant(sinasc, "DNRR2023.dbc")
    assert not national_variant(REGISTRY["sia_bpa_individualizado"], "BIBR2401.dbc")


def test_national_variant_accepts_two_digit_year() -> None:
    """The live SINASC/PRELIM/DNRES directory carries DNEX25.dbc beside
    DNEX2025.dbc and DNEX2026.dbc (confirmed live 2026-09-21): DATASUS is
    inconsistent about the year width for this family."""
    assert national_variant(REGISTRY["sinasc_nascidos_vivos"], "DNEX25.dbc")
