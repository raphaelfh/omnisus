"""Build src/omnisus/data/auxiliares-bootstrap.zip from hashed DATASUS files.

    uv run python scripts/build_bootstrap_zip.py

Every source is a file of ``SIM/CID10/TABELAS`` registered in
``sources/registry.json``, plus the packaged ``sources/cnv/sim/CBO2002.CNV``. Each
download must match its registered SHA-256, else the build stops. The zip carries one
Parquet file per table and ``manifest.json`` (table -> rows and sources).
"""

from __future__ import annotations

import ftplib
import hashlib
import io
import json
import tempfile
import zipfile
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


def aux_cid10(rows: list[dict[str, Any]], chapters: list[dict[str, Any]]) -> pl.DataFrame:
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

    for r in rows:
        if not r["DESCR"].startswith(display(r["CID10"])):
            raise SystemExit(f"CID-10 {r['CID10']}: DESCR does not start with its code")
    return pl.DataFrame(
        {
            "codigo": [r["CID10"] for r in rows],
            "descricao": [r["DESCR"][len(display(r["CID10"])) :].strip() for r in rows],
            "capitulo": [chapter(r["CID10"]) for r in rows],
            "capitulo_descricao": [chapters[chapter(r["CID10"]) - 1]["DESCRICAO"] for r in rows],
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
    tables = {
        "aux_uf": (aux_uf(read["TABUF.DBF"][0]), ["TABUF.DBF"]),
        "aux_municipios": (aux_municipios(read["CADMUN.DBF"][0]), ["CADMUN.DBF"]),
        "aux_cid10": (
            aux_cid10(read["CID10.DBF"][0], read["CIDCAP10.DBF"][0]),
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
            manifest[table] = {"rows": frame.height, "sources": sources}
            print(f"  {table}: {frame.height} rows")
        zf.writestr(
            _entry("manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
