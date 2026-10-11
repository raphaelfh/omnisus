"""explorar.py imports a scope, explores it with widgets and cites it, on a real SIM file.

The fake server in `tests/support/fake_datasus.py` serves `sim_rr_2022_mini`, the whole
DORR2022.dbc (`tests/fixtures/FIXTURES.md`), for the scope the import widgets open on.
`app.run()` uses each widget's default, as `marimo export` does.
"""

from __future__ import annotations

import errno
import gzip
import hashlib
import importlib.util
import io
import os
import shutil
import sys
from pathlib import Path

import duckdb
import polars as pl
import pytest
from tests.support import fake_datasus
from tests.support.datasus_names import filename_for
from tests.unit.test_fixture_provenance import load_fixture_rows

import omnisus as sus
from omnisus.lake._transactions import CommitOutcomeUnknown
from omnisus.lake.catalog import data_dir
from omnisus.sources import sigtap
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp import _runner

ROOT = Path(__file__).resolve().parents[3]
EXPLORAR = ROOT / "notebooks" / "explorar.py"
ARQUIVO = ROOT / "tests" / "fixtures" / "dbc" / "sim_rr_2022_mini.dbc"
ESCOPO = ScopeKey(uf="RR", ano=2022)
ARQUIVO_2023 = ROOT / "tests" / "fixtures" / "dbc" / "sim_rr_2023_mini.dbc"
ESCOPO_2023 = ScopeKey(uf="RR", ano=2023)


def _registros(arquivo: Path) -> int:
    nome = f"dbc/{arquivo.name}"
    return int(next(r for r in load_fixture_rows() if r["file"] == nome)["records"])


REGISTROS = _registros(ARQUIVO)
SHA256 = hashlib.sha256(ARQUIVO.read_bytes()).hexdigest()


