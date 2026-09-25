import asyncio

import pytest

from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp._runner import run_scopes
from tests.support import fake_datasus
from tests.support.connection_faults import FaultyConnection


@pytest.mark.asyncio
async def test_dead_producer_does_not_leave_queue_waiter():
    from omnisus.sources.datasus_ftp import _runner

    baseline = asyncio.all_tasks()

    async def fail():
        raise ValueError("producer stopped")

    producer = asyncio.create_task(fail())
    queue = asyncio.Queue(maxsize=1)
    with pytest.raises(_runner._ProducerStoppedError):
        await asyncio.wait_for(_runner._next_fetched(queue, producer), timeout=2)
    assert not (asyncio.all_tasks() - baseline)


@pytest.mark.asyncio
async def test_abnormal_producer_cancels_and_awaits_sibling(tmp_path, monkeypatch):
    from omnisus import ImportAbortedError
    from omnisus.sources.datasus_ftp import _runner

    sibling_started = asyncio.Event()
    sibling_cancelled = asyncio.Event()

    async def fetch(entry, **_kw: object):
        if entry.name == "DORR2021.dbc":
            return b"first"
        sibling_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            sibling_cancelled.set()
            raise

    real_queue = asyncio.Queue

    class FailingQueue(real_queue):
        async def put(self, item):
            if item is not None and item[0] == 0:
                await sibling_started.wait()
                raise RuntimeError("queue rejected item")
            await super().put(item)

    scopes = [ScopeKey(uf="RR", ano=year) for year in (2021, 2022)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, b"first"))
    monkeypatch.setattr(_runner, "fetch_dbc_bytes", fetch)
    monkeypatch.setattr(_runner.asyncio, "Queue", FailingQueue)
    baseline = asyncio.all_tasks()
    with (
        Lake.local(f"ducklake:{tmp_path}/producer.ducklake") as lake,
        pytest.raises(ImportAbortedError),
    ):
        await asyncio.wait_for(
            _runner.run_scopes(
                "sim_obitos", scopes=scopes, lake=lake, concurrency=2, batch_size=1
            ),
            timeout=2,
        )
    assert sibling_cancelled.is_set()
    assert not (asyncio.all_tasks() - baseline)


@pytest.mark.asyncio
async def test_producer_failure_marks_rolled_back_write_as_determined(
    tmp_path, monkeypatch, dbc_fixture
):
    from omnisus import ImportAbortedError
    from omnisus.sources.datasus_ftp import _runner

    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    first_written = asyncio.Event()
    real_publish = _runner.publish_staged

    def observe_first_write(dataset, scope, staged, lake, **kwargs):
        result = real_publish(dataset, scope, staged, lake, **kwargs)
        if scope.ano == 2021:
            first_written.set()
        return result

    real_queue = asyncio.Queue

    class FailSecondPutQueue(real_queue):
        async def put(self, item):
            if item is not None and item[0] == 1:
                await first_written.wait()
                raise RuntimeError("queue rejected second item")
            await super().put(item)

    scopes = [ScopeKey(uf="RR", ano=year) for year in (2021, 2022)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, raw))
    monkeypatch.setattr(_runner, "publish_staged", observe_first_write)
    monkeypatch.setattr(_runner.asyncio, "Queue", FailSecondPutQueue)
    baseline = asyncio.all_tasks()
    with Lake.local(f"ducklake:{tmp_path}/known-rollback.ducklake") as lake:
        with pytest.raises(ImportAbortedError) as caught:
            await asyncio.wait_for(
                _runner.run_scopes(
                    "sim_obitos", scopes=scopes, lake=lake, concurrency=1, batch_size=2
                ),
                # A hang guard, not a speed check: without the native wheel the
                # first scope's real DBC is decoded in pure Python on the runner.
                timeout=30,
            )
        assert [(outcome.scope, outcome.status) for outcome in caught.value.report.outcomes] == [
            (scopes[0], "failed")
        ]
        assert caught.value.unresolved == ((1, scopes[1]),)
        assert (
            lake.connect()
            .execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'lake' AND table_name = 'sim_obitos'"
            )
            .fetchall()
            == []
        )
        assert lake.is_usable
    assert not (asyncio.all_tasks() - baseline)


