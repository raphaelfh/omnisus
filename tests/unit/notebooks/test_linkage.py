"""The linkage notebook labels through the library, not by hand."""

import re
from pathlib import Path

LINKAGE = Path(__file__).resolve().parents[3] / "notebooks" / "linkage.py"


def test_linkage_labels_er_errors_with_odb_label():
    """The ER dictionary labels `co_erro` (MOTERRO.dbf); the notebook shows it."""
    texto = LINKAGE.read_text(encoding="utf-8")
    assert "não rotula `co_erro`" not in texto
    assert 'columns=["co_erro"]' in texto


def _rodar(monkeypatch, tmp_path, fonte, servidos):
    """Run the notebook text ``fonte`` with EXECUTAR on, the server listing only
    ``servidos`` (dataset -> {scope: bytes}). Returns the outputs as plain text, the
    defs and the downloaded paths."""
    import importlib.util
    import sys

    from tests.support import fake_datasus

    runner = sys.modules["omnisus.sources.datasus_ftp._runner"]
    listagens, baixados = {}, []
    for dataset, payloads in servidos.items():
        baixados.append(fake_datasus.serve(monkeypatch, dataset, payloads))
        listagens[dataset] = runner.list_sources

    def listagem(d, **kw):
        nome = getattr(d, "name", d)
        return listagens[nome](d, **kw) if nome in listagens else {}

    for alvo in (
        "omnisus.sources.datasus_ftp._runner.list_sources",
        "omnisus.sources.datasus_ftp.inventory.list_sources",
        "omnisus.list_sources",
    ):
        monkeypatch.setattr(alvo, listagem)
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(tmp_path / "lake"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["linkage.py", "--executar", "true"])
    caminho = tmp_path / "linkage.py"
    caminho.write_text(fonte, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("notebook_linkage", caminho)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    outputs, defs = module.app.run()
    html = " ".join(str(getattr(o, "text", o)) for o in outputs if o is not None)
    return re.sub(r"<[^>]+>", "", html), defs, [path for lista in baixados for path in lista]


def test_linkage_names_the_required_bases_it_cannot_find(monkeypatch, tmp_path, dbc_fixture):
    """Only SIM RR 2022 is listed (the real DORR2022.dbc excerpt): SINASC and SIH RD are
    missing, so the notebook says it needs them and stops, before downloading anything,
    instead of a KeyError (#44)."""
    from omnisus.sources._base import ScopeKey

    sim = {ScopeKey(uf="RR", ano=2022): dbc_fixture("sim_rr_2022_mini").read_bytes()}
    texto, defs, baixados = _rodar(
        monkeypatch, tmp_path, LINKAGE.read_text(encoding="utf-8"), {"sim_obitos": sim}
    )

    assert "Faltam: sinasc_nascidos_vivos, sih_aih_reduzida." in texto
    assert "verificacoes" not in defs
    assert baixados == []


def test_linkage_refuses_to_skip_a_required_base(monkeypatch, tmp_path, dbc_fixture):
    """SIM, SINASC and SIH RD are all listed, but SINASC is in PULAR: the notebook names
    it and stops before any download (#44). The SIH listing reuses the real RD RR 2024-01
    excerpt as RR 2022-01; it is listed, never downloaded."""
    from omnisus.sources._base import ScopeKey

    fonte = LINKAGE.read_text(encoding="utf-8")
    assert fonte.count("    PULAR = set()\n") == 1
    fonte = fonte.replace("    PULAR = set()\n", '    PULAR = {"sinasc_nascidos_vivos"}\n')
    servidos = {
        "sim_obitos": {ScopeKey(uf="RR", ano=2022): dbc_fixture("sim_rr_2022_mini").read_bytes()},
        "sinasc_nascidos_vivos": {
            ScopeKey(uf="RR", ano=2022): dbc_fixture("sinasc_rr_2022_mini").read_bytes()
        },
        "sih_aih_reduzida": {
            ScopeKey(uf="RR", ano=2022, mes=1): dbc_fixture("sih_rr_2024_01_mini").read_bytes()
        },
    }
    texto, defs, baixados = _rodar(monkeypatch, tmp_path, fonte, servidos)

    assert "Faltam: sinasc_nascidos_vivos." in texto
    assert "verificacoes" not in defs
    assert baixados == []
