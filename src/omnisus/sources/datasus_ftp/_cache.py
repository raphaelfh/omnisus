"""Persistence for the FTP inventory.

One Parquet per listed directory, named from the slugified remote path plus a
short digest so ``ls`` is debuggable and distinct paths cannot collide.
Staleness and the skipped count are properties of the listing, not of its
rows, so they live in the file's Parquet key-value metadata — a zero-row frame
carries them just as well as a full one, and there is no sidecar to
desynchronise.

The cache is never authoritative: anything unreadable is a miss,
never an error. It knows nothing about FTP.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl
import structlog

from omnisus.sources.datasus_ftp.inventory import FtpEntry, Listing

logger = structlog.get_logger(__name__)

_SLUG_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")

_KEY_FETCHED_AT = "omnisus.fetched_at"
_KEY_SKIPPED = "omnisus.skipped"
_KEY_LISTING_PATH = "omnisus.listing_path"


def cache_dir() -> Path:
    """Directory holding cached listings.

    ``OMNISUS_CACHE_DIR`` wins; otherwise ``${XDG_CACHE_HOME:-~/.cache}``.
    """
    override = os.environ.get("OMNISUS_CACHE_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "omnisus" / "inventory"


def cache_path(remote_path: str) -> Path:
    """Cache file for one remote directory: a readable slug plus a digest.

    The slug alone is not injective — ``/a/b`` and ``/a_b`` both slugify to
    ``a_b``, and serving one directory's listing for another is worse than a
    miss (failures must be misses, not wrong data). The digest is
    taken over the same normalised path the slug is, so a trailing slash still
    maps to one file.
    """
    key = remote_path.strip("/")
    slug = _SLUG_UNSAFE.sub("_", key) or "root"
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=4).hexdigest()
    return cache_dir() / f"{slug}-{digest}.parquet"


def write_cache(listing: Listing) -> Path:
    """Persist a listing atomically. Returns the file written."""
    target = cache_path(listing.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).replace(tzinfo=None)
    frame = pl.DataFrame(
        {
            "name": [e.name for e in listing.entries],
            "path": [e.path for e in listing.entries],
            "parent": [e.parent for e in listing.entries],
            "is_dir": [e.is_dir for e in listing.entries],
            "size_bytes": [e.size_bytes for e in listing.entries],
            "modified": [e.modified for e in listing.entries],
        },
        schema={
            "name": pl.Utf8,
            "path": pl.Utf8,
            "parent": pl.Utf8,
            "is_dir": pl.Boolean,
            "size_bytes": pl.Int64,
            "modified": pl.Datetime("us"),
        },
    )
    tmp = target.with_suffix(".parquet.tmp")
    try:
        frame.write_parquet(
            tmp,
            compression="zstd",
            metadata={
                _KEY_FETCHED_AT: now.isoformat(),
                _KEY_SKIPPED: str(listing.skipped),
                _KEY_LISTING_PATH: listing.path,
            },
        )
        os.replace(tmp, target)
    except Exception:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise
    return target


def read_cached(remote_path: str, *, ttl_hours: float = 24.0) -> Listing | None:
    """Return the cached listing, or ``None`` on miss, stale or unreadable.

    Never raises: a corrupt cache is a miss. Freshness is read from
    the file's metadata before the frame, so a stale entry costs one metadata
    read rather than a full decode.
    """
    target = cache_path(remote_path)
    try:
        meta = pl.read_parquet_metadata(target)
        fetched_at = datetime.fromisoformat(meta[_KEY_FETCHED_AT])
        skipped = int(meta[_KEY_SKIPPED])
        listing_path = meta[_KEY_LISTING_PATH]
    except Exception as exc:
        if target.exists():
            logger.warning("inventory.cache_unreadable", path=str(target), error=str(exc))
        return None
    # >=, not >: Windows' clock ticks about every 16 ms, so a listing written and
    # read in one tick has age exactly zero, and ttl_hours=0 must still miss.
    if datetime.now(UTC).replace(tzinfo=None) - fetched_at >= timedelta(hours=ttl_hours):
        return None
    try:
        frame = pl.read_parquet(target)
        entries = tuple(
            FtpEntry(
                name=row["name"],
                path=row["path"],
                parent=row["parent"],
                is_dir=row["is_dir"],
                size_bytes=int(row["size_bytes"]),
                modified=row["modified"],
            )
            for row in frame.iter_rows(named=True)
        )
    except Exception as exc:
        logger.warning("inventory.cache_malformed", path=str(target), error=str(exc))
        return None
    return Listing(entries=entries, skipped=skipped, path=listing_path)
