"""explorar.py imports a scope, explores it with widgets and cites it, on a real SIM file.

The fake server in `tests/support/fake_datasus.py` serves `sim_rr_2022_mini`, the whole
DORR2022.dbc (`tests/fixtures/FIXTURES.md`), for the scope the import widgets open on.
`app.run()` uses each widget's default, as `marimo export` does.
"""

from __future__ import annotations

import errno
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


def _rodar(monkeypatch, *argumentos: str) -> dict:
    """Run the notebook as `marimo export` would; return what its cells define."""
    monkeypatch.setattr(sys, "argv", ["explorar.py", *argumentos])
    spec = importlib.util.spec_from_file_location("notebook_explorar", EXPLORAR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, definidos = module.app.run()
    return definidos


@pytest.fixture(scope="module")
def importado(tmp_path_factory) -> tuple[Path, dict, list[str]]:
    """The lake the notebook's import section fills, what its cells define then, and
    the server paths it downloaded."""
    pasta = tmp_path_factory.mktemp("explorar") / "lake"
    with pytest.MonkeyPatch.context() as monkeypatch:
        baixados = fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
        definidos = _rodar(monkeypatch, "--lake", str(pasta), "--executar", "true")
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


def test_a_reimport_counts_as_already_in_the_lake_and_an_unlisted_scope_as_not_published(
    importado, monkeypatch
):
    pasta, _, _ = importado
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    de_novo = _rodar(monkeypatch, "--lake", str(pasta), "--executar", "true")["relatorio"]
    fake_datasus.serve(monkeypatch, "sim_obitos", {})
    ausente = _rodar(monkeypatch, "--lake", str(pasta), "--executar", "true")["relatorio"]

    assert de_novo["situacao"].to_list() == ["já estava no lake"]
    assert ausente["situacao"].to_list() == ["o DATASUS não publica"]
    assert "not in the server listing" in ausente["motivo"].item()


def test_imports_several_years_at_once(monkeypatch, tmp_path):
    fake_datasus.serve(
        monkeypatch,
        "sim_obitos",
        {ESCOPO: ARQUIVO.read_bytes(), ESCOPO_2023: ARQUIVO_2023.read_bytes()},
    )

    definidos = _rodar(
        monkeypatch, "--lake", str(tmp_path), "--anos", "2022,2023", "--executar", "true"
    )

    assert definidos["relatorio"]["situacao"].to_list() == ["importado", "importado"]
    assert definidos["totais"] == {"sim_obitos": REGISTROS + _registros(ARQUIVO_2023)}


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
    antes = _rodar(
        monkeypatch, "--lake", str(tmp_path), "--anos", "2022 2023", "--executar", "true"
    )
    baixados = fake_datasus.serve(monkeypatch, "sim_obitos", arquivos)
    depois = _rodar(
        monkeypatch, "--lake", str(tmp_path), "--anos", "2022 2023", "--executar", "true"
    )

    assert antes["relatorio"]["situacao"].to_list() == ["importado", "falhou ao baixar"]
    assert "connection reset by peer" in antes["relatorio"]["motivo"][1]
    assert antes["totais"] == {"sim_obitos": REGISTROS}
    assert depois["relatorio"]["situacao"].to_list() == ["já estava no lake", "importado"]
    assert [p.rsplit("/", 1)[1] for p in baixados] == ["DORR2023.dbc"]


def test_a_scope_imported_by_another_omnisus_version_asks_for_and_takes_substituir(
    monkeypatch, tmp_path
):
    """A new parser version (another omnisus release or dictionary) on the same file."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    _rodar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")
    versao = _runner.parser_version
    monkeypatch.setattr(_runner, "parser_version", lambda d: versao(d) + "-nova")

    recusado = _rodar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")["relatorio"]
    substituido = _rodar(
        monkeypatch, "--lake", str(tmp_path), "--executar", "true", "--substituir", "true"
    )["relatorio"]

    assert recusado["situacao"].to_list() == ["falhou ao gravar"]
    assert "request replace explicitly" in recusado["motivo"].item()
    assert substituido["situacao"].to_list() == ["importado"]


def test_another_writer_on_the_lake_stops_the_import_with_a_message(monkeypatch, tmp_path):
    """As when the notebook is open in two tabs, or `sus.load` runs in a terminal."""
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})

    with sus.Lake.local(f"ducklake:{tmp_path / 'omnisus.ducklake'}"):
        definidos = _rodar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")

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
    definidos = _rodar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")

    assert "database is locked" in definidos["parada"]
    assert definidos["relatorio"]["situacao"].to_list() == ["sem resultado"]


def test_a_full_disk_stops_the_import_instead_of_downloading_the_rest(monkeypatch, tmp_path):
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})

    def disco_cheio(*_a, **_kw):
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    monkeypatch.setattr(_runner, "stage_raw", disco_cheio)
    todas = ",".join(sus.ALL_UFS)
    definidos = _rodar(monkeypatch, "--lake", str(tmp_path), "--ufs", todas, "--executar", "true")

    assert "Disco cheio" in definidos["parada"]
    assert definidos["relatorio"].filter(escopo="RR_2022")["situacao"].item() == "falhou ao gravar"
    assert definidos["relatorio"]["situacao"].to_list()[-3:] == ["não tentado"] * 3


def test_an_unexpected_error_becomes_a_message_and_keeps_the_report(monkeypatch, tmp_path):
    """Such as a listing that names one scope in two directories."""

    def listagem_incoerente(d, **_kw):
        raise ValueError("sim_obitos: RR_2022 is published as both final and prelim")

    monkeypatch.setattr(_runner, "list_sources", listagem_incoerente)
    definidos = _rodar(monkeypatch, "--lake", str(tmp_path), "--executar", "true")

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
            raise sus.FtpUnavailable("/dissemin/publicos/SIM/CID10/DORES: 3 attempts failed")
        return listar(d, **kw)

    monkeypatch.setattr(_runner, "list_sources", responde_uma_vez)
    todas = ",".join(sus.ALL_UFS)
    definidos = _rodar(monkeypatch, "--lake", str(tmp_path), "--ufs", todas, "--executar", "true")
    relatorio = definidos["relatorio"]

    assert relatorio.height == len(sus.ALL_UFS)
    assert relatorio.filter(escopo="RR_2022")["situacao"].item() == "importado"
    assert relatorio["situacao"].value_counts(sort=True).rows() == [
        ("o DATASUS não publica", len(sus.ALL_UFS) - 4),
        ("não tentado", 3),
        ("importado", 1),
    ]
    assert "não respondeu" in definidos["parada"]
    assert definidos["totais"] == {"sim_obitos": REGISTROS}


def test_a_base_without_chosen_scopes_has_no_rows_and_no_citation(importado, monkeypatch):
    pasta, _, _ = importado
    monkeypatch.setattr(sys, "argv", ["explorar.py", "--lake", str(pasta)])
    spec = importlib.util.spec_from_file_location("notebook_explorar", EXPLORAR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    saidas, definidos = module.app.run(defs={"escolhidas": {"sim_obitos": []}})
    texto = " ".join(getattr(s, "text", "") for s in saidas if s is not None)

    assert definidos["totais"] == {"sim_obitos": 0}
    assert definidos["amostras"]["sim_obitos"].height == 0
    assert definidos["perfil"]["registros"].sum() == 0
    assert definidos["citacoes"] == {}
    assert "Nenhum escopo escolhido para citar." in texto
    assert "Baixar citação" not in texto
    # The cell that reopens the lake shows nothing, not its DuckDB connection.
    assert not [s for s in saidas if isinstance(s, duckdb.DuckDBPyConnection)]
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

    depois = _rodar(monkeypatch, "--lake", str(tmp_path / "copiado"))

    assert depois["totais"] == {"sim_obitos": REGISTROS}
    assert depois["amostras"]["sim_obitos"].height == REGISTROS
    assert SHA256 in depois["citacoes"]["sim_obitos"]
