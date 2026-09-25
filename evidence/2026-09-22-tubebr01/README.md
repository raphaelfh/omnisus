# TUBEBR01: the file year follows the diagnosis date

Read on 2026-09-22 from `ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/TUBEBR01.dbc`.

| | |
| --- | --- |
| `SIZE` / bytes received | 3,146,296 |
| `MDTM` | `20240710123400` |
| SHA-256 | `bd9071632d7e50defc24822c22cff373471c074f9e65fd20155d6be8e3176c57` |
| Records, fields | 87,265, 97 |

- `ID_AGRAVO` = `A169` in 87,265 of 87,265 records.
- `DT_DIAG` year is 2001 in 87,265 of 87,265 records.
- `NU_ANO` = 2001 in 83,651 records (95.86%); the other 3,614 fall in 2002 (2,989),
  2003 (486), 2004 (64), 2005 (26), 2006 (17), 2007 (1), 2008 (8), 2009 (13),
  2010 (5), 2011 (1), 2015 (2) and 2017 (2).
- `DT_NOTIFIC` year matches `NU_ANO` in every record.

No official document states that the file year follows the diagnosis date; the TB
dictionary (22 pages) and the Notificação Individual v5 were searched. It is an
observation of the files, like the `TUBEBR25` count in
`evidence/2026-09-12-sinan-e-dispensacao.md`. The file is too large to commit
(the fixture is an excerpt of `TUBEBR20`, see `tests/fixtures/FIXTURES.md`).
