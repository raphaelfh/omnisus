"""Each base notebook runs every step, with `EXECUTAR` on, over a real DATASUS file.

The fake server in `tests/support/fake_datasus.py` lists and serves one committed
file (`tests/fixtures/FIXTURES.md`) for the scope the notebook reads, so discovery,
`sus.load`, `sus.check_columns`, the analysis and `sus.cite` all see real rows.
`sinan.py` also runs on each other agravo it offers, and `bases.py` on a national dataset.

Left out: `ibge_populacao.py` reads the IBGE API and `medicamentos.py` the Hórus
stock API, which have no committed response; `linkage.py` needs about thirty
tables. `test_notebooks_abrem_offline.py` still opens all of them.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
from tests.support import fake_datasus

from omnisus.sources._base import ScopeKey

NOTEBOOKS = Path(__file__).resolve().parents[3] / "notebooks"

# (notebook, dataset) -> (scope the notebook reads, fixture of that server file or of an
# excerpt of it, directory, a table that step 5 writes for that dataset)
CASOS = {
    ("bases.py", "cnes_leitos"): (
        ScopeKey(uf="RR", ano=2024, mes=1),
        "cnes_lt_rr_2024_01_mini",
        "final",
        "registros_no_recorte",
    ),
    ("bases.py", "sinan_chagas"): (
        ScopeKey(uf=None, ano=2023),
        "sinan_chagas_br_2023",
        "prelim",
        "registros_no_recorte",
    ),
    ("sim_obitos.py", "sim_obitos"): (
        ScopeKey(uf="RR", ano=2022),
        "sim_rr_2022_mini",
        "final",
        "obitos_por_sexo_e_causa",
    ),
    ("sinasc_nascidos_vivos.py", "sinasc_nascidos_vivos"): (
        ScopeKey(uf="RR", ano=2022),
        "sinasc_rr_2022_mini",
        "final",
        "tipo_de_parto",
    ),
    ("sih_aih_reduzida.py", "sih_aih_reduzida"): (
        ScopeKey(uf="RR", ano=2024, mes=1),
        "sih_rr_2024_01_mini",
        "final",
        "campo_morte",
    ),
    ("sia.py", "sia_bpa_individualizado"): (
        ScopeKey(uf="RR", ano=2024, mes=1),
        "sia_bi_rr_2024_01_mini",
        "final",
        "quantidade_por_procedimento",
    ),
    ("cnes_estabelecimentos.py", "cnes_estabelecimentos"): (
        ScopeKey(uf="RR", ano=2024, mes=1),
        "cnes_rr_2024_01_mini",
        "final",
        "estabelecimentos_por_tipo",
    ),
    ("sinan.py", "sinan_chagas"): (
        ScopeKey(uf=None, ano=2023),
        "sinan_chagas_br_2023",
        "prelim",
        "classificacao_e_evolucao",
    ),
    ("sinan.py", "sinan_hanseniase"): (
        ScopeKey(uf=None, ano=2026),
        "sinan_hanseniase_br_2026",
        "prelim",
        "modo_de_entrada_e_alta",
    ),
    ("sinan.py", "sinan_tuberculose"): (
        ScopeKey(uf=None, ano=2020),
        "sinan_tuberculose_br_2020_excerpt",
        "prelim",
        "tipo_de_entrada_e_encerramento",
    ),
}

# The dataset a notebook opens on, for notebooks that run on more than one.
ABRE_EM = {"sinan.py": "sinan_chagas", "bases.py": "cnes_leitos"}


@pytest.mark.parametrize(("nome", "dataset"), sorted(CASOS))
def test_notebook_runs_every_step_on_real_rows(nome, dataset, monkeypatch, tmp_path, dbc_fixture):
    escopo, fixture, release, tabela = CASOS[nome, dataset]
    servido = dbc_fixture(fixture).read_bytes()
    fake_datasus.serve(monkeypatch, dataset, {escopo: servido}, release=release)
    listagem = sys.modules["omnisus.sources.datasus_ftp._runner"].list_sources
    monkeypatch.setattr("omnisus.sources.datasus_ftp.inventory.list_sources", listagem)
    monkeypatch.setattr("omnisus.list_sources", listagem)
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(tmp_path / "lake"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [nome, "--executar", "true"])
    caminho = NOTEBOOKS / nome
    spec = importlib.util.spec_from_file_location(f"notebook_{caminho.stem}", caminho)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # For another dataset the test replaces the parameter cell; marimo replaces a cell
    # only whole, so it gives every definition of that cell.
    if dataset != ABRE_EM.get(nome, dataset):
        parametros = {"BASE": dataset, "ANO": escopo.ano, "EXECUTAR": True, "executar": True}
        if nome == "bases.py":
            parametros |= {"UF": escopo.uf, "MES": escopo.mes}
        module.app.run(defs=parametros)
    else:
        module.app.run()

    pasta = tmp_path / "resultados" / dataset
    citacao = (pasta / "citacao.txt").read_text(encoding="utf-8")
    assert hashlib.sha256(servido).hexdigest() in citacao
    assert (pasta / f"{tabela}.csv").exists(), sorted(f.name for f in pasta.glob("*.csv"))
