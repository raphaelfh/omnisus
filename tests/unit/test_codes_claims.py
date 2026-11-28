"""A code map is either written as a claim or it is not there (#72).

The maintainer's rule: a field with ``x-decode`` has an authored ``/field/codes`` claim, with
its evidence or, when the map was measured and not read, ``method: fixture-measure``,
``unreviewed`` and an open issue on the field; a map no DEF and no registered document backs
is removed, with an issue saying what was consulted.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
import yaml

import omnisus as sus
from omnisus.metadata import sources_registry
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.cnv import cnv_map, parse_cnv

DICIONARIOS = Path(sus.__file__).parent / "data" / "dicionarios"


def _decoded_fields():
    for path in sorted(DICIONARIOS.glob("*.yaml")):
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
        for field in raw["schema"]["fields"]:
            if field.get("x-decode"):
                yield path.stem, field


@pytest.mark.parametrize(
    ("dataset", "field"), [pytest.param(d, f, id=f"{d}.{f['name']}") for d, f in _decoded_fields()]
)
def test_every_code_map_has_an_authored_codes_claim(dataset, field) -> None:
    claims = (field.get("x-metadata") or {}).get("claims", [])
    (claim,) = [c for c in claims if c["target"] == "/field/codes"]
    if claim["method"] == "fixture-measure":
        issues = (field["x-metadata"]).get("issues", [])
        assert claim["status"] == "unreviewed" and claim["reviewer"] is None
        assert any(i["status"] == "open" for i in issues), "a measured map keeps an open issue"
    else:
        assert claim["evidence"], "a read map cites its source"


def _field(dataset: str, name: str) -> dict:
    raw = yaml.load(
        (DICIONARIOS / f"{dataset}.yaml").read_text(encoding="utf-8"), Loader=yaml.CSafeLoader
    )
    return next(f for f in raw["schema"]["fields"] if f["name"] == name)


@pytest.mark.parametrize(
    ("dataset", "name"),
    [
        ("sim_obitos", "_source_release"),
        ("sih_aih_reduzida", "_source_release"),
    ],
)
def test_a_map_nothing_backs_is_gone(dataset, name) -> None:
    assert "x-decode" not in _field(dataset, name)


ESC2010_IN_THE_DOCUMENT = {
    "0": "Sem escolaridade",
    "1": "Fundamental I (1ª a 4ª série)",
    "2": "Fundamental II (5ª a 8ª série)",
    "3": "Médio (antigo 2º Grau)",
    "4": "Superior incompleto",
    "5": "Superior completo",
    "9": "Ignorado",
}


@pytest.mark.parametrize(("name", "page"), [("esc2010", 2), ("escmae2010", 3)])
def test_esc2010_labels_are_the_ones_the_estrutura_do_sim_writes(name, page) -> None:
    """The maintainer chose the document over the older labels, which no source had (#184)."""
    field = _field("sim_obitos", name)
    assert field["x-decode"] == ESC2010_IN_THE_DOCUMENT
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["evidence"][0]["source_id"], claim["evidence"][0]["pages"]) == (
        "sim-b4195ac8e0f8",
        [page],
    )
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == f"{name}-rotulo-diverge-do-pdf"
    ]
    assert issue["status"] == "resolved" and "1-5 ano" in issue["description"]


@pytest.mark.parametrize(
    ("name", "page"),
    [("assistmed", 4), ("codificado", 6), ("esc2010", 2), ("escmae2010", 3)],
)
def test_a_human_review_against_the_estrutura_do_sim_verifies_the_codes(name, page) -> None:
    """A reviewer compared the map with the Estrutura do SIM, the one document the claim cites."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        ("sim-b4195ac8e0f8", [page]),
    ]
    assert "tabela DO" not in claim["method"]


@pytest.mark.parametrize("name", ["atestante", "tppos"])
def test_a_reviewer_closes_the_conflict_between_the_cnv_and_the_document(name) -> None:
    """`atestante` differs in wording, `tppos` in the codes; `test_sim_cnv_claims` has each."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["method"]) == ("verified_in_source", "cnv-parse")
    issues = field["x-metadata"]["issues"]
    assert issues and all(i["status"] == "resolved" for i in issues)
    assert all("marcelaqs" in i["description"] for i in issues)