def _executar(monkeypatch, *argumentos: str, defs: dict | None = None) -> tuple[str, dict]:
    """Run the notebook as `marimo export` would; return the text it shows and what its
    cells define."""
    monkeypatch.setattr(sys, "argv", ["explorar.py", *argumentos])
    spec = importlib.util.spec_from_file_location("notebook_explorar", EXPLORAR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    saidas, definidos = module.app.run(defs=defs)
    assert not [s for s in saidas if isinstance(s, duckdb.DuckDBPyConnection)]
    return " ".join(getattr(s, "text", "") for s in saidas if s is not None), definidos


def _rodar(monkeypatch, *argumentos: str) -> dict:
    """What the notebook's cells define."""
    return _executar(monkeypatch, *argumentos)[1]


def _importar(monkeypatch, pasta: Path, *argumentos: str) -> dict:
    """Click *Importar* on the lake in `pasta`, with the widgets that `argumentos` set."""
    return _rodar(monkeypatch, "--lake", str(pasta), "--executar", "true", *argumentos)


@pytest.fixture(scope="module")
def importado(tmp_path_factory) -> tuple[Path, dict, list[str]]:
    """The lake the notebook's import section fills, what its cells define then, and
    the server paths it downloaded."""
    pasta = tmp_path_factory.mktemp("explorar") / "lake"
    with pytest.MonkeyPatch.context() as monkeypatch:
        baixados = fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
        definidos = _importar(monkeypatch, pasta)
    return pasta, definidos, baixados


def test_imports_explores_and_cites_a_real_scope(importado):
    _, definidos, baixados = importado

    assert [p.rsplit("/", 1)[1] for p in baixados] == [
        filename_for(sus.resolve("sim_obitos"), ESCOPO)
    ]
    assert definidos["relatorio"].rows() == [("RR_2022", "importado", None)]
    assert definidos["importacao"] == "importado: 1"
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    amostra = definidos["amostras"]["sim_obitos"]
    assert amostra.height == REGISTROS
    # Labels from the dictionary, and the harmonised categories of a validated source.
    assert {"sexo", "sexo_rotulo", "idade_anos_completos"} <= set(amostra.columns)
    assert definidos["perfil"]["registros"].sum() == REGISTROS
    assert len(definidos["consulta"]) == 100  # the SQL cell's starting query
    citacao = definidos["citacoes"]["sim_obitos"]
    assert SHA256 in citacao
    assert filename_for(sus.resolve("sim_obitos"), ESCOPO) in citacao


def test_each_tab_downloads_the_dictionary_of_the_labels_it_shows(importado):
    """One row per code, with the label the table shows and the document it comes from."""
    _, definidos, _ = importado
    descricao = sus.describe_dataset("sim_obitos")

    nome, conteudo = definidos["dicionarios"]["sim_obitos"]
    dicionario = pl.read_csv(io.BytesIO(conteudo), infer_schema=False)
    sexo = dicionario.filter(coluna="sexo")
    na_tabela = definidos["amostras"]["sim_obitos"].select("sexo", "sexo_rotulo").drop_nulls()

    assert nome == f"sim_obitos_dicionario_{descricao['dictionary_version']}.csv"
    assert set(na_tabela.unique().iter_rows()) <= set(sexo.select("codigo", "rotulo").iter_rows())
    assert set(sexo["fonte_sha256"]) <= {d["sha256"] for d in descricao["sources"]}
    assert set(dicionario["coluna"]) == {f["name"] for f in descricao["schema"]["fields"]}
    # The note says what a `conflicting` map conflicts with.
    tipobito = dicionario.filter(coluna="tipobito")
    assert set(tipobito["conferencia"]) == {"conflicting"}
    assert "cnv-difere-do-mapa-anterior" in tipobito["nota"][0]


def test_a_table_outside_the_dataset_registry_offers_its_packaged_dictionary(
    monkeypatch, tmp_path
):
    """`aux_sigtap_procedimentos`, which `sus.import_sigtap` publishes, is not a dataset of
    `sus.datasets()` but has a dictionary in the package."""
    nomes = ROOT / "tests" / "fixtures" / "listings" / "sigtap_tup_downloads_nlst.txt.gz"
    zip_200801 = ROOT / "tests" / "fixtures" / "sigtap" / "TabelaUnificada_200801.zip"
    monkeypatch.setattr(
        sigtap, "list_names", lambda: gzip.decompress(nomes.read_bytes()).decode().splitlines()
    )
    monkeypatch.setattr(
        sigtap, "download", lambda _: (zip_200801.read_bytes(), "2009-01-08T00:00")
    )
    sus.import_sigtap(years=[2008], months=[1], target=f"ducklake:{tmp_path / 'omnisus.ducklake'}")

    definidos = _rodar(monkeypatch, "--lake", str(tmp_path))

    assert definidos["dicionarios"]["aux_sigtap_procedimentos"][0] == (
        "aux_sigtap_procedimentos_dicionario_"
        f"{sus.describe_dataset('aux_sigtap_procedimentos')['dictionary_version']}.csv"
    )


def test_a_reimport_counts_as_already_in_the_lake_and_an_unlisted_scope_as_not_published(
    importado, monkeypatch
):
    pasta, _, _ = importado
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    de_novo = _importar(monkeypatch, pasta)["relatorio"]
    fake_datasus.serve(monkeypatch, "sim_obitos", {})
    ausente = _importar(monkeypatch, pasta)["relatorio"]

    assert de_novo["situacao"].to_list() == ["já estava no lake"]
    assert ausente["situacao"].to_list() == ["o DATASUS não publica"]
    assert "not in the server listing" in ausente["motivo"].item()


def test_a_failed_download_is_reported_and_a_second_click_imports_only_what_is_missing(
    monkeypatch, tmp_path
):
    arquivos = {ESCOPO: ARQUIVO.read_bytes(), ESCOPO_2023: ARQUIVO_2023.read_bytes()}
    fake_datasus.serve(monkeypatch, "sim_obitos", arquivos)
    baixar = _runner.fetch_dbc_bytes

    async def falha_em_2023(entry, **kw):
        if entry.name.endswith("2023.dbc"):
            raise ConnectionResetError(f"{entry.path}: connection reset by peer")
        return await baixar(entry, **kw)

    monkeypatch.setattr(_runner, "fetch_dbc_bytes", falha_em_2023)
    antes = _importar(monkeypatch, tmp_path, "--anos", "2022,2023")
    baixados = fake_datasus.serve(monkeypatch, "sim_obitos", arquivos)
    # Repeated, as a shell user may also write it.
    depois = _importar(monkeypatch, tmp_path, "--anos", "2022", "--anos", "2023")

    assert antes["relatorio"]["situacao"].to_list() == ["importado", "falhou ao baixar"]
    assert "connection reset by peer" in antes["relatorio"]["motivo"][1]
    assert antes["totais"] == {"sim_obitos": REGISTROS}
    assert depois["relatorio"]["situacao"].to_list() == ["já estava no lake", "importado"]
    assert [p.rsplit("/", 1)[1] for p in baixados] == ["DORR2023.dbc"]
    assert depois["totais"] == {"sim_obitos": REGISTROS + _registros(ARQUIVO_2023)}


def test_imports_the_chosen_months_of_a_monthly_base_in_order(monkeypatch, tmp_path):
    arquivo = ROOT / "tests" / "fixtures" / "dbc" / "sih_er_rr_2024_01_mini.dbc"
    janeiro = ScopeKey(uf="RR", ano=2024, mes=1)
    fake_datasus.serve(monkeypatch, "sih_aih_rejeitada_erro", {janeiro: arquivo.read_bytes()})

    definidos = _importar(
        monkeypatch,
        tmp_path,
        "--base",
        "sih_aih_rejeitada_erro",
        "--anos",
        "2024",
        "--meses",
        "2,1",
    )

    assert definidos["relatorio"]["escopo", "situacao"].rows() == [
        ("RR_2024_01", "importado"),
        ("RR_2024_02", "o DATASUS não publica"),
    ]
    assert definidos["totais"] == {"sih_aih_rejeitada_erro": _registros(arquivo)}


def test_a_command_line_year_outside_the_base_coverage_is_left_out(monkeypatch, tmp_path):
    """The SIM in CID-9 ends in 1995; the widgets still open, with no year chosen."""
    definidos = _rodar(
        monkeypatch, "--lake", str(tmp_path), "--base", "sim_obitos_cid9", "--anos", "1995,2022"
    )

    assert definidos["anos_novos"].value == [1995]
    assert [str(e) for e in definidos["escopos_novos"]] == ["RR_1995"]


def test_a_scope_imported_by_another_omnisus_version_asks_for_and_takes_substituir(
    monkeypatch, tmp_path
):
    """A new parser version (another omnisus release or dictionary) on the same file."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    _importar(monkeypatch, tmp_path)
    versao = _runner.parser_version
    monkeypatch.setattr(_runner, "parser_version", lambda d: versao(d) + "-nova")

    texto, recusado = _executar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")
    substituido = _importar(monkeypatch, tmp_path, "--substituir", "true")["relatorio"]

    assert recusado["relatorio"]["situacao"].to_list() == ["falhou ao gravar"]
    assert "request replace explicitly" in recusado["relatorio"]["motivo"].item()
    assert "os desfeitos da mesma parte entram no clique seguinte" in texto
    assert substituido["situacao"].to_list() == ["importado"]


def test_another_writer_on_the_lake_stops_the_import_with_a_message(monkeypatch, tmp_path):
    """As when the notebook is open in two tabs, or `sus.load` runs in a terminal."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})

    with sus.Lake.local(f"ducklake:{tmp_path / 'omnisus.ducklake'}"):
        definidos = _importar(monkeypatch, tmp_path)

    assert "Outro processo está gravando neste lake" in definidos["parada"]
    assert definidos["relatorio"]["situacao"].to_list() == ["não tentado"]


def test_an_aborted_write_shows_its_innermost_cause_and_leaves_the_scope_unresolved(
    monkeypatch, tmp_path
):
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})

    def commit_incerto(*_a, **_kw):
        try:
            raise OSError("database is locked")
        except OSError as e:
            raise CommitOutcomeUnknown("commit outcome unknown; inspect before retry") from e

    monkeypatch.setattr(_runner, "publish_staged", commit_incerto)
    definidos = _importar(monkeypatch, tmp_path)

    assert "database is locked" in definidos["parada"]
    assert definidos["relatorio"]["situacao"].to_list() == ["sem resultado"]


