"""Build src/omnisus/data/auxiliares-bootstrap.zip from hashed DATASUS files.

    uv run python scripts/build_bootstrap_zip.py

Sources are registered ``SIM/CID10/TABELAS`` files and the packaged
``CBO2002.CNV`` and ``CID10GRUPOS.CNV`` members. Downloads and packaged members
must match their registered SHA-256, else the build stops. The zip carries one
Parquet file per table and ``manifest.json`` (table -> rows and sources).
"""

from __future__ import annotations

import ftplib
import hashlib
import io
import json
import re
import tempfile
import zipfile
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import polars as pl
from dbfread2 import DBF

from omnisus.metadata import sources_registry
from omnisus.transforms.cnv import cnv_map, parse_cnv

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "src" / "omnisus" / "data" / "auxiliares-bootstrap.zip"
CNV = ROOT / "src" / "omnisus" / "data" / "dicionarios" / "sources" / "cnv"
TABELAS = "ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/TABELAS/"
# The DBF headers do not state these reliably (CID10 declares none); read from the text.
ENCODING = {
    "TABUF.DBF": "ascii",
    "CADMUN.DBF": "cp850",
    "CID10.DBF": "cp1252",
    "CIDCAP10.DBF": "ascii",
    "TABOCUP.DBF": "cp850",
    "TABPAIS.DBF": "ascii",
}


