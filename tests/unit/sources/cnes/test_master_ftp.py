"""Tests for CNES names from the full CNES base (FTP zip -> lake.cnes_master).

The fixture is six records of the real tbEstabelecimento202312.csv
(tests/fixtures/FIXTURES.md): four hospitals with a nome fantasia, one of them
with a leading-zero code, one establishment with only a razão social, and one
pessoa física (TP_PFPJ=1) whose names are blanked in the fixture.

The real file has no row without a name and no repeated CO_CNES (checked on all 509875
rows of 202312), and the committed pessoa física has its names blanked. The tests that
need those cases build a ZIP from the fixture's CSV and say so: they are synthetic,
for malformed or sensitive input only.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest
from structlog.testing import capture_logs

from omnisus.lake import Lake
from omnisus.sources.cnes.importers.master_ftp import (
    FTP_FONTE,
    import_cnes_master_ftp,
    read_names,
)

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "cnes_base"
    / "BASE_DE_DADOS_CNES_202312.ZIP"
)
CODES = ["0860638", "2319659", "2320886", "4339517", "6185177"]
PESSOA_FISICA = "3107981"
MEMBER = "tbEstabelecimento202312.csv"


def _synthetic_zip(tmp_path: Path, edit) -> Path:
    """Synthetic: the fixture's CSV text passed through ``edit``, zipped under the same name."""
    with zipfile.ZipFile(FIXTURE) as zf:
        text = zf.read(MEMBER).decode("latin-1")
    path = tmp_path / "BASE_DE_DADOS_CNES_202312.ZIP"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(MEMBER, edit(text).encode("latin-1"))
    return path


def _line_of(text: str, code: str) -> str:
    (line,) = [ln for ln in text.splitlines() if f'";"{code}";"' in ln]
    return line


def _seed(lake: Lake, codes: list[str]) -> None:
    con = lake.connect()
    con.execute(
        f"CREATE TABLE {lake.alias}.cnes_estabelecimentos "
        "(cnes VARCHAR, tp_unid VARCHAR, codufmun VARCHAR, ano INTEGER, mes INTEGER)"
    )
    con.executemany(
        f"INSERT INTO {lake.alias}.cnes_estabelecimentos VALUES (?, '05', '140010', 2023, 12)",
        [(c,) for c in codes],
    )


