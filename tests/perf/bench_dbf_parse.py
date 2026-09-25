"""DBF → Arrow in isolation, plus DBC → Parquet as a separate phase.

Use scripts/benchmark_resources.py for controlled fresh-process RSS evidence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp.dbf_batches import open_dbf_batches
from omnisus.sources.datasus_ftp.parse import BATCH_ROWS
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario

CASES = [("sim_rr_2023_mini", "sim_obitos"), ("sih_rr_2024_01_mini", "sih_aih_reduzida")]


@pytest.mark.perf
@pytest.mark.parametrize("backend", ["python", "rust"])
@pytest.mark.parametrize(("fixture_name", "dataset"), CASES)
def test_bench_dbf_to_arrow(benchmark, dbc_fixture, backend, fixture_name, dataset) -> None:
    if backend == "rust":
        pytest.importorskip("omnisus_dbf")
    fixture: Path = dbc_fixture(fixture_name)
    dbf = dbc.decompress_bytes(fixture.read_bytes())
    encoding = load_dicionario(dataset).encoding

    def run() -> int:
        count = 0
        with open_dbf_batches(
            dbf, encoding=encoding, batch_rows=BATCH_ROWS, backend=backend
        ) as batches:
            for batch in batches:
                count += batch.num_rows
                del batch
        return count

    rows = benchmark.pedantic(run, rounds=7, warmup_rounds=1, iterations=1)
    assert rows > 0


@pytest.mark.perf
@pytest.mark.parametrize("backend", ["python", "rust"])
@pytest.mark.parametrize(("fixture_name", "dataset"), CASES)
def test_bench_dbc_to_parquet(
    benchmark, dbc_fixture, tmp_path, monkeypatch, backend, fixture_name, dataset
) -> None:
    if backend == "rust":
        pytest.importorskip("omnisus_dbf")
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", backend)
    raw = dbc_fixture(fixture_name).read_bytes()
    target = tmp_path / "staging.parquet"

    def run() -> int:
        return dbc_bytes_to_parquet(raw, target, dataset=dataset, ano=2023, uf="RR").rows

    rows = benchmark.pedantic(run, rounds=7, warmup_rounds=1, iterations=1)
    assert rows > 0
