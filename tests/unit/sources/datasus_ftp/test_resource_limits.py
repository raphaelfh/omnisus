import asyncio

import pytest

from omnisus import import_dataset
from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp import fetch
from tests.support import fake_datasus
from tests.support.listings import fixture_entry

SIM_DIR = "/dissemin/publicos/SIM/CID10/DORES"
RR_2023 = ScopeKey(uf="RR", ano=2023)


def test_download_size_is_checked_during_receipt(monkeypatch):
    class FTP:
        def __init__(self, *a, **kw):
            pass

        def connect(self, *a, **kw):
            pass

        def login(self):
            pass

        def cwd(self, *a):
            pass

        def close(self):
            pass

        def retrbinary(self, command, callback):
            callback(b"1234")
            callback(b"5678")

    monkeypatch.setattr(fetch.ftplib, "FTP", FTP)
    with pytest.raises(ValueError, match=r"limit|bytes"):
        asyncio.run(
            fetch.fetch_dbc_bytes(fixture_entry(SIM_DIR, "DORR2023.dbc", b"12345678"), max_bytes=5)
        )


def test_payload_limit_reports_failed_without_publication(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {RR_2023: raw})
    target = f"ducklake:{tmp_path}/limit.ducklake"
    report = import_dataset(
        "sim_obitos",
        scopes=[ScopeKey(uf="RR", ano=2023)],
        target=target,
        max_payload_bytes=1,
        max_inflight_bytes=2,
    )
    assert len(report.failed) == 1
    with Lake.local(target) as lake:
        assert "sim_obitos" not in lake.tables()


def test_managed_runner_skip_and_replace(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {RR_2023: raw})
    target = f"ducklake:{tmp_path}/replay.ducklake"
    kw = dict(scopes=[RR_2023], target=target)
    first = import_dataset("sim_obitos", **kw)
    second = import_dataset("sim_obitos", policy="skip_same", **kw)
    third = import_dataset("sim_obitos", policy="replace", **kw)
    assert len(first.ok) == 1 and len(second.skipped) == 1 and len(third.ok) == 1
    with Lake.local(target) as lake:
        assert (
            lake.connect().execute("SELECT count(*) FROM lake.sim_obitos").fetchone()[0]
            == first.rows
        )
        assert lake.publications(run_id=first.run_id)


def test_a_budget_of_one_file_makes_progress(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    scopes = [ScopeKey(uf="RR", ano=y) for y in (2021, 2022, 2023)]
    fake_datasus.serve(monkeypatch, "sim_obitos", dict.fromkeys(scopes, raw))
    report = import_dataset(
        "sim_obitos",
        scopes=scopes,
        target=f"ducklake:{tmp_path}/one.ducklake",
        concurrency=3,
        max_payload_bytes=len(raw),
        max_inflight_bytes=len(raw),
        batch_size=2,
    )
    assert len(report.ok) == 3


def test_failed_managed_attempt_is_durable_after_rollback(monkeypatch, tmp_path, dbc_fixture):
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {RR_2023: raw})
    target = f"ducklake:{tmp_path}/attempt.ducklake"
    kw = dict(scopes=[RR_2023], target=target)
    first = import_dataset("sim_obitos", **kw)
    failed = import_dataset("sim_obitos", policy="error_if_exists", run_id="failed-attempt", **kw)
    assert len(failed.failed) == 1
    with Lake.local(target) as lake:
        attempts = lake.attempts(run_id="failed-attempt")
        assert len(attempts) == 1 and attempts[0]["status"] == "failed"
        assert (
            lake.connect().execute("SELECT count(*) FROM lake.sim_obitos").fetchone()[0]
            == first.rows
        )