def download(name: str, into: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Records of one TABELAS file, after checking its bytes against the registry."""
    url = TABELAS + name
    entry = next(s for s in sources_registry()["sources"] if s["url"] == url)
    parsed = urlparse(url)
    raw = bytearray()
    with ftplib.FTP(parsed.hostname or "", timeout=120) as ftp:
        ftp.login()
        ftp.retrbinary(f"RETR {parsed.path}", raw.extend)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"{url}: SHA-256 {digest} differs from the registry's {entry['sha256']}")
    path = into / name
    path.write_bytes(raw)
    return [dict(r) for r in DBF(path, encoding=ENCODING[name])], {"url": url, "sha256": digest}


def aux_uf(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "codigo_ibge": [r["CODIGO"] for r in rows],
            "sigla": [r["SIGLA_UF"] for r in rows],
            "nome": [r["DESCRICAO"] for r in rows],
        }
    )


def _year(value: str) -> int | None:
    return int(value) if value.strip() else None


def aux_municipios(rows: list[dict[str, Any]]) -> pl.DataFrame:
    def coordinate(r: dict[str, Any], key: str) -> float | None:
        # CADMUN writes 0/0 where it has no position; 0°, 0° is in the Atlantic.
        return None if r["LATITUDE"] == 0 and r["LONGITUDE"] == 0 else r[key]

    return pl.DataFrame(
        {
            "codigo_ibge": [r["MUNCODDV"] for r in rows],
            "codigo_6": [r["MUNCOD"] for r in rows],
            "nome": [r["MUNNOME"] for r in rows],
            "uf_codigo": [r["UFCOD"] for r in rows],
            "situacao": [r["SITUACAO"] for r in rows],
            "ano_instalacao": [_year(r["ANOINST"]) for r in rows],
            "ano_extincao": [_year(r["ANOEXT"]) for r in rows],
            "sucessor": [r["SUCESSOR"] or None for r in rows],
            "latitude": [coordinate(r, "LATITUDE") for r in rows],
            "longitude": [coordinate(r, "LONGITUDE") for r in rows],
            "altitude": [r["ALTITUDE"] for r in rows],
            "area": [r["AREA"] for r in rows],
            "regiao_saude": [r["RSAUDCOD"] for r in rows],
            "macrorregiao_saude": [r["MSAUDCOD"] for r in rows],
        },
        schema_overrides={"ano_instalacao": pl.Int32, "ano_extincao": pl.Int32},
    )


def cid10_groups(raw: bytes) -> list[tuple[str, str, str, str]]:
    """Flat CID-10 ranges in TAB_SIH's CID10GRUPOS.CNV (not its nested GRUPO CNV)."""
    lines = raw.decode("cp1252").splitlines()
    if not lines or lines[0] != "265 3 L" or len(lines) != 266:
        raise ValueError("CID10GRUPOS.CNV: expected header and 265 categories")
    groups = []
    for number, line in enumerate(lines[1:], start=1):
        if not line[:7].strip().isdigit() or int(line[:7]) != number or line[7:9] != "  ":
            raise ValueError(f"CID10GRUPOS.CNV: invalid category {number}")
        label = line[9:60].strip()
        if not label:
            raise ValueError(f"CID10GRUPOS.CNV: category {number} has no description")
        if number == 265:
            if label != "Não preenchido" or line[60:].strip() != ",":
                raise ValueError("CID10GRUPOS.CNV: invalid empty-code category")
            continue
        match = re.fullmatch(r"([A-Z]\d{2})-([A-Z]\d{2}),", line[60:])
        if match is None:
            raise ValueError(f"CID10GRUPOS.CNV: invalid range at category {number}")
        first, last = match.groups()
        if first > last:
            raise ValueError(f"CID10GRUPOS.CNV: reversed range at category {number}")
        groups.append((first, last, f"{first}-{last}", label))
    ordered = sorted(groups)
    for previous, current in pairwise(ordered):
        if current[0] <= previous[1]:
            raise ValueError(f"CID10GRUPOS.CNV: overlapping ranges {previous[2]} and {current[2]}")
    return groups


def aux_cid10(
    rows: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    groups: list[tuple[str, str, str, str]],
) -> pl.DataFrame:
    def display(code: str) -> str:
        return code if len(code) == 3 else f"{code[:3]}.{code[3:]}"

    def chapter(code: str) -> int:
        found = [
            n
            for n, c in enumerate(chapters, start=1)
            if c["CAUSAS"][:3] <= code[:3] <= c["CAUSAS"][4:7]
        ]
        if len(found) != 1:
            raise SystemExit(f"CID-10 {code} falls in chapters {found}")
        return found[0]

    def group(code: str) -> tuple[str, str, str, str] | None:
        return next((g for g in groups if g[0] <= code[:3] <= g[1]), None)

    for r in rows:
        if not r["DESCR"].startswith(display(r["CID10"])):
            raise SystemExit(f"CID-10 {r['CID10']}: DESCR does not start with its code")
    matched_groups = [group(r["CID10"]) for r in rows]
    return pl.DataFrame(
        {
            "codigo": [r["CID10"] for r in rows],
            "descricao": [r["DESCR"][len(display(r["CID10"])) :].strip() for r in rows],
            "capitulo": [chapter(r["CID10"]) for r in rows],
            "capitulo_descricao": [chapters[chapter(r["CID10"]) - 1]["DESCRICAO"] for r in rows],
            "bloco": [g[2] if g else None for g in matched_groups],
            "bloco_descricao": [g[3] if g else None for g in matched_groups],
        },
        schema_overrides={"capitulo": pl.Int32},
    )


def aux_ocupacoes(tabocup: list[dict[str, Any]]) -> tuple[pl.DataFrame, dict[str, str]]:
    raw = (CNV / "sim" / "CBO2002.CNV").read_bytes()
    member = json.loads((CNV / "vinculos.json").read_text(encoding="utf-8"))["membros"][
        "sim/CBO2002.CNV"
    ]
    if hashlib.sha256(raw).hexdigest() != member["sha256"]:
        raise SystemExit("CBO2002.CNV differs from vinculos.json")
    archive = next(s for s in sources_registry()["sources"] if s["id"] == member["fonte"])
    cbo = {k: v for k, v in cnv_map(parse_cnv(raw.decode("cp1252"))).items() if k}
    frame = pl.DataFrame(
        {
            "esquema": ["cbo2002"] * len(cbo) + ["tabocup"] * len(tabocup),
            "codigo": list(cbo) + [r["CODIGO"] for r in tabocup],
            "descricao": list(cbo.values()) + [r["DESCRICAO"] for r in tabocup],
        }
    )
    source = {
        "url": archive["url"],
        "sha256": archive["sha256"],
        "member": member["membro"],
        "member_sha256": member["sha256"],
    }
    return frame, source


def _entry(name: str) -> zipfile.ZipInfo:
    """A fixed timestamp, so rebuilding from the same sources gives the same zip."""
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        into = Path(tmp)
        read = {name: download(name, into) for name in ENCODING}
    ocupacoes, cbo_source = aux_ocupacoes(read["TABOCUP.DBF"][0])
    member = json.loads((CNV / "vinculos.json").read_text(encoding="utf-8"))["membros"][
        "sih/CNV/CID10GRUPOS.CNV"
    ]
    raw_groups = (CNV / "sih/CNV/CID10GRUPOS.CNV").read_bytes()
    if hashlib.sha256(raw_groups).hexdigest() != member["sha256"]:
        raise SystemExit("CID10GRUPOS.CNV differs from vinculos.json")
    archive = next(s for s in sources_registry()["sources"] if s["id"] == member["fonte"])
    groups_source = {
        "url": archive["url"],
        "sha256": archive["sha256"],
        "member": member["membro"],
        "member_sha256": member["sha256"],
    }
    groups = cid10_groups(raw_groups)
    tables = {
        "aux_uf": (aux_uf(read["TABUF.DBF"][0]), ["TABUF.DBF"]),
        "aux_municipios": (aux_municipios(read["CADMUN.DBF"][0]), ["CADMUN.DBF"]),
        "aux_cid10": (
            aux_cid10(read["CID10.DBF"][0], read["CIDCAP10.DBF"][0], groups),
            ["CID10.DBF", "CIDCAP10.DBF"],
        ),
        "aux_ocupacoes": (ocupacoes, ["TABOCUP.DBF"]),
        "aux_paises": (
            pl.DataFrame(
                {
                    "codigo": [r["CODIGO"] for r in read["TABPAIS.DBF"][0]],
                    "descricao": [r["DESCRICAO"] for r in read["TABPAIS.DBF"][0]],
                }
            ),
            ["TABPAIS.DBF"],
        ),
    }
    manifest: dict[str, Any] = {}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for table, (frame, names) in tables.items():
            buf = io.BytesIO()
            frame.write_parquet(buf, compression="zstd")
            zf.writestr(_entry(f"{table}.parquet"), buf.getvalue())
            sources = [read[n][1] for n in names]
            if table == "aux_ocupacoes":
                sources.append(cbo_source)
            if table == "aux_cid10":
                sources.append(groups_source)
            manifest[table] = {"rows": frame.height, "sources": sources}
            print(f"  {table}: {frame.height} rows")
        zf.writestr(
            _entry("manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
