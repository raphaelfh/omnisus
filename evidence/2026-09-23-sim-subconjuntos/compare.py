"""Are the RR residents of DOINF, DOMAT and DOEXT records of DORR? One row per file.

    uv run --locked python evidence/2026-09-23-sim-subconjuntos/compare.py CACHE_DIR 2018 2023

A subset record "equals" a DORR record when every field both files have holds the same
trimmed bytes; "equals but CONTADOR" ignores that field, the file's own record counter.
Downloads are kept in CACHE_DIR and reused.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
from pathlib import Path

from omnisus_db.sources.datasus_ftp.dbc import decompress_bytes
from omnisus_db.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus_db.sources.datasus_ftp.fetch import _download

SUBSETS = ("DOINF", "DOMAT", "DOEXT")


async def fetch(cache: Path, directory: str, name: str) -> bytes:
    path = cache / name
    if not path.exists():
        path.write_bytes(await _download(directory, name, 900))
    return path.read_bytes()


def records(raw: bytes) -> list[dict[str, bytes]]:
    dbf = decompress_bytes(raw)
    count = int.from_bytes(dbf[4:8], "little")
    header = int.from_bytes(dbf[8:10], "little")
    length = int.from_bytes(dbf[10:12], "little")
    fields, offset = [], 1
    for field in _read_field_descriptors(dbf):
        fields.append((field.name.upper(), offset, field.width))
        offset += field.width
    return [
        {
            name: dbf[header + n * length + start : header + n * length + start + width].strip()
            for name, start, width in fields
        }
        for n in range(count)
    ]


def compare(do: list[dict[str, bytes]], subset: list[dict[str, bytes]]) -> tuple[int, int, int]:
    shared = [name for name in subset[0] if name in do[0]]
    loose = [name for name in shared if name != "CONTADOR"]
    exact = {tuple(r[k] for k in shared) for r in do}
    near = {tuple(r[k] for k in loose) for r in do}
    residents = [r for r in subset if r.get("CODMUNRES", b"").startswith(b"14")]
    equal = sum(tuple(r[k] for k in shared) in exact for r in residents)
    equal_but_counter = sum(tuple(r[k] for k in loose) in near for r in residents)
    return len(residents), equal, equal_but_counter


async def main(cache: Path, years: list[int]) -> None:
    print("file,sha256,records,fields,rr_residents,equal,equal_but_contador,dorr_sha256")
    for year in years:
        do_raw = await fetch(cache, "/dissemin/publicos/SIM/CID10/DORES", f"DORR{year}.dbc")
        do = records(do_raw)
        for kind in SUBSETS:
            name = f"{kind}{str(year)[2:]}.dbc"
            raw = await fetch(cache, "/dissemin/publicos/SIM/CID10/DOFET", name)
            subset = records(raw)
            rr, equal, near = compare(do, subset)
            print(
                f"{name},{hashlib.sha256(raw).hexdigest()},{len(subset)},{len(subset[0])},"
                f"{rr},{equal},{near},{hashlib.sha256(do_raw).hexdigest()}"
            )


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]), [int(y) for y in sys.argv[2:]]))
