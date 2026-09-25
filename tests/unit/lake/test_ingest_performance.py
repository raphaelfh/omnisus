"""What the performance work changed in the write path, asserted as behaviour.

These are correctness tests for performance work: each pins a property that a
regression would silently undo (extra snapshots, a discarded partition_by, a
third read of staging). Timing is measured in tests/perf/, not here.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from omnisus.lake import Lake


def _frame(n: int = 4) -> pl.LazyFrame:
    return pl.DataFrame(
        {
            "ano": [2020 + (i % 2) for i in range(n)],
            "uf": ["SP" if i % 2 else "RJ" for i in range(n)],
            "v": list(range(n)),
        }
    ).lazy()


def test_one_transaction_makes_one_snapshot_not_one_per_ingest(tmp_path: Path) -> None:
    """One snapshot per scope meant 648 snapshots for a wide SIH
    import; batching is just explicit transaction boundaries around the
    INSERTs that were already happening."""
    with Lake.local(f"ducklake:{tmp_path}/b.ducklake") as lake:
        lake.ingest("t", _frame(), partition_by=("ano", "uf"))
        before = len(lake.snapshots())

        with lake.transaction():
            for _ in range(3):
                lake.ingest("t", _frame())

        batched = len(lake.snapshots()) - before

        before = len(lake.snapshots())
        for _ in range(3):
            lake.ingest("t", _frame())
        unbatched = len(lake.snapshots()) - before

    assert batched == 1, "three ingests in one transaction must commit once"
    assert unbatched == 3, "the same three outside a transaction commit three times"


def test_a_failing_batch_rolls_back_to_nothing(tmp_path: Path) -> None:
    with Lake.local(f"ducklake:{tmp_path}/r.ducklake") as lake:
        lake.ingest("t", _frame())
        rows_before = lake.connect().execute("SELECT count(*) FROM lake.t").fetchone()[0]

        with pytest.raises(RuntimeError), lake.transaction():
            lake.ingest("t", _frame())
            raise RuntimeError("boom")

        rows_after = lake.connect().execute("SELECT count(*) FROM lake.t").fetchone()[0]
    assert rows_after == rows_before, "an aborted batch must leave nothing behind"


def test_declared_partitioning_is_actually_applied(tmp_path: Path) -> None:
    """A row must not lie: `Lake.ingest` accepted `partition_by` and then
    ran `del partition_by`, so every registry row's declared partitioning was a
    promise nothing kept. Asserted physically, on the files DuckLake writes.

    Small writes are inlined into the catalog rather than written as Parquet,
    so this uses enough rows to land on disk.
    """
    with Lake.local(f"ducklake:{tmp_path}/p.ducklake") as lake:
        lake.ingest("t", _frame(n=5_000), partition_by=("ano", "uf"))

    written = [
        path.relative_to(tmp_path).as_posix()
        for path in (tmp_path / "p.ducklake").rglob("*.parquet")
    ]
    assert written, "5k rows should be written as Parquet, not inlined"
    assert all("ano=" in path and "uf=" in path for path in written), written


def test_partitioning_is_not_applied_when_the_row_does_not_declare_it(
    tmp_path: Path,
) -> None:
    """The other direction, so the test above cannot pass by accident."""
    with Lake.local(f"ducklake:{tmp_path}/n.ducklake") as lake:
        lake.ingest("t", _frame(n=5_000))

    written = [
        path.relative_to(tmp_path).as_posix()
        for path in (tmp_path / "n.ducklake").rglob("*.parquet")
    ]
    assert written
    assert not any("ano=" in path for path in written), written


def test_repeated_ingests_do_not_re_ensure_the_table(tmp_path: Path) -> None:
    """Staging was read three times per scope: a schema-only CREATE, the
    INSERT, and a separate SELECT count(*). Only the INSERT is real work."""

    class _Spy:
        def __init__(self, inner: object) -> None:
            self.inner = inner
            self.sql: list[str] = []

        def execute(self, sql: str, *a: object, **k: object) -> object:
            self.sql.append(sql)
            return self.inner.execute(sql, *a, **k)  # type: ignore[attr-defined]

        def __getattr__(self, name: str) -> object:
            return getattr(self.inner, name)

    with Lake.local(f"ducklake:{tmp_path}/e.ducklake") as lake:
        lake.ingest("t", _frame(), partition_by=("ano", "uf"))
        spy = _Spy(lake._con)
        lake._con = spy  # type: ignore[assignment]
        lake.ingest("t", _frame())
        lake._con = spy.inner  # type: ignore[assignment]

    joined = " ".join(spy.sql)
    assert "CREATE TABLE" not in joined, "the table was already ensured this run"
    assert "count(*)" not in joined, (
        "the row count comes from the INSERT itself; the extra scan is gone"
    )
    scans = [q for q in spy.sql if "read_parquet" in q and not q.startswith("DESCRIBE")]
    assert len(scans) == 1, (
        "staging must be scanned exactly once (the INSERT). The DESCRIBE that "
        "reconciles era schemas reads only the Parquet footer, not the data.\n"
        + "\n".join(spy.sql)
    )


def test_ingest_reports_rows_without_a_second_scan(tmp_path: Path) -> None:
    with Lake.local(f"ducklake:{tmp_path}/c.ducklake") as lake:
        result = lake.ingest("t", _frame(n=7), partition_by=("ano", "uf"))
    assert result.rows == 7


def test_ingest_reports_a_real_snapshot_id(tmp_path: Path) -> None:
    """`snapshot_id` was None on every import ever run: ingest asked
    `ducklake_snapshots('lake.t')`, which does not bind, inside a bare
    `except Exception` that turned the error into None."""
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        before = lake.snapshots()
        result = lake.ingest("t", _frame())
        after = lake.snapshots()
        rows = (
            lake.connect().execute("SELECT ano, uf, v FROM lake.t ORDER BY ano, uf, v").fetchall()
        )
    assert result.snapshot_id is not None
    assert result.snapshot_id >= 0
    assert len(after) == len(before) + 1
    assert result.snapshot_id == after[-1]["snapshot_id"]
    assert "tables_created=[main.t]" in after[-1]["changes"]
    assert "inlined_insert=" in after[-1]["changes"]
    assert rows == [(2020, "RJ", 0), (2020, "RJ", 2), (2021, "SP", 1), (2021, "SP", 3)]


def test_snapshots_lists_history_instead_of_raising(tmp_path: Path) -> None:
    """`omnisus lake snapshots` was broken: the old query never bound."""
    with Lake.local(f"ducklake:{tmp_path}/h.ducklake") as lake:
        lake.ingest("t", _frame())
        snaps = lake.snapshots()
    assert snaps, "a lake with an ingest has snapshots"
    assert {"snapshot_id", "snapshot_time", "changes"} == set(snaps[0])


# --- schema drift across DATASUS eras --------------------------------------


def _era(cols: dict[str, list[object]]) -> pl.LazyFrame:
    return pl.DataFrame(cols).lazy()


def test_a_later_era_with_new_columns_widens_the_table(tmp_path: Path) -> None:
    """DATASUS changes its layouts between eras: SIM-DO is 42 columns in 1996,
    45 in 2005, 61 in 2010, 90 in 2015, 89 in 2020. A table created from the
    first scope to land rejected every wider era, so a multi-year import could
    not build a lake at all — the failure only appears against real data,
    because every fixture is a single year."""
    with Lake.local(f"ducklake:{tmp_path}/w.ducklake") as lake:
        lake.ingest("t", _era({"ano": [1996], "uf": ["RR"], "a": [1]}))
        lake.ingest("t", _era({"ano": [2015], "uf": ["RR"], "a": [2], "novo": ["x"]}))
        rows = lake.connect().execute("SELECT ano, a, novo FROM lake.t ORDER BY ano").fetchall()

    assert rows == [(1996, 1, None), (2015, 2, "x")]


def test_an_earlier_era_missing_columns_lands_as_null(tmp_path: Path) -> None:
    """The other direction: columns get removed too (`crm` vanished after 2015).
    A narrower era must land as NULL, never shift values one column left."""
    with Lake.local(f"ducklake:{tmp_path}/n.ducklake") as lake:
        lake.ingest("t", _era({"ano": [2015], "uf": ["RR"], "a": [1], "crm": ["123"]}))
        lake.ingest("t", _era({"ano": [2020], "uf": ["RR"], "a": [2]}))
        rows = lake.connect().execute("SELECT ano, a, crm FROM lake.t ORDER BY ano").fetchall()

    assert rows == [(2015, 1, "123"), (2020, 2, None)]


def test_columns_are_matched_by_name_not_position(tmp_path: Path) -> None:
    """Positional INSERT would silently write `uf` into `a` when the column
    order differs between eras — corrupt data rather than a loud failure."""
    with Lake.local(f"ducklake:{tmp_path}/o.ducklake") as lake:
        lake.ingest("t", _era({"ano": [2020], "uf": ["RR"], "a": [7]}))
        lake.ingest("t", _era({"a": [8], "ano": [2021], "uf": ["AC"]}))
        rows = lake.connect().execute("SELECT ano, uf, a FROM lake.t ORDER BY ano").fetchall()

    assert rows == [(2020, "RR", 7), (2021, "AC", 8)]
