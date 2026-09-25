"""Source identity, declared in the dictionary and checked once per file.

A DATASUS file is identified by the *mode* of its year column (and, when the
layout has one, of its agravo code): the whole file is rejected when the
mode is wrong, while the few off-year or mis-typed records real files carry
(tuberculosis, zika) stay in the lake untouched. Which columns and which code
is a per-dataset fact, so it lives in the YAML's ``x-identity`` block, and
changing it changes ``parser_version`` for free.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from omnisus.sources._base import UF_CODES, ScopeKey
from omnisus.transforms.dictionaries import Dicionario


def _mode(frame: pl.LazyFrame, column: str, *, width: int | None = None) -> str | None:
    """Most frequent trimmed text value (its first ``width`` characters, when given);
    ties break on the value, so the answer is deterministic."""
    value = pl.col(column).cast(pl.String).str.strip_chars()
    if width is not None:
        value = value.str.slice(0, width)
    top = (
        frame.select(value.alias("v"))
        .group_by("v")
        .len()
        .sort(["len", "v"], descending=[True, False])
        .limit(1)
        .collect()
    )
    return top["v"][0] if top.height else None


def validate_identity(staging: Path, dicionario: Dicionario, scope: ScopeKey) -> None:
    """Check each column the dictionary's ``x-identity`` names against ``scope``.

    ``year_column`` holds the year; ``month_column`` the ``AAAAMM`` of the file's month;
    ``uf_column`` a code whose first two digits are the UF's IBGE code (``UF_CODES``).
    ``code_column`` holds the agravo code ``code``. Each is compared by its mode.
    """
    spec = dicionario.raw.get("x-identity")
    if not spec:
        return
    frame = pl.scan_parquet(staging)
    columns = set(frame.collect_schema().names())
    expected = {
        "year_column": ("year", str(scope.ano)),
        "month_column": ("month", f"{scope.ano}{scope.mes or 0:02d}"),
        "uf_column": ("UF code", UF_CODES.get(scope.uf or "", "")),
    }
    for key, (what, want) in expected.items():
        column = spec.get(key)
        if column is None:
            continue
        if column not in columns:
            raise ValueError(f"{dicionario.name}: identity column {column!r} is missing")
        found = _mode(frame, column, width=2 if key == "uf_column" else None)
        if found is None:
            raise ValueError(f"{dicionario.name}: empty source file")
        if found != want:
            raise ValueError(
                f"{dicionario.name}: most frequent {column} is {found}, "
                f"not the scope {what} {want} ({scope})"
            )
    code_column = spec.get("code_column")
    if code_column and code_column in columns:
        code = _mode(frame, code_column)
        if code != spec["code"]:
            raise ValueError(
                f"{dicionario.name}: most frequent {code_column} is {code!r}, not {spec['code']!r}"
            )
