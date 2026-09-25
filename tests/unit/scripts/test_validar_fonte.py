"""`scripts/metadados/validar_fonte.py`: audit one more source for the analytical rules.

Real data: `sih_rr_2024_01_mini.dbc` is RDRR2401.dbc (SHA-256 37741f8b…), which is not
in SIH `validated_sources`; `sim_rr_2023_mini.dbc` is DORR2023.dbc, which is.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import yaml

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.inventory import ResolvedSource
from tests.support.datasus_names import filename_for
from tests.support.listings import fixture_entry

ROOT = Path(__file__).resolve().parents[3]
DBC = ROOT / "tests" / "fixtures" / "dbc"
DICIONARIOS = ROOT / "src" / "omnisus" / "data" / "dicionarios"
SIH_RR_2024_01 = ScopeKey(uf="RR", ano=2024, mes=1)


def load_script():
    script = ROOT / "scripts" / "metadados" / "validar_fonte.py"
    spec = importlib.util.spec_from_file_location("validar_fonte", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The script against a copy of the dictionaries and a fake server listing fixtures."""
    module = load_script()
    served = {
        ("sih_aih_reduzida", SIH_RR_2024_01): "sih_rr_2024_01_mini",
        ("sim_obitos", ScopeKey(uf="RR", ano=2023)): "sim_rr_2023_mini",
    }
    contents = {}

    def list_sources(d, **_kw):
        sources = {}
        for (dataset, scope), fixture in served.items():
            if dataset != d.name:
                continue
            raw = (DBC / f"{fixture}.dbc").read_bytes()
            entry = fixture_entry(d.directories()["final"], filename_for(d, scope, None), raw)
            contents[entry.path] = raw
            sources[scope] = ResolvedSource(release="final", files=(entry,))
        return sources

    async def fetch(entry, **_kw):
        return contents[entry.path]

    monkeypatch.setattr(module, "list_sources", list_sources)
    monkeypatch.setattr(module, "fetch_dbc_bytes", fetch)
    dictionaries = tmp_path / "dicionarios"
    shutil.copytree(DICIONARIOS, dictionaries)
    paths = {
        "dictionaries": dictionaries,
        "evidence": tmp_path / "evidence",
        "downloads": tmp_path / "downloads",
    }
    return module, paths


def _validated(dictionaries: Path, dataset: str) -> list[dict]:
    raw = yaml.safe_load((dictionaries / f"{dataset}.yaml").read_text(encoding="utf-8"))
    return raw["x-analytics"]["validated_sources"]


def test_audit_writes_evidence_and_leaves_the_dictionary_alone(workspace) -> None:
    module, paths = workspace
    before = (paths["dictionaries"] / "sih_aih_reduzida.yaml").read_bytes()

    code = module.main(
        ["sih_aih_reduzida", "--uf", "RR", "--year", "2024", "--month", "1"], **paths
    )

    assert code == 0
    (folder,) = paths["evidence"].glob("*/validacao-*")
    manifest = json.loads((folder / "manifest.json").read_text())
    acceptance = json.loads((folder / "acceptance.json").read_text())
    sha = hashlib.sha256((DBC / "sih_rr_2024_01_mini.dbc").read_bytes()).hexdigest()
    assert manifest[0]["sha256"] == sha
    assert manifest[0]["url"].endswith("/SIHSUS/200801_/Dados/RDRR2401.dbc")
    (audited,) = acceptance["files"]
    assert audited["candidate"] is True
    assert audited["states"]["sexo_status"] == [{"status": "valid", "n": 3714}]
    assert (paths["dictionaries"] / "sih_aih_reduzida.yaml").read_bytes() == before


def test_accept_appends_the_source_and_nothing_else(workspace) -> None:
    module, paths = workspace
    yaml_path = paths["dictionaries"] / "sih_aih_reduzida.yaml"
    before = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    code = module.main(
        ["sih_aih_reduzida", "--uf", "RR", "--year", "2024", "--month", "1", "--accept"],
        **paths,
    )

    assert code == 0
    after = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    added = after["x-analytics"]["validated_sources"].pop()
    assert added == {
        "uf": "RR",
        "ano": 2024,
        "mes": 1,
        "release": "final",
        "source_sha256": hashlib.sha256(
            (DBC / "sih_rr_2024_01_mini.dbc").read_bytes()
        ).hexdigest(),
    }
    assert after == before


def test_an_already_validated_source_is_not_added_twice(workspace) -> None:
    module, paths = workspace
    before = _validated(paths["dictionaries"], "sim_obitos")

    code = module.main(["sim_obitos", "--uf", "RR", "--year", "2023", "--accept"], **paths)

    assert code == 0
    assert _validated(paths["dictionaries"], "sim_obitos") == before


def test_a_scope_the_server_does_not_list_writes_nothing(workspace) -> None:
    module, paths = workspace

    code = module.main(
        ["sih_aih_reduzida", "--uf", "AC", "--year", "2024", "--month", "1", "--accept"],
        **paths,
    )

    assert code == 1
    assert not paths["evidence"].exists()
    assert _validated(paths["dictionaries"], "sih_aih_reduzida") == _validated(
        DICIONARIOS, "sih_aih_reduzida"
    )
