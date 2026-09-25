"""Plan folder, import outcomes JSON, and the unattended-run flag."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from omnisus._version import __version__
from omnisus.lake.catalog import data_dir
from omnisus.sources._base import ImportReport, ScopeKey


def run_without_buttons(cli_args: Mapping[str, object]) -> bool:
    """`-- --executar true` percorre as células de rede/escrita sem a UI.

    Combina com `EXECUTAR = True` na célula de parâmetros. Em `marimo edit`
    os argumentos CLI não chegam à célula: use a constante do notebook.
    """
    return str(cli_args.get("executar", "false")).lower() == "true"


def write_json(path: Path, payload: object) -> Path:
    text = json.dumps(payload, default=str, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


def save_plan(target: str, **details: Any) -> tuple[dict[str, Any], Path]:
    """Create the run folder and write `plano.json` before any download."""
    now = datetime.now(UTC)
    run_id = f"{now:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    folder = data_dir() / "execucoes" / run_id
    folder.mkdir(parents=True)
    plan = {
        **details,
        "target": target,
        "run_id": run_id,
        "omnisus": __version__,
        "created_at_utc": now.isoformat(),
    }
    write_json(folder / "plano.json", plan)
    return plan, folder


def outcomes_table(report: ImportReport) -> list[dict[str, Any]]:
    return [
        {
            "scope": str(outcome.scope),
            "status": outcome.status,
            "rows": outcome.result.rows if outcome.result else None,
            "reason": outcome.reason,
        }
        for outcome in report.outcomes
    ]


def record_import(
    folder: Path,
    report: ImportReport,
    unresolved: Iterable[tuple[int, ScopeKey]] = (),
) -> list[dict[str, Any]]:
    """Write `resultado.json` and return the outcomes table for display."""
    rows = outcomes_table(report)
    write_json(
        folder / "resultado.json",
        {
            "rows_imported": report.rows,
            "outcomes": rows,
            "unresolved": [{"index": i, "scope": str(scope)} for i, scope in unresolved],
        },
    )
    return rows
