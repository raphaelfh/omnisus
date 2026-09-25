"""The linkage notebook labels through the library, not by hand."""

from pathlib import Path

LINKAGE = Path(__file__).resolve().parents[3] / "notebooks" / "linkage.py"


def test_linkage_labels_er_errors_with_odb_label():
    """The ER dictionary labels `co_erro` (MOTERRO.dbf); the notebook shows it."""
    texto = LINKAGE.read_text(encoding="utf-8")
    assert "não rotula `co_erro`" not in texto
    assert 'columns=["co_erro"]' in texto
