"""The linkage notebook labels through the library, not by hand."""

from pathlib import Path

LINKAGE = Path(__file__).resolve().parents[3] / "notebooks" / "linkage.py"


def test_linkage_labels_er_errors_with_odb_label():
    """The ER dictionary labels `co_erro` (MOTERRO.dbf); the notebook shows it."""
    texto = LINKAGE.read_text(encoding="utf-8")
    assert "não rotula `co_erro`" not in texto
    assert 'columns=["co_erro"]' in texto


def test_linkage_names_the_required_bases_it_cannot_find(monkeypatch, tmp_path, dbc_fixture):
    """Only SIM RR 2022 is listed (the real DORR2022.dbc excerpt): SINASC and SIH RD are
    missing, so the notebook says it needs them and stops, before downloading anything,
    instead of a KeyError (#44)."""
    import importlib.util
    import sys

    from tests.support import fake_datasus

    from omnisus.sources._base import ScopeKey

    sim = ScopeKey(uf="RR", ano=2022)
    baixados = fake_datasus.serve(
        monkeypatch, "sim_obitos", {sim: dbc_fixture("sim_rr_2022_mini").read_bytes()}
    )
    so_o_sim = sys.modules["omnisus.sources.datasus_ftp._runner"].list_sources

    def listagem(d, **kw):
        return so_o_sim(d, **kw) if getattr(d, "name", d) == "sim_obitos" else {}

    for alvo in (
        "omnisus.sources.datasus_ftp._runner.list_sources",
        "omnisus.sources.datasus_ftp.inventory.list_sources",
        "omnisus.list_sources",
    ):
        monkeypatch.setattr(alvo, listagem)
    monkeypatch.setenv("OMNISUS_DATA_DIR", str(tmp_path / "lake"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["linkage.py", "--executar", "true"])
    spec = importlib.util.spec_from_file_location("notebook_linkage", LINKAGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    outputs, defs = module.app.run()

    mensagem = " ".join(str(getattr(o, "text", o)) for o in outputs if o is not None)
    assert "sinasc_nascidos_vivos" in mensagem and "sih_aih_reduzida" in mensagem
    assert "verificacoes" not in defs
    assert baixados == []
