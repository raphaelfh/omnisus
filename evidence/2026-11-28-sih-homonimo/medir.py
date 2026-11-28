"""Counts about `homonimo` in RD, RJ and ER files of the SIH. Only counts leave the files.

Usage: uv run --locked python evidence/2026-11-28-sih-homonimo/medir.py DIR OUT
DIR holds RD*.dbc, RJ*.dbc and ER*.dbc files of SIHSUS/200801_/Dados/ and RD*.dbc files of
2006 and 2007 of SIHSUS/199201_200712/Dados/; OUT is the JSON written.

RD and RJ files get one profile per value of `homonimo`. A "group" is the set of rows of a
file with the same values in the fields of a key (for example `nasc`, `sexo` and
`munic_res`); `other` counts the rows whose group has another `n_aih`, and `other_marked`
those whose group has another row with `homonimo` other than 0. `near` counts the rows
with another `n_aih` of the same `nasc`, `sexo` and `munic_res` whose stay overlaps theirs
or is up to 3 days apart. No value of a key, of a CPF or of an AIH number is written.

The RD files of 2006 and 2007 have another layout and get only `cpf_aut` and `gestor_cpf`
by value of `homonimo`.

`links` follows `n_aih` between files of the same UF: from an ER or RJ file to the RJ of
the same month and to the RD files of the next 4 months that are in DIR.

Age in years: `cod_idade` 2 (days) and 3 (months) are under one year, 4 is `idade` years,
5 is `idade` plus 100 years; any other unit has no age.
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
    "uf_zi_nasc_sexo_munic_res": ["uf_zi", "nasc", "sexo", "munic_res"],
    "cnes_nasc_sexo_munic_res": ["cnes", "nasc", "sexo", "munic_res"],
}
NEAR_KEY = KEYS["nasc_sexo_munic_res"]
NEAR_DAYS = 3
MONTHS_AHEAD = 4
# DBF/LIBGESTOR.dbf of TAB_SIH.zip: the codes 134 to 243 are the ones whose label starts
# with "CNS" (the manager released an AIH without the patient's card number).
CNS_CODES = (134, 243)
# CNV/motbloqueio.cnv of TAB_SIH.zip: the codes whose label has "DUPLICIDADE" before any
# other reason (01 "DUPLICIDADE", 03 "DUPLICIDADE E AGRAVO", ...).
BLOCKED_AS_DUPLICATE = [f"{n:02d}" for n in range(1, 16, 2)]
# DBF/MOTERRO.dbf of TAB_SIH.zip, by label: "AIH BLOQUEADA POR DUPLICIDADE" alone or with
# other reasons; "AIH CANCELADA POR DUPLICIDADE", the same; "AIH BLOQUEADA POR PERÍODOS DE
# INTERNAÇÃO SOBREPOSTOS NO MOVIMENTO" and "NO ESTADO".
ERRORS = {
    "duplicidade": [f"0200{n:02d}" for n in (*range(1, 16, 2), *range(18, 33, 2))],
    "duplicidade_cancelada": [f"0300{n:02d}" for n in range(1, 16, 2)],
    "sobrepostos": ["020081", "020082"],
}

MARKED = pl.col("homonimo") != "0"
AGE = (
    pl.when(pl.col("cod_idade").is_in(["2", "3"]))
    .then(0)
    .when(pl.col("cod_idade") == "4")
    .then(pl.col("idade"))
    .when(pl.col("cod_idade") == "5")
    .then(pl.col("idade") + 100)
)
AGE_GROUP = (
    pl.when(AGE.is_null())
    .then(pl.lit("unknown"))
    .when(AGE < 1)
    .then(pl.lit("00"))
    .when(AGE < 18)
    .then(pl.lit("01_17"))
    .when(AGE < 60)
    .then(pl.lit("18_59"))
    .otherwise(pl.lit("60_or_more"))
)
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
        (pl.len().over("n_aih") > 1).alias("n_aih_repeated"),
        day("dt_inter").alias("inter"),
        day("dt_saida").alias("saida"),
    )
    for name, key in KEYS.items():
        df = df.with_columns(
            (pl.col("n_aih").n_unique().over(key) > 1).alias(f"other:{name}"),
            ((MARKED.sum().over(key) - MARKED.cast(pl.UInt32)) > 0).alias(f"other_marked:{name}"),
        )
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
        "age": counts(rows, AGE_GROUP),
        "car_int": counts(rows, pl.col("car_int")),
        "cnes_distinct": rows["cnes"].n_unique(),
        "cobranca_first_digit": counts(rows, pl.col("cobranca").str.slice(0, 1)),
        "cpf_aut_filled": rows.filter(filled("cpf_aut")).height,
        "gestor_cod": counts(rows, GESTOR_COD_CLASS),
        "gestor_cpf_distinct": rows.filter(filled("gestor_cpf"))["gestor_cpf"].n_unique(),
        "gestor_cpf_filled": rows.filter(filled("gestor_cpf")).height,
        "gestor_tp": counts(rows, pl.col("gestor_tp")),
        "ident": counts(rows, pl.col("ident")),
        "n_aih_repeated": rows.filter("n_aih_repeated").height,
        "near": rows.filter("near").height,
        "other": {name: rows.filter(f"other:{name}").height for name in KEYS},
        "other_marked": {name: rows.filter(f"other_marked:{name}").height for name in KEYS},
        "seq_aih5_not_zero": rows.filter(filled("seq_aih5")).height,
        "sexo": counts(rows, pl.col("sexo")),
        "uf_zi_distinct": rows["uf_zi"].n_unique(),
    }
    for column in ("aud_just", "sis_just"):  # the layouts before 2012 do not have them
        if column in rows.columns:
            out[f"{column}_filled"] = rows.filter(filled(column)).height
    return out


def rd_entry(df: pl.DataFrame) -> dict[str, object]:
    df = with_groups(df)
    return {
        "by_homonimo": {
            value: rd_profile(df.filter(pl.col("homonimo") == value))
            for value in sorted(df["homonimo"].unique().to_list())
        },
        "cpf_aut_distinct": df.filter(filled("cpf_aut"))["cpf_aut"].n_unique(),
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
        "cpf_aut_distinct": df.filter(filled("cpf_aut"))["cpf_aut"].n_unique(),
    }


def rj_entry(df: pl.DataFrame) -> dict[str, object]:
    return {
        "by_homonimo": {
            value: {
                "rows": rows.height,
                "gestor_cpf_filled": rows.filter(filled("gestor_cpf")).height,
                "st_bloq": counts(rows, pl.col("st_bloq")),
                "st_mot_blo": counts(rows, MOT_BLO_CLASS),
                "st_situac": counts(rows, pl.col("st_situac")),
            }
            for value in sorted(df["homonimo"].unique().to_list())
            for rows in [df.filter(pl.col("homonimo") == value)]
        },
        "st_bloq": counts(df, pl.col("st_bloq")),
        "st_mot_blo": counts(df, MOT_BLO_CLASS),
    }


def er_entry(df: pl.DataFrame) -> dict[str, object]:
    return {
        name: {
            "rows": rows.height,
            "aih": rows["aih"].n_unique(),
        }
        for name, codes in ERRORS.items()
        for rows in [df.filter(pl.col("co_erro").is_in(codes))]
    }


def later(name: str) -> list[str]:
    """The names of the files of the same UF of the next months, `RDSP1412` -> `RDSP1501`..."""
    months = int(name[4:6]) * 12 + int(name[6:8]) - 1
    return [
        f"RD{name[2:4]}{(months + step) // 12:02d}{(months + step) % 12 + 1:02d}"
        for step in range(1, MONTHS_AHEAD + 1)
    ]


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
            groups["st_mot_blo_duplicidade_st_bloq_2"] = df.filter(
                (MOT_BLO_CLASS == "duplicidade") & (pl.col("st_bloq") == "2")
            )["n_aih"]
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
        for target in later(name):
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
            slim[path.stem] = df.select("n_aih", "homonimo", "st_bloq", "st_mot_blo")
        else:
            entry["co_erro"] = er_entry(df)
            slim[path.stem] = df.select("aih", "co_erro")
        files[path.name] = entry
    result = {"files": files, "links": links(slim)}
    text = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
