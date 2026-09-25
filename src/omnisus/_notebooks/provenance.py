"""Citation record written at the end of a notebook run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from omnisus._notebooks.plan import write_json
from omnisus._version import __version__
from omnisus.research import citation_from_publications


def record_provenance(
    folder: Path,
    *,
    plan: Mapping[str, Any],
    publications: Sequence[Mapping[str, Any]],
    snapshot_id: int,
    queries: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Write `proveniencia.json`: enough to cite and replay the result.

    Each query is `{"sql": str, "parameters": list}`: the exact statement and
    positional parameters of that execution, so the query can be replayed
    without guessing which UF, year or month it used.
    """
    for name, query in queries.items():
        if not isinstance(query, Mapping) or "sql" not in query or "parameters" not in query:
            raise ValueError(f"query {name!r} needs 'sql' and 'parameters' to be replayable")
    record = {
        "plan": dict(plan),
        "publications": [dict(row) for row in publications],
        "snapshot_id": snapshot_id,
        "citation": citation_from_publications(
            publications,
            snapshot_id=snapshot_id,
            dataset=plan.get("dataset") if isinstance(plan.get("dataset"), str) else None,
            run_id=plan.get("run_id") if isinstance(plan.get("run_id"), str) else None,
        ).text,
        "queries": {
            name: {"sql": query["sql"], "parameters": list(query["parameters"])}
            for name, query in queries.items()
        },
        "omnisus": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(folder / "proveniencia.json", record)
    return record
