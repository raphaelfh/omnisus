"""The pure parts of scripts/build_bootstrap_zip.py, on the SIGTAP and base files the
build reads (tests/fixtures/FIXTURES.md); the build itself needs the DATASUS server."""

from __future__ import annotations

import io
import zipfile
from importlib.resources import files
from pathlib import Path

import polars as pl
import pytest
from scripts.build_bootstrap_zip import aux_cid10, parse_tb_cid, sigtap_cid10

SIGTAP = Path(__file__).resolve().parents[2] / "fixtures" / "sigtap"
# tb_cid.txt codes that CID10.DBF (2020) lacks: the 9 of the first review, plus A925, A97,
# C823 to C826 and W460 to W469.
MISSING = [
    "A925", "A97", "C823", "C824", "C825", "C826", "N182", "N183", "N184", "N185", "P354",
    "U09", "U099", "U10", "U109", *[f"W46{n}" for n in range(10)],
]  # fmt: skip


def tb_cid_files() -> tuple[list[str], list[str]]:
    layout = (SIGTAP / "tb_cid_layout_202610.txt").read_text(encoding="latin-1").splitlines()
    lines = (SIGTAP / "tb_cid_202610.txt").read_text(encoding="latin-1").splitlines()
    return layout, lines


def packaged_codes() -> set[str]:
    raw = (files("omnisus.data") / "auxiliares-bootstrap.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        return set(pl.read_parquet(zf.read("aux_cid10.parquet"))["codigo"])


def test_tb_cid_is_read_with_its_layout() -> None:
    codes = parse_tb_cid(*tb_cid_files())
    assert len(codes) == 14246
    assert codes["N185"] == "Doença renal crônica, estádio 5"
    assert codes["A97"] == "Dengue (AGRAVO DE NOTIFICAÇÃO COMPULSÓRIA)"


def test_a_changed_tb_cid_layout_stops_the_build() -> None:
    """Synthetic layout: the malformed-input case of AGENTS.md rule 2."""
    layout, lines = tb_cid_files()
    layout[2] = "NO_CID,90,5,94,VARCHAR2"
    with pytest.raises(SystemExit, match=r"tb_cid_layout\.txt changed"):
        parse_tb_cid(layout, lines)


def test_sigtap_cid10_is_every_code_the_dbf_lacks() -> None:
    layout, lines = tb_cid_files()
    have = packaged_codes() - set(MISSING)
    found = sigtap_cid10(layout, lines, have)
    assert [c for c, _ in found] == MISSING
    assert dict(found)["W469"] == "Contato com agulha hipodérmica - local não especificado"
    assert sigtap_cid10(layout, lines, packaged_codes()) == []


def test_cid10_dbf_description_must_repeat_its_code() -> None:
    """Synthetic row: the malformed-input case of AGENTS.md rule 2."""
    with pytest.raises(SystemExit, match="A00: DESCR does not start with its code"):
        aux_cid10([{"CID10": "A00", "DESCR": "B00 Colera"}], [], [], [])
