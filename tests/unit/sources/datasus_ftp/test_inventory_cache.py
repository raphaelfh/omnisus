"""Inventory cache. Never authoritative: unreadable means miss,
never an error. Staleness lives in the file's metadata, not a sidecar."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from omnisus.sources.datasus_ftp._cache import (
    cache_dir,
    cache_path,
    read_cached,
    write_cache,
)
from omnisus.sources.datasus_ftp.inventory import FtpEntry, Listing

PATH = "/dissemin/publicos/SIM/CID10/DORES"


def _listing(path: str = PATH, n: int = 2) -> Listing:
    entries = tuple(
        FtpEntry(
            name=f"DOAC{1996 + i}.dbc",
            path=f"{path}/DOAC{1996 + i}.dbc",
            parent=path,
            is_dir=False,
            size_bytes=76107 + i,
            modified=datetime(2020, 1, 31, 14, 48),
        )
        for i in range(n)
    )
    return Listing(entries=entries, skipped=1, path=path)


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMNISUS_CACHE_DIR", str(tmp_path / "cache"))


def test_cache_dir_honours_the_env_override(tmp_path: Path) -> None:
    assert cache_dir() == tmp_path / "cache"


def test_cache_dir_falls_back_to_xdg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OMNISUS_CACHE_DIR", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert cache_dir() == tmp_path / "xdg" / "omnisus" / "inventory"


def test_cache_path_is_a_readable_slug_not_a_hash() -> None:
    p = cache_path(PATH)
    assert p.name.startswith("dissemin_publicos_SIM_CID10_DORES-")
    assert p.name.endswith(".parquet")
    assert p.parent == cache_dir()


def test_distinct_remote_paths_get_distinct_files() -> None:
    assert cache_path("/a/b") != cache_path("/a/c")


def test_write_then_read_roundtrips_entries_and_skipped() -> None:
    original = _listing()
    write_cache(original)
    got = read_cached(PATH)
    assert got is not None
    assert got.path == original.path
    assert got.skipped == original.skipped
    assert [e.name for e in got.entries] == [e.name for e in original.entries]
    assert got.entries[0].size_bytes == original.entries[0].size_bytes
    assert got.entries[0].modified == original.entries[0].modified
    assert got.entries[0].is_dir is False


def test_miss_returns_none() -> None:
    assert read_cached("/never/listed") is None


def test_entry_older_than_the_ttl_is_a_miss() -> None:
    write_cache(_listing())
    assert read_cached(PATH, ttl_hours=0) is None


def test_entry_within_the_ttl_is_a_hit() -> None:
    write_cache(_listing())
    assert read_cached(PATH, ttl_hours=24) is not None


def test_corrupt_file_is_a_miss_never_an_error() -> None:
    """The cache is never authoritative."""
    write_cache(_listing())
    cache_path(PATH).write_bytes(b"not a parquet file")
    assert read_cached(PATH) is None


def test_write_is_atomic_and_leaves_no_temp_files() -> None:
    write_cache(_listing())
    leftovers = [p.name for p in cache_dir().iterdir() if not p.name.endswith(".parquet")]
    assert leftovers == []


def test_rewrite_replaces_rather_than_appends() -> None:
    write_cache(_listing(n=2))
    write_cache(_listing(n=5))
    got = read_cached(PATH)
    assert got is not None
    assert len(got.entries) == 5


def test_large_sizes_survive_the_roundtrip() -> None:
    big = Listing(
        entries=(
            FtpEntry(
                name="base_aih1.duck",
                path=f"{PATH}/base_aih1.duck",
                parent=PATH,
                is_dir=False,
                size_bytes=12_000_440_320,
                modified=datetime(2026, 6, 7, 13, 54),
            ),
        ),
        skipped=0,
        path=PATH,
    )
    write_cache(big)
    got = read_cached(PATH)
    assert got is not None
    assert got.entries[0].size_bytes == 12_000_440_320


def test_empty_listing_roundtrips_as_empty_not_as_a_miss() -> None:
    """An empty directory is a real answer and must cache as one."""
    write_cache(Listing(entries=(), skipped=0, path=PATH))
    got = read_cached(PATH)
    assert got is not None
    assert got.entries == ()


def test_empty_listing_still_expires_with_the_ttl() -> None:
    """An empty directory has no rows, so its freshness cannot come from the
    frame — it comes from the file's metadata. Both halves are asserted on
    purpose: an implementation that always missed would satisfy the expiry
    half alone, which is exactly how the previous version of this test passed
    while proving nothing."""
    write_cache(Listing(entries=(), skipped=0, path=PATH))
    assert read_cached(PATH, ttl_hours=24) is not None
    assert read_cached(PATH, ttl_hours=0) is None


def test_skipped_survives_even_when_there_are_no_entries() -> None:
    """``skipped`` is a property of the listing, not of its rows. A zero-row
    frame cannot carry it in a column, and a listing that reports 0 lines
    skipped when 5 were dropped is a declaration that lies."""
    write_cache(Listing(entries=(), skipped=5, path=PATH))
    got = read_cached(PATH)
    assert got is not None
    assert got.skipped == 5


def test_paths_that_slugify_alike_do_not_collide() -> None:
    """``/a/b`` and ``/a_b`` both slugify to ``a_b``. Serving one directory's
    listing for another is worse than a miss, so the name carries a digest."""
    assert cache_path("/a/b") != cache_path("/a_b")


def test_a_trailing_slash_maps_to_the_same_cache_file() -> None:
    assert cache_path("/a/b") == cache_path("/a/b/")
