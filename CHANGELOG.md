# Changelog

## Unreleased

### omnisus-dbf 0.2.2

- The native reader reads D (date) fields with the semantics of dbfread's `parseD`, so
  SINAN national files no longer fall back to the Python reader. `API_VERSION` stays 2
  (#149).

### Dictionaries

- `sim_obitos` 2.16.1 and `sim_obitos_externos`, `sim_obitos_infantis` and
  `sim_obitos_maternos` 1.11.1: the code maps of `altcausa`, `assistmed`, `atestante`,
  `codificado`, `esc2010`, `escmae2010`, `morteparto`, `origem`, `tp_altera`,
  `tpnivelinv` and `tppos` (`tp_altera` only in `sim_obitos`) become
  `verified_in_source` after a human review against the registered documents. The conflicts of `atestante` and `tppos` are closed: the document
  and the CNV word code 1 of `atestante` differently, and for `tppos` the document lists
  1 and 2 where the files write S and N, so the files decide; each resolved issue keeps
  the previous text. No label or code changes. New source `sim-2177e17cf20b`, the
  Estrutura do SIM of 06/2025 on the Portal de Dados Abertos do SUS (#245).
- `sinasc_nascidos_vivos` 2.8.0: code `5` of `locnasc` gains the label "Aldeia indígena",
  which the manual of the DN (4th edition, p. 23) and the SINASC Estrutura of 1996 to
  2019 (p. 1) give it; `LOCOCOR.CNV` groups it under "Ignorado", and 740 of the 13,091
  rows of `DNRR2022.dbc` publish it. The map of `locnasc` is now kept by hand, the lines
  of the CNV with that one label replaced, outside the fields `gerar_decode_cnv.py`
  generates. `stdnnova` becomes `0` "Não" and `1` "Sim". 25 of the 26 code-map claims
  become `verified_in_source`: 23 reviewed by a human reviewer, and `locnasc` and
  `sttrabpart` by decision of the maintainer on her findings. Code `3` of `sttrabpart`
  stays unlabelled: only the Estrutura lists it and no row of that file publishes it
  (issue `sttrabpart-3-so-no-estrutura`), and so does code `9` of `paridade`, which only
  `Estrutura_SINASC_para_CD.pdf` lists (issue `paridade-9-so-no-estrutura-para-cd`). New sources: `sinasc-0ffc45994687` and
  `sinasc-5956ea4d8e89` (#246).
- `sia_apac_cirurgia_bariatrica`, `sia_apac_laudos_diversos`, `sia_apac_medicamentos`,
  `sia_apac_quimioterapia` and `sia_apac_tratamento_dialitico` 0.6.1 and
  `sia_psicossocial` 0.5.1: 48 `cnv-parse` claims on `/field/codes` go from
  `conflicting` to `verified_in_source` after a human review, and on each of these
  fields the issue `cnv-difere-do-mapa-anterior` is resolved. No label or code changes.
  `am_gestant` of `sia_apac_medicamentos` stays `conflicting`, with the issue open:
  `GESTANTE.CNV` labels `N` "Nao - (O paciente é gestante)" (#247).

## v0.5.1 — 2026-11-28

**Upgrading from 0.5.0:** no parser version changed (the import still reads the same
`encoding` and `x-identity` of every dictionary), so a 0.5.0 lake keeps every scope;
`load` downloads nothing again. Code `17` of `espec` gains a label in `sih_aih_reduzida`
and `sih_aih_rejeitada` (below); no other label or code changes.

### Dictionaries

- `registry.json` registers the `TAB_SIH.zip` republished on 2026-11-24
  (`sih-tab-2491e8d4f2db`). All 885 members were compared with the edition of 2026-10-15:
  58 `DBF/` members changed, none of them packaged, and the 33 members `vinculos.json`
  packages are identical, so they stay on `sih-tab-f05b32f32908` and
  `sih-tab-21e42384645a`; `evidence/2026-11-28-tab-sih-republicado/` has the member
  census (#255).
- `registry.json` registers the `TAB_SIA.zip` republished on 2026-11-24
  (`sia-tab-5e145464db62`). All 877 members were compared with the edition of 2026-10-15:
  30 `DBF/` members changed, none of them packaged, and the 53 members `vinculos.json`
  packages are identical, so they stay on `sia-tab-e5812b51d802` and
  `sia-tab-1ce232b217c6`; `evidence/2026-11-28-tab-sia-republicado/` has the member
  census.
- `sih_aih_reduzida` 2.31.0 and `sih_aih_rejeitada` 1.12.0: code `17` of `espec` gains
  the label "17-Estabelecimento Exclusivo UTI SUS". Portaria SAES/MS nº 245/2020, art. 2º,
  adds the code to the AIH speciality table; `LEITOS.CNV` lacks it. The map of `espec` is
  now kept by hand, the 41 lines of the CNV plus 17, outside the fields
  `gerar_decode_cnv.py` generates; its claim cites both sources and the issue
  `espec-17-sem-fonte` is resolved. No other label or code changes. In the `RDSP` files
  of 2020-01 to 2022-02 the code appears from 2020-07 on, in 1,963 AIH, and in 75 AIH of
  the `RJSP` files of 2022-01 to 2022-03; every one has `proc_rea` 0303010223 and `marca_uti`
  51 (`evidence/2026-11-28-sih-espec-17/`, #254).
- The page of `sih_aih_reduzida` (`docs/sources/sih_aih_reduzida.md`) gains the notes of
  a review against the SIH manual of 2012 and the norms behind the fields, each with its
  source in the registry and counts from real files: one admission can span several AIH
  and `n_aih` does not give the type; `cobranca` 61 to 67; external cause in the secondary
  diagnosis; `qt_diarias` is not length of stay; `sexo` 1 and 3; `marca_uti` 74 still
  published; `uti_int_to` and `marca_uci` only neonatal in the files read; `cid_morte`
  without the cause from 2015-02; `raca_cor` 99 and its end announced for April 2023;
  `diar_acom` counts billed daily rates; `uti_mes_to` above 31 and without 999 in the
  files read
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`, `evidence/2026-11-28-rd-uti-mes-to-regct/`,
  `evidence/2026-11-28-rd-medidas-da-revisao/`).

## v0.5.0 — 2026-11-21

**Upgrading from 0.4.1:** one entry is marked **Breaking** below. The dataset
`sih_aih_reduzida_1992_2007` no longer exists: import its months again as
`sih_aih_reduzida_1992_1997` and `sih_aih_reduzida_1998_2007`. A lake keeps the old
table, and nothing writes to it any more.

No parser version changed (no dictionary changed its `encoding` or `x-identity`), so
`skip_same` reports every other scope already published as unchanged.

### Datasets

- `cnes_estabelecimentos_ensino` covers 2007-03 to 2026-10, not to 2021-07: on 2026-11-20
  the server lists `EESP2610.dbc` (2026-11-17, one record, the 31 fields of the other EE
  files), the only file of 2020 onwards besides the empty `EEMG2107.dbc`. The weekly
  registry probe had failed on it (`evidence/2026-11-20-cnes-ee-2610/README.md`).
### Dictionaries

- **Breaking:** the dataset `sih_aih_reduzida_1992_2007` is split at 1998-01 into
  `sih_aih_reduzida_1992_1997` (43 fields, 7 DBF layouts, `diag_princ` in CID-9) and
  `sih_aih_reduzida_1998_2007` (80 fields, 12 layouts, `diag_princ` in CID-10), as decided
  in #12 (decision 1, ADR 0002 amendment of 2026-11-16). They share the directory
  `SIHSUS/199201_200712/Dados` and the prefix `RD`; `coverage` cuts the months. The old
  name no longer exists. Against a lake that imported it (RDRR0712, checked with the
  code of this change): `load`, `import_dataset`, `outdated` and `read(..., years=...)`
  raise `ValueError: unknown dataset`; `describe_dataset` and `label` raise
  `FileNotFoundError` (no dictionary); `read(table)` without `years` and `cite` still
  work, `cite` printing the table name as the title. The table `sih_aih_reduzida_1992_2007`
  stays in the lake and nothing writes to it any more; to move on, import the months again
  under the new names. Each new table has only the columns of its era. Both
  dictionaries are new, at 1.0.1, with the maps and claims the old one had (the
  generator output is unchanged); the issue `diag-princ-cid9-ate-1997` becomes
  `diag-princ-cid9` in the first, and the second declares no issue on `diag_princ`.
  `travar_versoes.py` gets
  `RETIRED`, so the old entry stays in `versoes.json`, at 1.3.2. Dates, foreign keys and
  the CNVs of the era stay for the next changes of #12. `num_proc` (1992-1997) and
  `insc_pn` and `seq_aih5` (1998-2007) are declared `string`, and the import writes the
  months that publish them as numbers as text, as 0.4.1 does (#40). The entries of
  0.4.1 and earlier name the dataset as it was then.
- A file name whose scope is outside a dataset's declared `coverage` is no longer read as
  a file of that dataset, for state rows as for the national ones of #225:
  `available` stops listing a name beyond the declared end (or before the start) of a
  bounded row, such as
  `sim_obitos_cid9` (1979-01 to 1995-12), which the importer already skipped with
  `outside_coverage`. It is what lets the two RD rows share one directory.
- `sih_aih_reduzida_1992_1997` and `sih_aih_reduzida_1998_2007` (1.1.2): `num_proc`,
  `insc_pn` and `seq_aih5` have the open issue `sem-zeros-a-esquerda`, with the months
  the DBF publishes each as a number and the code therefore has no zeros to its left:
  1996-01 to 1996-07 for `num_proc` (11 of the files of the census, #197) and 2004-07
  to 2006-03 for `insc_pn` and `seq_aih5` (35 files, #198 and #199). The counts are
  those of `evidence/2026-10-01-rd-1992-2007-layouts/census.csv`, whose README now says
  what the import does with the three fields (#40). The import does not change: it is
  the rule of 0.4.1. New fixture: `sih_rd_rr_1996_02_mini`, the 264 records of
  `RDRR9602`, where `num_proc` is `364` beside the `0489` of `RDRR9709`;
  `test_rd_n_as_text.py` imports it through `import_dataset` before and after a month
  that publishes text, in the two eras of the RD. Of the 71 real DBC fixtures, four now
  have a field staged with the type of the dictionary (`test_staged_types.py`).
- Every DATASUS dictionary (47) declares the columns the import adds, each with an
  `x-metadata.derivation`: `ano` and `uf` of a state file, `mes` of a monthly one,
  `_source_ano` of a national one, `_source_release` of all. Before, 42 declared none of
  them, 3 declared some without a `derivation` (`cnes_estabelecimentos`,
  `sinasc_nascidos_vivos`, `sih_aih_rejeitada_erro`) and only `sih_aih_reduzida` and
  `sim_obitos` declared all; `sus.check_columns` called the missing ones `not in
  dictionary`, and now gives them their label (#11). They come from
  `library_columns(dataset)`, the function the runner uses (staging takes the types from
  the same module), and are written by
  `scripts/metadados/gerar_colunas_lib.py`; the inventory tests count only the fields
  without a `derivation` of kind `source_partition` or `publication`. Each dictionary has
  a new minor `x-version`. The removal of the `_source_release` map already landed in
  0.3.0 (#174).
- `sih_aih_rejeitada_erro` declares `ano` and `mes` as `integer`, the type the lake
  stores, with `physical_type` `string` 4 and 2: the ER publishes ANO C(4) and MES C(2)
  and staging replaces them with the scope.
- `sia_apac_nefrologia` (1.12.0): `ap_mvm` and `ap_cmp` are `yearmonth`, like the
  competência fields of seven other SIA dictionaries, each with a `/field/logical_type`
  claim that cites the row of the AN layout (Informe Técnico SIASUS 2019-07, pp. 7 and
  8, "(AAAAMM)") and the lines of `APAC_Nefrologia.DEF` that bind the field to
  `ANOMES2008.CNV`; it stays `unreviewed` (read by an agent). Every record of `ANPA1410`
  and `ANRR1401` publishes a year and a month from 01 to 12 in both. No transform reads
  the type: the parser and `sus.label` still return the two fields as published, as
  strings; `describe_dataset` and the mapping panel report the new `logical_type`
  (#183).

## v0.4.1 — 2026-11-20

**Upgrading from 0.4.0:** two entries are marked **Breaking** below.

- `sinan_dengue` now covers 2014 onwards. Import 2000–2012 with `sinan_dengue_2000_2012`
  and 2013 with `sinan_dengue_2013`; rows of those years that a 0.4.0 lake already holds
  in the table `sinan_dengue` stay there and are not moved.
- A whole-number `N` field is staged with the type its dictionary declares (under Import,
  with what to do with a lake whose table has such a column as a number).

The parser version stays `dbc-staging-v2`, so `skip_same` reports every scope already
published as unchanged.

### Datasets

- **Breaking:** the dengue series is three datasets, one lake table per layout (#225).
  `sinan_dengue` now covers 2014 onwards (`DENGBR14` to `DENGBR26`); `DENGBR00` to
  `DENGBR12` are `sinan_dengue_2000_2012` (147 fields) and `DENGBR13` is
  `sinan_dengue_2013` (67 fields). In 0.4.0 `sinan_dengue` covered 2000 onwards, and the
  lake refused 2007–2013 in a table that held 2014 onwards, because `nu_idade_n` and
  `plaq_menor` change type. `available("sinan_dengue")` no longer lists 2000–2013, and
  importing one of those years into it returns `outside_coverage`; rows a 0.4.0 lake
  already holds stay where they are. The two new dictionaries carry the maps of the
  Notificação Individual block only, and no age rule. Tested on 2026-11-20 with eight
  files from the server in one lake (`evidence/2026-11-20-sinan-dengue/README.md`).
  - `Dataset.two_digit_from` names the first year of the hundred years a two-digit year is
    read in, when it is not the first covered year: `sinan_dengue` sets 2000, so
    `DENGBR07` is 2007 and not 2107.
  - A national file name whose year is outside the row's coverage is not read as a file
    of that row, so rows that share a prefix and a directory split the files by year.
  - `sinan_dengue` 1.0.1: `x-evidence` names the two datasets that hold the other layouts.
  - `notebooks/bases.py` lists the fields of a dictionary whose first labelled field comes
    after the hundredth (`sinan_dengue_2000_2012`); it raised a polars `ComputeError`.

### Import

- **Breaking.** A field the DBF header declares `N` with no decimals is staged with the
  type the dictionary declares: as text when that is `string` or `date`, the number with
  no zeros to its left, and as a number with decimals when it is `number`. Nothing else
  is converted. Staged as published, such a field had one type in some files and another
  in the rest, and the lake refused whichever was imported second (`UnsafeSchemaError`).
  Of the 70 real DBC fixtures, three change (`test_staged_types.py`): `RDRR9603`, where
  `num_proc` is `368` beside the `0489` of `RDRR9709`; `RDRR0407`, where `insc_pn` and
  `seq_aih5` are `0` in the 91 records of the fixture beside the `0000000000` and `000`
  of `RDRR0712` (#40); and `RDAC0909`, where 17 fields are `N1.0` (#219). In the headers
  of every `RD`, `SP` and `RJ` file (`evidence/2026-11-19-sih-cabecalhos/`) the fields it
  reaches are those of the 188 `RD` files of 1996-01 to 1996-07, the 567 of 2004-07 to
  2006-03 and `RDAC0909`; the files of the other datasets were not surveyed beyond their
  fixtures. A `Dataset` built by the user takes the same path: a whole number its
  dictionary declares `string`, `date` or `number` is no longer staged as BIGINT.
  **Upgrading:** the parser version stays `dbc-staging-v2`, so `skip_same` reports every
  scope already published as unchanged. A lake whose table has one of these columns as a
  number, because it began with such a file, refuses the files staged from now on, also
  under `replace`; no operation of the library changes the type of a column, and the
  table has to be imported again into a new lake (`docs/architecture.md`).
  `describe_dataset` gives `storage.dictionary_types` as `applied_to_whole_numbers`, not
  `descriptive`. `sih_aih_reduzida_1992_2007` (1.3.2) says in its `x-evidence` what
  staging does. New fixture: `sih_rd_rr_1996_03_excerpt`, five records of `RDRR9603`.

### Dictionaries

- `sih_aih_reduzida` (2.20.1): 110 fields take the `description` that Table 1 of
  `IT_SIHSUS_1603.pdf` prints for them, each with a `/field/description` claim
  (`pdf-read`, `verified_in_source`) that names the page and quotes the row;
  `describe_dataset` returned `description: null` for them. The table is transcribed in
  `evidence/2026-11-18-it-sihsus-1603-layout-rd/`. `fonte_orc` gets the label the
  `RD2008.DEF` gives it, "Fonte Orçamentária", and `sis_just` is "Justificativa do
  estabelecimento", as the document says, not "Justificativa do sistema"; each of the two
  labels has a `/field/label` claim (#182).
- `sih_aih_reduzida` (2.21.1): the 72 text fields that had no `physical_type` declare the
  width of their DBF descriptor in the last layout read (6, 2025-03 to 2026-07), from the
  census of `evidence/2026-10-06-rd-2008-layouts` (one file of RR, or AP, a month, plus SP
  and MG at the months a layout changes). The `/field/physical_type` claim is
  `verified_in_source` where Table 1 of `IT_SIHSUS_1603.pdf` prints the same width (66
  fields) and `conflicting` where it prints another: `nacional` (char(2), published
  C(3)), `raca_cor` (char(4), C(2)), `cbor` (char(3), C(6)), `gestor_cpf` (char(11),
  C(15)) and `gestor_cod` (char(3), C(5)). In the files read, `gestor_cod` and `insc_pn`
  are C(3) and C(10) until 2011-12 and C(5) and C(12) from 2012-01, while the table, "para
  janeiro de 2008 em diante", prints char(3) and char(12). Each of the six has the open
  issue `largura-difere-do-documento`. `fonte_orc`, which the document does not list,
  declares C(2) with an unreviewed claim that cites the census. Numeric fields stay
  without `physical_type`: the contract's `{type, length}` has no place for the decimals
  of 19 of the 36, and no dictionary uses a type other than `string` for the other 17
- `uf_zi` of `sih_aih_reduzida` (2.22.1) and of `sih_aih_rejeitada` (1.6.1) takes the labels
  of `CNV/br_municgestor.cnv`, the table `RD2008.DEF` (lines 175-176) and `RJ2008.DEF`
  (lines 177-178) bind it to, packaged from `TAB_SIH.zip` (`sih-tab-21e42384645a`):
  15,731 codes, a new `uf_zi_rotulo` column. The table has 5,569 municipality lines
  (Brasília's `530010` is on the line "530000 Distrito Federal") and, for each of the 26
  states, a line "Gestão estadual" for the code of the UF followed by `0000`: RDRR2401
  publishes `140000`, "140000 Roraima - Gestão estadual", in 2,920 of its 3,714 records.
  Each label starts with the code of its table line, as the table prints it, so a key
  listed as a second code or inside a range shows that line's code (`149999` is "140000
  Roraima - Gestão estadual"). 10,087 of the keys come from three lines that write
  ranges, which TabWin.pdf (pp. 90-91) documents only for codes of up to 4 characters;
  the open issue `uf_zi-faixa-em-codigo-longo` says so. The field leaves `sem_cnv` (#137) in both datasets. It keeps no reference to
  `aux_municipios`, where `140000` is "Município ignorado - RR" (#182).
  (#182).
- `sih_aih_reduzida` (2.23.1): 28 labels now come from a registered document, each with
  a `/field/label` claim; 27 change their text and `num_proc` keeps it. Nine are the
  words of `IT_SIHSUS_1603.pdf`: `ano_cmpt` and `mes_cmpt` ("Ano/Mês de processamento da
  AIH"), `qt_diarias`, `us_tot`, `cobranca`, `ind_vdrl`, `gestrisco`, `gestor_tp` and
  `cid_notif` ("CID de Notificação", not "notificação compulsória"). The 19 fields that
  document describes only as "Zerado" take the description of `Layout_REDUZIDA.pdf`
  (`sihsus-f6084d22de30`, transcribed in `evidence/2026-11-18-layout-reduzida-sihd/`),
  whose 75 fields are those of the RD files read from 2006-04 to 2007-12, and an open
  issue `rotulo-do-layout-ate-2007` that says the label is of that period. Examples:
  `val_sadtsr` was "Valor tomografia/ressonância" and is "Valor de SADT sem rateio";
  `val_obsang` was "Valor analgesia obstétrica" and is "Valor de anestesia"; the three
  `uti_int_*` said "UCI" and say "Dias em UTI ... (tipo ato = 34 ou 56)", while
  `IT_SIHSUS_1603` calls their total "unidade intermediaria", which their issue records.
  Where `IT_SIHSUS_1603` describes a field its text is used, even where the earlier
  layout said otherwise ("ANO COMPETÊNCIA", "MOTIVO DE COBRANCA", "GESTANTE DE ALTO
  RISCO"). `cid_notif` declares the reference to `aux_cid10`: `RD2008.DEF` (lines
  523-527) relates it to CID-10 tables, and the 49 filled rows of RDRR2401, all `Z302`,
  find their row; the open issue `cid_notif-laqueadura-no-def` records that the DEF
  calls the field "CID laqueadura". Other labels of the dictionary still have no claim
  (#182).
- `sih_aih_reduzida` (2.24.1): the `0` of `tpdisec1` to `tpdisec9` and the codes of
  `homonimo` keep no label, and their open issues now name the documents that were read.
  Two say what the `0` of the class of a secondary diagnosis is in another file: the
  layout of the SISAIH01 text interface for 09/2015 (`sihsus-af543b2b2c9b`, p. 7, "0 -
  Quando não é preenchido o campo anterior") and the dictionary of the tables `TB_AIH`
  and `TB_HAIH` (`sihsus-f70974716de8`, p. 4, "0-Quando campo anterior em branco"); no
  DEF relates `TPDISEC1-9` to them, and by the maintainer's decision in #182 a code of
  another file does not become a label without that. Two give "0 = não", "1 = sim" for
  the homonym mark: that dictionary (pp. 8-9) and the layout of the RD files of 2006-04
  to 2007-12 (`sihsus-f6084d22de30`, p. 2); the RD from 2008 publishes `2`, which
  neither lists. The passages are in
  `evidence/2026-11-18-sih-codigos-em-outros-documentos/` (#182).
- `sih_aih_reduzida` (2.25.1): `ano_cmpt` and `mes_cmpt` declare `string` and `rubrica`
  declares `integer`, the types the library stages from the files (`ANO_CMPT` C(4),
  `MES_CMPT` C(2), `RUBRICA` N(5)); they declared `integer`, `integer` and `string`.
  `describe_dataset` reports the new `logical_type`. The lake does not change: the
  import does not read `type` (only `check_columns` does, to tell the dates), so
  `ano_cmpt` was already text (`2024`) and `mes_cmpt` text with its leading zero (`01`).
  The three types are C(4), C(2) and N(5) in the 243 files of
  `evidence/2026-10-06-rd-2008-layouts`. Other dictionaries still declare a type their
  files do not stage, such as `insc_pn` of `sih_aih_reduzida_1992_2007` (#182).
- `sih_aih_reduzida` (2.26.1) and `sih_aih_rejeitada` (1.7.1): counts from 262 real RD
  files (`evidence/2026-11-18-rd-medidas/`: 238 of 2008-01 to 2026-07 with 1,994,690
  records, 222 of them of Roraima, and the 24 Roraima files of 2006 and 2007 with
  41,547) are quoted in the issues of the fields. `uf_zi`: every record of the five
  `RDDF` files read has `530000`, a code `br_municgestor.cnv` reaches only through a
  range, so the issue no longer says that no file publishes such a key (no `RJ` file of
  the Federal District was read). The 19 "Zerado" fields are filled in no record from
  2008; 13 of them are filled in the 21 files of 2006-04 to 2007-12, the months of the
  layout that gives their labels. `homonimo` publishes `0` and `2` in the files of every
  year from 2006 and `1` only in `RDAP2607`. `tpdisec1-9` are blank in the 12 Roraima
  files of 2014 and, from 2015-01, `0` exactly where the diagnosis of the same number is
  blank. `cid_notif` is `Z302` in 28,207 of its 28,388 filled records. No label changes
  (#182).
- `sih_aih_reduzida` (2.27.0) and `sih_aih_rejeitada` (1.8.0): the issue
  `uf_zi-faixa-em-codigo-longo` is resolved. The map keeps expanding the ranges
  `br_municgestor.cnv` writes in its 6-character codes, as the maintainer decided in
  #182: the table is followed as published, and the range `530000-530009` is the only
  reference to the code the `RDDF` files read publish. The reader's documentation
  (`transforms/cnv.py`) now says that it expands ranges of any width and why.
- `faec_tp` of `sih_aih_reduzida` (2.28.1) and of `sih_aih_rejeitada` (1.9.1) takes the
  labels of `CNV/TP_FINAN.CNV`, packaged from `TAB_SIH.zip` (`sih-tab-21e42384645a`): the
  100 codes the table lists one by one and the blank code, a new `faec_tp_rotulo` column.
  Two things were decided in #182. `RD2008.DEF` (lines 271-273) and `RJ2008.DEF` (lines
  274-276) write `DS_TPFIN` where the start column goes: the line has the shape of a DBF
  relation and names a CNV, and the package also has a `DBF/TP_FINAN.dbf` with that
  column, which differs from the CNV in 17 codes and 2 labels
  (`evidence/2026-11-18-tp-finan-cnv-e-dbf/`). The generator reads the CNV at position 1
  for the bindings `inicio_revisto` of `vinculos.json` lists, each pinned to what the
  line writes, and still refuses any other (`PROC_REA`). The first line of the table has
  the range `000000-999999`, "Não discriminado/Não se aplica"; `parse_cnv` no longer
  refuses the table and does not apply a range that spans every code of a long width
  (the one exception to expanding ranges), so a code outside the 100 has no label; a
  line with nothing but such a range raises. The 32 codes the 238 measured RD files
  publish are all among the 100. The open issue `faec_tp-faixa-de-reserva` records these
  points. The field leaves `sem_cnv` (#137) in both datasets.
- `sih_aih_reduzida` (2.29.1): 15 more labels are the words of `IT_SIHSUS_1603.pdf`, each
  with a `/field/label` claim, because they said more than that document or something
  else: `munic_res` and `munic_mov` (no "(IBGE)"; "Município do Estabelecimento"),
  `proc_rea` and `proc_solic` (no "(SIGTAP)"), `cgc_hosp` ("CNPJ do Estabelecimento"),
  `natureza`, `cid_asso` ("CID causa"), `cid_morte` ("CID da morte"), `uti_mes_to`,
  `uti_int_to` ("Quantidade de diárias em unidade intermediaria", not "Total dias UCI"),
  `contracep1`, `contracep2`, `insc_pn`, `cnaer` ("Código de acidente de trabalho", not
  "CNAE") and `gestor_cod`. With the nine of 2.23.1, 24 labels are the table's text up
  to its first full stop (up to ", no formato" for `ano_cmpt` and `mes_cmpt`). Some of
  the words that left were `RD2008.DEF`'s, not the document's ("Inscrição pré-natal",
  "Diárias UCI", "Causa Associada", `DBF\TB_SIGTAW.DBF` for the procedures), so each of
  the 15 claims also quotes the first DEF line that names the field. In all, 45 of the
  118 labels have a verified claim (25 from this document, 19 from the layout of
  2006-2007, `fonte_orc` from the DEF); the other 73 have none (#182).
- `sih_servicos_profissionais` (1.4.1) and `sih_aih_rejeitada` (1.10.1) declare
  `fonte_orc`, the field every `SP` and `RJ` file has had since 2025-03: C(2), the last
  of the header in the 510 files of each prefix up to 2026-09. On a real RJ file (the new
  fixture `sih_rj_rr_2026_08_mini`), `check_columns` reported it as "not in dictionary".
  It has no label and no map, because neither `SP2008.DEF` nor
  `RJ2008.DEF` names the field and the line of `RD2008.DEF` is the RD's; the issue
  `fonte_orc-sem-def` says so. The evidence is the DBF header of every `SP` and `RJ` file
  the server listed on 2026-11-19, read without any record
  (`evidence/2026-11-19-sih-cabecalhos/`), and the 18 `RJRR` files of 2025-03 to 2026-08,
  where the field is `00` in the 1,270 records (#182).
- The DBF header of every `RD` file the server listed on 2026-11-19 is in
  `evidence/2026-11-19-sih-cabecalhos/`: 5,165 files of 1992-2007 and 6,072 from 2008.
  The censuses of layouts, which read one UF a month, hold in every UF: the 19 layouts of
  1992-2007 and no other, with `num_proc`, `insc_pn` and `seq_aih5` published as numbers
  in every file of the months #40 names; and the 6 layouts from 2008 in all files but
  one. `RDAC0909.dbc`, which the server dates 2024-05-22, has 82 fields, 17 of them of
  another type, and `val_sh` and `val_sp` zeroed in its 4,540 records (#219). The fixture
  `sih_rd_ac_2009_09_excerpt` keeps five of them.
- `sih_aih_reduzida` (2.29.2): `val_sh` and `val_sp` have the open issue
  `zerado-em-rdac0909`. `RDAC0909.dbc` is imported as published, so in the lake the two
  sums for Acre in 2009-09 are zero; `val_tot` is filled in its 4,540 records, and both
  fields are filled in the 4,379 of `RDAC0908.dbc`
  (`evidence/2026-11-19-sih-cabecalhos/rdac0909.csv`, which now also counts the rows in
  which each field is blank; #219).
- `sih_aih_reduzida` (2.29.3): the issues `homonimo-sem-fonte` and `gestor_tp-sem-fonte`
  say that none of the 38 packaged DEF names the field. They said 37, the count before
  `APAC_Dados_Comuns.DEF` was packaged (#218); the test that reads every DEF now compares
  the count in the text.
- `sih_aih_reduzida` (2.29.4): the same two issues say 39 packaged DEF, the count with
  `DengueNETON3.0.def` (#226). The `main` changed the same lines as 2.19.1; the version
  goes past both so that neither locked content changes.

## v0.4.0 — 2026-11-20

**Upgrading from 0.3.0:** no parser version changed (the import still reads the same
`encoding` and `x-identity` of every dictionary), so a 0.3.0 lake keeps every scope;
`load` downloads nothing again. `sim_obitos` loses the fields `covid_clas` and `mat_clas`
and its primary key, and `esc2010` and `escmae2010` change labels in `sim_obitos` and its
three subsets (the entries below say which). One dataset is new: `sinan_dengue`.

### Dictionaries

- `sia_apac_nefrologia` (1.2.0): `ap_coidade` takes the age-unit map seven other APAC
  datasets carry (`2` Dias, `3` Meses, `4` Anos, `5` Anos (somar 100)), with a
  `fixture-measure`, `unreviewed` claim and the open issue `ap_coidade-sem-tabela`:
  `APAC_Nefrologia.DEF` lines 387-388 bind `AP_COIDADE` to `IDADEDET.CNV` and
  `IDADE18.CNV`. `ANPA1410` publishes only `4`; `2`, `3` and `5` were not measured in
  an AN file. `sus.label` now adds
  `ap_coidade_rotulo` for this dataset (#183).
- `sia_apac_nefrologia` (1.3.0): `ap_dtinic`, `ap_dtfim`, `ap_dtsolic`, `ap_dtaut` and
  `an_dtpdr` are `date` with `x-format: yyyyMMdd`, each with the observation of the 2
  records of `ANPA1410`. The Informe Técnico SIASUS 2019-07 (p. 8, layout of the AN)
  writes `AAAAMMDD` only for `AN_DTPDR`, whose `/field/format` claim cites the page and
  stays `unreviewed` (read by an agent). The four `ap_dt*` have no format in that layout:
  their claim is `fixture-measure`, `unreviewed`, with the open issue
  `formato-sem-documento`; `APAC_Nefrologia.DEF` places their year and year-month at
  position 1 and has no line for the day. `ap_dtocor`, blank in both records, stays
  `string` with the open issue `formato-sem-valor`. `check_columns` now checks the five
  dates; the lake still stores them as published, as strings (#183).
- `sia_apac_nefrologia` (1.4.0): the 60 fields of the AN layout of the Informe Técnico
  SIASUS 2019-07 (section 3.4.3, pp. 7-9) carry the document's `description`, each with
  a `/field/description` claim that quotes the row and stays `unreviewed` (read by an
  agent). Those 60 rows are the first 60 fields of `ANPA1410`, with the same order, name,
  type and width; `ap_natjur`, the 61st, is not in the layout and gets no description.
  The layout describes `ap_ufdif` and `ap_mndif` with "(N = não, S = sim)" while
  `ANPA1410` publishes `0` in the first and `1` in the second, codes `Invasao.CNV`
  labels: both fields keep the CNV map and gain the open issue
  `informe-diverge-do-arquivo` (#183).
- `registry.json` registers the `TAB_SIA.zip` republished on 2026-10-15
  (`sia-tab-1ce232b217c6`). The 49 members whose hash `vinculos.json` holds are identical
  to those of `sia-tab-e5812b51d802`, so the packaged members stay on that edition;
  `evidence/2026-11-18-tab-sia-republicado/` has the member census and what was not
  compared (#183).
- `sia_apac_nefrologia` (1.5.0): `ap_ufnacio` takes the 328 codes of `UFNACIO.CNV`
  (`010` BRASIL, the value `ANPA1410` publishes), with a `cnv-parse` claim:
  `APAC_Nefrologia.DEF` line 390 binds `AP_UFNACIO` to it. The member is packaged from
  the `TAB_SIA.zip` republished on 2026-10-15 (`sia-tab-1ce232b217c6`). `sus.label` now
  adds `ap_ufnacio_rotulo` for this dataset. The open issues of the five `ap_dt*`
  fields now give the widths the same edition has for `ANO_2008.CNV` (4) and
  `anomes2008.CNV` (6), which place the year in characters 1-4 (#183).
- `sia_apac_nefrologia` (1.6.0), from a second real file, `ANRR1401` (162 records, new
  fixture `sia_an_rr_2014_01_mini.dbc`, with `AP_CNSPCN` blanked): `ap_dtocor` is `date` with
  `x-format: yyyyMMdd`, measured in the one record that fills it (`fixture-measure`,
  `unreviewed`, open issue `formato-sem-documento` in place of `formato-sem-valor`).
  The file has 60 fields, the 60 rows of the Informe layout, and no `AP_NATJUR`:
  `ap_natjur` gains the open issue `ap_natjur-nem-sempre-publicado`. The issue of
  `ap_coidade` now says `5` was measured in an AN file too. The file reads the five
  other dates as `yyyyMMdd` in all 162 records; `ap_dtaut` (`20430101`) and `an_dtpdr`
  (`20161101`) each hold one implausible date and gain the open issue
  `data-implausivel` (#183).
- `sia_apac_nefrologia` (1.7.0): `ap_cnspcn` carries `x-crypto: datasus-cns`, as it
  does in five of the nine APAC dictionaries (the other four still declare the field
  without the mark). The row of the AN layout (Informe, p. 8) names the field and does
  not say it is ciphered; the mark is measured: `ANPA1410` fills the column in its 2
  records, and `ANRR1401` as published in its 162, with 15 characters and no digit.
  The fixture of `ANRR1401` blanks the column because the cipher is reversible, so the
  test reads `ANPA1410` only. The library does not decipher the value (#183).
- `sia_apac_nefrologia` (1.8.0): `ap_tippre` takes the 8 codes of `TIPOPRES.CNV`
  (`61` FILANTROPICO COM CNAS VALIDO in `ANPA1410`, `20` PRIVADO COM FINS LUCRATIVOS in
  `ANRR1401`), with a `cnv-parse` claim: `APAC_Nefrologia.DEF` line 220 binds
  `AP_TIPPRE` to it. Lines 216-218 bind the same field to `ESFERA.CNV` and
  `ESFERA_C.CNV`, which are not used: `ESFERA_C.CNV` groups the codes into four spheres,
  and `ESFERA.CNV` has those four rows plus one row, with another wording, for each of
  `20`, `22`, `60`, `61` and `80`. The field's open issue `def-liga-outra-tabela` records
  the choice. The member is packaged from the `TAB_SIA.zip` republished on 2026-10-15
  (`sia-tab-1ce232b217c6`). `sus.label` now adds `ap_tippre_rotulo` for this dataset
  (#183).
- `sia_apac_nefrologia` (1.9.0), from a census of the 2,145 `AN*.dbc` files the server
  lists (6,534,272 records, `evidence/2026-11-18-censo-sia-an/`): no map and no type
  changes; the open issues of the fields now carry what was counted. `ap_coidade`:
  `2`, `3` and `5` are counted in AN files, and `0` (18 records) has no label (new
  issue `codigo-sem-rotulo`). `ap_ufnacio`: 202 records hold a value `UFNACIO.CNV` does
  not label (new issue `codigo-sem-rotulo`). `ap_natjur`: the field is in the 27 files
  of 2011-12 and in `ANPA1410`, empty in 87,203 records and filled in 2. `ap_mndif` is
  `1` in every record and `ap_ufdif` only `0` or `1`; the `SIMNAO.CNV` of `TAB_SIA.zip`,
  now read, labels `S` and `N`, which no AN file publishes in either field. The six
  dates say how many filled values read as `yyyyMMdd` in any year; `ap_dtsolic`,
  `ap_dtaut` and `an_dtpdr` say how many do not, and how many files have a year outside
  1900-2100 or after 2015 (issue `data-implausivel`, new in `ap_dtsolic`). `an_albumi`
  and `an_hb` gain the open issue `escala-sem-documento`, with the records that hold
  integer zero, integers from 1 to 9, integers from 10 to 99 and text such as `3,`; no
  source read says the scale (#183).
- `ap_natjur` takes the map of `natjurc.cnv` in nine APAC dictionaries:
  `sia_apac_quimioterapia`, `sia_apac_medicamentos`, `sia_apac_laudos_diversos`,
  `sia_apac_cirurgia_bariatrica` and `sia_apac_tratamento_dialitico` (0.5.0),
  `sia_apac_radioterapia` (1.4.0), `sia_apac_fistula_arteriovenosa` (1.3.0),
  `sia_apac_acompanhamento_bariatrica` (1.1.0) and `sia_apac_nefrologia` (1.10.0).
  - The binding. `APAC_Dados_Comuns.DEF` (files `A?*.DBC`), now packaged, binds
    `AP_NATJUR` to `NATJURC.CNV` on lines 204-205. The DEF of seven of the datasets
    writes `AP_NAT_JUR`, and those of ACF and ATD have no line for the field, so
    `vinculos.json` names the common DEF for this field in the new key `def_do_campo`.
    `gerar_decode_cnv.py` refuses the key for a field a DEF of the dataset binds.
  - What supports it. The mask of a DEF alone does not say a file follows it (issue
    `amp-sem-def`). Here the published field has the name the line writes, and in a
    census of 9,527 files of the nine other APAC datasets
    (`evidence/2026-11-19-apac-ap-natjur/`) no field is named `AP_NAT_JUR` and each of
    the 28 values of the 2,276,452 filled records is a code of the table. AD, AM, AQ, AR
    and ATD were read in RR, AC and AP only; AN has 2 filled records. Each dictionary
    gains the open issue `ap_natjur-nem-sempre-publicado` with its own counts and the
    months whose files have no such field.
  - The table. The same DEF binds the field to `NATJUR.CNV` too, which the CNV reader
    refuses; the 97 code labels of the two members are the same. The map has those 97
    codes and the literal key `    -zzzz`, which is how the reader keeps the code of the
    line "Não especificado ou ignorado"; no four-character value matches it, so an empty
    `ap_natjur` has no label.
  - Not touched. `sia_apac_acompanhamento_multiprofissional`: 899 of its 903 files have
    the field, always empty. `pa_nat_jur` (PA) and `nat_jur` (RAAS, SAD), which their own
    DEF binds to the same tables, and `nat_jur` of the SIH wait for the choice of table
    of #7.
  - `sus.label` now adds `ap_natjur_rotulo` for the nine datasets (#183).

- `seriescfal`, `seriescmae` and `versaoscb` of `sim_obitos` (and of the three SIM subsets,
  generated from it) gain the code map of the CNV that `Obito_1996_CID10.def` binds each to:
  `SERIEFAL.CNV` for the two school grades, `VERSCB.CNV` for the SCB version. Both tables were
  already packaged and `sim_obitos_fetais` already used them. The claims are `cnv-parse`, written
  by `gerar_decode_cnv.py`; in DORR2022 and DORR2023 every value of the three fields is a key of
  its table. `SERIEFAL.CNV` also lists `0` and `9` (`Ign`), which the Estrutura do SIM does not:
  it says "Números de 1 a 8" for both fields, and no fixture holds `0` or `9`; the open issue
  `seriefal-cnv-lista-0-e-9` records it on each field. The DEF lines of the two grades begin
  with a lowercase `x`, and TabWin.pdf (p. 87) does not list `X`, in either case, among the
  functions of a DEF line: the open issue `def-liga-por-linha-x` says so. The same holds for
  the other maps `Obito_1996_CID10.def` binds by an `X` line, `versaoscb` among them. Versions: `sim_obitos` 2.9.0, the three
  subsets 1.4.0 (#184).
- 81 fields of `sim_obitos` have the `description` an official layout document gives them, each
  with a `/field/description` claim that cites the page: 75 from the Estrutura do SIM of 07/2025
  (`sim-b4195ac8e0f8`); `origem`, `tpobitocor` and `cb_pre` from the edition of 12/2019
  (`sim-b014389eca62`); `numerodo` and `ufinform` from the structure of the 2006 file
  (`sim-anterior-13cabba0b9a1`); `nudiasobin` from the dictionary of the DOM table
  (`sim-dom-fb396a277981`). The reading was made by an agent: the claims are `unreviewed`, with
  no reviewer. Two of the 81 replace a description that had no source: `natural` no longer says
  "código do país" and `peso` no longer says "(óbito fetal/menor 1 ano)", which the document
  does not say. The seven fields none of the four documents describes (`tp_altera`, `contador`,
  `estabdescr`, `fontesinf`, `nudiasinf`, `covid_clas`, `mat_clas`) keep `description: null` with
  a `not_found` claim.
- The label of `nudiasobco` changes from "Dias óbito-codificação" to "Dias óbito-conclusão da
  investigação", which is what the editions of 07/2025 (p. 7) and 12/2019 (p. 8) and the
  dictionary of the DOM table (p. 2) say the field is.
- Three open issues record where the files and the document differ: `horaobito` (the document
  says 5 characters, `00:00`; the files write 4 digits), `tppos` (the document says `1 – sim;
  2 – não`; the files write `S`, `N` or blank, the keys of `INVESTIG.CNV`) and `codestab` (the
  edition of 07/2025 says 8 characters; the files write 7 digits, as the structure of the 2006
  file says). The `/field/codes` claim of `origem` now cites the edition of 12/2019 first,
  which writes `1`, `2`, `3` and `9`, the form of the map; the fixtures hold only `1` and `2`.
  The issue of `esc2010` and `escmae2010` no longer says `ESCSERIE.CNV` is missing from
  `OBITOS_CID10_TAB.zip`: it is there, cited by a commented line of `Obito_1996_CID10.def` and
  by the DEF of the infant and maternal subsets. `registry.json` records the edition of
  `Estrutura_SIM_para_CD.pdf` (12/2019), that `Estrutura_SIM_Anterior.pdf` holds the layout of
  2006 and the one up to 2005, and that the five SIM sources read here were hashed again on
  2026-11-18. The three SIM subsets are regenerated. Versions: `sim_obitos` 2.10.0, the three
  subsets 1.5.0 (#184).

- 24 `/field/codes` claims of `sim_obitos` written by `gerar_decode_cnv.py` change from
  `conflicting` to `verified_in_source`, and the issue `cnv-difere-do-mapa-anterior` of each
  field is `resolved`: the map in force was already the one of the CNV, and the map it replaced
  had no claim. The issue keeps the older labels, some of which are the spelling of the
  Estrutura do SIM (`Cesáreo` where `PARTO.CNV` says `Cesário`). Two stay `conflicting`, where
  the document and the CNV say different things: `tppos` (the document lists `1` and `2`,
  which `INVESTIG.CNV` does not) and `atestante` (the document calls `1` "Assistente",
  `ATESTANT.CNV` calls it "Sim"). No code or label changes. Versions: `sim_obitos` 2.11.0, the three subsets 1.6.0 (#184).

- **Labels changed:** `esc2010` and `escmae2010` of `sim_obitos` (and of the three SIM subsets)
  take the labels the Estrutura do SIM of 07/2025 writes (p. 2 and 3): `1` is "Fundamental I
  (1ª a 4ª série)", not "Fundamental I (1-5 ano)"; `2` is "Fundamental II (5ª a 8ª série)", not
  "Fundamental II (6-9 ano)"; `3` is "Médio (antigo 2º Grau)", not "Médio". The older labels
  had no source; the edition of 12/2019 and the dictionary of the DOM table print the same
  text, and `ESCSERIE.CNV` the same categories in another spelling (`Fundamental II(5ª a 8ª
  serie)`, `Medio (antigo 2º Grau)`). `Obito_1996_CID10.def` binds the two fields to
  `ESCCICLO.CNV`, which no downloaded file has, so the map is read from the document. `esc2010_rotulo` and `escmae2010_rotulo` change accordingly. The
  claims go from `conflicting` to `unreviewed` (an agent read the page) and the issues are
  `resolved`. Versions: `sim_obitos` 2.12.0, the three subsets 1.7.0 (#184).

- `sim_obitos_externos`, `sim_obitos_infantis` and `sim_obitos_maternos` no longer declare
  that `idade` derives `idade_anos_completos`, `idade_status`, `idade_quantidade` and
  `idade_unidade`. They have no `x-analytics`, so `sus.load` never created those columns in
  them (ADR 0003); `gerar_subconjuntos_sim.py` copied the declaration from `sim_obitos` and now
  leaves it out. Nothing `sus.load` returns changes; `describe_dataset(subset)` now gives
  `derivation: None` for `idade`, and the subset's `metadata_hash` changes with it. The
  `applicability` text of the copied fields still points at `validated_sources`, which a
  subset does not have. Validating DOEXT, DOINF and DOMAT files so
  the subsets can have the age rule stays open in #177. Versions: the three subsets 1.8.0.

- `ocupmae` of `sim_obitos` (and of the three SIM subsets) declares the reference `ocup`
  already had: `aux_ocupacoes`, scheme `cbo2002`, from 2006. `Obito_1996_CID10.def` binds
  `OCUPMAE` to `CBO2002.CNV` (lines 331 and 332), and the DORR of each year from 1996 to 2024 writes
  `ocupmae` with 5 characters until 2005 and 6 digits from 2006. `ocup` does the same, except
  nine values of DORR2006 with 5 digits, which are the 5-digit form `aux_ocupacoes` keeps for
  CBO 2002 codes that start with 0. From 2006 on every filled `ocupmae` of those files is a
  `cbo2002` code of the table. Only Roraima was measured here.
  `sus.reference_join_sql("sim_obitos", "ocupmae")` now returns the join. Versions: `sim_obitos`
  2.13.0, the three subsets 1.9.0 (#184).

- **Fields removed:** `covid_clas` and `mat_clas` leave `sim_obitos`. None of the four
  registered layout documents lists them and none of the 1,011 files read carries them:
  `evidence/2026-11-18-sim-colunas-do/` has the columns of every `DO` file of `SIM/CID10/DORES`
  (1996 to 2024), `SIM/PRELIM/DORES` (2025 and 2026), `SIM/CID10/DOFET` and `SIM/PRELIM/DOFET`,
  read from the DBF headers on 2026-11-18. `sim_obitos` no longer declares `numerodo` as
  primary key: none of the 868 `DO<UF><year>` files carries the column. `numerodo`, `opor_do`,
  `tp_altera` and `cb_alt`, which a layout document describes and no `DO<UF><year>` file
  carries, stay declared, each with an open issue that cites the evidence; `DOREXT21.dbc`,
  which omnisus does not import, is the one file with `NUMERODO`, `TP_ALTERA` and `CB_ALT`.
  The issue of `ufinform` is resolved: the column is in the headers from 2002 to 2010. Versions:
  `sim_obitos` 2.14.0 (#184).

- `evidence/2026-11-18-sim-valores-do/` counts the values of every coded field of `sim_obitos`
  in 186 DO files: six UF in every year from 1996 to 2024 and four more in 2006, 2015 and
  2023 (2,557,540 records, each file with its SHA-256). The open issues of `tppos`,
  `horaobito`, `codestab`, `seriescfal` and `seriescmae` now cite it: `tppos` is never `1` or
  `2`; `horaobito` has 4 digits in 2,185,721 records, another shape in 1,324 and never
  `00:00`; `codestab` has 7 digits in every filled record but one; no record holds the `0` or
  `9` of `SERIEFAL.CNV`. A test lists the 17 fields whose files hold a value
  the map does not label. Versions: `sim_obitos` 2.15.0, the three subsets 1.10.0 (#184).

## v0.3.0 — 2026-11-17

**Upgrading from 0.2.3:** no parser version changed (the import still reads the same
`encoding` and `x-identity` of every dictionary), so a 0.2.3 lake keeps every scope;
`load` downloads nothing again. Some code maps were removed: the `<field>_rotulo` column
goes away and `sus.label(columns=[field])` raises for those fields (the entries marked
**Breaking** below). `import_cnes_master` changes which names it keeps (below, under API).

### API

- `read(dataset, years=..., ufs=..., months=...)` returns the rows `load` returns for
  the same arguments, harmonised categories included, from what the lake already has,
  without connecting to DATASUS: it works while the server is down, when `load` raises
  `FtpUnavailable`. It warns naming the requested scopes the lake lacks and raises
  `LookupError` when it has none of them. `read(table)` without `years` is unchanged
  (#92).
- `WriterBusyError`, `CommitOutcomeUnknown`, `CENSUS_YEARS` and
  `ESTIMATE_UNAVAILABLE_YEARS` are exported from `omnisus`, so a caller that imports
  only `omnisus.__all__` can catch the writer's errors and build the IBGE year selector.
  `Product.name` documents that it is also the relation the importer writes in the lake
  (#102).
- `publications()` and `reference_join_sql()` take `snapshot_id: int | None = None`:
  one attach reads the manifest and the `aux_*` vocabulary at snapshot `N` with
  `AT (VERSION => N)`, which wins over `LakeReader(snapshot_id=...)`. A snapshot from
  before the first import returns `[]`. `None` keeps the SQL and the rows of 0.2.3. The
  data table is pinned by the caller's `FROM` (#101).

- `sus.import_cnes_master_ftp(competencia, zip_path=..., download_dir=...)`
  fills `cnes_master` from
  `tbEstabelecimentoAAAAMM.csv` of the full CNES base on the FTP
  (`BASE_DE_DADOS_CNES_AAAAMM.ZIP`, about 576 MB for 202312) in one pass, instead of one
  request per code to the open-data API. Each row records `fonte`, `arquivo`, `sha256`,
  `competencia_nome` and, for a file the importer downloaded, the server `url` and
  `modificado_em` (MDTM); tables created by `import_cnes_master` gain those columns on the
  next write. `aux_cnes` exposes `nome_fantasia`, `razao_social`, `competencia_nome` and
  `fonte_nome` next to `nome`. The name is the one of the loaded competência, not of the
  code's last month in ST (#150). Only a pessoa jurídica (`TP_PFPJ=3`) keeps a name: a
  pessoa física (`TP_PFPJ=1`, whose names are the professional's) or any other value gets
  none, and neither does a row whose name holds a valid CPF, written plain or with dots,
  dash, slash or spaces in the CPF positions (600 of 202312, mostly empresário individual;
  `evidence/2026-11-09-cnes-cpf-em-nome-pj.md`). A row with no name
  is skipped, a `CO_CNES` repeated with another name is an error, and the counts go to the
  `cnes_master_ftp.rows_skipped` log. A name `cnes_master` already holds for a code whose
  row is not `TP_PFPJ=3`, or that the lake's ST marks anything but `'3'` in some month, is
  removed in the same transaction as the upsert, and so is every stored name that holds a
  valid CPF, of any code, on both paths. The removal is logical: after the next import a
  lake filled before these rules no longer returns those names, but they stay in earlier
  snapshots, in the old Parquet files and possibly in the catalog's column statistics, so
  recreate such a lake from scratch before sharing it. A clean stored name stays when the
  file now writes a CPF for the code. The razão social of an empresário individual
  (natureza jurídica 2135) is the person's civil name and is kept, as public CNPJ data;
  names with a CPF are not.
- `import_cnes_master` (API) fetches a name only for a code `cnes_estabelecimentos` marks
  `pf_pj = '3'` in every imported month, discovered or listed by hand: a pessoa física, a
  code outside the ST, or a lake whose ST has no `pf_pj` gets none (breaking: explicit
  codes not in the ST are no longer fetched). It writes no name holding a valid CPF, removes
  every stored one and the names of the codes the ST marks otherwise, and logs
  `pessoa_fisica`, `pf_pj_desconhecido` and, in `cnes_master.names_removed`, `cpf_no_nome`. Only imported months count: a code marked `'3'` in all of them
  and `'1'` in a month not imported is still taken as pessoa jurídica.
- `cite()` and `citation_from_publications()` with `accessed=None` print as the access
  date the UTC day of each row's `published_at` (when the publication was written to the
  lake) or, for IBGE, of `collected_at` (when the HTTP request was made), instead of the
  day the citation is generated: a file imported on 2026-10-18 and cited a week later
  stays "acessado em 2026-10-18". A value with an offset is converted to UTC first.
  `accessed=` still sets one date for every row. A row with neither column prints
  "(data de acesso desconhecida)"; a value that is not an ISO date raises `ValueError`.
- `cite(snapshot_id=N)` reads the publications, and the IBGE manifest, as they were at
  snapshot N: after a `replace`, citing an older snapshot keeps that snapshot's date and
  run. Without `snapshot_id`, a `LakeReader(snapshot_id=M)` cites M instead of the
  newest snapshot. A snapshot the lake does not have raises
  `duckdb.InvalidInputException`.
- `check_columns` reports the harmonised categories that `load` adds (`idade_*`,
  `sexo_*`, `<date>_data`, `<date>_data_status`) with `rule = "harmonised from <fields>"`,
  e.g. `"harmonised from idadepac, tpidadepac"`, instead of `"not in dictionary"`: 28
  columns of SIM RR 2023 were flagged. The names come from the same rules
  `analytical_projection` reads, `x-analytics` of the dictionary (#69).

### Dictionaries

- New dataset `sinan_dengue` (1.0.0): SINAN dengue notifications, one national file per
  year, `DENGBR00` to `DENGBR25` final and `DENGBR26` preliminary (listing of 2026-11-20).
  The dictionary is the 121-field layout of `DENGBR14` to `DENGBR26`, read from `DENGBR17`.
  82 fields have labels, each code citing a page of the Sinan Online Dengue/Chikungunya
  dictionary (`sinan-da262c3b9f20`) or a CNV of the `TAB_SINANNET.zip` read on 2026-11-20
  (`sinan-tab-24ac0c62fb84`, a republication in which the seven members already packaged
  are unchanged); `classi_fin` 8, "Inconclusivo", is in `Classdeng.cnv` only. The age rule
  is enabled for the audited final `DENGBR17`. The 27 files have four layouts: 2000–2006
  and 2014 onwards share a lake table, while the lake refuses 2007–2012 and 2013 in a
  table that holds 2014 onwards, because `nu_idade_n` and `plaq_menor` change type;
  `docs/sources/sinan_dengue.md` and `evidence/2026-11-20-sinan-dengue/` say what
  was read. `sinan.py` runs with `BASE = "sinan_dengue"`.
  - `gerar_sinan.py` dates the maps of an agravo listed in `revisado_em_agravo` with its
    own reading date; the other claims keep `revisado_em`.
  - `sih_aih_reduzida` 2.19.1: the issues `homonimo-sem-fonte` and `gestor_tp-sem-fonte`
    count 38 packaged DEF, with `DengueNETON3.0.def`.

- `registry.json` registers the `TAB_SIH.zip` republished on 2026-10-15
  (`sih-tab-21e42384645a`). The 33 members whose hash the repository holds are identical to
  those of the two editions already registered, so `vinculos.json` stays on
  `sih-tab-f05b32f32908`; `evidence/2026-11-15-tab-sih-republicado/` has the member census and
  what was not compared (#154).

- Every field with `x-decode` now has an authored `/field/codes` claim, or no map (#72). A test
  (`tests/unit/test_codes_claims.py`) holds the rule.
  - **Breaking:** `_source_release` of `sim_obitos` and `sih_aih_reduzida` loses its `x-decode`:
    `final` and `prelim` are not DATASUS codes. The `<field>_rotulo` column goes away and
    `sus.label(columns=[field])` raises where the map went.
  - `ap_coidade` of the seven APAC datasets and `tpidadepac` of the BPA-I: `fixture-measure` claim,
  `unreviewed`, on the open issue each field already had; the DEF lines are the evidence.
  - **Breaking:** `sexopac`, `catend`, `mn_ind` and `complex` of the BPA-I lose their `x-decode`, as
  `ap_coidade` and `ap_sexo` of the AMP did: none of the 12 packaged TAB_SIA DEF reads `BI*.DBC`, so no
  DEF binds a BPA-I field to a table, and the DEF of another product does not say the BPA-I follows
  it. The hand maps also differed from those tables (`'Mantido'` against `'Mantida'` in
  `MANT_IND.CNV`), and `catend` `'06'` is in no BPA-I fixture. Each field has the open issue
  `bpai-sem-def` with what was read and the codes of BIRR2401. `<field>_rotulo` goes away for the
  four; `notebooks/linkage.py` leaves the sex of the BPA-I null, as it does for a base without a
  sex map.
  - Nine SIM fields the 2025 Estrutura PDF lists (and the three SIM subsets, generated from
  `sim_obitos`), `paridade`, `stdnepidem` and `stdnnova` of SINASC, `racacor`, `ufdif` and `mndif` of
  the BPA-I: a claim that cites the PDF page, with no reviewer. Nothing here is marked verified: no
  human reviewed them.
    - `unreviewed`: `origem`, `assistmed`, `tpnivelinv`, `morteparto`, `altcausa`, `codificado` and
    `tp_altera` of the SIM (seven of the nine; `tp_altera` is not in the subsets), and the five
    SINASC and BPA-I fields other than `stdnnova`.
    - `conflicting`, with an open issue: `esc2010` and `escmae2010` of the SIM (the other two of the
    nine) and `stdnnova` of SINASC. The codes match the PDF but the labels do not (`'1-5 ano'`
    against `'1ª a 4ª série'`; `'Formulário novo (pós-2011)'` against a plain Sim). The maps stay
    as they were until the maintainer chooses.
  - Versions: `sim_obitos` 2.8.0, `sih_aih_reduzida` 2.19.0, `sinasc_nascidos_vivos` 2.6.0,
  `sia_bpa_individualizado` 0.7.0, and one minor each for the seven APAC datasets and the three SIM
  subsets.

- `derivation.output` of the age fields lists `idade_status` too, in the nine dictionaries
  with an age rule (`sim_obitos` 2.7.0, `sih_aih_reduzida` 2.18.0, `sinasc_nascidos_vivos`
  2.5.0, `sia_bpa_individualizado` 0.5.0, `sia_psicossocial` 0.4.0, `sia_atencao_domiciliar`
  1.3.0, `sinan_chagas` 1.3.0, `sinan_hanseniase` 1.3.0, `sinan_tuberculose` 1.1.0) and in the three
  SIM subsets, which copy `sim_obitos` (1.2.0). It had three of the four columns that
  `analytical_projection` creates, and `describe_dataset` exports that list. A test compares each
  dictionary's list with `harmonised_inputs`, the list `check_columns` uses (#164).

- `sih_aih_rejeitada` 1.5.0 and `sih_servicos_profissionais` 1.3.0: `nasc`, `dt_inter` and
  `dt_saida` of the RJ and `sp_dtinter` and `sp_dtsaida` of the SP are `type: date` with
  `x-format: yyyyMMdd`, so `check_columns` reports their invalid dates and range. No document
  read gives the whole format: the claim is `fixture-measure`, `unreviewed`, with the open issue
  `formato-sem-documento` and an `observations` entry (server file, SHA-256, `observed`).
  `RJ2008.DEF` and `SP2008.DEF` place the year (position 1) and the month (position 5) of
  `dt_inter`, `dt_saida` and `sp_dtinter`, and the claims cite those lines; nothing places the
  day. `IT_SIHSUS_1603.pdf` lays out only the RD and the SP (contents, p. 1), not the RJ, and
  the issues say so.
  `gestor_dt` of the RJ stays a string (no fixture fills it; issue `formato-sem-valor`) and the
  ER dates wait for a census of widths and patterns. The observation schema gains `observed`
  (#9).
- `check_columns` counts a date as invalid unless it has exactly eight digits, the guard
  `analytical_projection` already used: `'1012023'` no longer parses (#9).
- A test validates the resolved metadata of every field of every packaged dictionary against
  `docs/dicionario/schemas/column-metadata.schema.json`, and another reads every `x-format`
  against the committed fixtures (#9).

- `docs/dicionario/contrato.md` documents `method: fixture-measure`, the method of the
  `cod_idade` claims of the RD and the RJ (`sih_aih_reduzida` 2.17.1, `sih_aih_rejeitada`
  1.4.1), whose `reviewer` is now null: nobody reviewed them. Their `sem_cnv` reasons cite
  the DEF lines and members like the other entries, and the test checks them and every
  `aux_*` resource a reason names (review of #157).
- **Breaking:** `homonimo` and `gestor_tp` of `sih_aih_reduzida` (2.17.0) lose their
  code maps (`{'0': Não, '1': Sim}` and `{'0': Sem autorização, '1': Auditor, '2':
  Autorizador}`). No registered document lists their codes and none of the 37 packaged
  DEF names either field; the `homonimo` map also contradicted the data, since the RD
  publishes `0` and `2`. `sus.label` no longer adds `homonimo_rotulo` nor
  `gestor_tp_rotulo`, `sus.label(columns=["homonimo"])` (or `"gestor_tp"`) raises
  `ValueError`, and `check_columns` reports no `unlabelled_codes` for them. The issues
  `homonimo-sem-fonte` (rewritten) and `gestor_tp-sem-fonte` (new) say what was
  consulted (#10).
- The 1-character age unit is labelled `'5'`: "Anos (somar 100)", as `IDADEDET.CNV`
  reads 500-530 as 100 to 130 years, in `cod_idade` of `sih_aih_reduzida` (2.16.0, which
  called it "Mais de 100 anos") and `sih_aih_rejeitada` (1.4.0), `tpidadepac` of
  `sia_bpa_individualizado` (0.4.0) and `ap_coidade` of the seven APAC datasets with a
  map (`sia_apac_cirurgia_bariatrica` 0.3.0, `sia_apac_fistula_arteriovenosa` 1.1.0,
  `sia_apac_laudos_diversos` 0.3.0, `sia_apac_medicamentos` 0.3.0,
  `sia_apac_quimioterapia` 0.3.0, `sia_apac_radioterapia` 1.2.0,
  `sia_apac_tratamento_dialitico` 0.3.0). `cod_idade` `'0'` of the RD loses its
  "Ignorada" label, which no source gives (in the CNV `000` is "Idade inválida"):
  `cod_idade_rotulo` is null for it. The RJ `cod_idade` had no map and takes the RD's
  (`RJ2008.DEF` lines 193-196 bind it to the same CNVs), so `sus.label` adds
  `cod_idade_rotulo` to RJ rows. Every one of these maps was measured, not read: the
  CNVs label the 3-character composite, never the unit alone (issues
  `cod_idade-sem-tabela`, `tpidadepac-sem-tabela`, `ap_coidade-sem-tabela`) (#6).
- `uf_zi` of `sih_aih_reduzida` (2.15.0) is labelled "Município gestor", as
  `RD2008.DEF` (lines 175-176) names it, instead of "UF do gestor": RD files publish it
  with 6 digits, a municipality code (#155).
- `cnsprof` of `sia_bpa_individualizado` (0.3.0) is no longer labelled "criptografado"
  nor marked `x-crypto: datasus-cns`: the BPA-I files publish the professional's CNS in
  clear, which is why the fixtures blank it. `pa_cnsmed` (`sia_producao_ambulatorial`
  1.3.0) and `sp_pf_doc` (`sih_servicos_profissionais` 1.2.0) say the same, and
  `docs/sources/sia.md` warns that the lake keeps these columns as published (#68).
- `sih_aih_reduzida` (2.13.0) declares `fonte_orc`, which RD files publish from 2025-03
  (layout 6, `evidence/2026-10-06-rd-2008-layouts`), with the labels of `CNV/fonterem.CNV`
  of `TAB_SIH.zip`, now packaged, which `RD2008.DEF` binds to `FONTE_ORC`. `00`, the only
  value of the RDRR2503 excerpt, is not a key of the table and stays unlabeled (issue
  `fonte_orc-00-sem-fonte`). `check_columns` no longer reports the field as "not in
  dictionary" (#86).
- `etnia` of `sih_aih_reduzida` (2.14.0) and `sih_aih_rejeitada` (1.3.0) takes its labels
  from `CNV/etnia.cnv` of `TAB_SIH.zip`, now packaged, which `RD2008.DEF` and `RJ2008.DEF`
  bind to `ETNIA`. The table names `0001`-`0264` and opens with the range `0000-9999`,
  "NÃO INFORMADO", expanded as decided in #7: every other 4-digit code, `0000` included,
  takes that label only through the range (issue `etnia-nao-informado-pela-faixa`). In
  the RR and SP fixtures `0000` marks a non-indigenous patient (`raca_cor` 01-04), not an
  unknown ethnicity, as the SIH page and that issue say: count indigenous patients by
  `raca_cor`. 15 labels hold U+00AD, a soft hyphen, and a text search misses them
  (issue `etnia-hifen-suave`). The RD dictionary grows by 314 KB and the RJ one by 294 KB.
- The CID-10 fields of `sia_producao_ambulatorial` (1.2.0), `sia_apac_quimioterapia`
  (0.2.0) and `sia_apac_radioterapia` (1.1.0), 20 fields, declare a reference to
  `aux_cid10`, so `reference_join_sql` works for them. `0000` is "CID NAO INFORMADO" in
  `S_CID.DBF` of `TAB_SIA.zip` and finds no row. The census of the CID field widths and
  of the values without a row is in `evidence/2026-10-07-sia-cid-widths/`.
- `pa_cidpri` and `pa_cidsec` of `sia_producao_ambulatorial_1994_2007` (1.1.0) declare
  `aux_cid10` too (#82). Codes stay as published, so the values the PA of that era
  writes with no row in `aux_cid10` stay unlabelled: `0` (in both fields of every row
  with `pa_docorig` 'B' in PARR0712) and three-character categories padded with zero
  (`C610`), which `S_CID.DBF` calls "CID NÃO IDENTIFICADO", and `0000`. `C610` is not
  mapped to `C61`. No DEF of 1994-2007 is archived, so the fields come from the RR census instead.
- The CID-10 fields of six more SIA datasets declare `aux_cid10`: `sia_apac_laudos_diversos`
  (0.2.0), `sia_apac_medicamentos` (0.2.0), `sia_apac_nefrologia` (1.1.0) and
  `sia_apac_tratamento_dialitico` (0.2.0) (`ap_cidpri`, `ap_cidsec`, `ap_cidcas`),
  `sia_atencao_domiciliar` (1.2.0) (`cidpri`, `cidassoc`, `pa_cid`) and
  `sia_psicossocial` (0.3.0) (`cidpri`, `cidassoc`), 17 fields. Each is a field the
  dataset's DEF in `TAB_SIA.zip` relates to `S_CID.DBF`, and C(4) in the fixtures of
  `tests/unit/test_references.py` (AD of RR and SP, PS of RR and SP, AM and ATD of RR,
  AN of PA, SAD of MA); no field-width census was run for them. Their only value
  without a row there is `0000`.
- `sih_aih_reduzida` (2.14.1): RDRR2501 publishes `etnia` `X389` (2 rows) and `X401` (3), not
  digits, so outside the `0000-9999` range of `etnia.cnv` and unlabeled; the open issue
  `etnia-x389-x401-sem-fonte` says so, and the excerpt `sih_rd_rr_2025_01_excerpt` (the two
  `X389` rows, `GESTOR_CPF` blanked) pins it (#7).
- `vinculos.json` lists in `sem_cnv`, with the reason, the SIH fields `RD2008.DEF` and
  `RJ2008.DEF` bind to CNV members not packaged yet: `nat_jur` and `cnaer` of
  `sih_aih_reduzida` and `sih_aih_rejeitada`, and `gestor_cod` of `sih_aih_rejeitada`
  (#7, decision 4). No dictionary changes.
- `vinculos.json` lists in `sem_cnv` the other fields `RD2008.DEF` and `RJ2008.DEF` bind
  to a CNV with no map: 21 of `sih_aih_reduzida` and 20 of `sih_aih_rejeitada`. Each reason
  cites the DEF lines and why the binding gives no map: a grouping of the code (CID chapter
  and group, year and month of a date, region and UF of the municipality), a start other
  than 1 (`dias_perm`, `n_aih`), lines that put a field name where the start column goes
  (`faec_tp`, `proc_rea`) or a member not packaged (`uf_zi` and the rest). One test, which
  replaces the #130 one, fails when either DEF binds a field with no map and no reason, or
  when a reason's DEF, lines, members, member count, start columns or labels differ from the
  packaged DEF (#137). No dictionary changes.
- The 37 dictionaries that declared `x-partitions` no longer do, and each takes a patch
  `x-version`: the list had no reader and disagreed with `Dataset.partition_by`, which
  stays the one place a dataset's partitions are declared. `sinasc_nascidos_vivos`
  (2.4.1) also drops `_fonte_arquivo`, `_data_extracao`, `_hash_arquivo`, `_sistema` and
  `_grupo`, columns no import creates. A test fails when a dictionary declares
  `x-partitions` again or a `_` column other than `_source_ano` and `_source_release`
  (#71).
- The `sem_cnv` test of `RD2008.DEF` and `RJ2008.DEF` also fails when a reason cites a
  reference the field does not declare in `foreignKeys` (or leaves one out), says a
  member is packaged in a phrase whose "não" negates something else, quotes a text that
  is neither a DEF label nor a fixture value, cites a number outside its formulas
  (listed in a comment of the test), names the wrong field in place of a start column, or
  counts fixture rows wrongly. The reasons of `faec_tp` and `proc_rea` now name that
  field (`DS_TPFIN`, `IP_DSCR`), and the row count of `gestor_cod` of
  `sih_aih_rejeitada` is checked against the three RJ fixtures (#156). No dictionary
  changes.

### Packaging

- `ipykernel` leaves the required dependencies, where 0.2.3 put it without a changelog
  entry, for the new `colab` extra: a library-only install (a server reading the lake with
  `LakeReader`) no longer pulls the Jupyter kernel and its ~25 dependencies. The Colab
  notebook installs `"omnisus[colab]==<version>"`; `uv pip install "omnisus[colab]"` does
  the same elsewhere (#100).
- `release.yml` publishes to PyPI only after `native` passes as well as the wheel-only
  `gate`. Before, `publish` waited for `gate` alone, and v0.2.2 reached PyPI with the
  native parity job red (#118).

### Dictionaries

- `sih_aih_reduzida_1992_2007` (1.3.0) warns in the dictionary, not only in the docs,
  that `diag_princ` holds CID-9 (6 digits) from 1992-01 to 1997-12 and CID-10 from
  1998-01 to 2007-12 in the same column, so a filter such as `LIKE 'I21%'` over
  1992–2007 misses 1992–1997: open issue `diag-princ-cid9-ate-1997`, from the layout
  census in `evidence/2026-10-01-rd-1992-2007-layouts/` and the four RD fixtures.
  `cid_morte` and `cid_asso` get `cid-zero-a-esquerda`: RDRR0712 writes CID-10
  categories after a `0` (`0I64`), which do not join `aux_cid10`. Codes and labels do
  not change.
- `sia_apac_cirurgia_bariatrica` (0.2.0) is titled "SIASUS — APAC de Acompanhamento
  Pós-Cirurgia Bariátrica (ABO)": `TAB_SIA.zip` reads `ABO` files with
  `APAC_Pos_Cirurgia_Bariatica.def`, and every row of `ABOSP2401.dbc` has `ap_pripal`
  0301120056, post-surgery follow-up in SIGTAP. The dataset keeps its name; renaming it
  would change the API. It gains the labels that DEF binds for `ap_catend`
  (`CARAT_AT.CNV`), `ap_condic` (`TP_GESTAO.CNV`), `ap_motsai` (`MOTSAIPE.CNV`) and
  `ap_tpups` (`TP_ESTAB.CNV`), as `sia_apac_acompanhamento_bariatrica` already had.
  `ap_mn_ind` stays unlabelled: the DEF binds it to `MANT_IND.CNV` without the `CNV/`
  folder, which is not the packaged member; so do `ap_cid_c1`–`ap_cid_c5`, whose
  `CID_COM.CNV` is not archived.
- `docs/sources/sia.md` gives the Informe SIASUS 2019-07 bariatric follow-up layout
  (`ABUFMM.DBF`, 58 fields) to `AB`, whose header it matches, instead of `ABO`.

### Vocabularies

- `aux_cid10` (2.1.0) gains `bloco` and `bloco_descricao`: the CID-10 group of each code
  (`B50-B64`, "Doencas devidas a protozoários"), from `CID10-grup_d.cnv` in
  `SIM/CID10/TAB/OBITOS_CID10_TAB.zip`, the grouping the SIM DEF binds to `CAUSABAS`.
  Each block lies in one chapter. `O93` and `O930`–`O939`, a Brazilian extension, are in
  no group and have no block. `evidence/2026-10-11-blocos-cid10/` compares the groups
  with the WHO ICD-10 2019 and CBCD 2008 lists. Run `omnisus lake update-auxiliares` (or
  `Lake.bootstrap_auxiliares()`) to load the new columns (#103).
- `aux_municipios` (2.2.2) gains the six municipalities that the 2011
  `CADMUN.DBF` lacks and SIM, SINASC and SIH write: `150475`, `220672`, `421265`, `422000`,
  `431454` and `500627`, from `tb_municip.dbf` of the DATASUS territorial base
  (`territorio/tabelas/2026/06-base_territorial_jun26.zip`, registered with its SHA-256).
  Names are written as the base writes them, unaccented; `regiao_saude` and
  `macrorregiao_saude` are NULL in those rows, since the base codes regions in another
  scheme. `codmunnatu` `150475` of the SIM RR 2023 excerpt now resolves. Nazária
  (`220672`) was installed in 2009, before CADMUN, which does not list it. The build stops
  on a `CO_STATUS` outside the dictionary's enum (`REG ADM` and `IGNR`, which the base
  writes, included) and on an altitude that is not whole. `area` is NULL in Nazária,
  Pescaria Brava and Balneário Rincão, which the base writes empty. `aux_municipios`
  2.1.0, 2.2.0 and 2.2.1 and `aux_cid10` 2.2.0 were locked in `versoes.json` during the review
  of this change and never published.
- `aux_cid10` (2.3.0) gains the 25 codes of `tb_cid.txt` of the SIGTAP 202610 that
  `CID10.DBF` (2020) lacks: `A925`, `A97`, `C823`-`C826`, `N182`-`N185`, `P354`, `U09`,
  `U099`, `U10`, `U109` and `W460`-`W469` (`evidence/2026-10-31-cid10-sigtap-e-s-cid/`).
  The SIGTAP zip is registered with its SHA-256 and listed in the manifest as a second
  source. `N181` and `O987` appear in the data but are in neither file and stay out. The
  SIH `S_CID.DBF` labels `N182` and `N185` "CID NÃO IDENTIFICADO"; the table keeps the
  SIGTAP name (`docs/sources/vocabularios.md`). Run `omnisus lake update-auxiliares` (or
  `Lake.bootstrap_auxiliares()`) to load the new rows.

### Performance

- The age rule's SQL trims the 29 whitespace characters with one constant,
  `decode(unhex('…'))`, instead of 29 `chr()` calls joined by `||` in every trim.
  DuckDB binds the expressions again on every query, so a `load` with an age rule and an
  audit of `validar_fonte.py` plan in a fraction of the time (one SIM audit: 6 s to
  0.5 s). Values are the same; audit evidence written from now on records the new SQL
  text, older evidence keeps the `chr()` form.
- `describe_datasets()` reads the packaged dictionaries instead of calling
  `describe_dataset()` for each dataset (about 0.4 s to 3 ms per call). The table is the
  same; the consistency checks of `describe_dataset()` still run when it is called, and
  the tests call it for every dataset.
- Staging maps each batch's columns by name once, instead of rebuilding the list of
  column names for every field.
- `load_dicionario()` parses with libyaml (`yaml.CSafeLoader`) when PyYAML was built
  with it, as its wheels are, and with the pure-Python loader otherwise. The first load
  of `sih_aih_reduzida` in a process drops from about 0.7 s to 0.1 s, and a cold
  `describe_datasets()` from about 2.5 s to 0.4 s. The parsed dictionaries are the same.

## v0.2.3 — 2026-10-08

**Upgrading from 0.2.2:** no parser version changed (the import still reads the same
`encoding` and `x-identity` of every dictionary), so a 0.2.2 lake keeps every scope;
`load` downloads nothing again.

### API

- `read(table)` returns a lake table or view, whole, as a polars DataFrame: the `aux_*`
  vocabularies, the `ibge_populacao` view, or every scope of a dataset already imported.
  A table the lake does not have raises `LookupError` naming what imports it.

### Dictionaries

- `sim_obitos` (2.6.0, rule 1.2.0) and `sih_aih_reduzida` (2.12.0, rule 1.3.0) gain
  harmonised categories in every UF for SIM 2020–2024 and SIH 2020-01 to 2025-02: the
  135 DO and 1,674 RD files were audited in one batch under the written acceptance rule
  that ADR 0003 now records, and none was blocked (evidence in
  `evidence/2026-10-07-validacao-sim_obitos-2020-2024/` and
  `evidence/2026-10-07-validacao-sih_aih_reduzida-2020-01-2025-02/`). The formulas do not
  change; a caller that passes the old `rule_version` now gets `ValueError`. The fields'
  `derivation.rule_version` follows, and so do the SIM subsets that copy them
  (`sim_obitos_infantis`, `sim_obitos_maternos`, `sim_obitos_externos` 1.1.1). SIH from
  2025-03 (layout 6) waits for #86 (#85).
- `scripts/metadados/validar_fonte.py` audits a batch (`--ufs`, `--inicio`, `--fim`,
  `--referencia`; no `--ufs` for a national dataset) with one server listing. The
  reference must be the file validated by hand, and the batch stops as soon as it fails.
  A dropped connection resumes without downloading again, except a failed audit or one
  made under another dictionary version. Each run writes one evidence folder, with no
  local path, and never replaces an existing one. Removed: `--uf`, `--year`, `--month`,
  the `reports/evidence` default and the per-scope `acceptance.json` (#85).
- `docs/datasets.md` shows the validated scopes as UFs and intervals
  ("27 UFs, 2020 a 2024") instead of one entry per scope (#85).
- `sih_aih_reduzida.diagsec9` no longer references `aux_cid10`: the 157 RD files read
  from 2014-01 to 2026-07 (one RR or AP file a month, plus SP and MG at each layout
  change) publish `DIAGSEC9` as C(1), so no row could join. Its
  `physical_type` claim is `conflicting` (IT_SIHSUS_1603, p. 4, says `char (4)`) and the
  field carries the issue `diagsec9-c1`. `reference_join_sql("sih_aih_reduzida",
  "diagsec9")` now raises. Lakes keep their scopes: the parser version does not read
  references (#67).

### Docs site

- The `sih_aih_reduzida` profile gives the `ident` labels the dictionary has, from
  `TAB_SIH.zip`, `RD2008.DEF` → `IDENT.CNV`: 1 = "Normal", 5 = "Longa permanência" and
  "Outras/ignorado" for any other code from 0 to 9, 3 included. It said 1 = AIH
  principal, 3 = AIH de continuação and 5 = AIH de longa permanência, the map without a
  source that the dictionary dropped on 2026-09-26.
- The `load` docstring and the API page say that `load` adds the harmonised categories
  the dataset's dictionary defines (`describe_dataset(base)["analytics"]`), not age, sex
  and dates for every validated source: of the nine datasets with validated scopes,
  `sim_obitos` and `sih_aih_reduzida` define all three and the other seven age only.
  The docstring points to `describe_datasets()` and "Bases e argumentos", and says that
  a dataset whose dictionary defines no category gets no warning (#65).
- The profiles call `docs/datasets.md` "Bases e argumentos", not "catálogo" (in
  CONTEXT.md the catalog is the lake's database), and every link to it lands on a
  section: "Onde fica no servidor" when the sentence names a server directory, "Outras
  fontes" for IBGE population, the system's section otherwise. The CNES profile no
  longer says the package skips the LT file: it imports it as `cnes_leitos` (#64).

### Notebooks

- New `bases.py` lists every DATASUS FTP dataset with `describe_datasets()`, offline,
  with a count per system, and takes any of them to the citation: it shows the exact
  `load` call for `BASE` (no `ufs` for a national dataset, `months` only for a monthly
  one), says when the scope is outside the declared coverage, and shows the dictionary
  fields and the link to the system's section of "Bases e argumentos". Then
  `available_releases` (it stops there when the server does not list the scope),
  `load`, `check_columns`, the row count and `cite`. It opens on `cnes_leitos`, RR,
  January 2024 (#55).
- The Colab notebook shows every dataset right after the install, in a section of its
  own (#55).
- The Colab notebook goes through the library end to end with Roraima: SIM 2022, SIH
  processed in January 2023 and the IBGE 2022 census. It covers `describe_dataset`, `available`,
  `load`, `check_columns`, `outdated`, `label`, the harmonised age and sex categories,
  CID-10 chapters of SIM and SIH, deaths per 100,000 through `import_ibge_populacao`,
  and `cite`. It writes no SQL: `read` brings `aux_cid10`, `aux_municipios`, `aux_uf`
  and `ibge_populacao` as polars DataFrames, and the joins are in polars.
  The Google Drive lake is behind `USAR_DRIVE`, so "Run all" works without mounting it,
  and a scope that is not a validated source skips the harmonised section instead of
  failing. `tests/integration/test_colab_e2e.py` (e2e) runs it against the server for
  RR and SP, and for the 27 UFs with `OMNISUS_E2E_UFS=ALL`.
- `sia.py` and `sinan.py` point to `describe_datasets()` and `bases.py` instead of
  listing the `BASE` values by hand; `sia.py` says it runs on any SIA table the
  package imports (#55).
- When the server lists no file of `BASE` for `UF`, `sia.py`, `sih_aih_reduzida.py`,
  `cnes_estabelecimentos.py`, `medicamentos.py`, `sim_obitos.py` and
  `sinasc_nascidos_vivos.py` say so at discovery, suggest another `UF` and stop before
  `load`, as `bases.py` does; `sinan.py` does the same when the server lists no file of
  `BASE`. Before, discovery failed with polars' `ColumnNotFoundError` (#79).

## v0.2.2 — 2026-10-06

**Upgrading from 0.2.1:** no parser version or dictionary changed, so a 0.2.1 lake
keeps every scope; `load` downloads nothing again.

### API

- `describe_datasets()` returns every DATASUS FTP dataset the package curates as one
  polars table, offline: name, `category` (the system, as `describe_dataset` reports
  it), title, geography, cadence, declared coverage with the month for monthly datasets
  (`"2014-08"`), prefix, final and preliminary directories, columns, labelled columns
  and the scopes whose audited file is a validated source of the harmonised categories
  (#54).

### Docs site

- "Bases e argumentos" moves to Pesquisa, right after "Comece aqui", and is rendered from
  `describe_datasets()`: one section per system (CNES, SIA, SIH, SIM, SINAN, SINASC)
  linking its profiles, coverage with the month for monthly datasets ("2014-08 em
  diante", not "2014 em diante") and "+ preliminar", how each dataset is published
  ("por UF, mensal", "Brasil, anual"), the harmonised categories each dictionary defines
  (age, sex, dates) with the scopes validated for them, and the server directories in a
  section of their own. Dictionary links point at the release tag. The build fails on a
  link to a missing heading (#54).

### CLI

- `omnisus doctor` prints the installed `omnisus-dbf` (version and API, also when the API
  is incompatible) and the backend `OMNISUS_DBF_BACKEND` and `OMNISUS_DBC_BACKEND`
  resolve to. For DBF it says that Rust reads C/N fields only, so under `auto` a file
  with other field types is read in Python. An invalid setting is named (#45).

### Notebooks

- `linkage.py` checks that SIM, SINASC and SIH RD are published for the chosen UF and
  year, and not in `PULAR`, before downloading anything; if one is missing it names it
  and stops instead of failing later with `KeyError` or an empty `pl.concat` (#44).
- `sinan.py` also runs with `BASE = "sinan_tuberculose"`, where the researcher guide and
  the tuberculose profile send readers; the default stays `sinan_chagas`. Step 5 counts
  notifications by type of entry (`tratamento`) and closing status (`situa_ence`), with
  dictionary labels, instead of stopping with `ValueError` in the branch written for
  hanseníase (#53).

### omnisus-dbf 0.2.1

- Metadata only, same code and `API_VERSION` 2 as 0.2.0: its PyPI page gets the SPDX
  license `MIT`, project URLs, author and the updated README (#43). `omnisus` accepts it
  through `omnisus-dbf>=0.2.0,<0.3`.

## v0.2.1 — 2026-10-02

**Upgrading from 0.2.0:** no parser version changed, so a 0.2.0 lake keeps every
scope; `load` downloads nothing again.

### Docs site

- The site is deployed by release tags (`v*`), not by every push to `main`, so it
  describes the omnisus installed from PyPI. Pull requests still build it.

### Packaging

- `omnisus-dbf` is capped below its next minor (`>=0.2.0,<0.3`): omnisus accepts one
  `API_VERSION`, and only a new minor of `omnisus-dbf` may change it.
- Releases tag the release PR's head and publish before merging, so `main` never pins
  a version PyPI does not have yet (RELEASE.md).

### Messages

- When `skip_same` refuses a scope already in the lake, the reason says whether the
  server file changed or the same file was imported by another parser version (another
  omnisus release or dictionary), and `load` says to run the same call again with
  `policy='replace'`.

### Install with uv

- README, the researcher guide and getting-started install with `uv add omnisus` or
  `uv pip install omnisus`, say how to upgrade, and keep `pip install omnisus` as the
  fallback. The Colab notebook runs `!uv pip install -q omnisus==<version>`; Colab ships
  uv and sets `UV_SYSTEM_PYTHON`.
- Notebook instructions open the PyPI version pinned in each notebook
  (`uvx marimo edit --sandbox`, `uvx marimo export html --sandbox`); the checkout path
  is for contributors.
- The reproducibility guide adds "Fixar o ambiente" (`uv.lock` or `uv pip freeze`) and
  says that `cite` prints the running omnisus version and today's date unless
  `accessed=` is given.
- `omnisus-dbf` metadata: SPDX license `MIT`, project URLs and author; its README builds
  with `uv build` and drops stale release notes. These reach PyPI with the next
  `dbf-v*` release.

### SIH

- `sih_aih_reduzida_1992_2007` declares the 14 fields that the older RD layouts publish
  and the 2007 file lacked: `uti_total`, `us_sh`, `us_sp`, `us_sadt`, `us_ortp`,
  `us_sangue`, `us_rn`, `cod_arq`, `cont`, `semiplen` (labelled from `GESTAO.CNV`),
  `diag_sec`, `val_sang`, `cgc_mant` and `cod_seg` (#30). A census of one file per
  month finds 19 DBF layouts in 1992-2007 (`evidence/2026-10-01-rd-1992-2007-layouts/`).
  `num_proc`, `insc_pn` and `seq_aih5` change between numeric and text across months;
  importing both kinds into one lake table fails until #40 is decided.

## v0.2.0 — 2026-10-01

**Upgrading from 0.1.0:** #19 changed how a publication's parser version is computed, so
`load` refuses every scope a 0.1.0 lake already holds. Run each `load` once with
`policy="replace"`; later calls download nothing again.

### Rust decoder by default

- `omnisus` depends on `omnisus-dbf` 0.2.0, now on PyPI, on Linux x86_64, macOS
  (arm64, x86_64) and Windows x86_64 (#38). The `auto` backend then reads DBF and
  decompresses DBC in Rust; other platforms keep the Python decoders, and no install
  needs a Rust toolchain. `OMNISUS_DBF_BACKEND=python` and `OMNISUS_DBC_BACKEND=python`
  still select Python. The `--find-links` install is gone.
- A `dbf-v*` tag publishes `omnisus-dbf` to PyPI after the full native matrix passes
  (#37).

### On PyPI

- `omnisus` is published to PyPI: `pip install omnisus`. The Colab notebook and the
  PEP 723 header of every marimo notebook install `omnisus==0.2.0` from PyPI instead
  of a git commit.

### Import alias (breaking for copied code)

- Docs, notebooks and examples use `import omnisus as sus` instead of `odb` (#21).
  Only the alias in examples changed; the API names are the same.

### SIH dictionaries

- RD: `regct` gets the `REGCT.CNV` map, conflicts between the CNVs and the older
  map are resolved in favour of the CNV (#5); `tpdisec1`–`tpdisec9` get
  `TP_DIAGSEC.CNV` (#14); `diagsec1`–`diagsec9` link to `aux_cid10` (#22).
- RD and RJ: `nacional`, `contracep1`, `contracep2` and RJ `st_mot_blo` get the
  TAB_SIH maps (#20).
- `sih_aih_reduzida_1992_2007` gets the maps of `TAB_SIH_199201-199712.zip`, checked
  against the three packages of the era (#23, #36).
- Each identical CNV is stored once, and the evidence of the three RD eras is
  generated instead of written by hand (#36).

### Dictionary versions

- `src/omnisus/data/dicionarios/versoes.json` locks each dictionary's `x-version`
  to its content; a changed dictionary needs a higher version (#35).
- A publication's `parser_version` hashes only what the import reads from the
  dictionary, so editing a label or a claim no longer forces `replace` on scopes
  already imported (#19).

### Docs and notebooks

- README and site for researchers, Colab notebook, generated dataset arguments (#4);
  notebooks use only the public API (#16); leaner `AGENTS.md` (#15).

## v0.1.0 — 2026-09-25

First release of `omnisus`.

### What the package does

- Imports DATASUS FTP datasets (SIM and its subsets, SINASC, SIH, SIA, CNES, SINAN
  Chagas, hanseníase and tuberculose), IBGE population editions, CNES establishment
  names, SIGTAP and Hórus stock into a DuckLake lake. [Datasets](docs/datasets.md) lists
  every registry row.
- Records each imported scope as a publication with its server files and their
  SHA-256; `odb.cite` turns a snapshot into a citation.
- `odb.load`, `odb.label` and `odb.check_columns` cover an analysis from download to
  labelled rows. Labels come from dictionaries whose claims cite official documents
  registered with URL and SHA-256.
- Decodes DBC and DBF in Python, or in Rust with the optional `omnisus-dbf` package.

### Renamed: `omnisus-db` is now `omnisus` (breaking)

- Distribution, import and CLI are `omnisus`: `import omnisus as odb`,
  `omnisus import ...`. The native package is `omnisus-dbf` (import `omnisus_dbf`),
  in `native/omnisus-dbf`. No `omnisus_db` alias is kept.
- The inventory cache moves from `<cache>/omnisus-db/inventory` to
  `<cache>/omnisus/inventory`; the old one is only a cache and is rebuilt.
- Citations say "Importado com omnisus <versão>".
- Environment variables (`OMNISUS_*`) and lake tables (`_omnisus_*`) keep their
  names: existing lakes open unchanged.

### Removed since `omnisus-db` v0.3.2

- **`cnes_profissionais` (CNES `PF`).** The file names each professional with CPF and
  CNS and answers no clinical question. Its registry row, dictionary, DEF and fixture
  are gone.
- **`omnisus.transforms.cns`.** It deciphered the patient CNS of SIA files and had no
  public consumer.
- `Lake.vacuum` and `omnisus lake vacuum`, already deprecated: use `cleanup_files` /
  `lake cleanup-files`. Also the uncalled `import_st_scope` and
  `lake.schema.canonical_type`/`ddl_for_field`.
- Runtime dependencies nothing imported: `pandera`, `obstore`, `pydantic`,
  `pydantic-settings`, `tomli-w`; `moto` and `pyfakefs` from `dev`. `frictionless`
  is now a `dev` dependency.
- Tutorials 01–05 (they repeated the per-base notebooks), the exploration and
  development notebooks, and the 2026-09-10 audit snapshot pages (`catalogo.md`,
  `campos.csv`, `cobertura.csv`, `fontes/registro.json`) with their generator.

### Changed

- Notebooks live in `notebooks/`, one per base plus `linkage.py`, and pin
  `marimo>=0.25.0,<0.26` like the `notebooks` extra.
- Evidence cited by dictionaries, tests and docs lives in `evidence/`.
- URLs point to `github.com/raphaelfh/omnisus` and `raphaelfh.github.io/omnisus`.
- Docs match the code: `skip_same` skips without downloading, `not_listed` versus
  `fetch_failed`, a second writer fails at once with `WriterBusyError`.