SIM_DICIONARIO_2025 = "sim-2177e17cf20b"


@pytest.mark.parametrize(
    ("name", "page"),
    [("origem", 6), ("tpnivelinv", 8), ("morteparto", 8), ("altcausa", 8), ("tp_altera", 9)],
)
def test_a_human_review_against_the_open_data_edition_verifies_the_codes(name, page) -> None:
    """A reviewer compared the map with the Estrutura do SIM of the open data portal."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    assert (SIM_DICIONARIO_2025, [page]) in [
        (e["source_id"], e["pages"]) for e in claim["evidence"]
    ]


def test_tpnivelinv_also_cites_the_dictionary_of_table_dom() -> None:
    field = _field("sim_obitos", "tpnivelinv")
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert ("sim-dom-fb396a277981", [2]) in [
        (e["source_id"], e["pages"]) for e in claim["evidence"]
    ]


SINASC_ESTRUTURA_1996_2019 = "sinasc-0ffc45994687"
SINASC_MANUAL_DA_DN_2022 = "sinasc-5956ea4d8e89"
SINASC_TAB = "sinasc-tab-de43d0c99630"

SINASC_CNV_CONFLICTS_THE_REVIEWER_CLOSED = [
    "origem",
    "estcivmae",
    "escmae",
    "escmae2010",
    "escmaeagr1",
    "racacormae",
    "gestacao",
    "tpmetestim",
    "consultas",
    "kotelchuck",
    "gravidez",
    "parto",
    "stcesparto",
    "tpapresent",
    "tpnascassi",
    "tprobson",
    "sexo",
    "racacor",
    "idanomal",
    "tpfuncresp",
]


@pytest.mark.parametrize("name", SINASC_CNV_CONFLICTS_THE_REVIEWER_CLOSED)
def test_a_sinasc_cnv_conflict_the_reviewer_closed_is_verified(name) -> None:
    """The older map had no claim, so the CNV's stands. The reviewer compared 18 of the 20
    with the Estrutura; it gives no codes for KOTELCHUCK and TPROBSON (p. 2), which she
    compared with the CNV alone."""
    field = _field("sinasc_nascidos_vivos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == "cnv-difere-do-mapa-anterior"
    ]
    assert issue["status"] == "resolved" and "revisora marcelaqs" in issue["description"]
    only_the_cnv = name in ("kotelchuck", "tprobson")
    assert (SINASC_ESTRUTURA_1996_2019 in issue["description"]) is not only_the_cnv


def test_the_manual_of_the_dn_is_registered_with_the_edition_it_declares() -> None:
    """Its catalogue card (p. 3) gives the 4th edition, Ministério da Saúde, Brasília, 2022."""
    (manual,) = [s for s in sources_registry()["sources"] if s["id"] == SINASC_MANUAL_DA_DN_2022]
    assert (manual["edition"], manual["bytes"]) == ("2022", 6188796)


def test_the_tprobson_issue_says_the_cut_offs_are_the_writing_of_the_cnv() -> None:
    """ROBSON.CNV writes ">37sem" and "<36sem" where the older map said "≥ 37" and "< 37"."""
    sinasc = DICIONARIOS / "sources/cnv/sinasc"
    robson = cnv_map(parse_cnv((sinasc / "ROBSON.CNV").read_bytes().decode("latin-1")))
    assert ">37sem" in robson["01"] and "<36sem" in robson["10"]
    field = _field("sinasc_nascidos_vivos", "tprobson")
    assert field["x-decode"] == robson
    (issue,) = field["x-metadata"]["issues"]
    assert all(
        text in issue["description"]
        for text in (
            "≥ 37 sem, TP espontâneo",
            "< 37 sem",
            '">37sem"',
            '"<36sem"',
            "escrita do CNV",
        )
    )


@pytest.mark.parametrize(("name", "page"), [("paridade", 2), ("stdnepidem", 2), ("stdnnova", 2)])
def test_a_sinasc_map_read_from_the_document_is_verified_by_a_reviewer(name, page) -> None:
    field = _field("sinasc_nascidos_vivos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    assert (SINASC_ESTRUTURA_1996_2019, [page]) in [
        (e["source_id"], e["pages"]) for e in claim["evidence"]
    ]


def _labelled_rr_2022(dbc_fixture, name: str) -> Counter[tuple[str, str]]:
    """(code, label) -> rows of DNRR2022.dbc, the whole file (13,091 rows)."""
    raw = dbc_fixture("sinasc_rr_2022_mini").read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset="sinasc_nascidos_vivos").collect()
    return Counter(sus.label("sinasc_nascidos_vivos", frame.select(name), columns=[name]).rows())


def test_stdnnova_takes_the_labels_of_the_document(dbc_fixture) -> None:
    """Every row of DNRR2022.dbc publishes STDNNOVA 1, which the two documents call Sim."""
    assert _labelled_rr_2022(dbc_fixture, "stdnnova") == {("1", "Sim"): 13091}
    field = _field("sinasc_nascidos_vivos", "stdnnova")
    assert field["x-decode"] == {"0": "Não", "1": "Sim"}
    assert all(i["status"] == "resolved" for i in field["x-metadata"]["issues"])


def test_locnasc_5_takes_the_label_of_the_manual_and_the_estrutura(dbc_fixture) -> None:
    """#246, decision 1: lines 56 and 57 of NASCIDO.def bind LOCNASC to LOCOCOR.CNV, whose
    last line is a tabulation catch-all, "Ignorado 0,5,6,7,8,9". The manual of the DN
    (p. 23) writes "5. Aldeia indígena" and the Estrutura (p. 1) "5- Aldeia Indígena", and
    740 of the 13,091 rows of DNRR2022.dbc publish 5. The map is kept by hand: the lines
    of the CNV as the CNV writes them, with 5 in the words of the manual. The claim cites
    the three sources and says which code comes from which; the field left `campos`, so
    this test is what compares the map with the CNV."""
    label = "Aldeia indígena"
    sinasc = DICIONARIOS / "sources/cnv/sinasc"
    lines = (sinasc / "NASCIDO.def").read_text(encoding="latin-1").splitlines()[55:57]
    assert [[part.strip() for part in line.split(",")[1:]] for line in lines] == [
        ["LOCNASC", "1", "LOCOCOR.CNV"]
    ] * 2
    lococor = cnv_map(parse_cnv((sinasc / "LOCOCOR.CNV").read_bytes().decode("latin-1")))
    assert {code for code, text in lococor.items() if text == "Ignorado"} == set("056789")
    assert _labelled_rr_2022(dbc_fixture, "locnasc") == {
        ("1", "Hospital"): 11591,
        ("2", "Outro Estab de Saúde"): 72,
        ("3", "Domicílio"): 606,
        ("4", "Outros"): 81,
        ("5", label): 740,
        ("9", "Ignorado"): 1,
    }
    field = _field("sinasc_nascidos_vivos", "locnasc")
    assert field["x-decode"] == {**lococor, "5": label}
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["method"], claim["status"], claim["reviewer"]) == (
        "cnv-read",
        "verified_in_source",
        "marcelaqs",
    )
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        (SINASC_TAB, []),
        (SINASC_MANUAL_DA_DN_2022, [23]),
        (SINASC_ESTRUTURA_1996_2019, [1]),
    ]
    tabwin, manual, estrutura = (e["locator"] for e in claim["evidence"])
    assert tabwin.endswith("LOCOCOR.CNV") and '"5. Aldeia indígena' in manual
    assert estrutura.endswith('5- Aldeia Indígena."')
    assert all(f"'{code}'" in claim["note"] for code in "05678")
    assert [(i["id"], i["status"]) for i in field["x-metadata"]["issues"]] == [
        ("cnv-difere-do-mapa-anterior", "resolved")
    ]
    vinculos = json.loads((DICIONARIOS / "sources/cnv/vinculos.json").read_text("utf-8"))[
        "datasets"
    ]["sinasc_nascidos_vivos"]
    assert "locnasc" not in vinculos["campos"] and "LOCOCOR.CNV" in vinculos["sem_cnv"]["locnasc"]


def test_sttrabpart_3_stays_unlabelled_until_a_real_file_publishes_it(dbc_fixture) -> None:
    """#246, decision 2: the Estrutura (p. 2, position 52) lists 3, "Não se aplica", for
    STTRABPART; ANOMAL.CNV, which line 161 of NASCIDO.def binds to the field, and the
    manual of the DN (p. 34, field 37) do not, and no row of DNRR2022.dbc publishes 3.
    The map stays the CNV's, verified, and an open issue says where 3 was read."""
    assert _labelled_rr_2022(dbc_fixture, "sttrabpart") == {
        ("1", "Sim"): 1255,
        ("2", "Não"): 11824,
        ("9", "Ign"): 12,
    }
    sinasc = DICIONARIOS / "sources/cnv/sinasc"
    line = (sinasc / "NASCIDO.def").read_text(encoding="latin-1").splitlines()[160]
    assert [part.strip() for part in line.split(",")[1:]] == ["STTRABPART", "1", "ANOMAL.CNV"]
    anomal = cnv_map(parse_cnv((sinasc / "ANOMAL.CNV").read_bytes().decode("latin-1")))
    field = _field("sinasc_nascidos_vivos", "sttrabpart")
    assert field["x-decode"] == anomal and "3" not in anomal
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    replaced, code_3 = field["x-metadata"]["issues"]
    assert (replaced["id"], replaced["status"]) == ("cnv-difere-do-mapa-anterior", "resolved")
    assert (code_3["id"], code_3["status"]) == ("sttrabpart-3-so-no-estrutura", "open")
    assert all(
        text in code_3["description"]
        for text in (
            "'3'",
            "3\u2013 Não se aplica;",
            SINASC_ESTRUTURA_1996_2019,
            SINASC_MANUAL_DA_DN_2022,
            "ANOMAL.CNV",
            "13.091",
        )
    )