@pytest.mark.asyncio
async def test_cancel_with_full_queue_preserves_previous_commit(
    tmp_path, monkeypatch, dbc_fixture
):
    from omnisus.sources.datasus_ftp import _runner

    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    real_next = _runner._next_fetched
    paused = asyncio.Event()
    hold = asyncio.Event()
    calls = 0

    async def pause_second_item(queue, producer):
        nonlocal calls
        item = await real_next(queue, producer)
        calls += 1
        if calls == 2:
            while not queue.full():  # noqa: ASYNC110 - yield until deterministic state
                await asyncio.sleep(0)
            paused.set()
            await hold.wait()
        return item

    scopes = [ScopeKey(uf="RR", ano=year) for year in range(2015, 2024)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, raw))
    monkeypatch.setattr(_runner, "_next_fetched", pause_second_item)
    baseline = asyncio.all_tasks()
    with Lake.local(f"ducklake:{tmp_path}/cancel.ducklake") as lake:
        task = asyncio.create_task(
            _runner.run_scopes("sim_obitos", scopes=scopes, lake=lake, concurrency=1, batch_size=1)
        )
        try:
            # A hang guard, not a speed check. The first scope is decoded and
            # committed on the loop thread before the pause, so no timer can fire
            # during that work: a 5s guard failed whenever it took longer (pure
            # Python under coverage on the Windows runner; one 72s local stall).
            await asyncio.wait_for(paused.wait(), timeout=300)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=2)
            assert lake.is_usable
            assert lake.connect().execute(
                "SELECT DISTINCT ano FROM lake.sim_obitos"
            ).fetchall() == [(2015,)]
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert not (asyncio.all_tasks() - baseline)


