"""`notebooks/colab.ipynb` runs end to end against the live DATASUS server, per UF.

The code cells run in order in one namespace, without the install cell, with the UF
and the SIM year of the parameters cell replaced. RR and SP by default: the smallest
UF and the largest, whose SIM has deaths with an ignored municipality. One more case
reads a SIM year that is not a validated source (RR 2019), so `load` leaves the
harmonised categories out, as it does in the PyPI release for a scope validated later.

`OMNISUS_E2E_UFS=ALL` runs the 27 UFs, about 200 MB from DATASUS (SIM of one year and
SIH of one month per UF; 3 minutes on 2026-10-08): for a release or a change to the
notebook. A list such as
`OMNISUS_E2E_UFS=DF,AM` runs those. The UFs share one lake, so the IBGE census and the
vocabularies enter it once.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import omnisus as sus

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

NOTEBOOK = Path(__file__).resolve().parents[2] / "notebooks" / "colab.ipynb"
_UFS = os.environ.get("OMNISUS_E2E_UFS", "RR,SP")
UFS = list(sus.ALL_UFS) if _UFS == "ALL" else _UFS.split(",")


def _cells(uf: str, ano_sim: int) -> list[str]:
    """The code cells, without `!` lines, with `UF` and `ANO_SIM` replaced."""
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        code = "\n".join(
            line for line in "".join(cell["source"]).splitlines() if not line.startswith("!")
        )
        if 'UF = "RR"' in code:
            assert code.count('UF = "RR"') == 1 and code.count("ANO_SIM = 2022") == 1
            code = code.replace('UF = "RR"', f'UF = "{uf}"')
            code = code.replace("ANO_SIM = 2022", f"ANO_SIM = {ano_sim}")
        cells.append(code)
    return cells


@pytest.fixture(scope="module")
def lake(tmp_path_factory):
    return tmp_path_factory.mktemp("lake")


def _run(uf: str, ano_sim: int, lake: Path, monkeypatch, capsys) -> tuple[dict, str]:
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(lake))
    namespace: dict = {"display": lambda *args, **kwargs: None}
    for i, code in enumerate(_cells(uf, ano_sim)):
        exec(compile(code, f"colab.ipynb, code cell {i + 1}", "exec"), namespace)
    return namespace, capsys.readouterr().out


@pytest.mark.parametrize("uf", UFS)
def test_the_colab_notebook_runs_for_the_uf(uf, lake, monkeypatch, capsys) -> None:
    ns, out = _run(uf, 2022, lake, monkeypatch, capsys)

    assert ns["obitos"].height > 0 and ns["aih"].height > 0
    assert f"DO{uf}2022.dbc" in out and f"RD{uf}2301.dbc" in out
    assert "IBGE · população (ibge_populacao)" in out
    municipios = ns["taxa"]["municipio"].to_list()
    assert municipios and len(municipios) == len(set(municipios))
    assert ns["taxa"]["obitos"].sum() <= ns["obitos"].height
    taxa = ns["taxa"]
    esperada = [1e5 * o / p for o, p in zip(taxa["obitos"], taxa["populacao"], strict=True)]
    assert taxa["obitos_por_100_mil"].to_list() == pytest.approx(esperada, abs=0.05)


def test_a_scope_without_a_validated_source_still_runs(lake, monkeypatch, capsys) -> None:
    """SIM RR 2019 is not in `validated_sources`: no harmonised categories."""
    with pytest.warns(UserWarning, match="sim_obitos: harmonised categories left out"):
        ns, out = _run("RR", 2019, lake, monkeypatch, capsys)

    assert "idade_anos_completos" not in ns["obitos"].columns
    assert "load deixou as categorias harmonizadas de fora" in out
    assert "DORR2019.dbc" in out
