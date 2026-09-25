"""Row counts in the lake versus the publication manifest, per scope."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from omnisus.lake import LakeReader
from omnisus.lake.publication import scope_filter
from omnisus.lake.sql import qualified
from omnisus.sources._base import ScopeKey


def reconcile(
    reader: LakeReader, dataset: str, scopes: Sequence[ScopeKey]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Lake counts versus published rows, per scope, plus the active publications."""
    active = [
        row
        for row in reader.publications()
        if row["dataset"] == dataset and row["active"] and row["scope"] in scopes
    ]
    comparison = []
    for scope in scopes:
        where, args = scope_filter(scope)
        sql = f"SELECT count(*) FROM {qualified(reader.alias, dataset)} WHERE {where}"
        counted = reader.connect().execute(sql, args).fetchone()
        assert counted is not None
        (in_lake,) = counted
        published = sum(row["rows"] for row in active if row["scope"] == scope)
        comparison.append(
            {
                "scope": str(scope),
                "lake_rows": in_lake,
                "published_rows": published,
                "matches": in_lake == published,
            }
        )
    return comparison, active
