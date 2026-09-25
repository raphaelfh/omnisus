"""Build DATASUS file names for tests. Production code resolves names from listings."""

from __future__ import annotations

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import Dataset


def filename_for(d: Dataset, scope: ScopeKey, part: str | None = None) -> str:
    if d.geography == "national":
        return f"{d.prefix}{d.national_code}{scope.ano % 100:02d}.dbc"
    suffix = "" if part is None else (f"_{part}" if part.isdigit() else part)
    if d.monthly:
        return f"{d.prefix}{scope.uf}{scope.ano % 100:02d}{scope.mes:02d}{suffix}.dbc"
    year = f"{scope.ano:04d}" if d.year_digits == 4 else f"{scope.ano % 100:02d}"
    return f"{d.prefix}{scope.uf}{year}.dbc"