@pytest.mark.asyncio
async def test_cancelled_fetch_closes_ftp_and_joins_worker(monkeypatch):
    import threading

    started = threading.Event()
    closed = threading.Event()
    finished = threading.Event()

    class FTP:
        def __init__(self, *a, **kw):
            pass

        def connect(self, *a, **kw):
            pass

        def login(self):
            pass

        def cwd(self, *a):
            pass

        def close(self):
            closed.set()

        def retrbinary(self, command, callback):
            callback(b"x" * 1024)
            started.set()
            closed.wait(2)
            finished.set()

    monkeypatch.setattr(fetch.ftplib, "FTP", FTP)
    task = asyncio.create_task(
        fetch.fetch_dbc_bytes(fixture_entry(SIM_DIR, "DORR2023.dbc", b"x" * 2048), max_bytes=2048)
    )
    assert await asyncio.to_thread(started.wait, 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    try:
        assert closed.is_set() and finished.is_set()
    finally:
        closed.set()


@pytest.mark.asyncio
async def test_cancellation_during_ftp_greeting_keeps_event_loop_responsive(monkeypatch):
    import contextlib
    import socket
    import threading

    started = threading.Event()
    client, server = socket.socketpair()

    class FTP(fetch.ftplib.FTP):
        def connect(self, *args, **kwargs):
            self.sock = client
            self.sock.settimeout(2)
            self.file = self.sock.makefile("r", encoding=self.encoding)
            started.set()
            return self.getresp()

    def release_greeting():
        with contextlib.suppress(OSError):
            server.sendall(b"220 controlled greeting\r\n")

    monkeypatch.setattr(fetch.ftplib, "FTP", FTP)
    task = asyncio.create_task(fetch.fetch_dbc_bytes(fixture_entry(SIM_DIR, "DORR2023.dbc", b"")))
    assert await asyncio.to_thread(started.wait, 2)
    # The fallback prevents a broken implementation from hanging the suite.
    fallback = threading.Timer(0.5, release_greeting)
    fallback.start()
    loop = asyncio.get_running_loop()
    tick = loop.create_future()
    beginning = loop.time()
    loop.call_later(0.02, lambda: tick.set_result(loop.time() - beginning))
    try:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert await tick < 0.25
    finally:
        fallback.cancel()
        server.close()
        client.close()


@pytest.mark.asyncio
async def test_failed_download_retry_does_not_retain_buffers(monkeypatch):
    import io
    import weakref

    live = weakref.WeakSet()
    resident = []

    class Buffer(io.BytesIO):
        def __init__(self):
            super().__init__()
            live.add(self)

    class FTP:
        def __init__(self, *a, **kw):
            pass

        def connect(self, *a, **kw):
            pass

        def login(self):
            pass

        def cwd(self, *a):
            pass

        def close(self):
            pass

        def retrbinary(self, command, callback):
            callback(b"x" * 1024)
            resident.append(sum(b.tell() for b in live if not b.closed))
            raise ConnectionResetError("controlled failure")

    monkeypatch.setattr(fetch.ftplib, "FTP", FTP)
    monkeypatch.setattr(fetch.io, "BytesIO", Buffer)
    with pytest.raises(fetch.FtpUnavailable):
        await fetch.fetch_dbc_bytes(
            fixture_entry(SIM_DIR, "DORR2023.dbc", b"x" * 1024),
            max_bytes=1024,
            max_retries=3,
            backoff_seconds=0,
        )
    assert resident == [1024, 1024, 1024]
    assert all(b.closed for b in live)


@pytest.mark.parametrize("already_committed", [False, True])
def test_skip_depends_on_commit_that_published_source(
    monkeypatch, tmp_path, dbc_fixture, already_committed
):
    from omnisus.sources.datasus_ftp import _runner

    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    fake_datasus.serve(monkeypatch, "sim_obitos", {RR_2023: raw, ScopeKey(uf="RR", ano=2024): raw})
    target = f"ducklake:{tmp_path}/dependency.ducklake"
    if already_committed:
        import_dataset("sim_obitos", scopes=[ScopeKey(uf="RR", ano=2023)], target=target)
    real_publish = _runner.publish_staged

    def fail_2024_write(d, scope, staged, lake, **kwargs):
        # A write failure, after staging: only that rolls the batch back.
        if scope.ano == 2024:
            raise RuntimeError("write failed")
        return real_publish(d, scope, staged, lake, **kwargs)

    monkeypatch.setattr(_runner, "publish_staged", fail_2024_write)
    report = import_dataset(
        "sim_obitos",
        scopes=[
            ScopeKey(uf="RR", ano=2023),
            ScopeKey(uf="RR", ano=2023),
            ScopeKey(uf="RR", ano=2024),
        ],
        target=target,
        policy="skip_same",
        batch_size=3,
        concurrency=1,
    )
    assert [o.status for o in report.outcomes] == (
        ["skipped", "skipped", "failed"] if already_committed else ["failed", "failed", "failed"]
    )
