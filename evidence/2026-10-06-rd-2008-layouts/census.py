"""The DBF field layout of the RD files from 2008 on, one row per file read.

    uv run --locked python evidence/2026-10-06-rd-2008-layouts/census.py CACHE_DIR \
        evidence/2026-10-06-rd-2008-layouts/census.csv

The same reading as `evidence/2026-10-01-rd-1992-2007-layouts/census.py`, for the
`200801_` directory: for every month the server lists, from the first to the last, it
reads RDRRaamm.dbc, or RDAPaamm.dbc when the server does not list the RR file. Where two
consecutive months differ in layout it also reads RDSP and RDMG of both months, to show
the change is not one UF's. Downloads are kept in CACHE_DIR and reused; sizes and dates
come from the live listing, and a file whose size differs from the listing's stops the
run and is not kept. The CSV goes to the path given, not stdout, which carries the
client's log lines.

`fields` is the header's descriptor list in file order, each `NAME TYPE WIDTH.DECIMALS`;
`layout` numbers the distinct lists in the order of the first month that has them. The
layouts, with the fields each adds, drops and resizes, are printed on stderr.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import itertools
import sys
from pathlib import Path

from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus.sources.datasus_ftp.fetch import _download
from omnisus.sources.datasus_ftp.inventory import FtpEntry, list_dir

DIRECTORY = "/dissemin/publicos/SIHSUS/200801_/Dados"
UFS = ("RR", "AP")
BOUNDARY_UFS = ("SP", "MG")
COLUMNS = [
    "file",
    "month",
    "server_modified",
    "size_bytes",
    "sha256",
    "records",
    "layout",
    "fields",
]


def header(dbf: bytes) -> tuple[int, str]:
    """Record count and descriptor list of one DBF."""
    fields = " ".join(
        f"{f.name} {f.kind}{f.width}.{f.decimals}" for f in _read_field_descriptors(dbf)
    )
    return int.from_bytes(dbf[4:8], "little"), fields


def month_of(name: str) -> str:
    aamm = name[4:8]
    return f"20{aamm[:2]}-{aamm[2:]}"


def months(listed: dict[str, FtpEntry]) -> list[str]:
    """Every aamm from the first to the last RR or AP file the server lists."""
    found = sorted(name[4:8] for name in listed if name[:4] in ("RDRR", "RDAP"))
    first, last = (int(found[0][:2]), int(found[0][2:])), (int(found[-1][:2]), int(found[-1][2:]))
    return [
        f"{year:02d}{month:02d}"
        for year in range(first[0], last[0] + 1)
        for month in range(1, 13)
        if first <= (year, month) <= last
    ]


async def read(cache: Path, entry: FtpEntry) -> list[object]:
    path = cache / entry.name
    cached = path.exists()
    raw = path.read_bytes() if cached else await _download(entry.parent, entry.name, 900)
    if len(raw) != entry.size_bytes:
        raise ValueError(f"{entry.name}: {len(raw)} bytes, the listing says {entry.size_bytes}")
    if not cached:
        path.write_bytes(raw)
    records, fields = header(decompress_bytes(raw))
    modified = entry.modified.strftime("%Y-%m-%dT%H:%M")
    sha256 = hashlib.sha256(raw).hexdigest()
    return [entry.name, month_of(entry.name), modified, entry.size_bytes, sha256, records, fields]


def pick(listed: dict[str, FtpEntry], ufs: tuple[str, ...], month: str) -> list[FtpEntry]:
    return [listed[f"RD{uf}{month}.dbc"] for uf in ufs if f"RD{uf}{month}.dbc" in listed]


async def census(cache: Path) -> list[list[object]]:
    listed = {e.name: e for e in list_dir(DIRECTORY).files}
    rows = [await read(cache, pick(listed, UFS, month)[0]) for month in months(listed)]
    boundaries = sorted(
        {
            str(row[0])[4:8]
            for before, after in itertools.pairwise(rows)
            if before[6] != after[6]
            for row in (before, after)
        }
    )
    for month in boundaries:
        for entry in pick(listed, BOUNDARY_UFS, month):
            rows.append(await read(cache, entry))
    layouts: dict[str, int] = {}
    for row in sorted(rows, key=lambda r: (r[1], r[0])):
        row.insert(6, layouts.setdefault(row[6], len(layouts) + 1))
    return rows


def summary(rows: list[list[object]]) -> None:
    previous: dict[str, str] = {}
    for layout in sorted({row[6] for row in rows}):  # type: ignore[type-var]
        own = [row for row in rows if row[6] == layout]
        parts = str(own[0][7]).split(" ")
        fields = dict(zip(parts[::2], parts[1::2], strict=True))
        span = sorted(str(row[1]) for row in own)
        added = [n for n in fields if n not in previous]
        dropped = [n for n in previous if n not in fields]
        resized = [f"{n} {previous[n]}->{t}" for n, t in fields.items() if previous.get(n, t) != t]
        print(
            f"layout {layout}: {span[0]}..{span[-1]}, {len(own)} files, {len(fields)} fields;"
            f" adds {' '.join(added) or '-'}; drops {' '.join(dropped) or '-'};"
            f" resizes {', '.join(resized) or '-'}",
            file=sys.stderr,
        )
        previous = fields


def main(cache: str, out: str) -> None:
    rows = asyncio.run(census(Path(cache)))
    rows.sort(key=lambda r: (r[1], r[0]))
    with Path(out).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    summary(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
