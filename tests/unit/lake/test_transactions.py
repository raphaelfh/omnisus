import asyncio

import polars as pl
import pytest

from omnisus.lake import Lake
from tests.support.connection_faults import FaultyConnection


class CleanupInterrupted(BaseException):
    pass


def test_ingest_results_receive_the_committed_batch_snapshot(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/snap.ducklake") as lake:
        direct = lake.ingest("sample", pl.DataFrame({"i": [1]}).lazy())
        assert direct.snapshot_id == lake.snapshots()[-1]["snapshot_id"]
        with lake.transaction() as receipt:
            first = lake.ingest("sample", pl.DataFrame({"i": [2]}).lazy())
            second = lake.ingest("sample", pl.DataFrame({"i": [3]}).lazy())
            assert first.snapshot_id is None
            assert second.snapshot_id is None
        actual = lake.snapshots()[-1]["snapshot_id"]
        assert first.snapshot_id == second.snapshot_id == receipt.snapshot_id == actual
        assert actual > direct.snapshot_id


def test_rolled_back_result_never_gets_a_snapshot(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/pending.ducklake") as lake:
        with pytest.raises(ValueError), lake.transaction():
            result = lake.ingest("sample", pl.DataFrame({"i": [1]}).lazy())
            raise ValueError("reject")
        assert result.snapshot_id is None
        assert "sample" not in lake.tables()


def test_snapshot_read_failure_does_not_reclassify_a_committed_write(tmp_path, monkeypatch):
    with Lake.local(f"ducklake:{tmp_path}/metadata.ducklake") as lake:
        read = lake._read_snapshot
        calls = 0

        def fail_second_read():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("snapshot query failed")
            return read()

        monkeypatch.setattr(lake, "_read_snapshot", fail_second_read)
        result = lake.ingest("sample", pl.DataFrame({"i": [1]}).lazy())
        assert result.snapshot_id is None
        assert lake.connect().execute("SELECT * FROM lake.sample").fetchall() == [(1,)]
        assert lake.is_usable


def test_schema_cache_recovers_after_rollback(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/cache.ducklake") as lake:
        lake.ingest("sample", pl.DataFrame({"i": [1]}).lazy())
        frame = pl.DataFrame({"i": [2], "new_column": [3]}).lazy()
        with pytest.raises(ValueError, match="abort"), lake.transaction():
            lake.ingest("sample", frame)
            raise ValueError("abort")
        lake.ingest("sample", frame)
        assert lake.connect().execute(
            "SELECT i, new_column FROM lake.sample ORDER BY i"
        ).fetchall() == [(1, None), (2, 3)]


@pytest.mark.parametrize("timing", ["before", "after"])
def test_commit_failure_invalidates_handle(tmp_path, timing):
    from omnisus.lake import CommitOutcomeUnknown

    with Lake.local(f"ducklake:{tmp_path}/commit.ducklake") as lake:
        original = lake.connect()
        injected = RuntimeError("commit acknowledgement failed")
        lake._con = FaultyConnection(original, **{timing: {"COMMIT": injected}})
        with pytest.raises(CommitOutcomeUnknown) as caught, lake.transaction():
            lake.connect().execute("CREATE TABLE lake.sample(i INTEGER)")
            lake.connect().execute("INSERT INTO lake.sample VALUES (1)")
        assert caught.value.__cause__ is injected
        assert lake.is_usable is False
        with pytest.raises(RuntimeError, match="unusable"):
            lake.connect()
        for operation in (
            lake.tables,
            lake.snapshots,
            lake.bootstrap_auxiliares,
            lake.ensure_aux_cnes_view,
            lambda: lake.optimize("sample"),
        ):
            with pytest.raises(RuntimeError, match="unusable"):
                operation()
        if timing == "after":
            assert original.execute("SELECT * FROM lake.sample").fetchall() == [(1,)]


def test_failed_rollback_preserves_original_cause(tmp_path):
    from omnisus.lake import TransactionStateError

    with Lake.local(f"ducklake:{tmp_path}/rollback.ducklake") as lake:
        lake._con = FaultyConnection(
            lake.connect(), before={"ROLLBACK": RuntimeError("rollback unavailable")}
        )
        original = ValueError("bad input")
        with pytest.raises(TransactionStateError) as caught, lake.transaction():
            raise original
        assert caught.value.__cause__ is original
        assert lake.is_usable is False


def test_begin_failure_stops_the_handle(tmp_path):
    from omnisus.lake import TransactionStateError

    with Lake.local(f"ducklake:{tmp_path}/begin.ducklake") as lake:
        injected = RuntimeError("cannot begin")
        lake._con = FaultyConnection(lake.connect(), before={"BEGIN": injected})
        with pytest.raises(TransactionStateError) as caught, lake.transaction():
            pytest.fail("body must not run")
        assert caught.value.__cause__ is injected
        assert not lake.is_usable


@pytest.mark.parametrize("signal", [asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()])
def test_begin_interruption_preserves_signal_and_invalidates_handle(tmp_path, signal):
    with Lake.local(f"ducklake:{tmp_path}/begin-interrupted.ducklake") as lake:
        lake._con = FaultyConnection(lake.connect(), before={"BEGIN": signal})
        with pytest.raises(type(signal)) as caught, lake.transaction():
            pytest.fail("body must not run")
        assert caught.value is signal
        assert lake.is_usable is False


@pytest.mark.parametrize("signal", [asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()])
def test_rollback_interruption_preserves_original_signal(tmp_path, signal):
    with Lake.local(f"ducklake:{tmp_path}/rollback-interrupted.ducklake") as lake:
        cleanup_signal = CleanupInterrupted()
        lake._con = FaultyConnection(lake.connect(), before={"ROLLBACK": cleanup_signal})
        with pytest.raises(type(signal)) as caught, lake.transaction():
            raise signal
        assert caught.value is signal
        assert lake.is_usable is False


def test_empty_and_nested_transactions(tmp_path):
    lake = Lake.local(f"ducklake:{tmp_path}/empty.ducklake")
    with lake.transaction() as receipt:
        assert receipt.committed is False
        with pytest.raises(RuntimeError, match="nested"), lake.transaction():
            pass
    assert receipt.committed is True
    assert receipt.snapshot_id is None
    lake.close()
    lake.close()
    assert lake.is_usable is False


@pytest.mark.parametrize("phase", ["body", "commit"])
@pytest.mark.parametrize("signal_type", [asyncio.CancelledError, KeyboardInterrupt, SystemExit])
def test_first_interruption_during_cleanup_is_preserved(tmp_path, phase, signal_type):
    with Lake.local(f"ducklake:{tmp_path}/cleanup-first.ducklake") as lake:
        original = ValueError("original failure")
        signal = signal_type("cleanup interrupted")
        faults = {"ROLLBACK": signal}
        if phase == "commit":
            faults["COMMIT"] = original
        lake._con = FaultyConnection(lake.connect(), before=faults)
        with pytest.raises(signal_type) as caught, lake.transaction():
            if phase == "body":
                raise original
        assert caught.value is signal
        assert caught.value.__cause__ is original
        assert not lake.is_usable
        assert not lake.in_transaction
        with pytest.raises(RuntimeError, match="unusable"):
            lake.connect()


@pytest.mark.parametrize("signal_type", [asyncio.CancelledError, KeyboardInterrupt, SystemExit])
def test_commit_interruption_precedes_cleanup_interruption(tmp_path, signal_type):
    with Lake.local(f"ducklake:{tmp_path}/commit-first.ducklake") as lake:
        signal = signal_type("commit interrupted")
        lake._con = FaultyConnection(
            lake.connect(), before={"COMMIT": signal, "ROLLBACK": CleanupInterrupted()}
        )
        with pytest.raises(signal_type) as caught, lake.transaction():
            pass
        assert caught.value is signal
        assert not lake.is_usable
