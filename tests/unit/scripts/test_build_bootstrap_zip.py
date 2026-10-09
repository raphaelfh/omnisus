"""CID-10 groups are parsed from a real TAB_SIH member (AGENTS.md rule 2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts import build_bootstrap_zip

SOURCE = Path(__file__).resolve().parents[2] / "fixtures/cnv/CID10GRUPOS.CNV"


def test_official_cid10_groups_are_flat_nonoverlapping_ranges() -> None:
    groups = build_bootstrap_zip.cid10_groups(SOURCE.read_bytes())

    assert len(groups) == 264
    assert groups[0] == ("A00", "A09", "A00-A09", "Doenças infecciosas intestinais")
    assert groups[15] == ("B50", "B64", "B50-B64", "Doenças devidas a protozoários")
    assert groups[46] == ("E10", "E14", "E10-E14", "Diabetes mellitus")
    assert groups[-1] == ("U99", "U99", "U99-U99", "CID 10ª Revisão não disponível")


def test_overlapping_cid10_ranges_are_rejected() -> None:
    """Synthetic corruption of the hashed member tests the decoder's integrity gate."""
    raw = SOURCE.read_bytes().replace(b"B50-B64", b"A00-A09", 1)

    with pytest.raises(ValueError, match="overlap"):
        build_bootstrap_zip.cid10_groups(raw)