def test_a_full_disk_stops_the_import_instead_of_downloading_the_rest(monkeypatch, tmp_path):
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})

    def disco_cheio(*_a, **_kw):
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    monkeypatch.setattr(_runner, "stage_raw", disco_cheio)
    todas = ",".join(sus.ALL_UFS)
    definidos = _importar(monkeypatch, tmp_path, "--ufs", todas)

    assert "Disco cheio" in definidos["parada"]
    assert definidos["relatorio"].filter(escopo="RR_2022")["situacao"].item() == "falhou ao gravar"
    assert definidos["relatorio"]["situacao"].to_list()[-3:] == ["não tentado"] * 3


def test_an_unexpected_error_becomes_a_message_and_keeps_the_report(monkeypatch, tmp_path):
    """Such as a listing that names one scope in two directories."""

    def listagem_incoerente(d, **_kw):
        raise ValueError("sim_obitos: RR_2022 is published as both final and prelim")

    monkeypatch.setattr(_runner, "list_sources", listagem_incoerente)
    definidos = _importar(monkeypatch, tmp_path)

    assert "ValueError: sim_obitos: RR_2022 is published as both" in definidos["parada"]
    assert definidos["relatorio"]["situacao"].to_list() == ["não tentado"]


def test_when_the_server_stops_answering_what_was_imported_stays_and_the_rest_is_not_tried(
    monkeypatch, tmp_path
):
    """The import runs in parts; a part that fails stops the rest, not the parts before it."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    listar = _runner.list_sources
    listagens = []

    def responde_uma_vez(d, **kw):
        listagens.append(d.name)
        if len(listagens) > 1:
            # ftplib raises a bare EOFError when the server drops the connection.
            erro = sus.FtpUnavailable("/dissemin/publicos/SIM/CID10/DORES: 3 attempts failed")
            raise erro from EOFError()
        return listar(d, **kw)

    monkeypatch.setattr(_runner, "list_sources", responde_uma_vez)
    todas = ",".join(sus.ALL_UFS)
    definidos = _importar(monkeypatch, tmp_path, "--ufs", todas)
    relatorio = definidos["relatorio"]

    assert relatorio.height == len(sus.ALL_UFS)
    assert relatorio.filter(escopo="RR_2022")["situacao"].item() == "importado"
    assert relatorio["situacao"].value_counts(sort=True).rows() == [
        ("o DATASUS não publica", len(sus.ALL_UFS) - 4),
        ("não tentado", 3),
        ("importado", 1),
    ]
    assert (
        "não respondeu (/dissemin/publicos/SIM/CID10/DORES: 3 attempts failed)"
        in (definidos["parada"])
    )
    assert definidos["totais"] == {"sim_obitos": REGISTROS}


def test_an_interrupt_leaves_the_running_part_without_result_and_the_rest_not_tried(
    monkeypatch, tmp_path
):
    """In marimo the running part ends before the interrupt reaches the cell; its report
    is lost, so its scopes have no result."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    listar = _runner.list_sources
    listagens = []

    def interrompe_na_segunda(d, **kw):
        listagens.append(d.name)
        if len(listagens) == 2:
            raise KeyboardInterrupt
        return listar(d, **kw)

    monkeypatch.setattr(_runner, "list_sources", interrompe_na_segunda)
    todas = ",".join(sus.ALL_UFS)
    definidos = _importar(monkeypatch, tmp_path, "--anos", "2021,2022", "--ufs", todas)

    assert definidos["parada"].startswith("Interrompido.")
    assert definidos["relatorio"]["situacao"].value_counts(sort=True).rows() == [
        ("o DATASUS não publica", 24),
        ("sem resultado", 24),
        ("não tentado", 2 * len(sus.ALL_UFS) - 48),
    ]


