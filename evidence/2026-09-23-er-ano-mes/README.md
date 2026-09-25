# ER's own ANO and MES against the file name

`census.csv` has one row per `ER*.dbc` file listed in
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/` on 2026-09-23:
server time, size, SHA-256, records, and the number of rows whose `ANO` or `MES`
differs from the year and month in the file name (`ERUFAAMM.dbc`).

- 4,931 files, 2011-01 to 2026-07, 14,656,815 records.
- `ano_differs` and `mes_differs` are 0 in every file.
- Every file has the layout `ANO C(4)`, `MES C(2)`.

`census.py` is the script, cleaned up after the run. Its `differing()` function
reproduces the `ERRR2401.dbc` row from the committed fixture
`tests/fixtures/dbc/sih_er_rr_2024_01_mini.dbc` (the same SHA-256). It reports all
31 rows as differing when that file is named as February. The run itself retried
failed downloads and appended each result as it arrived. The comparison was the
same.
