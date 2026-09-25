"""Cooperative, process-lifetime local writer exclusion.

The lock file is deliberately never unlinked: removing it could allow a third
process to lock a new inode while a waiter still owns the old one.
"""

import errno
import sys
from pathlib import Path
from typing import BinaryIO


class WriterBusyError(RuntimeError):
    """Another library handle owns this local catalog's writer lock."""


class WriterLock:
    def __init__(self, catalog_uri: str):
        self._file: BinaryIO | None = None
        scheme, _, body = catalog_uri.partition(":")
        if scheme not in ("sqlite", "duckdb"):
            return  # Remote catalogs require external coordination.
        catalog = Path(body).expanduser().resolve()
        catalog.parent.mkdir(parents=True, exist_ok=True)
        lock_path = catalog.with_name(catalog.name + ".writer.lock")
        handle = open(lock_path, "a+b")  # noqa: SIM115 -- owned until close(), across calls
        try:
            # sys.platform, not os.name: mypy narrows on it, so each branch
            # type-checks only on the platform where its module exists.
            if sys.platform == "win32":
                import msvcrt

                handle.seek(0, 2)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException as exc:
            handle.close()
            if not isinstance(exc, OSError) or exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            raise WriterBusyError(
                "another writer already owns this local catalog; close it before retrying"
            ) from None
        self._file = handle

    def close(self):
        if self._file is not None:
            self._file.close()  # OS releases the lock, including after process death.
            self._file = None
