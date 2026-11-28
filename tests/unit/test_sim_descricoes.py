"""Every `sim_obitos` field says what the official layout documents say about it (#184).

Four documents of `sources/registry.json` were read page by page: the Estrutura do SIM of
07/2025 (`sim-b4195ac8e0f8`) and of 12/2019 (`sim-b014389eca62`), the structure of the 2006
file (`sim-anterior-13cabba0b9a1`) and the dictionary of the DOM table
(`sim-dom-fb396a277981`). A field with no description before #184 takes the text of the
07/2025 edition with a `/field/description` claim that cites the page; six fields that
edition leaves blank or out take the text of the document that describes them. The reading
was made by an agent, so every claim is `unreviewed` with no reviewer. A field none of the
four describes keeps `description: null` with a `not_found` claim, which needs the same
evidence as a description (AGENTS.md rule 1).
"""

from __future__ import annotations

import pytest

import omnisus as sus
from omnisus.metadata import sources_registry
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.library_columns import library_columns
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

ESTRUTURA_2025 = "sim-b4195ac8e0f8"
ESTRUTURA_2019 = "sim-b014389eca62"
ESTRUTURA_2025_OPEN_DATA = "sim-2177e17cf20b"
ESTRUTURA_2006 = "sim-anterior-13cabba0b9a1"
DICIONARIO_DOM = "sim-dom-fb396a277981"
EVERY_PAGE = list(range(1, 10))

# Field -> the page of the Estrutura do SIM 2025 whose "Descrição" column describes it.
DESCRIBED = {
    **dict.fromkeys(["tipobito", "dtobito", "horaobito", "natural", "codmunnatu", "dtnasc"], 1),
    **dict.fromkeys(["idade", "sexo", "racacor", "estciv", "esc2010", "seriescfal"], 2),
    **dict.fromkeys(
        [
            "codmunres",
            "lococor",
            "codmunocor",
            "idademae",
            "escmae2010",
            "seriescmae",
            "ocupmae",
            "qtdfilvivo",
            "qtdfilmort",
        ],
        3,
    ),
    **dict.fromkeys(
        [
            "semagestac",
            "gravidez",
            "parto",
            "obitoparto",
            "peso",
            "tpmorteoco",
            "assistmed",
            "necropsia",
        ],
        4,
    ),
    **dict.fromkeys(
        [
            "linhaii",
            "causabas",
            "atestante",
            "comunsvoim",
            "dtatestado",
            "circobito",
            "acidtrab",
            "fonte",
            "esc",
        ],
        5,
    ),
    **dict.fromkeys(
        [
            "escmae",
            "obitograv",
            "obitopuerp",
            "exame",
            "cirurgia",
            "causabas_o",
            "numerolote",
            "dtinvestig",
            "dtcadastro",
            "stcodifica",
            "codificado",
            "versaosist",
            "versaoscb",
            "fonteinv",
            "dtrecebim",
            "atestado",
            "dtrecoriga",
            "opor_do",
            "causamat",
        ],
        6,
    ),
    **dict.fromkeys(
        [
            "escmaeagr1",
            "escfalagr1",
            "stdoepidem",
            "stdonova",
            "difdata",
            "nudiasobco",
            "dtcadinv",
            "dtconinv",
        ],
        7,
    ),
    **dict.fromkeys(
        [
            "fontes",
            "tpresginfo",
            "tpnivelinv",
            "dtcadinf",
            "morteparto",
            "dtconcaso",
            "altcausa",
            "tppos",
        ],
        8,
    ),
    **dict.fromkeys(["gestacao", "cb_alt"], 9),
}

# Blank in the 07/2025 edition (origem, tpobitocor) or absent from it -> the document and
# the page that describe the field.
DESCRIBED_ELSEWHERE = {
    "origem": (ESTRUTURA_2019, 6),
    "tpobitocor": (ESTRUTURA_2019, 8),
    "cb_pre": (ESTRUTURA_2019, 9),
    "numerodo": (ESTRUTURA_2006, 1),
    "ufinform": (ESTRUTURA_2006, 4),
    "nudiasobin": (DICIONARIO_DOM, 2),
}

# In no row of the four documents.
NOT_LISTED = ["contador", "estabdescr", "fontesinf", "nudiasinf"]

# Described before #184 in the maintainers' words, with no claim. Each says something the
# documents do not (the CBO eras, the `aux_cnes` lookup, the `*J189*A419` form), so it stays.
AUTHORED_BEFORE = ["ocup", "codestab", "linhaa", "linhab", "linhac", "linhad"]

# Columns the import adds; the document is about the DBF.
ADDED_BY_THE_IMPORT = [c.name for c in library_columns(REGISTRY["sim_obitos"])]


def _columns() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def _description_claim(column: dict) -> dict:
    (claim,) = [c for c in column["claims"] if c["target"] == "/field/description"]
    return claim


def test_every_field_is_in_exactly_one_group() -> None:
    groups = [
        *DESCRIBED,
        *DESCRIBED_ELSEWHERE,
        "tp_altera",
        *NOT_LISTED,
        *AUTHORED_BEFORE,
        *ADDED_BY_THE_IMPORT,
    ]
    assert sorted(groups) == sorted(_columns())


@pytest.mark.parametrize(
    ("name", "source", "page"),
    [
        *((name, ESTRUTURA_2025, page) for name, page in sorted(DESCRIBED.items())),
        *((name, *where) for name, where in sorted(DESCRIBED_ELSEWHERE.items())),
    ],
)
def test_a_described_field_cites_the_page_and_has_no_reviewer(name, source, page) -> None:
    column = _columns()[name]
    claim = _description_claim(column)
    assert column["field"]["description"]
    assert (claim["status"], claim["reviewer"]) == ("unreviewed", None)
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [(source, [page])]


