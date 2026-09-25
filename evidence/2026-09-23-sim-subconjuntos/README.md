# SIM subsets are DO records

`compare.csv` has one row per national subset file (`SIM/CID10/DOFET/DOINF`, `DOMAT`,
`DOEXT` + year) for 1996, 2000, 2005, 2010, 2015, 2017, 2018, 2019, 2022, 2023 and 2024.
Each row gives the file's SHA-256 and the SHA-256 of `SIM/CID10/DORES/DORR<year>.dbc`,
all downloaded 2026-09-23. It counts the subset's RR residents (`CODMUNRES` starting
with 14) that equal a DORR record on every field both files have (`equal`), and on
every field but `CONTADOR`, the file's own record counter (`equal_but_contador`).
`compare.py` is the script.

- 2018 to 2024: every RR-resident record equals a DORR record, byte for byte. From 2019
  on the two layouts are identical (87 fields).
- 1996, 2000, 2005, 2017: every record equals a DORR record once `CONTADOR` is set aside.
- 2010 and 2015 have gaps: DOINF10 58/126, DOMAT10 0/1, DOEXT10 109/372, DOMAT15 0/11,
  DOEXT15 490/536.

To see what differs, each RR subset record was matched to the DORR record with the same
`DTOBITO`, `DTNASC`, `SEXO`, `CAUSABAS` and `HORAOBITO`. Over the 11 years, 7,999 records
had exactly one such DORR record and 28 had none or several. Apart from `CONTADOR`, the
only differences were 498 values blank in the subset and filled in DORR: `CODBAIRES` and
`CODBAIOCOR` in 2010, `NUDIASOBIN` in 2015. No field held two different non-blank values.
