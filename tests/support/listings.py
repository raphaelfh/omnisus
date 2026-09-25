"""Real DATASUS LIST output (tests/fixtures/listings) served to the inventory."""

from __future__ import annotations

import ftplib
import gzip
from datetime import datetime
from pathlib import Path

import pytest

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import Dataset
from omnisus.sources.datasus_ftp.inventory import FtpEntry
from tests.support.datasus_names import filename_for

LISTINGS = Path(__file__).resolve().parents[1] / "fixtures" / "listings"


def listing_lines(fixture: str) -> list[str]:
    """The raw LIST lines saved in ``tests/fixtures/listings/<fixture>.txt.gz``."""
    text = gzip.decompress((LISTINGS / f"{fixture}.txt.gz").read_bytes()).decode("latin-1")
    return [line for line in text.splitlines() if line]


def serve_listings(monkeypatch: pytest.MonkeyPatch, by_directory: dict[str, str]) -> None:
    """Make ``inventory._blocking_list`` answer each directory with its fixture.

    A directory not in ``by_directory`` answers 550, as the server does.
    """

    def fake(path: str, _timeout: float) -> list[str]:
        if path not in by_directory:
            raise ftplib.error_perm(f"550 {path}: not found")
        return listing_lines(by_directory[path])

    monkeypatch.setattr("omnisus.sources.datasus_ftp.inventory._blocking_list", fake)


def fixture_entry(
    directory: str, name: str, raw: bytes, modified: datetime | None = None
) -> FtpEntry:
    """A listing entry for bytes a test already holds (size taken from the bytes)."""
    return FtpEntry(
        name=name,
        path=f"{directory}/{name}",
        parent=directory,
        is_dir=False,
        size_bytes=len(raw),
        modified=modified or datetime(2024, 1, 1, 0, 0),
    )


def listed(d: Dataset, scope: ScopeKey, raw: bytes) -> list[tuple[FtpEntry, bytes]]:
    """``raw`` as the one file the final directory lists for ``scope``: ``ingest_raw``'s input."""
    return [(fixture_entry(d.ftp_dir, filename_for(d, scope), raw), raw)]