@pytest.mark.parametrize(
    ("name", "pages_2025"),
    # tp_altera: page 9 of the 07/2025 edition lists its codes and does not say what it is.
    [("tp_altera", [9]), *((name, EVERY_PAGE) for name in NOT_LISTED)],
)
def test_a_field_no_document_describes_is_not_found(name, pages_2025) -> None:
    column = _columns()[name]
    claim = _description_claim(column)
    assert column["field"]["description"] is None
    assert (claim["status"], claim["reviewer"]) == ("not_found", None)
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        (ESTRUTURA_2025, pages_2025),
        (ESTRUTURA_2019, EVERY_PAGE),
        (ESTRUTURA_2006, list(range(1, 8))),
        (DICIONARIO_DOM, list(range(1, 9))),
    ]


def _open_issue(name: str, issue: str) -> dict:
    (found,) = [i for i in _columns()[name]["issues"] if i["id"] == issue]
    assert found["status"] == "open"
    return found


@pytest.mark.parametrize("fixture", ["sim_rr_2022_mini", "sim_rr_2023_mini"])
def test_horaobito_is_four_digits_where_the_document_says_five_characters(
    dbc_fixture, fixture
) -> None:
    """Real data: DORR2022 and DORR2023 write HHMM, the document says `00:00` in 5 characters."""
    frame = dbc_bytes_to_lazyframe(
        dbc_fixture(fixture).read_bytes(), dataset="sim_obitos"
    ).collect()
    values = {v for v in frame["horaobito"].to_list() if v}
    assert values and all(len(v) == 4 and v.isdigit() for v in values)
    assert "HHMM" in _open_issue("horaobito", "horaobito-formato-diverge-do-pdf")["description"]


def test_nudiasobco_label_says_what_the_documents_say() -> None:
    """Three documents describe NUDIASOBCO as days to the conclusion of the investigation."""
    column = _columns()["nudiasobco"]
    assert column["field"]["label"] == "Dias óbito-conclusão da investigação"
    assert "conclusão da investigação" in column["field"]["description"]
    assert not column["issues"]


SIM_FIXTURES = [
    "sim_rr_2022_mini",
    "sim_rr_2023_mini",
    "sim_doext_br_2023_excerpt",
    "sim_doinf_br_2023_excerpt",
    "sim_domat_br_2023_mini",
]


def _values(dbc_fixture, fixture: str, name: str) -> set[str]:
    frame = dbc_bytes_to_lazyframe(
        dbc_fixture(fixture).read_bytes(), dataset="sim_obitos"
    ).collect()
    return {v for v in frame[name].to_list() if v}


@pytest.mark.parametrize("fixture", SIM_FIXTURES)
def test_tppos_is_s_or_n_where_the_document_says_1_or_2(dbc_fixture, fixture) -> None:
    """Real data: the files write the keys of INVESTIG.CNV, not the codes of the document."""
    assert _values(dbc_fixture, fixture, "tppos") == {"S", "N"}
    codes = {c["value"] for c in _columns()["tppos"]["field"]["codes"]}
    assert {"S", "N"} <= codes and not {"1", "2"} & codes
    (issue,) = [
        i for i in _columns()["tppos"]["issues"] if i["id"] == "tppos-codigos-divergem-do-pdf"
    ]
    assert "INVESTIG.CNV" in issue["description"]


@pytest.mark.parametrize("fixture", SIM_FIXTURES)
def test_codestab_is_seven_digits_where_the_document_says_eight(dbc_fixture, fixture) -> None:
    """Real data: every CODESTAB that is filled has 7 digits; the document declares 8."""
    values = _values(dbc_fixture, fixture, "codestab")
    assert values and all(len(v) == 7 and v.isdigit() for v in values)
    issue = _open_issue("codestab", "codestab-tamanho-diverge-do-pdf")["description"]
    assert "8 caracteres" in issue and "C(07)" in issue


def test_origem_codes_cite_the_edition_that_writes_them_as_the_map_does() -> None:
    """The 12/2019 edition writes 1, 2, 3 and 9; those of 06/2025 and 07/2025 write 01, 02, 03."""
    (claim,) = [c for c in _columns()["origem"]["claims"] if c["target"] == "/field/codes"]
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        (ESTRUTURA_2019, [6]),
        (ESTRUTURA_2025, [5]),
        (ESTRUTURA_2025_OPEN_DATA, [6]),
    ]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    editions = {s["id"]: s["edition"] for s in sources_registry()["sources"]}
    assert all(editions[e["source_id"]] in claim["note"] for e in claim["evidence"])


def test_the_open_data_edition_is_registered_with_the_month_it_declares() -> None:
    """Every page of Dicionario_SIM_2025.pdf says "Arquivo atualizado em 06/2025"."""
    (source,) = [s for s in sources_registry()["sources"] if s["id"] == ESTRUTURA_2025_OPEN_DATA]
    assert source["edition"] == "06/2025"


def test_the_2006_structure_is_registered_with_both_layouts() -> None:
    """Estrutura_SIM_Anterior.pdf holds the 2006 layout (p. 1-4) and the one up to 2005 (p. 5-7)."""
    (source,) = [s for s in sources_registry()["sources"] if s["id"] == ESTRUTURA_2006]
    assert "2005" in source["title"] and "2006" in source["title"]
    assert source["edition"] == "2006 e até 2005"