def test_a_report_of_many_scopes_keeps_a_reason_that_comes_after_the_first_hundred(
    monkeypatch, tmp_path
):
    """The newest year comes last and is often not published yet."""

    def importa_ate_2022(dataset, *, scopes, **_kw):
        return sus.ImportReport(
            tuple(
                sus.ScopeOutcome(s, "ok")
                if s.ano < 2023
                else sus.ScopeOutcome(s, "skipped", reason="not in the listing", code="not_listed")
                for s in scopes
            )
        )

    monkeypatch.setattr(sus, "import_dataset", importa_ate_2022)
    todas = ",".join(sus.ALL_UFS)
    relatorio = _importar(
        monkeypatch, tmp_path, "--anos", "2019,2020,2021,2022,2023", "--ufs", todas
    )["relatorio"]

    assert relatorio.height == 5 * len(sus.ALL_UFS)
    assert relatorio.row(-1) == ("TO_2023", "o DATASUS não publica", "not in the listing")


def test_the_free_disk_line_survives_a_folder_it_cannot_read(monkeypatch, tmp_path):
    """As a Google Drive or network folder that is not mounted, or one macOS protects."""

    def sem_permissao(_pasta):
        raise PermissionError(13, "Operation not permitted")

    monkeypatch.setattr(shutil, "disk_usage", sem_permissao)
    texto, definidos = _executar(monkeypatch, "--lake", str(tmp_path / "nao" / "existe"))

    assert "Disco livre: ? GiB na pasta do lake" in texto
    assert [str(e) for e in definidos["escopos_novos"]] == ["RR_2022"]
    assert not (tmp_path / "nao").exists()


