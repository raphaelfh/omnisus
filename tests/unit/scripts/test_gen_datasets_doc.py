"""docs/datasets.md tells a researcher which arguments each dataset accepts.

The page is rendered from the registry and the packaged dictionaries, so it changes
with every version that changes them (CI runs the generator with ``--check``).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.transforms.dictionaries import load_dicionario

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "gen_datasets_doc.py"


def _render() -> str:
    spec = importlib.util.spec_from_file_location("gen_datasets_doc", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render()


def _row(page: str, dataset: str) -> list[str]:
    line = next(line for line in page.splitlines() if line.startswith(f"| `{dataset}` |"))
    return [cell.strip() for cell in line.strip("|").split("|")]


def test_state_dataset_takes_ufs_and_its_first_year():
    _, titulo, years, ufs, months, *_ = _row(_render(), "sim_obitos")
    assert titulo == load_dicionario("sim_obitos").title
    assert years.startswith(str(REGISTRY["sim_obitos"].coverage[0][0]))
    assert ufs == "`['RR', ...]`"
    assert months == "—"


def test_national_dataset_takes_ufs_none():
    _, _, _, ufs, _, *_ = _row(_render(), "sinan_chagas")
    assert ufs == "`None`"


def test_monthly_dataset_takes_months():
    _, _, _, _, months, *_ = _row(_render(), "sih_aih_reduzida")
    assert months == "1 a 12"


def test_labelled_columns_are_counted_from_the_dictionary():
    fields = load_dicionario("sim_obitos").fields
    decoded = sum(1 for field in fields if field.get("x-decode"))
    cells = _row(_render(), "sim_obitos")
    assert cells[5].startswith(f"[{decoded}]")
