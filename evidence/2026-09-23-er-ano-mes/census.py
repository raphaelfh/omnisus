"""Every ER file on the server: SHA-256, records, and rows whose ANO/MES differ from its name.

    uv run --locked python evidence/2026-09-23-er-ano-mes/census.py census.csv

ER files are named ERUFAAMM.dbc. A row "differs" when its ANO is not 20AA or its MES
is not MM, compared as numbers after trimming; a blank or non-numeric value differs.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import sys

from omnisus_db.sources.datasus_ftp.dbc import decompress_bytes
from omnisus_db.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus_db.sources.datasus_ftp.fetch import fetch_dbc_bytes
from omnisus_db.sources.datasus_ftp.inventory import FtpEntry, list_dir_cached

DIRECTORY = "/dissemin/publicos/SIHSUS/200801_/Dados"
COLUMNS = [
    "file",
    "server_modified",
    "size_bytes",
    "sha256",
    "records",
    "ano_differs",
    "mes_differs",
    "layout",
]


def differing(name: str, raw: bytes) -> tuple[int, int, int, str]:
    """Records, rows whose ANO differs, rows whose MES differs, and the two layouts."""
    dbf = decompress_bytes(raw)
    records = int.from_bytes(dbf[4:8], "little")
    header = int.from_bytes(dbf[8:10], "little")
    length = int.from_bytes(dbf[10:12], "little")
    fields, offset = {}, 1
    for field in _read_field_descriptors(dbf):
        width = field.width + (field.decimals << 8 if field.kind == "C" else 0)
        fields[field.name] = (offset, width, field.kind)
        offset += width
    expected = {"ANO": 2000 + int(name[4:6]), "MES": int(name[6:8])}
    counts = dict.fromkeys(expected, 0)
    for number in range(records):
        record = dbf[header + number * length : header + (number + 1) * length]
        for column, want in expected.items():
            start, width, _ = fields[column]
            value = record[start : start + width].strip()
            counts[column] += not value.isdigit() or int(value) != want
    layout = " ".join(f"{c} {fields[c][2]}{fields[c][1]}" for c in expected)
    return records, counts["ANO"], counts["MES"], layout


async def census() -> list[list[object]]:
    files = sorted(
        (e for e in list_dir_cached(DIRECTORY).files if e.name.startswith("ER")),
        key=lambda e: e.name,
    )
    limit = asyncio.Semaphore(4)

    async def one(entry: FtpEntry) -> list[object]:
        async with limit:
            raw = await fetch_dbc_bytes(entry)
        records, ano, mes, layout = await asyncio.to_thread(differing, entry.name, raw)
        modified = entry.modified.strftime("%Y-%m-%dT%H:%M")
        sha256 = hashlib.sha256(raw).hexdigest()
        return [entry.name, modified, entry.size_bytes, sha256, records, ano, mes, layout]

    return list(await asyncio.gather(*(one(e) for e in files)))


def main(path: str) -> None:
    rows = asyncio.run(census())
    with open(path, "w", newline="") as sink:
        writer = csv.writer(sink, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    total = [sum(row[i] for row in rows) for i in (4, 5, 6)]  # type: ignore[misc]
    print(f"files {len(rows)} records {total[0]} ano_differs {total[1]} mes_differs {total[2]}")


if __name__ == "__main__":
    main(sys.argv[1])
