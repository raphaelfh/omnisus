# RD from 2008: DIAGSEC9 is C(1) in every file read that has it

`census.csv` has one row per `RD*.dbc` file read from
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`, listed on
2026-10-06: server time, size, SHA-256, records, layout number and the DBF field
descriptors (`NAME TYPE WIDTH.DECIMALS`, in file order). `census.py` wrote it, the same
reading as `evidence/2026-10-01-rd-1992-2007-layouts/census.py` for this directory:

    uv run --locked python evidence/2026-10-06-rd-2008-layouts/census.py CACHE_DIR \
        evidence/2026-10-06-rd-2008-layouts/census.csv

- 243 files, 3,776,680 records, server times from 2013-11-01 to 2026-09-06.
- One file per month from 2008-01 to 2026-07 (223 months, 684,614 records): `RDRR`,
  except 2026-07, read from `RDAP`.
- 6 distinct descriptor lists (layouts), each one run of consecutive months. At each of
  the 10 months on either side of a layout change, `RDSP` and `RDMG` have the same layout
  as the `RDRR` file of that month.

| Layout | Months | Files | Fields | Adds | Changes width |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | 2008-01 to 2010-12 | 38 | 86 | (first) | |
| 2 | 2011-01 to 2011-12 | 16 | 93 | NAT_JUR AUD_JUST SIS_JUST VAL_SH_FED VAL_SP_FED VAL_SH_GES VAL_SP_GES | |
| 3 | 2012-01 to 2012-12 | 16 | 93 | | INSC_PN C10 to C12, GESTOR_COD C3 to C5 |
| 4 | 2013-01 to 2013-12 | 16 | 95 | VAL_UCI MARCA_UCI | |
| 5 | 2014-01 to 2025-02 | 138 | 113 | DIAGSEC1-9 TPDISEC1-9 | |
| 6 | 2025-03 to 2026-07 | 19 | 114 | FONTE_ORC | |

No layout drops a field.

**What it settles (#67).** `DIAGSEC1` to `DIAGSEC9` enter in 2014-01 and keep their
widths to 2026-07: `DIAGSEC1` to `DIAGSEC8` are C(4) and `DIAGSEC9` is C(1) in all 157
files read that have the field, the `RDSP` and `RDMG` reads included. The census reads
one UF a month, so it does not show every UF's file; the fixtures RDSP2201 and RDSP2308
also have `DIAGSEC9` C(1). IT_SIHSUS_1603
(`sihsus-1e89d5f2cc41`, p. 4) gives `DIAGSEC9 char (4)`. A one-character field cannot
hold a CID-10 code (3 or 4 characters), so `sih_aih_reduzida.diagsec9` declares no
reference to `aux_cid10`, and its `physical_type` claim is `conflicting`.