def test_read_names_prefers_fantasia_and_records_provenance() -> None:
    recs = {r["cnes"]: r for r in read_names(FIXTURE, "202312")}
    assert sorted(recs) == CODES
    assert recs["2320886"]["nome"] == "HOSPITAL JOSE GUEDES CATAO"
    assert recs["2320886"]["razao_social"] == "ESTADO DE RORAIMA"
    assert recs["0860638"]["nome"] == "HOSPITAL HELIO MACEDO"
    assert recs["4339517"]["nome"] == "ASSOCIACAO PESTALOZZI DE DIVINO DE SAO LOURENCO"
    assert recs["4339517"]["nome_fantasia"] is None
    assert recs["2320886"]["sha256"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert recs["2320886"]["competencia_nome"] == "202312"
    assert recs["2320886"]["arquivo"] == "BASE_DE_DADOS_CNES_202312.ZIP"


def test_a_pessoa_fisica_row_gives_no_name() -> None:
    """The committed pessoa física has its names blanked; the row is left out, not written empty."""
    with capture_logs() as logs:
        recs = {r["cnes"] for r in read_names(FIXTURE, "202312")}
    assert PESSOA_FISICA not in recs
    (skipped,) = [e for e in logs if e["event"] == "cnes_master_ftp.rows_skipped"]
    assert (skipped["pessoa_fisica"], skipped["sem_nome"]) == (1, 0)


def test_a_pessoa_fisica_name_in_the_file_never_reaches_the_records(tmp_path: Path) -> None:
    """Synthetic: the real pessoa física has the professional's name in NO_FANTASIA (and in
    NO_RAZAO_SOCIAL); the fixture blanks it, so a name is put back here."""

    def with_names(text: str) -> str:
        line = _line_of(text, PESSOA_FISICA)
        return text.replace(
            line, line.replace('"";"";"', '"DR EXEMPLO";"CONSULTORIO DR EXEMPLO";"', 1)
        )

    path = _synthetic_zip(tmp_path, with_names)
    assert "CONSULTORIO DR EXEMPLO" in zipfile.ZipFile(path).read(MEMBER).decode("latin-1")
    recs = read_names(path, "202312")
    assert sorted(r["cnes"] for r in recs) == CODES
    assert "EXEMPLO" not in repr(recs)


def test_a_row_without_any_name_is_skipped_and_the_month_still_loads(tmp_path: Path) -> None:
    """Synthetic: the real file has no row with both names empty; the razão social of the
    fixture's only fantasia-less establishment is blanked to make one."""

    def nameless(text: str) -> str:
        line = _line_of(text, "4339517")
        return text.replace(
            line, line.replace("ASSOCIACAO PESTALOZZI DE DIVINO DE SAO LOURENCO", "")
        )

    path = _synthetic_zip(tmp_path, nameless)
    with capture_logs() as logs:
        recs = read_names(path, "202312")
    assert sorted(r["cnes"] for r in recs) == [c for c in CODES if c != "4339517"]
    (skipped,) = [e for e in logs if e["event"] == "cnes_master_ftp.rows_skipped"]
    assert (skipped["pessoa_fisica"], skipped["sem_nome"]) == (1, 1)
    target = f"ducklake:{tmp_path}/sem_nome.ducklake"
    assert import_cnes_master_ftp("202312", zip_path=path, target=target) == 4


def test_read_names_rejects_zip_without_the_month_file() -> None:
    with pytest.raises(ValueError, match="tbestabelecimento202311"):
        read_names(FIXTURE, "202311")


def test_import_fills_view_and_a_second_load_keeps_existing_names(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/ftp.ducklake"
    with Lake.local(target) as lake:
        _seed(lake, CODES)
    assert import_cnes_master_ftp("202312", zip_path=FIXTURE, target=target) == 5
    assert import_cnes_master_ftp("202312", zip_path=FIXTURE, target=target) == 0
    with Lake.local(target) as lake:
        rows = (
            lake.connect()
            .execute(
                f"SELECT cnes, nome, competencia_nome, fonte_nome "
                f"FROM {lake.alias}.aux_cnes WHERE cnes IN ('0860638', '4339517') ORDER BY cnes"
            )
            .fetchall()
        )
    assert rows == [
        ("0860638", "HOSPITAL HELIO MACEDO", "202312", FTP_FONTE),
        ("4339517", "ASSOCIACAO PESTALOZZI DE DIVINO DE SAO LOURENCO", "202312", FTP_FONTE),
    ]


def test_import_rejects_bad_competencia() -> None:
    with pytest.raises(ValueError, match="AAAAMM"):
        import_cnes_master_ftp("2023-12", zip_path=FIXTURE)


def test_api_rows_keep_working_alongside_provenance_columns(tmp_path: Path) -> None:
    """A cnes_master created by the old 4-column importer gains the new columns."""
    target = f"ducklake:{tmp_path}/legado.ducklake"
    with Lake.local(target) as lake:
        _seed(lake, CODES)
        lake.connect().execute(
            f"CREATE TABLE {lake.alias}.cnes_master "
            "(cnes VARCHAR, nome VARCHAR, nome_fantasia VARCHAR, razao_social VARCHAR)"
        )
        lake.connect().execute(
            f"INSERT INTO {lake.alias}.cnes_master VALUES ('2320886', 'API', 'API', NULL)"
        )
    assert import_cnes_master_ftp("202312", zip_path=FIXTURE, target=target) == 4
    with Lake.local(target) as lake:
        row = (
            lake.connect()
            .execute(
                f"SELECT nome, competencia_nome FROM {lake.alias}.aux_cnes WHERE cnes = '2320886'"
            )
            .fetchone()
        )
    assert row == ("API", None)
