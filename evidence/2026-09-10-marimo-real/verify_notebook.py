"""One-time acceptance check; run from repo root with the prepared local lake."""

import asyncio
import inspect
import io
import json
import runpy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import polars as pl
from marimo._runtime.exceptions import MarimoRuntimeException

import omnisus_db as odb


def run_cell(cell, **refs):
    result = cell.run(**refs)
    return asyncio.run(result) if inspect.isawaitable(result) else result


ns = runpy.run_path("notebooks/api_dados_reais.py")
with (
    patch.object(
        odb, "available", side_effect=AssertionError("Unexpected FTP refresh")
    ) as available,
    patch.object(
        odb, "import_dataset", side_effect=AssertionError("Unexpected import")
    ) as importer,
):
    outputs, definitions = ns["app"].run()
    available.assert_not_called()
    importer.assert_not_called()
assert definitions["real_data"].height == 6557
assert pl.read_parquet(io.BytesIO(definitions["summary_parquet"])).equals(
    definitions["annual_summary"]
)
_, filtered = run_cell(
    ns["filter_real_data"],
    pl=pl,
    real_data=definitions["real_data"],
    residency_filter=SimpleNamespace(value=False),
    type_filter=SimpleNamespace(value="Não fetal"),
    year_filter=SimpleNamespace(value="2022"),
)
assert filtered["filtered"].height == 3246
_, empty = run_cell(
    ns["filter_real_data"],
    pl=pl,
    real_data=definitions["real_data"],
    residency_filter=SimpleNamespace(value=False),
    type_filter=SimpleNamespace(value="Fetal"),
    year_filter=SimpleNamespace(value="Todos"),
)
assert empty["filtered"].is_empty()
try:
    run_cell(
        ns["read_real_lake"],
        manifest={**definitions["manifest"], "snapshots": []},
        odb=odb,
        real_target=definitions["real_target"],
    )
except (AssertionError, MarimoRuntimeException) as exc:
    # marimo wraps failures raised inside a cell, preserving the original cause.
    original = exc.__cause__ or exc
    assert isinstance(original, AssertionError)
    assert "Histórico" in str(original)
else:
    raise AssertionError("Snapshot mismatch was not rejected")
verification = {
    "checked_at_utc": datetime.now(UTC).isoformat(),
    "manifest": definitions["manifest"],
    "quality": definitions["quality"].to_dicts(),
    "transaction": definitions["transaction_evidence"],
    "summary_sha256": definitions["summary_sha256"],
    "checks": {
        "real_import": "passed: 2 ok, 0 failed, 0 skipped",
        "default_open_without_reimport": "passed",
        "row_counts_reconciled": 6557,
        "filter_2022_non_fetal": 3246,
        "empty_fetal_selection": "passed",
        "parquet_export_roundtrip": "passed",
        "changed_snapshot_rejected": "passed",
        "derived_commit_and_rollback": "passed",
    },
}
Path("evidence/2026-09-10-marimo-real/verification.json").write_text(
    json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(verification["checks"], ensure_ascii=False, indent=2))
