"""explorar.py imports a scope, explores it with widgets and cites it, on a real SIM file.

The fake server in `tests/support/fake_datasus.py` serves `sim_rr_2022_mini`, the whole
DORR2022.dbc (`tests/fixtures/FIXTURES.md`), for the scope the import widgets open on.
`app.run()` uses each widget's default, as `marimo export` does.

The second test moves the lake's folder before exploring, as when the folder is copied
from Google Drive to another computer or to molab: the catalog records the absolute
path where the lake was created.
"""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

from tests.support import fake_datasus
from tests.support.datasus_names import filename_for
from tests.unit.test_fixture_provenance import load_fixture_rows

import omnisus as sus
from omnisus.sources._base import ScopeKey

EXPLORAR = Path(__file__).resolve().parents[3] / "notebooks" / "explorar.py"
ESCOPO = ScopeKey(uf="RR", ano=2022)
REGISTROS = int(
    next(r for r in load_fixture_rows() if r["file"] == "dbc/sim_rr_2022_mini.dbc")["records"]
)


def _rodar(monkeypatch, tmp_path, *argumentos: str) -> dict:
    """Run the notebook as `marimo export` would; return what its cells define."""
    listagem = sys.modules["omnisus.sources.datasus_ftp._runner"].list_sources
    monkeypatch.setattr("omnisus.sources.datasus_ftp.inventory.list_sources", listagem)
    monkeypatch.setattr("omnisus.list_sources", listagem)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["explorar.py", *argumentos])
    spec = importlib.util.spec_from_file_location("notebook_explorar", EXPLORAR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, definidos = module.app.run()
    return definidos


def _importar(monkeypatch, tmp_path, dbc_fixture, pasta: Path) -> tuple[dict, bytes, list[str]]:
    servido = dbc_fixture("sim_rr_2022_mini").read_bytes()
    baixados = fake_datasus.serve(monkeypatch, "sim_obitos", {ESCOPO: servido})
    definidos = _rodar(monkeypatch, tmp_path, "--executar", "true", "--lake", str(pasta))
    return definidos, servido, baixados


def test_imports_explores_and_cites_a_real_scope(monkeypatch, tmp_path, dbc_fixture):
    definidos, servido, baixados = _importar(monkeypatch, tmp_path, dbc_fixture, tmp_path / "lk")

    assert [p.rsplit("/", 1)[1] for p in baixados] == [
        filename_for(sus.resolve("sim_obitos"), ESCOPO)
    ]
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    amostra = definidos["amostras"]["sim_obitos"]
    assert amostra.height == REGISTROS
    # Labels from the dictionary, and the harmonised categories of a validated source.
    assert {"sexo", "sexo_rotulo", "idade_anos_completos"} <= set(amostra.columns)
    assert definidos["perfil"]["registros"].sum() == REGISTROS
    citacao = definidos["citacoes"]["sim_obitos"]
    assert hashlib.sha256(servido).hexdigest() in citacao
    assert filename_for(sus.resolve("sim_obitos"), ESCOPO) in citacao


def test_the_row_limit_caps_the_table_but_not_the_counts(monkeypatch, tmp_path, dbc_fixture):
    pasta = tmp_path / "lk"
    _importar(monkeypatch, tmp_path, dbc_fixture, pasta)

    definidos = _rodar(monkeypatch, tmp_path, "--lake", str(pasta), "--linhas", "100")

    assert definidos["amostras"]["sim_obitos"].height == 100
    assert definidos["totais"] == {"sim_obitos": REGISTROS}
    assert definidos["perfil"]["registros"].sum() == REGISTROS


def test_reads_the_lake_after_its_folder_moved(monkeypatch, tmp_path, dbc_fixture):
    antes, servido, _ = _importar(monkeypatch, tmp_path, dbc_fixture, tmp_path / "criado")
    shutil.move(tmp_path / "criado", tmp_path / "copiado")

    depois = _rodar(monkeypatch, tmp_path, "--lake", str(tmp_path / "copiado"))

    assert depois["totais"] == {"sim_obitos": REGISTROS}
    assert depois["amostras"]["sim_obitos"].equals(antes["amostras"]["sim_obitos"])
    assert hashlib.sha256(servido).hexdigest() in depois["citacoes"]["sim_obitos"]