def test_paridade_9_stays_unlabelled_until_a_real_file_publishes_it(dbc_fixture) -> None:
    """The Estrutura_SINASC_para_CD.pdf (p. 6) lists 9, ignorado, for PARIDADE; the
    Estrutura of 1996 to 2019 (p. 2) writes only 1 and 0, and no row of DNRR2022.dbc
    publishes 9. The map keeps 0 and 1, and an open issue says where 9 was read."""
    assert _labelled_rr_2022(dbc_fixture, "paridade") == {
        ("0", "Nulípara"): 3739,
        ("1", "Multípara"): 9352,
    }
    field = _field("sinasc_nascidos_vivos", "paridade")
    assert field["x-decode"] == {"0": "Nulípara", "1": "Multípara"}
    (issue,) = field["x-metadata"]["issues"]
    assert (issue["id"], issue["status"]) == ("paridade-9-so-no-estrutura-para-cd", "open")
    assert all(
        text in issue["description"]
        for text in (
            "'9'",
            "sinasc-9ac143d5eae6",
            SINASC_ESTRUTURA_1996_2019,
            '"1 \u2013 Multípara; 0- Nulípara."',
            "13.091",
            "3.739",
            "9.352",
        )
    )


SIA_APAC_WITH_THE_COMMON_BLOCK = [
    "sia_apac_cirurgia_bariatrica",
    "sia_apac_laudos_diversos",
    "sia_apac_medicamentos",
    "sia_apac_quimioterapia",
    "sia_apac_tratamento_dialitico",
]
SIA_APAC_CLOSED_BY_REVIEW = [
    "ap_racacor",
    "ap_ufdif",
    "ap_mndif",
    "ap_tpapac",
    "ap_obito",
    "ap_encerr",
    "ap_perman",
    "ap_alta",
    "ap_transf",
]
SIA_CNV_MAPS_CLOSED_BY_REVIEW = [
    (dataset, name)
    for dataset in SIA_APAC_WITH_THE_COMMON_BLOCK
    for name in SIA_APAC_CLOSED_BY_REVIEW
] + [
    ("sia_apac_medicamentos", "am_transpl"),
    ("sia_psicossocial", "racacor"),
    ("sia_psicossocial", "sit_rua"),
]