def test_a_base_without_chosen_scopes_has_no_rows_and_no_citation(importado, monkeypatch):
    pasta, _, _ = importado

    texto, definidos = _executar(
        monkeypatch, "--lake", str(pasta), defs={"escolhidas": {"sim_obitos": []}}
    )

    assert definidos["totais"] == {"sim_obitos": 0}
    assert definidos["amostras"]["sim_obitos"].height == 0
    assert definidos["perfil"]["registros"].sum() == 0
    assert definidos["citacoes"] == {}
    assert "Nenhum escopo escolhido para citar." in texto
    assert "Baixar citação" not in texto
    assert "Baixar o dicionário (CSV)" in texto  # the tab still offers its dictionary
    # The harmonised columns come last; the tab's table shows every column, not the first 50.
    assert "data-max-columns='&quot;all&quot;'" in texto


def test_the_row_limit_caps_the_table_but_not_the_counts(importado, monkeypatch):
    pasta, _, _ = importado

    definidos = _rodar(monkeypatch, "--lake", str(pasta), "--linhas", "100")

    assert definidos["amostras"]["sim_obitos"].height == 100
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    assert definidos["perfil"]["registros"].sum() == REGISTROS


def test_without_lake_it_opens_the_folder_sus_load_writes_to(importado, monkeypatch, tmp_path):
    """$OMNISUS_DATA_DIR, else data/raw under the working directory, as `data_dir()` says."""
    pasta, _, _ = importado
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(pasta))

    definidos = _rodar(monkeypatch)

    assert definidos["diretorio"] == data_dir().resolve()
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    monkeypatch.delenv("OMNISUS_DATA_DIR")
    assert _rodar(monkeypatch)["diretorio"] == data_dir().resolve()
    # A literal `~` (as from a .env file) is not the home folder for `sus.load` either.
    monkeypatch.setenv("OMNISUS_DATA_DIR", "~/omnisus")
    assert _rodar(monkeypatch)["diretorio"] == data_dir().resolve()


def test_reads_the_lake_after_its_folder_moved(monkeypatch, tmp_path):
    """As when the folder is copied from Google Drive to another computer or to molab:
    the catalog records the absolute path where the lake was created."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    sus.import_dataset(
        "sim_obitos",
        scopes=[ESCOPO],
        target=f"ducklake:{tmp_path / 'criado' / 'omnisus.ducklake'}",
    )
    shutil.move(tmp_path / "criado", tmp_path / "copiado")

    depois = _importar(monkeypatch, tmp_path / "copiado")

    assert depois["totais"] == {"sim_obitos": REGISTROS}
    assert depois["amostras"]["sim_obitos"].height == REGISTROS
    assert SHA256 in depois["citacoes"]["sim_obitos"]
    # It only reads there: an import goes to the folder where the lake was created.
    assert "pasta onde foi criado" in depois["parada"]
    assert depois["relatorio"]["situacao"].to_list() == ["não tentado"]


def test_a_reader_holding_the_catalog_stops_the_import_with_a_message(monkeypatch, tmp_path):
    """Another notebook or DuckDB session with a read transaction open on the lake."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    _importar(monkeypatch, tmp_path)

    with sus.LakeReader(f"ducklake:{tmp_path / 'omnisus.ducklake'}") as leitor:
        conexao = leitor.connect()
        conexao.execute("BEGIN TRANSACTION")
        conexao.execute("SELECT count(*) FROM lake.sim_obitos").fetchall()
        definidos = _importar(monkeypatch, tmp_path)
        conexao.execute("ROLLBACK")

    assert "outro programa está lendo este lake" in definidos["parada"]
