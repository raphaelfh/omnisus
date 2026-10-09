"""RD from 2008: the dictionary declares every field the layouts of real files publish (#86).

The census of `SIHSUS/200801_/Dados` (evidence/2026-10-06-rd-2008-layouts) finds layout 5
from 2014-01 and layout 6 from 2025-03, which adds FONTE_ORC. One fixture of each layout:
RDRR2401 and an excerpt of RDRR2503.
"""

from __future__ import annotations

import pytest
from scripts.gen_dicionario import fields_of

from omnisus.sources.datasus_ftp import dbc
from omnisus.transforms.dictionaries import load_dicionario

DATASET = "sih_aih_reduzida"
LAYOUTS = {"sih_rr_2024_01_mini": 5, "sih_rd_rr_2025_03_excerpt": 6}


def fixture_fields(dbc_fixture, fixture: str) -> dict[str, str]:
    raw = dbc_fixture(fixture).read_bytes()
    return {f["name"]: f["type"] for f in fields_of(dbc.decompress_bytes(raw))}


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_every_field_of_the_layout_is_declared(dbc_fixture, fixture):
    declared = {f["name"] for f in load_dicionario(DATASET).fields}
    assert sorted(set(fixture_fields(dbc_fixture, fixture)) - declared) == []


def test_fonte_orc_is_declared_with_the_generator_type_and_no_labels(dbc_fixture):
    """No DEF of TAB_SIH.zip cites FONTE_ORC, so the field has no code map, and its issue
    says what was consulted."""
    published = fixture_fields(dbc_fixture, "sih_rd_rr_2025_03_excerpt")
    field = load_dicionario(DATASET).field_def("fonte_orc")
    assert field is not None
    assert field["type"] == published["fonte_orc"]
    assert "x-decode" not in field
    (issue,) = [i for i in field["x-metadata"]["issues"] if i["id"] == "fonte_orc-sem-fonte"]
    assert issue["status"] == "open"
