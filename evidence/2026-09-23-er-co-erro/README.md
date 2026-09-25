# CO_ERRO values in every ER file

`co_erro.csv` has one row per `CO_ERRO` value found in the 4,931 `ER*.dbc` files listed
in `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/` on 2026-09-23
(2011-01 to 2026-07; their SHA-256 are in `evidence/2026-09-23-er-ano-mes/census.csv`): rows,
files, and whether `DBF/MOTERRO.dbf` of `TAB_SIH.zip` (`sih-tab-f05b32f32908`, member SHA-256
`1cf988a1…47892`) lists it.

- 14,656,815 rows, 398 distinct values, all of 6 characters.
- 15 values (8,048 rows) are not in `MOTERRO.dbf`.
- None of the table's 60 codes of 4 characters appears.

`census.py` is the script, cleaned up after the run; `in_moterro` was added by comparing
each value with the `CD_MOT_ERR` codes of `MOTERRO.dbf`. The run retried failed downloads
and appended each file's counts as it arrived.
