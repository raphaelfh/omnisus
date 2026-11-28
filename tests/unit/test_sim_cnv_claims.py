"""A `sim_obitos` map read from the CNV is verified, even where an older map differed (#184).

`gerar_decode_cnv.py` marks a claim `conflicting` when the map it replaces disagreed with
the CNV. The older maps had no claim, so the disagreement is history: the claim is
`verified_in_source` and the issue that keeps the older labels is `resolved`, as in
`sih_aih_reduzida`. Two fields were closed by a reviewer instead. The Estrutura do SIM calls
`atestante` 1 "Assistente" where the CNV says "Sim": other words, which the reviewer reads as
the same answer. It gives `tppos` the codes 1 and 2 where the files write S and N: other
codes, and the files decide. Each resolved issue keeps the text of the previous map.
"""

from __future__ import annotations

import pytest

import omnisus as sus

ISSUE = "cnv-difere-do-mapa-anterior"


def _columns() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def _replaced_maps() -> dict[str, tuple[dict, dict]]:
    found = {}
    for column in _columns().values():
        issues = [i for i in column["issues"] if i["id"] == ISSUE]
        if issues:
            (claim,) = [c for c in column["claims"] if c["target"] == "/field/codes"]
            found[column["field"]["name"]] = (claim, issues[0])
    return found


def test_twenty_six_maps_replaced_an_older_one() -> None:
    assert len(_replaced_maps()) == 26


@pytest.mark.parametrize("name", sorted(set(_replaced_maps()) - {"atestante", "tppos"}))
def test_a_map_that_replaced_one_with_no_claim_is_verified(name) -> None:
    claim, issue = _replaced_maps()[name]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert issue["status"] == "resolved" and "não tinha claim" in issue["description"]


def test_a_reviewer_closed_atestante_where_the_document_words_code_1_otherwise() -> None:
    claim, issue = _replaced_maps()["atestante"]
    assert (claim["status"], issue["status"]) == ("verified_in_source", "resolved")
    text = issue["description"]
    # The resolved issue keeps the previous map and the two wordings.
    assert "'1' era 'Assistente', CNV 'Sim'" in text and "ATESTANT.CNV" in text
    # The reading is the reviewer's: no form or manual of the DO is a registered source.
    assert "Resolvido em 2026-11-25 pela revisora marcelaqs" in text
    assert "segundo a revisora" in text
    # The 1996 DEF links the field on an X line; the CID-9 DEF on active T and S lines.
    assert "XMedico Atest, ATESTANTE, 1, ATESTANT.CNV" in text and "def-liga-por-linha-x" in text
    assert "TAtestante, ATESTANTE, 1, ATESTANT.CNV" in text
    assert "SAtestante, ATESTANTE, 1, ATESTANT.CNV" in text


def test_a_reviewer_closed_tppos_where_the_files_write_other_codes_than_the_document() -> None:
    claim, issue = _replaced_maps()["tppos"]
    assert (claim["status"], issue["status"]) == ("verified_in_source", "resolved")
    text = issue["description"]
    # The resolved issue keeps the previous map.
    assert "'1' era 'Sim', CNV não lista" in text and "'2' era 'Não', CNV não lista" in text
    assert "Resolvido em 2026-11-25 pela revisora marcelaqs" in text
    # What closes it is what the files write, not a reading of the two wordings.
    codes = next(
        i["description"]
        for i in _columns()["tppos"]["issues"]
        if i["id"] == "tppos-codigos-divergem-do-pdf"
    )
    assert "Resolvido em 2026-11-25 pela revisora marcelaqs: os códigos diferem" in codes
    assert "quem decide são os arquivos" in codes
    assert "S em 374.509 registros, N em 951.045" in codes
