"""Every CO_ERRO value in the ER files on the server, with rows and files.

    uv run --locked python evidence/2026-09-23-er-co-erro/census.py counts.csv

Values are read from the DBF bytes and right-stripped, as the lake stores them.
"""

from __future__ import annotations

import asyncio
import collections
import csv
import sys

from omnisus_db.sources.datasus_ftp.dbc import decompress_bytes
from omnisus_db.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus_db.sources.datasus_ftp.fetch import fetch_dbc_bytes
from omnisus_db.sources.datasus_ftp.inventory import FtpEntry, list_dir_cached

DIRECTORY = "/dissemin/publicos/SIHSUS/200801_/Dados"


def values(raw: bytes) -> collections.Counter[str]:
    dbf = decompress_bytes(raw)
    records = int.from_bytes(dbf[4:8], "little")
    header = int.from_bytes(dbf[8:10], "little")
    length = int.from_bytes(dbf[10:12], "little")
    offset = 1
    for field in _read_field_descriptors(dbf):
        width = field.width + (field.decimals << 8 if field.kind == "C" else 0)
        if field.name == "CO_ERRO":
            start, size = offset, width
        offset += width
    return collections.Counter(
        dbf[header + n * length + start : header + n * length + start + size]
        .decode("latin-1")
        .rstrip()
        for n in range(records)
    )


async def census() -> list[collections.Counter[str]]:
    files = [e for e in list_dir_cached(DIRECTORY).files if e.name.startswith("ER")]
    limit = asyncio.Semaphore(4)

    async def one(entry: FtpEntry) -> collections.Counter[str]:
        async with limit:
            raw = await fetch_dbc_bytes(entry)
        return await asyncio.to_thread(values, raw)

    return list(await asyncio.gather(*(one(e) for e in files)))


def main(path: str) -> None:
    per_file = asyncio.run(census())
    rows = collections.Counter[str]()
    files = collections.Counter[str]()
    for counts in per_file:
        rows.update(counts)
        files.update(counts.keys())
    with open(path, "w", newline="") as sink:
        writer = csv.writer(sink, lineterminator="\n")
        writer.writerow(["co_erro", "rows", "files"])
        writer.writerows([code, rows[code], files[code]] for code in sorted(rows))
    print(f"files {len(per_file)} rows {sum(rows.values())} distinct {len(rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
