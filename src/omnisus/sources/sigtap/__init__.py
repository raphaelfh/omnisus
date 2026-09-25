"""SIGTAP procedures (Tabela Unificada) by competência, as lake publications.

The server publishes one ``TabelaUnificada_YYYYMM[_vNNNNNNNNNN].zip`` per month in
``ftp2.datasus.gov.br/public/sistemas/tup/downloads``. Each zip carries
``tb_procedimento.txt`` (fixed width, cp1252) and ``tb_procedimento_layout.txt``, and the
layout changes over time (value columns 10 wide in 2008-01, 12 in 2026-09), so every zip
is read through its own layout. One competência is one national monthly publication of
``aux_sigtap_procedimentos``; nothing is packaged.
"""

from __future__ import annotations

import contextlib
import ftplib
import hashlib
import io
import re
import tempfile
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from omnisus.lake import Lake
from omnisus.lake.publication import ImportPolicy, SourceFile
from omnisus.sources._base import ImportReport, ScopeKey, ScopeOutcome

HOST = "ftp2.datasus.gov.br"
DIRECTORY = "/public/sistemas/tup/downloads"
TABLE = "aux_sigtap_procedimentos"
PARSER_VERSION = "sigtap-tb-procedimento-v1"
_NAME = re.compile(r"TabelaUnificada_(\d{4})(\d{2})(?:_v\d{10})?\.zip")


@dataclass(frozen=True)
class Column:
    name: str  # lower case, as the lake stores it
    start: int  # 1-based, inclusive, as the layout writes it
    end: int
    number: bool  # layout type NUMBER -> BIGINT; every other type stays text


def competencias(names: Iterable[str]) -> dict[tuple[int, int], str]:
    """(ano, mes) -> file name, for every name that is a Tabela Unificada zip."""
    found: dict[tuple[int, int], str] = {}
    for name in names:
        match = _NAME.fullmatch(name)
        if match is None:
            continue
        key = (int(match.group(1)), int(match.group(2)))
        if key in found:
            raise ValueError(f"competência {key} listed twice: {found[key]}, {name}")
        found[key] = name
    return found


def list_names() -> list[str]:
    """``NLST`` of the downloads directory; this server answers ``LIST`` in Unix format."""
    with contextlib.closing(ftplib.FTP(HOST, timeout=60)) as ftp:
        ftp.encoding = "latin-1"
        ftp.login()
        return ftp.nlst(DIRECTORY)


def available_sigtap() -> list[tuple[int, int]]:
    """Competências the server lists now, oldest first."""
    return sorted(competencias(Path(name).name for name in list_names()))


def download(name: str) -> tuple[bytes, str]:
    """The zip's bytes and its server mtime (``MDTM``, ``YYYY-MM-DDTHH:MM``)."""
    raw = bytearray()
    with contextlib.closing(ftplib.FTP(HOST, timeout=120)) as ftp:
        ftp.login()
        ftp.cwd(DIRECTORY)
        stamp = ftp.sendcmd(f"MDTM {name}").split()[-1]
        ftp.retrbinary(f"RETR {name}", raw.extend)
    return bytes(raw), f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[8:10]}:{stamp[10:12]}"


def parse_layout(text: str) -> list[Column]:
    """``Coluna,Tamanho,Inicio,Fim,Tipo`` rows; the size must equal ``Fim - Inicio + 1``."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines[:1] != ["Coluna,Tamanho,Inicio,Fim,Tipo"]:
        raise ValueError(f"unexpected SIGTAP layout header: {lines[:1]!r}")
    columns = []
    for line in lines[1:]:
        name, size, start, end, kind = line.split(",")
        if int(end) - int(start) + 1 != int(size):
            raise ValueError(f"SIGTAP layout row does not add up: {line!r}")
        columns.append(Column(name.lower(), int(start), int(end), kind == "NUMBER"))
    return columns


def read_procedimentos(zip_bytes: bytes) -> pl.DataFrame:
    """``tb_procedimento.txt`` read through the zip's own layout; text right-stripped."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        layout = parse_layout(zf.read("tb_procedimento_layout.txt").decode("latin-1"))
        text = zf.read("tb_procedimento.txt").decode("cp1252")
    width = layout[-1].end
    lines = [line for line in text.splitlines() if line]
    if any(len(line) != width for line in lines):
        raise ValueError(f"tb_procedimento.txt line is not {width} characters")
    data: dict[str, list[object]] = {}
    for c in layout:
        values = [line[c.start - 1 : c.end] for line in lines]
        data[c.name] = [int(v) for v in values] if c.number else [v.rstrip() for v in values]
    return pl.DataFrame(data, schema_overrides={c.name: pl.Int64 for c in layout if c.number})


def _publish(lake: Lake, scope: ScopeKey, name: str, policy: ImportPolicy) -> ScopeOutcome:
    raw, modified = download(name)
    frame = read_procedimentos(raw)
    expected = f"{scope.ano}{scope.mes:02d}"
    stamped = set(frame["dt_competencia"].unique())
    if stamped != {expected}:
        raise ValueError(f"{name} holds competência {sorted(stamped)}, not {expected}")
    frame = frame.with_columns(
        pl.lit(scope.ano, pl.Int32).alias("_source_ano"),
        pl.lit(scope.mes, pl.Int32).alias("_source_mes"),
    )
    uri = f"ftp://{HOST}{DIRECTORY}/{name}"
    digest = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "scope.parquet"
        frame.write_parquet(staging)
        result = lake.publish_scope(
            TABLE,
            staging,
            scope=scope,
            source_sha256=digest,
            parser_version=PARSER_VERSION,
            policy=policy,
            partition_by=("_source_ano",),
            source_uri=uri,
            source_files=(SourceFile(uri, digest, len(raw), modified),),
        )
    if result is None:
        return ScopeOutcome(
            scope, "skipped", reason="same source already published", code="unchanged"
        )
    return ScopeOutcome(scope, "ok", result=result)


def import_sigtap(
    wanted: Iterable[tuple[int, int]], *, lake: Lake, policy: ImportPolicy = "skip_same"
) -> ImportReport:
    """Publish each requested (ano, mes); one outcome per request, in order."""
    listed = competencias(Path(name).name for name in list_names())
    outcomes = []
    for ano, mes in wanted:
        scope = ScopeKey(uf=None, ano=ano, mes=mes)
        name = listed.get((ano, mes))
        if name is None:
            outcomes.append(
                ScopeOutcome(
                    scope,
                    "skipped",
                    reason=f"{DIRECTORY} lists no {ano}{mes:02d}",
                    code="not_listed",
                )
            )
            continue
        try:
            outcomes.append(_publish(lake, scope, name, policy))
        except ftplib.all_errors as exc:
            outcomes.append(ScopeOutcome(scope, "failed", reason=str(exc), code="fetch_failed"))
        except ValueError as exc:
            outcomes.append(ScopeOutcome(scope, "failed", reason=str(exc), code="ingest_failed"))
    return ImportReport(outcomes=tuple(outcomes))
