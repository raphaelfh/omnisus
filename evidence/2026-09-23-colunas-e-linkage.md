# Public DATASUS files link well only through a shared event

A new tutorial notebook, [`notebooks/linkage.py`](../notebooks/linkage.py), loads SIM, SINASC, SIH, SIA BPA-I and CNES for one UF and year. It checks every column of every table against the packaged decoder, then tests deterministic record linkage between the bases. It measures linkage quality with a negative control and with variables that were not used as keys. On RR 2022 three linkages are reliable, and each rests on an **event both records share**:

- **SIH → SIM**: in-hospital deaths. 88.2% linked, 1 chance pair in the control.
- **SIM → SINASC**: infant deaths. 72.4% linked, 5.6% estimated chance.
- **SINASC → SIH**: births linked to the mother's admission. 83.2% of births in SUS-billing hospitals linked, 1.9% estimated chance.

A fourth linkage has no shared event: **SIM → SIA** on birth date, sex and municipality. It looks productive (1,037 pairs), but the negative control finds 605 of them by chance, and 16.8% of the pairs have outpatient care only after the death, so it should not be used. CEP exists only in SIH and cannot link across bases. The decoder check also found codes the dictionaries do not label, and impossible dates that a format check cannot catch.

**Update.** The notebook now covers every family published for the UF and year, and the pre-set verdict rule drops the SIM → SINASC mother's-age pass; see [`2026-09-23-linkage-ampliado.md`](2026-09-23-linkage-ampliado.md). The numbers below are this report's own run.

