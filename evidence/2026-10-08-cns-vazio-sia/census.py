"""How many SIA rows carry no patient CNS, per file.

    uv run --locked python evidence/2026-10-08-cns-vazio-sia/census.py OUT_DIR [CACHE_DIR]

Files read from ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados:

- APAC de medicamentos (AM) of every UF, 2025-08 and the latest month listed;
- AM of SP and GO, every month from 2024-01 to the latest;
- BPA-I, RAAS psicossocial and the other APAC with a CNS field marked
  ``x-crypto: datasus-cns`` (AQ, ATD, AD, ABO): every UF in 2024-10 and 2026-07,
  SP and GO also in 2024-11 and 2025-08.

Writes ``census.csv``, one row per file, and ``autorizacao.csv``: the AM files of SP
and GO by month of ``ap_dtaut`` (authorisation date, YYYYMMDD as published). A CNS is
empty when it is null or blank. A file already in ``census.csv`` is not read again,
so an interrupted run resumes. With CACHE_DIR, downloaded bytes are kept there and
reused when their size equals the listed size.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import re
import sys
from pathlib import Path

import polars as pl

import omnisus as sus
from omnisus.sources.datasus_ftp.fetch import fetch_dbc_bytes
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

DIRECTORY = "/dissemin/publicos/SIASUS/200801_/Dados"
# prefix -> (dataset, patient CNS column)
CNS = {
    "AM": ("sia_apac_medicamentos", "ap_cnspcn"),
    "AQ": ("sia_apac_quimioterapia", "ap_cnspcn"),
    "ATD": ("sia_apac_tratamento_dialitico", "ap_cnspcn"),
    "AD": ("sia_apac_laudos_diversos", "ap_cnspcn"),
    "ABO": ("sia_apac_cirurgia_bariatrica", "ap_cnspcn"),
    "BI": ("sia_bpa_individualizado", "cns_pac"),
    "PS": ("sia_psicossocial", "cns_pac"),
}
NAME = re.compile(r"^(AM|AQ|ATD|AD|ABO|BI|PS)([A-Z]{2})(\d{2})(\d{2})(?:_\d)?\.dbc$")
CENSUS = [
    "prefix",
    "file",
    "server_modified",
    "size_bytes",
    "sha256",
    "records",
    "cns_column",
    "cns_empty",
]
BY_AUTHORISATION = ["file", "ap_dtaut_month", "records", "cns_empty"]


def selected(entries: list[sus.FtpEntry]) -> list[sus.FtpEntry]:
    """The files this census reads, in a stable order."""
    files = {}
    for e in entries:
        if m := NAME.match(e.name):
            files[e.name] = (e, m.group(1), m.group(2), m.group(3) + m.group(4))
    latest = {}
    for _, prefix, uf, yymm in files.values():
        if prefix == "AM":
            latest[uf] = max(latest.get(uf, yymm), yymm)
    keep = []
    for e, prefix, uf, yymm in files.values():
        if prefix == "AM":
            wanted = yymm in ("2508", latest[uf]) or (uf in ("SP", "GO") and yymm >= "2401")
        else:
            wanted = yymm in ("2410", "2607") or (uf in ("SP", "GO") and yymm in ("2411", "2508"))
        if wanted:
            keep.append(e)
    return sorted(keep, key=lambda e: e.name)


def read(entry: sus.FtpEntry, cache: Path | None) -> bytes:
    path = cache / entry.name if cache else None
    if path and path.exists() and path.stat().st_size == entry.size_bytes:
        return path.read_bytes()
    raw = asyncio.run(fetch_dbc_bytes(entry))
    if path:
        path.write_bytes(raw)
    return raw


def main(out: Path, cache: Path | None) -> None:
    census_path, authorisation_path = out / "census.csv", out / "autorizacao.csv"
    done = set()
    if census_path.exists():
        with census_path.open() as f:
            done = {row["file"] for row in csv.DictReader(f)}
    for path, header in ((census_path, CENSUS), (authorisation_path, BY_AUTHORISATION)):
        if not path.exists():
            path.write_text(",".join(header) + "\n")
    for entry in selected(sus.browse(DIRECTORY, refresh=True)):
        if entry.name in done:
            continue
        prefix, uf, yy = NAME.match(entry.name).group(1, 2, 3)  # type: ignore[union-attr]
        dataset, column = CNS[prefix]
        raw = read(entry, cache)
        frame = dbc_bytes_to_lazyframe(raw, dataset=dataset, ano=2000 + int(yy), uf=uf)
        frame = frame.select(
            pl.col("ap_dtaut").str.slice(0, 6).alias("ap_dtaut_month")
            if prefix == "AM"
            else pl.lit(None),
            pl.col(column).str.strip_chars().fill_null("").eq("").alias("empty"),
        ).collect()
        if prefix == "AM" and uf in ("SP", "GO"):
            months = (
                frame.group_by("ap_dtaut_month")
                .agg(pl.len(), pl.col("empty").sum())
                .sort("ap_dtaut_month")
            )
            with authorisation_path.open("a", newline="") as f:
                csv.writer(f).writerows([entry.name, *row] for row in months.iter_rows())
        with census_path.open("a", newline="") as f:
            csv.writer(f).writerow(
                [
                    prefix,
                    entry.name,
                    entry.modified.isoformat(timespec="minutes"),
                    entry.size_bytes,
                    hashlib.sha256(raw).hexdigest(),
                    frame.height,
                    column,
                    int(frame["empty"].sum()),
                ]
            )
        print(entry.name, flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
