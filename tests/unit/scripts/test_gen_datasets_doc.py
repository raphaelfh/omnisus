"""docs/datasets.md helps a researcher choose a dataset, grouped by system.

The page is rendered from ``sus.describe_datasets()`` and the profiles in
``docs/sources/``, so it changes with every version that changes them (CI runs the
generator with ``--check``). Cells are read by their column header, not by position.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from functools import cache
from pathlib import Path

import omnisus as sus

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "gen_datasets_doc.py"
DOCS = ROOT / "docs"


@cache
def _render() -> str:
    spec = importlib.util.spec_from_file_location("gen_datasets_doc", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render()


def _sections(page: str) -> dict[str, str]:
    """Body of every H2 section, keyed by its title."""
    parts = re.split(r"^## (.+)$", page, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _row(section: str, dataset: str) -> dict[str, str]:
    """The table row of ``dataset`` in ``section``, keyed by column header."""
    lines = section.splitlines()
    header = next(line for line in lines if line.startswith("| Base |"))
    row = next(line for line in lines if line.startswith(f"| `{dataset}` |"))
    return dict(zip(_cells(header), _cells(row), strict=True))


def _dataset(name: str) -> dict:
    return sus.describe_datasets().filter(name=name).row(0, named=True)


def _system_row(name: str) -> dict[str, str]:
    return _row(_sections(_render())[_dataset(name)["category"]], name)


def test_every_dataset_sits_under_the_section_of_its_system():
    sections = _sections(_render())
    for name, system in sus.describe_datasets().select("name", "category").iter_rows():
        assert f"| `{name}` |" in sections[system], (name, system)


def test_monthly_coverage_keeps_the_month():
    atd = _system_row("sia_apac_tratamento_dialitico")
    assert atd["Cobertura"] == "2014-08 em diante"
    assert atd["Publicação"] == "por UF, mensal"
    assert _system_row("cnes_estabelecimentos_ensino")["Cobertura"] == "2007-03 a 2021-07"


def test_national_yearly_dataset_says_brasil_anual():
    assert _system_row("sinan_chagas")["Publicação"] == "Brasil, anual"
    assert _system_row("sim_obitos_cid9")["Cobertura"] == "1979 a 1995"


def test_sim_obitos_shows_the_preliminary_directory_and_its_validated_scopes():
    sim = _system_row("sim_obitos")
    assert sim["Cobertura"] == "1996 em diante + preliminar"
    scopes = _dataset("sim_obitos")["validated_scopes"]
    assert "SP_2024" in scopes
    assert sim["Categorias harmonizadas"] == ", ".join(f"`{s}`" for s in scopes)
    assert _system_row("sia_apac_nefrologia")["Categorias harmonizadas"] == "—"

    server = _row(_sections(_render())["Onde fica no servidor"], "sim_obitos")
    assert server["Prefixo"] == "`DO`"
    assert server["Diretório"] == "`SIM/CID10/DORES`"
    assert server["Preliminar"] == "`SIM/PRELIM/DORES`"


def test_labelled_columns_link_the_dictionary_of_this_release():
    labelled = _dataset("sim_obitos")["labelled_fields"]
    url = (
        f"https://github.com/raphaelfh/omnisus/blob/v{sus.__version__}"
        "/src/omnisus/data/dicionarios/sim_obitos.yaml"
    )
    assert _system_row("sim_obitos")["Colunas com rótulo"] == f"[{labelled}]({url})"


def test_every_system_links_profiles_that_cite_each_of_its_datasets():
    sections = _sections(_render())
    table = sus.describe_datasets()
    for system in table["category"].unique():
        profiles = re.findall(r"\]\((sources/[^)#]+\.md)\)", sections[system])
        assert profiles, system
        texts = [(DOCS / path).read_text(encoding="utf-8") for path in profiles]
        for name in table.filter(category=system)["name"]:
            assert any(f"`{name}`" in text for text in texts), (system, name)


def test_the_generator_reads_only_the_public_api():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    modules |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert {m for m in modules if m.split(".")[0] == "omnisus"} == {"omnisus"}
