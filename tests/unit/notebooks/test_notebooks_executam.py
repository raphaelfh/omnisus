"""Each base notebook runs every step, with `EXECUTAR` on, over a real DATASUS file.

The fake server in `tests/support/fake_datasus.py` lists and serves one committed
file (`tests/fixtures/FIXTURES.md`) for the scope the notebook reads, so discovery,
`sus.load`, `sus.check_columns`, the analysis and `sus.cite` all see real rows.
`bases.py` runs on every registry row and `sia.py` on every SIA table, each with the
file `scripts/build_fixtures.py` names for it; `sinan.py` on each agravo it offers.

The server also lists the next month and another UF of that scope, with the same
bytes under the other name. The test asserts the notebook downloads only its own
file, so those bytes are never read, and a `sus.load` call that lost `months` or
`ufs` fails here.

When the server lists no file for the scope, each notebook says so at discovery and
stops before `sus.load`.

Left out: `ibge_populacao.py` reads the IBGE API and `medicamentos.py` the Hórus
stock API, which have no committed response; `linkage.py` needs about thirty
tables. `medicamentos.py` runs only in the stop at discovery, with the Hórus cell
stopped. `test_notebooks_abrem_offline.py` still opens all of them.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

import marimo as mo
import polars as pl
import pytest
from tests.support import fake_datasus
from tests.support.datasus_names import filename_for
from tests.unit.test_fixture_provenance import load_fixture_rows

import omnisus as sus
from omnisus.sources._base import ScopeKey

ROOT = Path(__file__).resolve().parents[3]
NOTEBOOKS = ROOT / "notebooks"
FIXTURES = {row["file"]: row for row in load_fixture_rows()}


def _arquivo_de_cada_base() -> dict[str, tuple[ScopeKey, str, str]]:
    """dataset -> (scope, fixture, directory), from `scripts/build_fixtures.py`.

    `test_public_api.py` checks that its map has every registry row. The directory
    is the one the fixture's row in FIXTURES.md names.
    """
    script = ROOT / "scripts" / "build_fixtures.py"
    spec = importlib.util.spec_from_file_location("build_fixtures", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bases = {}
    for dataset, escopo, arquivo in module.TARGETS:
        pasta = urlparse(FIXTURES[f"dbc/{arquivo}"]["source"]).path.rsplit("/", 1)[0]
        release = {p: r for r, p in sus.resolve(dataset).directories().items()}[pasta]
        bases[dataset] = (escopo, arquivo.removesuffix(".dbc"), release)
    return bases


ARQUIVO = _arquivo_de_cada_base()
SIA = sus.describe_datasets().filter(category="SIA")["name"].to_list()
# sia.py step 5: the table it writes for the three SIA tables it analyses.
SIA_ANALISADAS = {
    "sia_bpa_individualizado": "quantidade_por_procedimento",
    "sia_apac_medicamentos": "apac_por_procedimento_principal",
    "sia_psicossocial": "acoes_por_cid_principal",
}

# (notebook, dataset) -> (scope the notebook reads, fixture of that server file or of an
# excerpt of it, directory, a table that step 5 writes for that dataset)
CASOS = {
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
    **{("bases.py", d): (*ARQUIVO[d], "registros_no_recorte") for d in ARQUIVO},
    **{("sia.py", d): (*ARQUIVO[d], SIA_ANALISADAS.get(d, "registros_no_recorte")) for d in SIA},
}

# The dataset each notebook opens on. A case on another dataset replaces the parameter
# cell; marimo replaces a cell only whole, and ignores a definition no cell makes.
ABRE_EM = {
    "bases.py": "cnes_leitos",
    "cnes_estabelecimentos.py": "cnes_estabelecimentos",
    "medicamentos.py": "sia_apac_medicamentos",
    "sia.py": "sia_bpa_individualizado",
    "sih_aih_reduzida.py": "sih_aih_reduzida",
    "sim_obitos.py": "sim_obitos",
    "sinan.py": "sinan_chagas",
    "sinasc_nascidos_vivos.py": "sinasc_nascidos_vivos",
}


def _abrir(nome, monkeypatch, tmp_path):
    """The notebook module, with the lake and `resultados/` under `tmp_path`."""
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
    return module


@pytest.mark.parametrize(("nome", "dataset"), sorted(CASOS))
def test_notebook_runs_every_step_on_real_rows(nome, dataset, monkeypatch, tmp_path, dbc_fixture):
    escopo, fixture, release, tabela = CASOS[nome, dataset]
    servido = dbc_fixture(fixture).read_bytes()
    listados = {escopo: servido}
    if escopo.mes is not None:
        listados[replace(escopo, mes=escopo.mes % 12 + 1)] = servido
    if escopo.uf is not None:
        listados[replace(escopo, uf="AC" if escopo.uf != "AC" else "AP")] = servido
    baixados = fake_datasus.serve(monkeypatch, dataset, listados, release=release)
    module = _abrir(nome, monkeypatch, tmp_path)

    if dataset == ABRE_EM[nome]:
        module.app.run()
    else:
        parametros = {"BASE": dataset, "UF": escopo.uf, "ANO": escopo.ano, "MES": escopo.mes}
        module.app.run(defs=parametros | {"EXECUTAR": True, "executar": True})

    assert [p.rsplit("/", 1)[1] for p in baixados] == [filename_for(sus.resolve(dataset), escopo)]
    pasta = tmp_path / "resultados" / dataset
    citacao = (pasta / "citacao.txt").read_text(encoding="utf-8")
    assert hashlib.sha256(servido).hexdigest() in citacao
    assert (pasta / f"{tabela}.csv").exists(), sorted(f.name for f in pasta.glob("*.csv"))
    if tabela == "registros_no_recorte":
        registros = pl.read_csv(pasta / f"{tabela}.csv")["registros"].item()
        assert registros == int(FIXTURES[f"dbc/{fixture}.dbc"]["records"])


@pytest.mark.parametrize("nome", sorted(ABRE_EM))
def test_notebook_stops_at_discovery_when_the_server_lists_no_file_for_the_scope(
    nome, monkeypatch, tmp_path, dbc_fixture
):
    """The server lists the notebook's dataset for AC only (the notebooks open on RR),
    or nothing for a national dataset (#79)."""
    dataset = ABRE_EM[nome]
    escopo, fixture, release = ARQUIVO[dataset]
    servido = dbc_fixture(fixture).read_bytes()
    listados = {} if escopo.uf is None else {replace(escopo, uf="AC"): servido}
    baixados = fake_datasus.serve(monkeypatch, dataset, listados, release=release)
    # medicamentos.py, part B: the Hórus API has no committed response, so its cell stops.
    monkeypatch.setattr("omnisus.sources.medicamentos.fetch_stock_page", lambda **_: mo.stop(True))
    module = _abrir(nome, monkeypatch, tmp_path)

    saidas, definidos = module.app.run()

    assert baixados == []
    assert "dados" not in definidos
    assert not (tmp_path / "resultados").exists()
    assert any("não lista" in getattr(s, "text", "") for s in saidas)


@pytest.mark.parametrize(
    ("dataset", "ano", "mes", "fora"),
    [
        ("cnes_leitos", 2024, 1, False),
        ("sim_obitos_cid9", 2024, 1, True),
        ("sim_obitos_cid9", 1995, 1, False),
        ("cnes_estabelecimentos_ensino", 2021, 7, False),
        ("cnes_estabelecimentos_ensino", 2021, 8, True),
        ("cnes_estabelecimentos_ensino", 2007, 2, True),
    ],
)
def test_bases_says_when_the_scope_is_outside_the_declared_coverage(
    dataset, ano, mes, fora, monkeypatch, tmp_path
):
    module = _abrir("bases.py", monkeypatch, tmp_path)

    parametros = {"BASE": dataset, "UF": "RR", "ANO": ano, "MES": mes}
    saidas, _ = module.app.run(defs=parametros | {"EXECUTAR": False, "executar": False})

    texto = " ".join(getattr(s, "text", "") for s in saidas)
    assert ("fora da cobertura declarada" in texto) is fora
