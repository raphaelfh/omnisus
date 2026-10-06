"""The registry probe lists each directory on first use, so one that fails fails alone.

The probe run of 2026-10-05 timed out opening the data connection for the first
directory it listed (SINAN/DADOS/FINAIS) and errored all 307 checks, those of the
24 other directories included. Real LIST lines (tests/fixtures/listings) stand in
for the server; the TimeoutError is the fault that run logged.
"""

from __future__ import annotations

import pytest

from omnisus.sources.datasus_ftp import inventory
from omnisus.sources.datasus_ftp.inventory import FtpUnavailable
from tests.support.listings import listing_lines, listing_per_directory

SINAN = "/dissemin/publicos/SINAN/DADOS/FINAIS"
SIA = "/dissemin/publicos/SIASUS/200801_/Dados"


def test_a_directory_that_times_out_fails_only_its_own_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def server(path: str, _timeout: float) -> list[str]:
        calls.append(path)
        if path == SINAN:
            raise TimeoutError("timed out")
        return listing_lines("siasus_200801_dados")

    monkeypatch.setattr(inventory, "_blocking_list", server)
    monkeypatch.setattr(inventory.time, "sleep", lambda _seconds: None)
    listing = listing_per_directory(timeout_seconds=1.0)

    with pytest.raises(FtpUnavailable):
        listing(SINAN)
    assert listing(SIA).entries
    with pytest.raises(FtpUnavailable):
        listing(SINAN)
    assert calls.count(SINAN) == 3  # list_dir's retry budget, spent once
    assert calls.count(SIA) == 1
