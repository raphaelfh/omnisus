"""Counts about `homonimo` in RD, RJ and ER files of the SIH. Only counts leave the files.

Usage: uv run --locked python evidence/2026-11-28-sih-homonimo/medir.py DIR OUT
DIR holds RD*.dbc, RJ*.dbc and ER*.dbc files of SIHSUS/200801_/Dados/ and RD*.dbc files of
2006 and 2007 of SIHSUS/199201_200712/Dados/; OUT is the JSON written.

RD and RJ files get one profile per value of `homonimo`. A "group" is the set of rows of a
file with the same values in the fields of a key (`nasc`, `sexo` and `munic_res`, or
`nasc`, `sexo` and `cep`); `other` counts the rows whose group has another `n_aih`, and
`other_marked_nasc_sexo_cep` those whose group has another row with `homonimo` other than
0. `near` counts the rows with another `n_aih` of the same `nasc`, `sexo` and `munic_res`
whose stay overlaps theirs or is up to 3 days apart. No value of a key, of a CPF or of an
AIH number is written.

The RD files of 2006 and 2007 have another layout and get only `cpf_aut` and `gestor_cpf`
by value of `homonimo`.

`links` follows `n_aih` between files of the same UF: from an ER or RJ file to the RJ of
the same month and to the RD file of the next month, when they are in DIR.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import polars as pl

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

DATASETS = {
    "RD": "sih_aih_reduzida",
    "RJ": "sih_aih_rejeitada",
    "ER": "sih_aih_rejeitada_erro",
}
OLD_LAYOUT = "sih_aih_reduzida_1998_2007"
OLD_LAYOUT_YEARS = ("06", "07")
KEYS = {
    "nasc_sexo_munic_res": ["nasc", "sexo", "munic_res"],
    "nasc_sexo_cep": ["nasc", "sexo", "cep"],
}
MARKED_KEY = KEYS["nasc_sexo_cep"]
NEAR_KEY = KEYS["nasc_sexo_munic_res"]
NEAR_DAYS = 3
# DBF/LIBGESTOR.dbf of TAB_SIH.zip: the codes 134 to 243 are the ones whose label starts
# with "CNS" (the manager released an AIH without the patient's card number).
CNS_CODES = (134, 243)
# CNV/motbloqueio.cnv of TAB_SIH.zip: the codes whose label has "DUPLICIDADE" before any
# other reason (01 "DUPLICIDADE", 03 "DUPLICIDADE E AGRAVO", ...).
BLOCKED_AS_DUPLICATE = [f"{n:02d}" for n in range(1, 16, 2)]
# DBF/MOTERRO.dbf of TAB_SIH.zip, by label: "AIH BLOQUEADA POR DUPLICIDADE" alone or with
# other reasons (020001 to 020015 odd, 020018 to 020032 even); "AIH CANCELADA POR
# DUPLICIDADE", the same (030001 to 030015 odd); "AIH BLOQUEADA POR PERÍODOS DE INTERNAÇÃO
# SOBREPOSTOS NO MOVIMENTO" and "NO ESTADO". The codes of other kinds of duplicate are
# left out: 020054, 020055, 020077 to 020080, 030054, 030055 and 030077.
ERRORS = {
    "duplicidade": [f"0200{n:02d}" for n in (*range(1, 16, 2), *range(18, 33, 2))],
    "duplicidade_cancelada": [f"0300{n:02d}" for n in range(1, 16, 2)],
    "sobrepostos": ["020081", "020082"],
}

MARKED = pl.col("homonimo") != "0"
GESTOR_COD = pl.col("gestor_cod").cast(pl.Int64, strict=False)
GESTOR_COD_CLASS = (
    pl.when(GESTOR_COD.is_null())
    .then(pl.lit("blank"))
    .when(GESTOR_COD == 0)
    .then(pl.lit("zero"))
    .when(GESTOR_COD.is_between(*CNS_CODES))
    .then(pl.lit("cns"))
    .otherwise(pl.lit("other"))
)
MOT_BLO_CLASS = (
    pl.when(pl.col("st_mot_blo") == "00")
    .then(pl.lit("00"))
    .when(pl.col("st_mot_blo").is_in(BLOCKED_AS_DUPLICATE))
    .then(pl.lit("duplicidade"))
    .otherwise(pl.lit("other"))
)


def filled(column: str) -> pl.Expr:
    """True when the text has something other than spaces and zeros."""
    return pl.col(column).cast(pl.Utf8).fill_null("").str.replace_all(r"[0\s]", "") != ""


def counts(df: pl.DataFrame, by: pl.Expr) -> dict[str, int]:
    table = df.group_by(by.cast(pl.Utf8).fill_null("").alias("key")).len().sort("key")
    return {str(k): int(n) for k, n in table.rows()}


def day(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8).str.to_date("%Y%m%d", strict=False)


def with_groups(df: pl.DataFrame) -> pl.DataFrame:
    """Add, per row, what the other rows of its groups have. No key value is kept."""
    df = df.with_row_index("row").with_columns(
        day("dt_inter").alias("inter"),
        day("dt_saida").alias("saida"),
        ((MARKED.sum().over(MARKED_KEY) - MARKED.cast(pl.UInt32)) > 0).alias("other_marked"),
    )
    for name, key in KEYS.items():
        df = df.with_columns((pl.col("n_aih").n_unique().over(key) > 1).alias(f"other:{name}"))
    side = df.select("row", "n_aih", "inter", "saida", *NEAR_KEY)
    pairs = side.join(side, on=NEAR_KEY, suffix="_2").filter(
        (pl.col("n_aih") != pl.col("n_aih_2"))
        & (pl.col("inter_2") <= pl.col("saida").dt.offset_by(f"{NEAR_DAYS}d"))
        & (pl.col("inter") <= pl.col("saida_2").dt.offset_by(f"{NEAR_DAYS}d"))
    )
    return df.with_columns(pl.col("row").is_in(pairs["row"].unique().implode()).alias("near"))


def rd_profile(rows: pl.DataFrame) -> dict[str, object]:
    out: dict[str, object] = {
        "rows": rows.height,
        "cnes_distinct": rows["cnes"].n_unique(),
        "cobranca_first_digit": counts(rows, pl.col("cobranca").str.slice(0, 1)),
        "cpf_aut_filled": rows.filter(filled("cpf_aut")).height,
        "gestor_cod": counts(rows, GESTOR_COD_CLASS),
        "gestor_cpf_distinct": rows.filter(filled("gestor_cpf"))["gestor_cpf"].n_unique(),
        "gestor_cpf_filled": rows.filter(filled("gestor_cpf")).height,
        "gestor_tp": counts(rows, pl.col("gestor_tp")),
        "ident": counts(rows, pl.col("ident")),
        "near": rows.filter("near").height,
        "other": {name: rows.filter(f"other:{name}").height for name in KEYS},
        "other_marked_nasc_sexo_cep": rows.filter("other_marked").height,
        "seq_aih5_not_zero": rows.filter(filled("seq_aih5")).height,
        "uf_zi_distinct": rows["uf_zi"].n_unique(),
    }
    if "aud_just" in rows.columns:  # the files of 2008-01 do not have it
        out["aud_just_filled"] = rows.filter(filled("aud_just")).height
    return out


def rd_entry(df: pl.DataFrame) -> dict[str, object]:
    df = with_groups(df)
    return {
        "by_homonimo": {
            value: rd_profile(df.filter(pl.col("homonimo") == value))
            for value in sorted(df["homonimo"].unique().to_list())
        },
        "uf_zi_distinct": df["uf_zi"].n_unique(),
    }


def rd_old_entry(df: pl.DataFrame) -> dict[str, object]:
    return {
        "by_homonimo": {
            value: {
                "rows": rows.height,
                "cpf_aut_filled": rows.filter(filled("cpf_aut")).height,
                "gestor_cpf_filled": rows.filter(filled("gestor_cpf")).height,
            }
            for value in sorted(df["homonimo"].unique().to_list())
            for rows in [df.filter(pl.col("homonimo") == value)]
        },
    }


def rj_entry(df: pl.DataFrame) -> dict[str, object]:
    return {
        "by_homonimo": {
            value: {
                "rows": rows.height,
                "gestor_cpf_filled": rows.filter(filled("gestor_cpf")).height,
                "st_bloq": counts(rows, pl.col("st_bloq")),
                "st_mot_blo": counts(rows, MOT_BLO_CLASS),
            }
            for value in sorted(df["homonimo"].unique().to_list())
            for rows in [df.filter(pl.col("homonimo") == value)]
        },
    }


def er_entry(df: pl.DataFrame) -> dict[str, int]:
    """The AIH numbers the file has with each kind of error."""
    return {
        name: df.filter(pl.col("co_erro").is_in(codes))["aih"].n_unique()
        for name, codes in ERRORS.items()
    }


def next_rd(name: str) -> str:
    """The RD file of the same UF of the next month: `RJSP1412` -> `RDSP1501`."""
    months = int(name[4:6]) * 12 + int(name[6:8])
    return f"RD{name[2:4]}{months // 12:02d}{months % 12 + 1:02d}"


def by_homonimo_in(aih: pl.Series, frame: pl.DataFrame) -> dict[str, int]:
    """Of the AIH numbers given, how many are in `frame`, by the `homonimo` they have there."""
    found = frame.filter(pl.col("n_aih").is_in(aih.unique().implode()))
    per_aih = found.group_by("n_aih").agg(pl.col("homonimo").unique().sort().str.join("+"))
    return counts(per_aih, pl.col("homonimo"))


def links(frames: dict[str, pl.DataFrame]) -> dict[str, object]:
    out: dict[str, object] = {}
    for name in sorted(frames):
        kind, df = name[:2], frames[name]
        if kind == "RJ":
            groups = {
                f"homonimo_{value}": df.filter(pl.col("homonimo") == value)["n_aih"]
                for value in sorted(df["homonimo"].unique().to_list())
            }
        elif kind == "ER":
            groups = {
                f"co_erro_{error}": df.filter(pl.col("co_erro").is_in(codes))["aih"]
                for error, codes in ERRORS.items()
            }
            same_month = "RJ" + name[2:]
            if same_month in frames:
                out[f"{name}>{same_month}"] = {
                    group: {
                        "aih": aih.n_unique(),
                        "by_homonimo_there": by_homonimo_in(aih, frames[same_month]),
                    }
                    for group, aih in groups.items()
                }
        else:
            continue
        target = next_rd(name)
        if target in frames:
            out[f"{name}>{target}"] = {
                group: {
                    "aih": aih.n_unique(),
                    "by_homonimo_there": by_homonimo_in(aih, frames[target]),
                }
                for group, aih in groups.items()
            }
    return out


def main() -> None:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    files: dict[str, dict] = {}
    slim: dict[str, pl.DataFrame] = {}
    for path in sorted(folder.glob("*.dbc")):
        kind = path.name[:2]
        old = kind == "RD" and path.name[4:6] in OLD_LAYOUT_YEARS
        raw = path.read_bytes()
        dataset = OLD_LAYOUT if old else DATASETS[kind]
        df = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect()
        entry: dict[str, object] = {
            "bytes": len(raw),
            "rows": df.height,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        if old:
            entry["homonimo"] = counts(df, pl.col("homonimo"))
            entry.update(rd_old_entry(df))
        elif kind == "RD":
            entry["homonimo"] = counts(df, pl.col("homonimo"))
            entry.update(rd_entry(df))
            slim[path.stem] = df.select("n_aih", "homonimo")
        elif kind == "RJ":
            entry["homonimo"] = counts(df, pl.col("homonimo"))
            entry.update(rj_entry(df))
            slim[path.stem] = df.select("n_aih", "homonimo")
        else:
            entry["co_erro"] = er_entry(df)
            slim[path.stem] = df.select("aih", "co_erro")
        files[path.name] = entry
    result = {"files": files, "links": links(slim)}
    text = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