@pytest.mark.asyncio
@pytest.mark.parametrize("years", [(2022,), (2021, 2022, 2023)])
async def test_bad_dbc_is_never_omitted(tmp_path, monkeypatch, dbc_fixture, years):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    scopes = [ScopeKey(uf="RR", ano=year) for year in years]
    fake_datasus.serve(
        monkeypatch, "sim_obitos", {s: b"invalid dbc" if s.ano == 2022 else raw for s in scopes}
    )
    with Lake.local(f"ducklake:{tmp_path}/mixed.ducklake") as lake:
        report = await run_scopes(
            "sim_obitos", scopes=scopes, lake=lake, concurrency=1, batch_size=2
        )
        assert [outcome.scope for outcome in report.outcomes] == scopes
        # 2022 is rejected while staging, before it writes: 2021, in the same
        # batch, still commits.
        expected = ["failed"] if len(years) == 1 else ["ok", "failed", "ok"]
        assert [outcome.status for outcome in report.outcomes] == expected
        if len(years) == 1:
            assert report.rows == 0
        else:
            stored = (
                lake.connect()
                .execute("SELECT ano, count(*) FROM lake.sim_obitos GROUP BY ano ORDER BY ano")
                .fetchall()
            )
            assert stored == [(2021, report.rows // 2), (2023, report.rows // 2)]
            assert report.rows > 0


@pytest.mark.asyncio
async def test_repeated_input_positions_are_preserved(tmp_path, monkeypatch, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    scope = ScopeKey(uf="RR", ano=2023)
    fake_datasus.serve(monkeypatch, "sim_obitos", {scope: raw})
    with Lake.local(f"ducklake:{tmp_path}/repeat.ducklake") as lake:
        report = await run_scopes("sim_obitos", scopes=[scope, scope], lake=lake)
        assert [outcome.scope for outcome in report.outcomes] == [scope, scope]
        assert len(report.ok) == 2
        assert (
            lake.connect().execute("SELECT count(*) FROM lake.sim_obitos").fetchone()[0]
            == report.rows
        )


@pytest.mark.asyncio
async def test_commit_unknown_aborts_without_retry(tmp_path, monkeypatch, dbc_fixture):
    from omnisus import ImportAbortedError

    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    scopes = [ScopeKey(uf="RR", ano=year) for year in (2021, 2022)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, raw))
    with Lake.local(f"ducklake:{tmp_path}/unknown.ducklake") as lake:
        real = lake.connect()
        lake._con = FaultyConnection(real, after={"COMMIT": RuntimeError("ack lost")})
        with pytest.raises(ImportAbortedError) as caught:
            await run_scopes("sim_obitos", scopes=scopes, lake=lake, batch_size=1, concurrency=1)
        assert caught.value.report.rows == 0
        assert caught.value.unresolved == tuple(enumerate(scopes))
        assert real.execute("SELECT DISTINCT ano FROM lake.sim_obitos").fetchall() == [(2021,)]
        assert not lake.is_usable


@pytest.mark.asyncio
async def test_abort_keeps_previously_committed_progress(tmp_path, monkeypatch, dbc_fixture):
    from omnisus import ImportAbortedError

    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()

    class FailSecondCommit(FaultyConnection):
        commits = 0

        def execute(self, sql, parameters=None):
            if sql.strip().upper() == "COMMIT":
                self.commits += 1
                if self.commits == 2:
                    raise RuntimeError("second commit unavailable")
            return super().execute(sql, parameters)

    scopes = [ScopeKey(uf="RR", ano=year) for year in (2021, 2022, 2023)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, raw))
    with Lake.local(f"ducklake:{tmp_path}/partial.ducklake") as lake:
        lake._con = FailSecondCommit(lake.connect())
        with pytest.raises(ImportAbortedError) as caught:
            await run_scopes("sim_obitos", scopes=scopes, lake=lake, batch_size=1, concurrency=1)
        assert [outcome.scope for outcome in caught.value.report.ok] == scopes[:1]
        assert caught.value.report.rows > 0
        assert caught.value.unresolved == ((1, scopes[1]), (2, scopes[2]))


@pytest.mark.asyncio
async def test_nested_runner_rejects_without_disturbing_enclosing_transaction(
    tmp_path, monkeypatch
):
    from contextlib import contextmanager

    scope = ScopeKey(uf="RR", ano=2023)
    fetched = fake_datasus.serve(monkeypatch, "sim_obitos", {scope: b"must not fetch"})
    baseline = asyncio.all_tasks()
    with Lake.local(f"ducklake:{tmp_path}/nested.ducklake") as lake:
        real_transaction = lake.transaction
        attempts = 0

        @contextmanager
        def bounded_transaction():
            nonlocal attempts
            attempts += 1
            if attempts > 2:
                pytest.fail("runner repeatedly attempts nested transaction entry")
            with real_transaction() as receipt:
                yield receipt

        with lake.transaction() as receipt:
            lake.connect().execute("CREATE TABLE lake.caller(i INTEGER)")
            lake.connect().execute("INSERT INTO lake.caller VALUES (1)")
            monkeypatch.setattr(lake, "transaction", bounded_transaction)
            with pytest.raises(RuntimeError, match=r"nested|active|existing"):
                await run_scopes("sim_obitos", scopes=[scope], lake=lake)
            assert lake.in_transaction
            assert lake.is_usable
            assert not receipt.committed
            lake.connect().execute("INSERT INTO lake.caller VALUES (2)")
        assert receipt.committed
        assert lake.connect().execute("SELECT * FROM lake.caller ORDER BY i").fetchall() == [
            (1,),
            (2,),
        ]
        assert not fetched
    assert not (asyncio.all_tasks() - baseline)
