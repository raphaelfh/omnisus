"""explorar.py imports a scope, explores it with widgets and cites it, on a real SIM file.

The fake server in `tests/support/fake_datasus.py` serves `sim_rr_2022_mini`, the whole
DORR2022.dbc (`tests/fixtures/FIXTURES.md`), for the scope the import widgets open on.
`app.run()` uses each widget's default, as `marimo export` does.

The last test moves the lake's folder before exploring, as when the folder is copied
from Google Drive to another computer or to molab: the catalog records the absolute
path where the lake was created.
"""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from tests.support import fake_datasus
from tests.support.datasus_names import filename_for
from tests.unit.test_fixture_provenance import load_fixture_rows

import omnisus as sus
from omnisus.sources._base import ScopeKey

ROOT = Path(__file__).resolve().parents[3]
EXPLORAR = ROOT / "notebooks" / "explorar.py"
ARQUIVO = ROOT / "tests" / "fixtures" / "dbc" / "sim_rr_2022_mini.dbc"
ESCOPO = ScopeKey(uf="RR", ano=2022)
REGISTROS = int(
    next(r for r in load_fixture_rows() if r["file"] == "dbc/sim_rr_2022_mini.dbc")["records"]
)
SHA256 = hashlib.sha256(ARQUIVO.read_bytes()).hexdigest()


def _rodar(monkeypatch, pasta: Path, *argumentos: str) -> dict:
    """Run the notebook on the lake in `pasta`, as `marimo export` would; return its defs."""
    monkeypatch.chdir(pasta.parent)
    monkeypatch.setattr(sys, "argv", ["explorar.py", "--lake", str(pasta), *argumentos])
    return _executar(monkeypatch)


def _executar(monkeypatch) -> dict:
    spec = importlib.util.spec_from_file_location("notebook_explorar", EXPLORAR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, definidos = module.app.run()
    return definidos


@pytest.fixture(scope="module")
def importado(tmp_path_factory) -> tuple[Path, dict]:
    """The lake the notebook's import section fills, and what its cells define then."""
    pasta = tmp_path_factory.mktemp("explorar") / "lake"
    with pytest.MonkeyPatch.context() as monkeypatch:
        baixados = fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
        definidos = _rodar(monkeypatch, pasta, "--executar", "true")
    assert [p.rsplit("/", 1)[1] for p in baixados] == [
        filename_for(sus.resolve("sim_obitos"), ESCOPO)
    ]
    return pasta, definidos


def test_imports_explores_and_cites_a_real_scope(importado):
    _, definidos = importado

    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    amostra = definidos["amostras"]["sim_obitos"]
    assert amostra.height == REGISTROS
    # Labels from the dictionary, and the harmonised categories of a validated source.
    assert {"sexo", "sexo_rotulo", "idade_anos_completos"} <= set(amostra.columns)
    assert definidos["perfil"]["registros"].sum() == REGISTROS
    citacao = definidos["citacoes"]["sim_obitos"]
    assert SHA256 in citacao
    assert filename_for(sus.resolve("sim_obitos"), ESCOPO) in citacao


def test_the_row_limit_caps_the_table_but_not_the_counts(importado, monkeypatch):
    pasta, _ = importado

    definidos = _rodar(monkeypatch, pasta, "--linhas", "100")

    assert definidos["amostras"]["sim_obitos"].height == 100
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    assert definidos["perfil"]["registros"].sum() == REGISTROS


def test_opens_the_lake_omnisus_data_dir_names(importado, monkeypatch, tmp_path):
    """Like `sus.load` and the other notebooks, without `--lake` it opens $OMNISUS_DATA_DIR."""
    pasta, _ = importado
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(pasta))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["explorar.py"])

    definidos = _executar(monkeypatch)

    assert definidos["totais"] == {"sim_obitos": REGISTROS}


def test_reads_the_lake_after_its_folder_moved(importado, monkeypatch, tmp_path):
    _, antes = importado
    fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: ARQUIVO.read_bytes()})
    sus.import_dataset(
        "sim_obitos",
        scopes=[ESCOPO],
        target=f"ducklake:{tmp_path / 'criado' / 'omnisus.ducklake'}",
    )
    shutil.move(tmp_path / "criado", tmp_path / "copiado")

    depois = _rodar(monkeypatch, tmp_path / "copiado")

    assert depois["totais"] == {"sim_obitos": REGISTROS}
    assert depois["amostras"]["sim_obitos"].equals(antes["amostras"]["sim_obitos"])
    assert SHA256 in depois["citacoes"]["sim_obitos"]