def _codes_claim_and_cnv_issue(dataset: str, name: str) -> tuple[dict, dict]:
    metadata = _field(dataset, name)["x-metadata"]
    (claim,) = [c for c in metadata["claims"] if c["target"] == "/field/codes"]
    (issue,) = [i for i in metadata["issues"] if i["id"] == "cnv-difere-do-mapa-anterior"]
    return claim, issue


@pytest.mark.parametrize(("dataset", "name"), SIA_CNV_MAPS_CLOSED_BY_REVIEW)
def test_a_sia_cnv_map_whose_conflict_a_reviewer_closed_is_verified(dataset, name) -> None:
    """The older map had no claim: the claim and the issue both say who closed it and when."""
    claim, issue = _codes_claim_and_cnv_issue(dataset, name)
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert "encerrado em 2026-11-26 pela revisora marcelaqs" in claim["note"]
    assert issue["status"] == "resolved" and "revisora marcelaqs" in issue["description"]


@pytest.mark.parametrize("dataset", SIA_APAC_WITH_THE_COMMON_BLOCK)
def test_the_closed_ap_tpapac_issue_says_the_4_of_the_older_map_has_no_label(dataset) -> None:
    """The older map had a '4' that TP_APAC.CNV does not list: not the same meaning."""
    _, issue = _codes_claim_and_cnv_issue(dataset, "ap_tpapac")
    older, closing = issue["description"].split("Resolvido em 2026-11-26")
    assert "'4' era 'Fora de rede (encerramento)', CNV não lista" in older
    assert "'4'" in closing and "sem fonte" in closing
    assert "4" not in _field(dataset, "ap_tpapac")["x-decode"]


def test_am_gestant_stays_conflicting_because_the_cnv_contradicts_itself(dbc_fixture) -> None:
    """AMRR2401 gives N to every male patient, so N cannot mean pregnant (FIXTURES.md)."""
    claim, issue = _codes_claim_and_cnv_issue("sia_apac_medicamentos", "am_gestant")
    assert (claim["status"], issue["status"]) == ("conflicting", "open")
    assert "GESTANTE.CNV" in issue["description"]
    assert "sia_am_rr_2024_01_mini.dbc" in issue["description"]
    frame = dbc_bytes_to_lazyframe(
        dbc_fixture("sia_am_rr_2024_01_mini").read_bytes(), dataset="sia_apac_medicamentos"
    ).collect()
    counts = Counter(zip(frame["am_gestant"], frame["ap_sexo"], strict=True))
    assert counts == {("N", "F"): 1234, ("N", "M"): 841, ("S", "F"): 8}
    assert _field("sia_apac_medicamentos", "ap_sexo")["x-decode"]["M"] == "Masculino"
    for quoted in ("2.083 linhas", "'N' em 2.075", "'S' em 8", "1.234", "841"):
        assert quoted in issue["description"]
