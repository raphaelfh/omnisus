"""Benchmark DBC staging and publication, creating a fresh lake for each round.

The resource script additionally isolates publication from pre-staged Parquet.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from omnisus.lake import Lake
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet


@pytest.mark.perf
@pytest.mark.parametrize("backend", ["python", "rust"])
def test_bench_full_pipeline_sim(benchmark, dbc_fixture, tmp_path, monkeypatch, backend) -> None:
    if backend == "rust":
        pytest.importorskip("omnisus_dbf")
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", backend)
    fixture: Path = dbc_fixture("sim_rr_2023_mini")
    raw = fixture.read_bytes()

    def run() -> int:
        with TemporaryDirectory(prefix="bench-lake-", dir=tmp_path) as directory:
            root = Path(directory)
            staging = root / "input.parquet"
            dbc_bytes_to_parquet(raw, staging, dataset="sim_obitos", ano=2023, uf="RR")
            with Lake.local(f"ducklake:{root}/fresh.ducklake") as lake:
                result = lake.ingest_parquet("sim_obitos", staging, partition_by=("ano", "uf"))
                return result.rows

    rows = benchmark.pedantic(run, rounds=7, warmup_rounds=1, iterations=1)
    assert rows > 0
