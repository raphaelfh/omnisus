"""Local, fresh-process DBF benchmarks; no network or nationwide inference.

PYTHONPATH=src .venv/bin/python scripts/benchmark_resources.py --repeat 4

Defaults to one warmup and seven measurements per backend/corpus/phase, with
alternating backend order. --repeat is deterministic DBF record amplification,
not the number of rounds. --comparison historical preserves baseline/staging.
RSS uses Unix resource.getrusage, so controlled runs require Linux or macOS.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import polars as pl
import pyarrow.parquet as pq

from omnisus.sources.datasus_ftp import dbc, parse
from omnisus.sources.datasus_ftp.dbf_batches import open_dbf_batches
from omnisus.sources.datasus_ftp.native import API_VERSION
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = [
    ("sim_rr_2023_mini", "sim_obitos", 2023, None),
    ("sih_rr_2024_01_mini", "sih_aih_reduzida", 2024, 1),
]
PHASES = ("dbf_to_arrow", "parquet", "lake_publication")
METRICS = ("seconds", "peak_rss_bytes", "peak_temp_disk_bytes_sampled")


def file_hash(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def disk_bytes(root):
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass
    return total


def peak_rss():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def measure(operation, root):
    """Capture before validation; ru_maxrss includes imports and input setup."""
    peak_disk = disk_bytes(root)
    before_rss = peak_rss()
    stopped = threading.Event()

    def monitor():
        nonlocal peak_disk
        while not stopped.is_set():
            peak_disk = max(peak_disk, disk_bytes(root))
            stopped.wait(0.005)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    start = time.perf_counter()
    try:
        rows = operation()
        seconds = time.perf_counter() - start
        rss = peak_rss()
        peak_disk = max(peak_disk, disk_bytes(root))
    finally:
        stopped.set()
        thread.join()
    return {
        "seconds": seconds,
        "rows": rows,
        "peak_rss_bytes": rss,
        "rss_before_phase_bytes": before_rss,
        "peak_temp_disk_bytes_sampled": peak_disk,
        "temp_sample_interval_ms": 5,
    }


def signature(batches):
    """Ordered logical values and schema, retaining at most 1,024 Python rows."""
    digest = hashlib.sha256()
    rows = 0
    schemas = []
    for batch in batches:
        schema = [[field.name, str(field.type), field.nullable] for field in batch.schema]
        if not schemas or schemas[-1] != schema:
            schemas.append(schema)
        rows += batch.num_rows
        for offset in range(0, batch.num_rows, 1024):
            for row in batch.slice(offset, 1024).to_pylist():
                digest.update((json.dumps(row, default=str, ensure_ascii=False) + "\n").encode())
    return {"rows": rows, "ordered_rows_sha256": digest.hexdigest(), "schemas": schemas}


def parquet_signature(path):
    with pq.ParquetFile(path) as parquet:
        return signature(parquet.iter_batches(batch_size=1024))


def assert_rust_used(mode):
    """Explicit native selection must both import successfully and open a reader."""
    if mode != "rust":
        return None
    import omnisus_dbf as native
    from omnisus_dbf import _native

    if native.API_VERSION != API_VERSION:
        raise AssertionError(f"Expected native API_VERSION={API_VERSION}")
    original = native.open_reader
    calls = {
        "open_reader_calls": 0,
        "module": native.__file__,
        "binary": _native.__file__,
        "binary_sha256": file_hash(_native.__file__),
        "version": native.__version__,
    }

    def counted(*args, **kwargs):
        reader = original(*args, **kwargs)
        calls["open_reader_calls"] += 1
        return reader

    def forbidden(*args, **kwargs):
        raise AssertionError("Rust benchmark unexpectedly invoked Python record parsing")

    native.open_reader = counted
    parse._stream_records = forbidden
    return calls


def historical_parquet(raw, target, args):
    """Reproduce the old accumulating Polars parser solely for historical probes."""
    dic = load_dicionario(args.dataset)
    dbf = dbc.decompress_bytes(raw)
    parse._check_dbf_length(dbf, dataset=args.dataset)
    batches, buffer, count = [], [], 0
    records = parse._stream_records(dbf, encoding=dic.encoding)
    try:
        for record in records:
            count += 1
            buffer.append(record)
            if len(buffer) >= parse.BATCH_ROWS:
                batches.append(pl.DataFrame(buffer, infer_schema_length=None))
                buffer.clear()
        if buffer:
            batches.append(pl.DataFrame(buffer, infer_schema_length=None))
    finally:
        records.close()
    parse._check_record_count(dbf, count, dataset=args.dataset)
    frame = pl.concat(batches, how="diagonal_relaxed")
    partitions = [pl.lit(args.ano).cast(pl.UInt16).alias("ano"), pl.lit("RR").alias("uf")]
    if args.mes is not None:
        partitions.append(pl.lit(args.mes).cast(pl.UInt8).alias("mes"))
    frame.rename({c: c.lower() for c in frame.columns}).with_columns(
        partitions
    ).lazy().sink_parquet(target)
    return count


def worker(args):
    parse.BATCH_ROWS = args.batch_rows
    os.environ["OMNISUS_DBF_BACKEND"] = "python" if args.worker == "staging" else args.worker
    native = assert_rust_used(args.worker) if args.phase != "lake_publication" else None
    if args.phase == "lake_publication":
        installed = {
            row[0]: row[1]
            for row in duckdb.sql(
                "SELECT extension_name, installed FROM duckdb_extensions() "
                "WHERE extension_name IN ('ducklake', 'sqlite_scanner')"
            ).fetchall()
        }
        if not all(installed.get(name) for name in ("ducklake", "sqlite_scanner")):
            raise RuntimeError("Benchmark requires locally cached DuckLake and SQLite extensions")
    raw = None if args.phase == "lake_publication" else Path(args.input).read_bytes()
    if args.dbf:
        dbc.decompress_bytes = lambda _: raw
    with tempfile.TemporaryDirectory(prefix="dbf-bench-") as directory:
        tempfile.tempdir = directory
        root = Path(directory)
        target = Path(args.staging_output) if args.staging_output else root / "output.parquet"
        encoding = load_dicionario(args.dataset).encoding
        lake = None

        def operation():
            nonlocal lake
            if args.phase == "dbf_to_arrow":
                count = 0
                with open_dbf_batches(
                    raw, encoding=encoding, batch_rows=args.batch_rows, backend=args.worker
                ) as batches:
                    for batch in batches:
                        count += batch.num_rows
                        del batch
                return count
            if args.phase == "parquet":
                if args.worker == "baseline":
                    return historical_parquet(raw, target, args)
                return dbc_bytes_to_parquet(
                    raw, target, dataset=args.dataset, ano=args.ano, uf="RR", mes=args.mes
                ).rows

            from omnisus.lake import Lake
            from omnisus.sources._base import ScopeKey

            lake = Lake.local(f"ducklake:{root}/fresh.ducklake")
            result = lake.publish_scope(
                args.dataset,
                Path(args.input),
                scope=ScopeKey(ano=args.ano, uf="RR", mes=args.mes),
                source_sha256=args.source_sha256,
                parser_version="dbc-staging-v1:benchmark",
                partition_by=("ano", "uf") if args.mes is None else ("ano", "uf", "mes"),
            )
            return result.rows

        gc.collect()
        measured = measure(operation, root)
        measured.update({"mode": args.worker, "phase": args.phase})
        if native is not None:
            if not native["open_reader_calls"]:
                raise AssertionError("No native reader used during timed operation")
            measured["native_evidence"] = dict(native)
        try:
            if args.phase == "dbf_to_arrow":
                with open_dbf_batches(
                    raw, encoding=encoding, batch_rows=args.batch_rows, backend=args.worker
                ) as batches:
                    measured["validation"] = signature(batches)
            elif args.phase == "parquet":
                measured["output_bytes"] = target.stat().st_size
                measured["validation"] = parquet_signature(target)
                if args.worker in ("baseline", "staging"):
                    # Historical Polars writes large_string, while Arrow staging
                    # writes string; retain that comparison's logical schema.
                    measured["validation"]["schemas"] = [
                        [
                            [name, str(dtype)]
                            for name, dtype in pl.read_parquet_schema(target).items()
                        ]
                    ]
            else:
                # DuckLake row IDs preserve insertion order; an unordered SELECT
                # would not provide evidence for the ordered-row contract.
                result = lake.connect().execute(
                    f'SELECT * FROM lake."{args.dataset}" ORDER BY rowid'
                )
                with result.to_arrow_reader(batch_size=1024) as reader:
                    measured["validation"] = signature(reader)
                expected = parquet_signature(args.input)
                if measured["validation"] != expected:
                    raise AssertionError("Published rows/schema differ from staging Parquet")
                measured["publication_matches_staging"] = True
                measured["backend_in_timed_phase"] = (
                    "none; input was pre-staged in another process"
                )
            if measured["rows"] != measured["validation"]["rows"]:
                raise AssertionError("Timed row count differs from validation")
        finally:
            if lake is not None:
                lake.close()
        print(json.dumps(measured))


def stats(values):
    median = statistics.median(values)
    return {
        "median": median,
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        "median_absolute_deviation": statistics.median(abs(value - median) for value in values),
    }


def run_worker(args, case, phase, mode, path, *, staging_output=None):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        mode,
        "--phase",
        phase,
        "--input",
        str(path),
        "--dataset",
        case["dataset"],
        "--ano",
        str(case["ano"]),
        "--batch-rows",
        str(args.batch_rows),
        "--source-sha256",
        case["sha256"],
    ]
    if case["mes"] is not None:
        command.extend(["--mes", str(case["mes"])])
    if phase == "parquet" and case["amplified"]:
        command.append("--dbf")
    if staging_output is not None:
        command.extend(["--staging-output", str(staging_output)])
    process = subprocess.run(command, capture_output=True, text=True, env=os.environ.copy())
    if process.returncode:
        raise RuntimeError(f"Worker failed ({mode}, {phase}):\n{process.stdout}\n{process.stderr}")
    result = json.loads(process.stdout.strip().splitlines()[-1])
    native = result.get("native_evidence")
    if native is not None:
        previous = getattr(args, "native_binary_sha256", native["binary_sha256"])
        if previous != native["binary_sha256"]:
            raise AssertionError("Native binary changed during benchmark")
        args.native_binary_sha256 = native["binary_sha256"]
    return result


def corpus(directory, repeat):
    cases = []
    for name, dataset, ano, mes in FIXTURES:
        fixture = ROOT / "tests/fixtures/dbc" / f"{name}.dbc"
        data = dbc.decompress_bytes(fixture.read_bytes())
        nrec, header, length = parse._read_dbf_geometry(data)
        kinds = Counter()
        for offset in range(32, header, 32):
            if data[offset] == 13:
                break
            kinds[chr(data[offset + 11])] += 1
        for amplified in (False, True):
            factor = repeat if amplified else 1
            label = name + ("_dbf_amplified" if amplified else "")
            path = directory / f"{label}.dbf"
            with path.open("wb") as output:
                if amplified:
                    patched = bytearray(data[:header])
                    patched[4:8] = (nrec * factor).to_bytes(4, "little")
                    output.write(patched)
                    records = memoryview(data)[header : header + nrec * length]
                    for _ in range(factor):
                        output.write(records)
                    output.write(b"\x1a")
                else:
                    output.write(data)
            cases.append(
                {
                    "corpus": label,
                    "dataset": dataset,
                    "ano": ano,
                    "mes": mes,
                    "source_fixture": str(fixture.relative_to(ROOT)),
                    "source_dbc_sha256": file_hash(fixture),
                    "source_dbc_bytes": fixture.stat().st_size,
                    "sha256": file_hash(path),
                    "dbf_bytes": path.stat().st_size,
                    "declared_records": nrec * factor,
                    "field_types": dict(kinds),
                    "encoding": load_dicionario(dataset).encoding,
                    "repeat": factor,
                    "amplified": amplified,
                    "dbf_path": path,
                    "parquet_input": path if amplified else fixture,
                }
            )
    return cases


def environment(cpu_description=None):
    cpu = platform.processor()
    cpu_detection_error = None
    if sys.platform == "darwin":
        detected = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
        )
        if detected.returncode == 0:
            cpu = detected.stdout.strip()
        else:
            cpu_detection_error = detected.stderr.strip()
    elif Path("/proc/cpuinfo").exists():
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            cpu,
        )
    packages = {}
    for name in (
        "omnisus",
        "omnisus-dbf",
        "dbfread2",
        "pyarrow",
        "polars",
        "duckdb",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    lock = ROOT / "native/omnisus-dbf/Cargo.lock"
    crates = {}
    if lock.exists():
        crates = {
            package["name"]: package["version"]
            for package in tomllib.loads(lock.read_text())["package"]
            if package["name"] in ("arrow-array", "arrow-schema", "arrow-pyarrow", "pyo3")
        }
    return {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu_description or cpu,
        "cpu_description_override": cpu_description,
        "cpu_detection_error": cpu_detection_error,
        "logical_cpus": os.cpu_count(),
        "packages": packages,
        "crates": crates,
        "duckdb_extensions": duckdb.sql(
            "SELECT extension_name, extension_version, installed FROM duckdb_extensions() "
            "WHERE extension_name IN ('ducklake', 'sqlite_scanner') ORDER BY extension_name"
        ).fetchall(),
        "environment": {
            name: os.environ.get(name)
            for name in (
                "OMNISUS_DBF_BACKEND",
                "POLARS_MAX_THREADS",
                "OMP_NUM_THREADS",
                "RAYON_NUM_THREADS",
            )
        },
        "source_sha256": {
            str(path.relative_to(ROOT)): file_hash(path)
            for path in (
                ROOT / "scripts/benchmark_resources.py",
                ROOT / "src/omnisus/sources/datasus_ftp/parse.py",
                ROOT / "src/omnisus/sources/datasus_ftp/dbf_contract.py",
                ROOT / "src/omnisus/sources/datasus_ftp/dbf_batches.py",
                ROOT / "src/omnisus/sources/datasus_ftp/staging.py",
                ROOT / "native/omnisus-dbf/Cargo.lock",
            )
            if path.exists()
        },
    }


def comparisons(cases):
    observed = []
    for case in cases:
        for phase in case["phases"]:
            summaries = phase["summary"]
            if {"python", "rust"} <= summaries.keys():
                python, rust = summaries["python"], summaries["rust"]
                observed.append(
                    {
                        "corpus": case["corpus"],
                        "phase": phase["phase"],
                        "python_over_rust_median_seconds": python["seconds"]["median"]
                        / rust["seconds"]["median"],
                        "rust_over_python_median_peak_rss": rust["peak_rss_bytes"]["median"]
                        / python["peak_rss_bytes"]["median"],
                    }
                )
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", choices=["backends", "historical"], default="backends")
    parser.add_argument(
        "--backend",
        choices=["python", "rust"],
        action="append",
        help="Repeat to select both; default is both backends",
    )
    parser.add_argument("--phases", nargs="+", choices=PHASES, default=list(PHASES))
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repeat", type=int, default=12)
    parser.add_argument("--batch-rows", type=int, default=100_000)
    parser.add_argument("--cpu-description", help="Verified CPU model if sandbox blocks detection")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/rust-dbf-performance.json")
    parser.add_argument(
        "--rust-build-profile",
        choices=["release", "unknown"],
        default="unknown",
        help="Record release only after verifying the installed wheel build",
    )
    parser.add_argument("--rust-wheel", type=Path, help="Local release wheel used for this run")
    parser.add_argument(
        "--worker", choices=["python", "rust", "baseline", "staging"], help=argparse.SUPPRESS
    )
    parser.add_argument("--phase", choices=PHASES, default="parquet", help=argparse.SUPPRESS)
    parser.add_argument("--input", help=argparse.SUPPRESS)
    parser.add_argument("--dataset", default="sim_obitos", help=argparse.SUPPRESS)
    parser.add_argument("--ano", type=int, default=2023, help=argparse.SUPPRESS)
    parser.add_argument("--mes", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--dbf", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--staging-output", help=argparse.SUPPRESS)
    parser.add_argument("--source-sha256", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if min(args.rounds, args.repeat, args.batch_rows) < 1 or args.warmups < 0:
        parser.error("rounds, repeat and batch-rows must be positive; warmups must be nonnegative")
    if args.worker:
        worker(args)
        return
    modes = list(dict.fromkeys(args.backend or ["python", "rust"]))
    phases = args.phases
    if args.comparison == "historical":
        modes, phases = ["baseline", "staging"], ["parquet"]
    evidence = {
        "completed": False,
        "invocation": [sys.executable, *sys.argv],
        "environment": environment(args.cpu_description),
        "comparison": args.comparison,
        "batch_rows": args.batch_rows,
        "rounds": args.rounds,
        "warmups": args.warmups,
        "rust_build_profile": args.rust_build_profile,
        "rust_wheel": None
        if args.rust_wheel is None
        else {"path": str(args.rust_wheel), "sha256": file_hash(args.rust_wheel)},
        "method": {
            "fresh_process_per_run": True,
            "order": "alternate backend order each round",
            "validation": "after timing/RSS capture; streaming ordered rows and Arrow schema",
            "rss": "Unix ru_maxrss captured before validation; includes imports and phase setup",
            "dbf_to_arrow": "read DBF bytes before timer; consume and discard one batch at a time",
            "dbc_to_parquet": "read DBC bytes before timer; includes decompression, parsing, IPC and Parquet",
            "dbf_to_parquet": "amplified DBF only; decompression bypassed, never counted as DBC time",
            "lake_publication": "pre-stage in separate process; time fresh Lake.local plus publish_scope commit; close after validation",
            "network": "none; versioned fixtures and locally cached DuckDB extensions required",
        },
        "limitations": [
            "Local synthetic amplification repeats fixture records and does not represent national heterogeneity.",
            "The amplified input is DBF, not recompressed DBC; no invented decompression speedup.",
            "No OS page-cache eviction; process warmups do not warm the measured Python interpreter.",
            "Temporary disk sampled every 5 ms is a lower bound; input corpus files are excluded.",
            "RSS includes process imports/input setup; validation happens after the captured high-water mark.",
            "Small local samples and background machine activity limit extrapolation and statistical confidence.",
            "DBC decompression still materializes the entire DBF; native reader owns an initial DBF copy.",
            "Lake timings include catalog creation and transactional publication, and exclude parsing and teardown.",
        ],
        "cases": [],
    }
    if args.comparison == "historical":
        evidence["method"]["validation"] = (
            "after timing/RSS capture; streaming ordered rows and logical Polars schema"
        )
    with tempfile.TemporaryDirectory(prefix="dbf-corpus-") as directory:
        root = Path(directory)
        for case in corpus(root, args.repeat):
            output_case = {
                key: value
                for key, value in case.items()
                if key not in ("dbf_path", "parquet_input")
            }
            output_case["phases"] = []
            evidence["cases"].append(output_case)
            for phase in phases:
                name = (
                    ("dbf_to_parquet" if case["amplified"] else "dbc_to_parquet")
                    if phase == "parquet"
                    else phase
                )
                result = {"phase": name, "warmups": [], "runs": []}
                staged = {}
                if phase == "lake_publication":
                    for mode in modes:
                        target = root / f"{case['corpus']}-{mode}.parquet"
                        prep = run_worker(
                            args,
                            case,
                            "parquet",
                            mode,
                            case["parquet_input"],
                            staging_output=target,
                        )
                        staged[mode] = target
                        result.setdefault("staging_preparation", {})[mode] = {
                            "validation": prep["validation"],
                            "native_evidence": prep.get("native_evidence"),
                        }
                reference = None
                for round_number in range(args.warmups + args.rounds):
                    warmup = round_number < args.warmups
                    order = modes if round_number % 2 == 0 else list(reversed(modes))
                    for mode in order:
                        path = (
                            staged[mode]
                            if phase == "lake_publication"
                            else case["dbf_path"]
                            if phase == "dbf_to_arrow"
                            else case["parquet_input"]
                        )
                        run = run_worker(args, case, phase, mode, path)
                        run["round"] = round_number if warmup else round_number - args.warmups
                        validation = run.pop("validation")
                        if reference is None:
                            reference = validation
                        if validation != reference:
                            raise AssertionError(
                                f"Equivalence failed: {case['corpus']}/{name}/{mode}"
                            )
                        run["matches_reference"] = True
                        result["warmups" if warmup else "runs"].append(run)
                result["validation"] = reference
                result["equivalent"] = True
                result["summary"] = {
                    mode: {
                        metric: stats(
                            [run[metric] for run in result["runs"] if run["mode"] == mode]
                        )
                        for metric in METRICS
                    }
                    for mode in modes
                }
                output_case["phases"].append(result)
                print(f"{case['corpus']}: {name} complete", file=sys.stderr, flush=True)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    evidence["observed_comparisons"] = comparisons(evidence["cases"])
    dbc_phases = [
        phase
        for case in evidence["cases"]
        for phase in case["phases"]
        if phase["phase"] == "dbc_to_parquet"
    ]
    if dbc_phases and all({"python", "rust"} <= phase["summary"].keys() for phase in dbc_phases):
        totals = {
            mode: sum(phase["summary"][mode]["seconds"]["median"] for phase in dbc_phases)
            for mode in ("python", "rust")
        }
        evidence["aggregate_dbc_to_parquet"] = {
            "definition": "sum of corpus medians; original real DBC fixtures only",
            "median_seconds_sums": totals,
            "rust_over_python": totals["rust"] / totals["python"],
        }
    evidence["completed"] = True
    evidence["finished_at_utc"] = datetime.now(UTC).isoformat()
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