Reading key. Every number comes from one execution of the notebook on 2026-09-23 against the 27 DATASUS files listed under [Provenance](#provenance), with `UF = "RR"` and `ANO = 2022`. A different UF or year changes the tables. "Chance pairs" means pairs found by the negative control described in [Method](#method-and-its-limits).

## How to run it

```bash
uv run --locked --extra notebooks marimo edit notebooks/linkage.py
```

Set `EXECUTAR = True` (or pass `-- --executar true` to `marimo export html`). The download is about 16 MB, and the notebook runs in about 20 s after that. Opening it downloads and writes nothing; `tests/unit/notebooks/test_notebooks_abrem_offline.py` enforces this.

The notebook has six sections:

1. Download the five bases.
2. Check each column against the decoder.
3. Find linkage candidates.
4. Run the deterministic linkage (five subsections).
5. Compare linkage quality side by side.
6. Learnings.

## Rows loaded

| Base | Scope | Rows | Columns |
| --- | --- | ---: | ---: |
| `sim_obitos` | RR 2022 (by residence) | 3,246 | 90 |
| `sinasc_nascidos_vivos` | RR 2022 (by residence) | 13,091 | 64 |
| `sih_aih_reduzida` | RR 2022, 12 competências (by facility) | 46,613 | 117 |
| `sia_bpa_individualizado` | RR 2022, 12 competências (by facility) | 242,269 | 40 |
| `cnes_estabelecimentos` | RR 2022-12 | 885 | 212 |

## Column check with the decoder

`verificar_colunas(base, dados)` produces one row per column, with these fields:

- the dictionary label;
- the decoder rule: `x-decode`, a declared date format, `x-display`, or none;
- the empty share;
- the number of distinct values;
- the first filled value, raw and after `odb.display_row`;
- the codes no `x-decode` key labels, and how many rows carry them;
- invalid dates, and the minimum and maximum date.

An "unlabeled" code comes from `decode_coverage`, which matches keys exactly, and is then filtered: a code counts only if `Dicionario.decode` also leaves it unchanged. So codes the decoder labels after trimming or integer fallback are not reported. Blank values are counted as empty, not as unlabeled.

| Base | Columns | With a decoder rule | Outside the dictionary | Always empty | With unlabeled codes |
| --- | ---: | ---: | ---: | ---: | ---: |
| SIM | 90 | 52 | 0 | 8 | 2 |
| SINASC | 64 | 35 | 1 | 1 | 1 |
| SIH | 117 | 27 | 0 | 11 | 3 |
| SIA BPA-I | 40 | 10 | 4 (partition columns) | 0 | 2 |
| CNES | 212 | 2 | 200 | 16 | 0 |

These codes appear in the files but no `x-decode` key covers them:

| Base · column | Published codes | Rows | Dictionary keys |
| --- | --- | ---: | --- |
| SIH · `natureza` | `00` | 46,613 (all) | `10` to `80` |
| SIH · `vincprev` | `0` | 46,613 (all) | `1`, `2`, `9` |
| SIH · `homonimo` | `2` | 138 | `0`, `1` |
| SIM · `tpresginfo` | `1`, `2`, `3` | 23 | `01`, `02`, `03` |
| SIM · `tpobitocor` | `6` | 3 | `1` to `5`, `9` |
| SINASC · `tpdocresp` | `0` | 20 | `1` to `5` |
| SIA · `tpidadepac` | `0`, `5`, `9` | 191 | `2`, `3`, `4` |
| SIA · `tpfin` | `05` | 233 | `01`, `04`, `06`, `07` |

The 2026-09-20 microdatasus report found `homonimo` 2 and `vincprev` 0 on RR 2024-01, so these two gaps now appear in two years. `tpresginfo` is a padding mismatch: the file has `1` and the key is `01`, and the integer fallback only matches integer keys. That is the same pattern that report found for CNES `turno_at`.

**Status after an earlier change.** The table above is the measurement of 2026-09-23, before that PR. Each code now has a decision, recorded with its evidence in the dictionary claims:

| Base · column | Code(s) | Decision |
| --- | --- | --- |
| SIH · `natureza` | `00` | Labelled "Ignorado"; only the `00-99` line of `NATUREZA.CNV` lists it |
| SIH · `vincprev` | `0` | Labelled "Não classificado"; only the `0-9` line of `VINCPREV.CNV` lists it |
| SIH · `homonimo` | `2` | Unlabeled, open issue `homonimo-sem-fonte`: no source gives any code |
| SIM · `tpresginfo` | `1`, `2`, `3` | Labelled; keys as the files write them (Estrutura do SIM 2025, p. 8) |
| SIM · `tpobitocor` | `6` | Labelled; the field is the moment of a maternal death (Estrutura do SIM 2025, p. 7), map replaced |
| SINASC · `tpdocresp` | `0` | Unlabeled, open issue `tpdocresp-0-sem-fonte`: the 2020 Estrutura lists only 1–5 |
| SIA · `tpidadepac` | `0`, `5`, `9` | Unlabeled, open issue `tpidadepac-sem-tabela`: the only tables read `TPIDADEPAC`+`IDADEPAC` together |
| SIA · `tpfin` | `05` | Labelled "05 Incentivo - MAC" from TAB_SIA `FINANC.CNV` |

A later change goes further on two rows. A CNV code listed on two lines now takes the later line (ManualTabnet.pdf, p. 21), so `natureza` and `vincprev` take their whole CNV map (`00` and `0` keep the labels above). SIA `idadepac` now shows the age that `TPIDADEPAC`+`IDADEPAC` encode (TAB_SIA `IDADEDET.CNV`), so a rerun counts 11 SIA columns with a decoder rule. `tpidadepac` `0`, `5`, `9` stay unlabeled.

None of these fields feeds the linkage below, so no linkage result changes.

Other findings from the column check:

- **SIH `cid_morte` and `cid_asso` are `0000` in every AIH.** The cause of death of a hospitalised patient exists only in SIM.
- **Every date parses, but three are impossible.** SIA has 27 birth dates before 1900 (the earliest is 1192-06-05). SIH has 3 births on `1899-12-30`, which looks like a placeholder. SINASC has one mother born on 11/05/2022 whose recorded age is 21. A format check reports 0% invalid for all three columns; only the min–max range shows the problem.
- **SIM does not publish `numerodo`** (and SINASC does not publish `numerodn`), although both dictionaries declare them. The public files have no record identifier to link on.
- **The CNES ST dictionary declares 12 of the 212 columns.**

## Linkage candidates

Filled share of each candidate variable (%). A dash means the base has no such column.

| Variable | SIM | SINASC | SIH | SIA | CNES |
| --- | ---: | ---: | ---: | ---: | ---: |
| birth date | 99.7 | 100 | 100 | 100 | — |
| sex | 100 | 100 | 100 | 100 | — |
| municipality of residence | 100 | 100 | 100 | 100 | — |
| CEP of residence | — | — | 100 | — | — |
| establishment (CNES code) | 65.1 | 89.1 | 100 | 100 | 100 |
| event date | 100 | 100 | 100 | 100 (month only) | — |
| mother's birth date | — | 99.9 | — | — | — |
| mother's age | 6.2 | 100 | — | — | — |
| birth weight | 5.9 | 100 | — | — | — |
| patient CNS (encrypted) | — | — | — | 95.9 | — |

SIM mother's age and birth weight are low overall because only deaths before one year of life fill them: the 191 filled weights and 201 filled mother's ages all belong to the 246 deaths before 365 days.

**Sex has four codings**: SIM `1/2`, SINASC `1/2`, SIH `1/3`, SIA `M/F`. The SINASC dictionary also labels them `M`/`F`/`I`, while the others spell them out. The notebook maps each code to its decoder label and keeps the first letter, which gives one comparable variable. Without that step, joining SIH on sex would silently lose every woman.

**CEP is not a linkage variable here.** Among the five bases, only SIH has a patient CEP; CNES `cod_cep` is the facility's address. Boa Vista (140010) spreads 32,827 admissions over 1,920 CEPs, with 18.9% in the most common one. Every other municipality in the top 15 has 2 to 6 CEPs, and the most common one holds 50.6% to 98.5% of its admissions. Outside the capital, CEP behaves like a code for the municipality, not the address.

**Birth date + sex + municipality does not identify a person.** The table shows the share of records whose key combination appears exactly once in the base:

| Base | Key | Unique |
| --- | --- | ---: |
| SINASC | birth date + sex + municipality | 21.4% |
| SINASC | + birth weight | 97.7% |
| SINASC | + birth weight + mother's age | 99.8% |
| SINASC (mothers) | mother's birth date + facility + birth date | 98.0% |
| SIM | birth date + sex + municipality | 96.4% |
| SIM | birth date + sex + death date | 99.9% |
| SIH | birth date + sex + municipality | 38.8% |
| SIH | + CEP | 64.3% |
| SIH | birth date + sex + discharge date + facility | 96.8% |
| SIA (people by CNS) | birth date + sex + municipality | 45.5% |

SIH has no patient identifier, so its low figures mix readmissions of the same person with different people who share a key.

## Deterministic linkage results

| Linkage | Records in A | Pairs | % of A linked | Chance pairs (control) | Estimated chance | Strongest validation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SIH deaths → SIM | 1,340 | 1,182 | 88.2 | 1 | 0.1% | residence municipality equal in 85.9% |
| SIM infant deaths → SINASC | 196 | 142 | 72.4 | 8 | 5.6% | delivery type equal in 96.4% |
| SINASC births in SIH hospitals → SIH | 10,638 | 8,846 | 83.2 | 168 | 1.9% | admission diagnosis in ICD-10 chapter XV in 96.8% |
| SIM → SIA people | 3,246 | 1,037 | 31.9 | 605 | 58.3% | outpatient care only after the death in 16.8% |

### SIH → SIM: in-hospital deaths

A holds the AIHs with `morte = 1`, which the dictionary labels "Com óbito". B holds every death certificate.

| Pass | Keys | Pairs | Control |
| ---: | --- | ---: | ---: |
| 1 | birth date + sex + discharge date = death date + facility | 1,085 | 1 |
| 2 | birth date + sex + date | 68 | 0 |
| 3 | birth date + sex + municipality + facility | 29 | 0 |

- **Where the pairs died.** In SIM, 1,181 of the 1,182 pairs have place of death "Hospital". Residence municipality agrees in 85.9% of the pairs from passes 1–2, where it was not a key. ICD-10 chapter agrees in 49.9%; it compares the admission diagnosis with the underlying cause of death, so it is informative rather than a test.
- **Link rate by discharge month.** In 2022 it ranges from 87.7% to 100% per month. The 44 deaths discharged in November and December 2021 appear in 2022 competências, and only 2 of them find a certificate, because the SIM 2021 file was not loaded.
- **Facility disagreements are a few repeated code pairs**, which points to one facility registered under two codes rather than to wrong links: SIH `7521251` where SIM has `2320592` (37 pairs), `2319659` against `9472339` (21), and `9472339` against `0145742` (8). Establishing which code is right needs a CNES history, which this notebook does not load.

### SIM → SINASC: infant deaths

A holds the deaths of people born in 2022 who died before 365 days of life, 196 records. Both files are organised by residence, so almost every infant death should have a birth record; the link rate therefore approximates sensitivity.

| Pass | Keys | Pairs | Control |
| ---: | --- | ---: | ---: |
| 1 | birth date + sex + municipality + birth weight | 117 | 0 |
| 2 | birth date + sex + municipality + mother's age | 23 | 5 |
| 3 | birth date + sex + municipality + facility | 2 | 3 |

- **Only pass 1 is clean.** Pass 2 carries about 20% chance pairs. Pass 3 finds fewer pairs than its own control, so it is noise and a study should drop it.
- **Agreement on variables that were not keys:**
  - delivery type: 96.4%;
  - pregnancy type: 99.3%;
  - gestational-age band (compared through decoder labels): 68.3%;
  - exact gestational weeks: 47.7%, or 73.4% within ±2 weeks;
  - mother's age, outside pass 2: 81.4%.
- **Birth weight outside pass 1 never matches exactly** (0 of 20 pairs), and 40% match within ±100 g. The pass-2 pairs show both real near-matches (3,100 against 3,010 g; 705 against 750 g) and dropped-digit typos (485 against 4,850 g; 435 against 4,435 g). An exact-weight key misses these links.
- **Of the 54 unlinked deaths, 33 have no birth weight** and 24 have no mother's age.

### SINASC → SIH: the birth and the mother's admission

In a delivery AIH the patient is the mother, and SINASC records her birth date (`dtnascmae`). To make "the birth falls inside the admission" an equality, the notebook expands each admission of a woman into one row per day in hospital. It also groups the live births of one mother on one day in one facility into a single delivery, so twins count once. The key is then mother's birth date + facility + day. Here A holds the deliveries and B the admission-days, so the negative control shifts the mother's birth date.

- **Coverage:**
  - deliveries in hospitals that appear in SIH: 8,840 of 10,632 linked (83.1%), plus 6 of 6 in other health facilities that appear in SIH;
  - hospital deliveries in facilities absent from SIH (840): none linked, as expected, since SIH holds only what SUS paid;
  - deliveries at home, other places or unknown places: none linked.
- **Validation:**
  - the admission diagnosis is in ICD-10 chapter XV (pregnancy, childbirth and the puerperium) in 96.8% of pairs;
  - residence municipality agrees in 94.1%;
  - 0.2% of admissions link to more than one delivery;
  - of the 66 linked deliveries with two or more live births, SINASC records a twin or triplet pregnancy for 86.4%.

### SIM → SIA: the weak-key trap

SIA shares no event with SIM, so the only possible key is birth date + sex + municipality. The SIA side is one row per encrypted CNS with its birth date, sex and municipality. The linkage returns 1,037 pairs, and the same linkage with birth dates shifted by 7 days returns 605. Among the 1,037 pairs, 16.8% have their first outpatient record after the month of the death, which is impossible for a true pair unless the record itself is wrong. Most of these links are coincidences between people who share a birthday in the same municipality.

### Establishment codes against CNES

| Base | Records with a code | % found in CNES RR 2022-12 | Distinct codes not found | % of those records with the event in another UF |
| --- | ---: | ---: | ---: | ---: |
| SIM | 2,113 | 91.5 | 41 | 34.6 |
| SINASC | 11,663 | 93.1 | 28 | 5.5 |
| SIH | 46,613 | 100 | 0 | — |
| SIA | 242,269 | 100 | 0 | — |

SIH and SIA are organised by facility UF, so all their codes are RR facilities. SIM and SINASC are organised by residence. Some of their unknown codes belong to events in other UFs, but most do not: SIM's `2320592` is one example. Whether the rest are closed facilities or earlier codes needs other CNES months, which were not loaded.

## Method and its limits

The notebook uses three rules:

- **1:1 only.** A key combination must appear exactly once in A and exactly once in B; repeated combinations are ambiguous and dropped (`ligar`).
- **Passes.** Keys go from strictest to loosest, and each pass only sees records not yet linked (`ligar_em_passos`).
- **A negative control in every pass.** The same join runs with A's birth date shifted by 7 days, over the same remaining records. No one is the same person as someone born a week later, so every control pair is a coincidence, and the count estimates the false positives of that pass.

Running the control over the same remaining records matters. A first draft ran the whole cascade again for the control. Its early passes found almost nothing, which left a much larger pool for the later passes, so it reported 27 chance pairs in SIH → SIM pass 3 where the corrected control finds 0.

Limits:

- **The control estimates chance agreement, not every error.** A pair whose keys agree because of a shared data-entry mistake is not counted.
- **Shifting the birth date by 7 days slightly changes the population.** Some infants born late in December move into the next year. The effect on the counts is small, and the shift keeps the control away from true pairs with a one-day typo.
- **"% of A linked" is a sensitivity only where every A should be in B**: infant deaths by residence, and in-hospital deaths inside the SIM year. There is no gold standard; validation uses variables that were not keys.
- **Deterministic keys miss typo-level differences.** The weight typos above are an example. A tolerant or probabilistic linkage would recover more pairs and needs its own control.
- **One UF, one year.** RR is small. In a large UF, municipality-level keys become less unique, and the chance rates rise.

## Learnings

1. **Decode before you link.** Sex is coded four ways, and the dictionaries label it two ways. Comparing decoder labels (delivery type, pregnancy type, gestational band, place of death) turns the dictionary into the harmonisation layer.
2. **A shared event makes the key.** Death date = discharge date, the delivery day inside the admission, and birth weight each turn a key that is unique for about 20% to 45% of records into one that is 97% to 100% unique. Birth date + sex + municipality alone is not a person identifier.
3. **Always run a negative control.** It is one extra join per pass. It separates SIH → SIM (0.1% estimated chance) from SIM → SIA (58.3%), which have similar-looking raw pair counts, and it shows which pass to drop in a cascade.
4. **Validate with variables that were not keys, and allow for measurement noise.** Exact equality understates agreement on gestational weeks and birth weight; within ±2 weeks or ±100 g the picture is clearer.
5. **File organisation shapes coverage.** SIM and SINASC are organised by residence, while SIH, SIA and CNES are organised by facility. SIH competências also carry discharges from the previous year. Both show up in the link rates and in the CNES checks.
6. **The column check finds dictionary gaps on real data.** It found codes the dictionaries do not label (SIH `natureza`, `vincprev` and `homonimo`; SIM `tpresginfo`; SIA `tpidadepac` and `tpfin`; SINASC `tpdocresp`; SIM `tpobitocor`), columns that are never filled, and impossible dates that a format check misses.

## Follow-ups this work suggests

- **Unlabeled codes.** Confirm and add labels for the codes listed under [Column check](#column-check-with-the-decoder), against the hashed TAB CNVs or source documents, per the zero-assumption policy. `tpresginfo` is the same padding mismatch as CNES `turno_at`; it needs keys as published, or a documented padding rule. Done in PR #25; see the status note under [Column check](#column-check-with-the-decoder).
- **Implausible dates.** Decide whether the analytical projection should flag them. The decoder is display-only and passes them through unchanged.
- **Facility code pairs.** Loading other CNES competências would show whether `2320592`, `0145742` and the other codes missing from CNES RR 2022-12 are closed facilities or earlier codes.

## Provenance

Every file came from `ftp.datasus.gov.br`. The SHA-256 hashes were read from the lake's `_omnisus_sources` table.

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| DORR2022.dbc | 6643344fe1ab587d648e5e0ea8cf7e3ef9e5b5b7021a12dcbbc54f5724d2ec65 | 275,221 |
| DNRR2022.dbc | 55edaa6508cb58cc35e8ce7a74d5950198d91dd3c5c4c64d9e0c8199667601db | 641,046 |
| RDRR2201.dbc | 00c5ee1079dca6d947892b221851693c0c1f13d60ee14d3ec1be3a8932dc7d55 | 265,559 |
| RDRR2202.dbc | e6207cbeaad1d20dfc6ec5a3dcd6070bfe4dd58e0dff25fdd4041945cd671832 | 252,712 |
| RDRR2203.dbc | 5ccab0c5af5bf25e69e97d91beb16637d9db1ed8ca944d74f435e380db6334f3 | 309,582 |
| RDRR2204.dbc | 433b97deeb0fe0a74a481d1e6377bff66178f9eba06bc9cf992d486917fc2cab | 292,263 |
| RDRR2205.dbc | e7f867bcfd4c51feb0c79ab322e3f613ab4c07baff36fb31b57f93c7177a00e6 | 325,659 |
| RDRR2206.dbc | 22fea9cb1c5517d2c79de4d620cbf234be9715c2c78fcad54d7c68c38e9c2b77 | 50,318 |
| RDRR2207.dbc | 246f920bbd2f9a7f5b98597a280d75108d6276eccf5967e2b73b0f22092db80a | 308,161 |
| RDRR2208.dbc | adffac19f16c5e98cb3ef543ea2bb18c86dbc7443dd0baeb8aa09672bac80954 | 368,638 |
| RDRR2209.dbc | fe2b8399c0743c82050743bf1b293c1e3ffa1dacd3d2e095889cbf49b12b858d | 300,510 |
| RDRR2210.dbc | 6f18774b0c19491ecf31cab908d47b5ddb862282edc6a21441eee5dc50dcb2e9 | 352,598 |
| RDRR2211.dbc | 9e0d65d02a140e03afe6c6c35b4076ca2a8b8cb9c658ae7da2625dae35bb1662 | 334,610 |
| RDRR2212.dbc | 4a665f136f34c2a8a4eccc317af4593a4999e624d24ccce2b359b42b6e8582e9 | 329,543 |
| BIRR2201.dbc | 03d41d139dd970f25a565471053a5459f7cd77ef7d2633a63f33db2f8725340a | 766,384 |
| BIRR2202.dbc | e9d359f1422add2c1b2cf0be707c9a88ffba7c2290d0e7fec9edf5bfffce2b7a | 763,985 |
| BIRR2203.dbc | 0b6ef6b20ab1754d42a1ee6c0f0a2ee08814f4f32ecfbcd3c899bf3edcd47c82 | 940,207 |
| BIRR2204.dbc | 1f84e042c436e5cdeee724e8e81f2dba3e7d26b3aad22b67b076baffca0c0c63 | 854,400 |
| BIRR2205.dbc | 99cfc5ebf78e25000632e9428d2bad463ab4c6e5fbea1e7ff00721e9d50ba300 | 1,178,856 |
| BIRR2206.dbc | eb6ab2df7c137c2b0c3f323f6a6a38e029b861d39956691749ec2b7089d25616 | 342,523 |
| BIRR2207.dbc | bf1c0d7196639f707fe8a49229426d7798a03b845626e318eb66a238112f1eda | 1,141,592 |
| BIRR2208.dbc | d5e88dcbfdbd75a5a04adfa14c8fb12fa888a41fe3c72dacdf94eb5a32e1fedc | 1,352,697 |
| BIRR2209.dbc | 28e0c18eb2e12deba6ab378d14e22e257d22aa956f6f8b5304df506ac487e4b4 | 1,128,514 |
| BIRR2210.dbc | a9c234f7bbe36e545a6a14db36a16e89dc86d790f6c349ae3bd3a1bccd07c195 | 983,373 |
| BIRR2211.dbc | a3335858c684feb66dba96b48f913784085b8953ac23a4a16f539c54bb96fb4e | 1,091,595 |
| BIRR2212.dbc | 0045b4d3929ccf5960aa5aa16f0ba0b9eae4ba7d0ed0a7c7d92e9858deee4e83 | 938,791 |
| STRR2212.dbc | 5a3700a98a1e4eec7d8f1e6d0a5b942b5fffde82bd9b4240f90266c88e665c97 | 40,527 |

The ICD-10 chapters come from `aux_cid10`, part of the packaged `auxiliares-bootstrap.zip`, which the notebook loads into the lake with `Lake.bootstrap_auxiliares()`.

## Verification

- **Red first.** `tests/unit/notebooks/test_notebooks_abrem_offline.py` listed `tutorial/06_colunas_e_linkage.py` before the file existed. `test_every_notebook_is_checked` and `test_notebooks_index_links_every_notebook_in_molab` failed (2 failed).
- **Green.** `uv run --locked --extra notebooks pytest -q tests/unit/notebooks/` then passed with 108 tests, including the checks that the new notebook opens offline, writes nothing, carries PEP 723 metadata and a molab badge, and uses no `mo.ui` widgets.
- **Executed end to end.** `marimo export html notebooks/linkage.py -- --executar true` completed with no failing cell.
- **Linters.** `ruff check`, `ruff format --check` and `pre-commit run --files` on the changed files pass.
