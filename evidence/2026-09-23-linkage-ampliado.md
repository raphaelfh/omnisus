# Linkage beyond the first five bases: an identifier helps, a demographic key does not

[`notebooks/linkage.py`](../notebooks/linkage.py) now covers every DATASUS family published for one UF and year, not only the five bases of the [first report](2026-09-23-colunas-e-linkage.md). The new ones are:

- SIH: professional services (SP), rejected AIHs (RJ) and their error codes (ER);
- SIA: psicossocial RAAS (PS) and the APAC families;
- the four national SIM subsets;
- SINAN: tuberculose, hanseníase and Chagas.

The notebook checks the columns of each new base against the decoder. It then tests eleven new linkages, each with a negative control and a validation on variables that were not keys. It ran on RR 2022, the main run, and on SP 2022 as a stability check.

**What is usable for research:**

- **Links through a published identifier.** Error below 1%, except for bariatric surgery:
  - *SIH professional services → AIH reduzida* (`sp_naih` = `n_aih`). Every SP AIH is in RD, and dates, diagnosis, procedure and total value agree in 100%.
  - *SIH rejected → approved AIH* (`n_aih`). This one is SP only:
    - in SP, 61% of rejection records have the same number in RD, with the same birth date in 99.7% of them;
    - in RR, a rejected AIH never came back approved.
  - *SIA encrypted CNS across SIA families*. The same value has the same sex in 96% to 100% of people and the same age ±1 year in 91% to 99%, against about 50% and 5% in the control.
  - *APAC bariatric surgery → AIH of the surgery* (`ab_numaih`). SP only. The surgery date falls inside the admission in 92.4% of pairs, against 32.8% in the control. But only 27.6% of 2022 surgeries are found in RD SP 2022.
- **SIM subsets.** DOINF, DOMAT and DOEXT are exact copies of DO records: every row equals one DO row on all 87 shared columns, in RR and in SP. DOFET is a separate register. A study that has DO does not need to link the subsets.
- **Maternal death → admission.** Deaths link to the admission of a woman on the same birth date, date and hospital:
  - RR: 9 of 19, with no chance pairs;
  - SP: 114 of 207, with no chance pairs in the kept pass, and 79.9% of pairs have "death" in the SIH (use with caution);
  - fewer than half of the pairs are obstetric admissions (ICD-10 chapter XV).

**What is not usable:**

- Birth date + sex + municipality between SIA and SIM or SIH: 56% to 78% chance.
- Age + sex + CEP between APAC and SIH or SIM:
  - 15% to 31% chance for SIH, and 50% to 120% for SIM;
  - quimioterapia → SIH in SP is the one borderline case (15.1% chance).
- SINAN → SIM on birth year + sex + municipality: 73% to 93% chance in SP, even when restricted to cases closed as death.

Reading key. Every number comes from one execution of the notebook on 2026-09-23, per UF, against the files listed under [Provenance](#provenance). "Chance" is the negative-control estimate described in [Method](#method-changes-since-the-first-report). The notebook prose is in Portuguese; its row labels are quoted as the notebook prints them.

## How to run it

```bash
uv run --locked --extra notebooks marimo edit notebooks/linkage.py
```

Set `EXECUTAR = True`. RR 2022 downloads about 63 MB (145 RR files and 7 national files) and runs in 2 to 4 minutes.

For the SP run, set `UF = "SP"` and:

```python
PULAR = {"sia_bpa_individualizado", "sih_servicos_profissionais", "sia_apac_medicamentos"}
```

- These three do not fit in memory as one DataFrame (BPA-I SP alone is 3.36 GB compressed).
- The run below also skipped `cnes_estabelecimentos` and `sih_aih_reduzida (ano seguinte)`, which did not import before the undecodable-byte fix. The [addendum](#addendum-2026-09-23-rd-sp-2023-after-the-undecodable-byte-fix) has the numbers with them.

With `PULAR` set, SP 2022 downloads about 520 MB (134 SP files plus the national ones) and runs in about 14 minutes, peaking at about 15 GB of memory.

## What DATASUS publishes

The notebook asks the server first (`odb.available`). Families with no file are shown as "não publicada" and skipped.

| Family | RR 2022 | SP 2022 |
| --- | --- | --- |
| SIH RD, SP, RJ, ER | 12 months | 12 months |
| SIH RD of the next year (for rejected AIHs) | 12 months (2023) | 12 months (not imported) |
| SIA BPA-I, PS, ATD, AM, AD, ACF | 12 months | 12 months |
| SIA AQ (quimioterapia) | 10 months, no 06 and 07 | 12 months |
| SIA ABO (bariatric surgery), AR (radioterapia), AMP | not published | 12 months |
| SIA AB (bariatric follow-up) | not published for any UF in 2022 | not published |
| SIA AN (nefrologia) | only 2008–2014 | only 2008–2014 |
| SIA SAD (atenção domiciliar) | only 2012–2018 | only 2012–2018 |
| SIM DOFET, DOINF, DOMAT, DOEXT | national file, final | same |
| SINAN tuberculose | national file, **preliminary** | same |
| SINAN hanseníase, Chagas | national file, final | same |

**June 2022 is incomplete in RR.** RD has 668 AIHs in June, against 3,340 to 4,863 in the other months. The professional-service file has 12,093 rows, against 50,859 to 63,375, and BPA-I has 7,220 against 16,207 to 27,768. PS, ATD and the other APAC families have a normal June. SP 2022 has no such gap.

## Column check of the new bases

`verificar_colunas` is the first report's check. The only change is that a code counts as unlabeled when `Dicionario.decode` returns `None`, which is how v0.3.1 signals an unknown code. It gives one row per column: dictionary label, decoder rule, % empty, examples, codes no `x-decode` key labels, and the min–max of each date. In both runs, these codes appear with no label:

| Base · column | Codes | Rows (RR) | Rows (SP) |
| --- | --- | ---: | ---: |
| SIA PS · `tp_droga` | `AC`, `ACO`, `AO` (SP also `A O`, `CA`) | 5,771 | 362,613 |
| SIA AQ, ATD, AD · `ap_coidade` | `5` (SP AD also `0`) | 2 (AD) | 172 + 12 + 156 |
| SIA AQ, ATD, AD · `ap_tpapac` | `4` | — | 1 + 1 + 77 |
| SIA AR · `ar_finali` | `7` | — | 41 |
| SIH RD and RJ · `espec` | `17` | — | 36 + 75 |
| SIH RJ · `financ` | `00` | — | 196 |
| SINASC · `tpdocresp` | `0` (known) | 20 | 13,010 |
| SINAN tuberculose (preliminary) | 8 fields with codes outside the map, some of them stray characters (`2/`, `[2`, `,`, `-`) | 4,909 | same national file |

Other findings:

- **Dates that parse but cannot be true.** A format check reports 0% invalid for all of these:
  - APAC dates: authorisation in 2222, 3033, 8202, 8282 and 9202; request in 0022, 0222 and 0572; AQ diagnosis in 0009; treatment start in 5016 and 7200;
  - PS birth date in 1366;
  - SINASC mother's birth date in 0980.
- **`tippre` in the psicossocial file loads as `tippre  `**, with trailing spaces in the column name. The dictionary's `tippre` then matches nothing, and the column appears as both "declared and absent" and "outside the dictionary".
- **Dictionaries without code maps:**
  - The SIM subsets, RJ and ER have raw dictionaries: no labels, and no `x-decode` on sex. ER's `co_erro` has no labels at all.
  - AR, ACF and AMP have no `x-decode` on `ap_coidade`, so their age is unusable without an assumption; AMP also has none on `ap_sexo`. This is why AR is missing from the age-key linkage below.
- **Staging overwrites file columns named like partitions.** ER has its own `ANO` and `MES`; the published table keeps the partition values. A byte-level read of the 12 RR 2022 ER files showed they are equal in all 338 rows, so nothing was lost there. This check was a separate script, not the notebook; the file hashes are in the provenance table.

## Linkage results

The rule was set before the numbers:

- **viable**: every kept pass ≤ 5% chance and the strongest non-key validation ≥ 90%;
- **use with caution**: 5% to 20% chance, or validation 75% to 90%;
- **not viable**: anything else.

A pass is dropped when its chance estimate is above 20%, or when its control finds as many pairs as the pass itself. Exact keys have no chance estimate. Their validation shows, next to it, the agreement of the **neighbour-identifier control**.

### RR 2022

| Linkage | Records in A | Pairs kept | % of A linked | Pairs dropped | Control pairs | Chance | Validation | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| SIH deaths → SIM | 1,340 | 1,182 | 88.2 | 0 | 1 | 0.1% | municipality equal in 85.9% | use with caution |
| SIM infant deaths → SINASC | 196 | 117 | 59.7 | 25 | 0 | 0.0% | delivery type equal in 96.4% | viable |
| SINASC deliveries → SIH | 10,638 | 8,846 | 83.2 | 0 | 168 | 1.9% | diagnosis in chapter XV in 96.8% | viable |
| SIM → BPA-I people | 3,246 | 0 | 0 | 1,037 | — | — | — | not viable |
| SIH professional services → RD (`n_aih`) | 46,613 | 46,613 | 100 | — | — | — | discharge date equal in 100% (control 13.7%) | viable |
| SIH rejected → RD (`n_aih`) | 271 | 8 | 3.0 | — | — | — | same birth date in 50% (control 0%) | not viable |
| SIA CNS in another family → BPA-I CNS | 10,854 | 6,230 | 57.4 | — | — | — | sex equal in 97.1% (control 51.0%) | viable |
| SIM → PS people | 3,246 | 0 | 0 | 32 | — | — | — | not viable |
| BPA-I people → SIH | 82,380 | 0 | 0 | 5,364 | — | — | — | not viable |
| PS people → SIH chapter V | 3,067 | 23 | 0.7 | 0 | 3 | 13.0% | admission within the care period in 60.9% | not viable |
| AQ → SIH chapter II | 681 | 0 | 0 | 84 | — | — | — | not viable |
| AQ → SIM chapter II | 681 | 0 | 0 | 15 | — | — | — | not viable |
| ATD → SIH chapter XIV | 441 | 0 | 0 | 62 | — | — | — | not viable |
| ATD → SIM chapter XIV | 441 | 0 | 0 | 10 | — | — | — | not viable |
| DOMAT → SIH (women) | 19 | 9 | 47.4 | 0 | 0 | 0.0% | admission ended in death in 100% | viable (n = 9) |
| SINAN TB, all cases → SIM | 494 | 0 | 0 | 29 | — | — | — | not viable |
| SINAN TB, closed as death → SIM | 25 | 0 | 0 | 2 | — | — | — | not viable |
| SINAN hanseníase, all → SIM | 65 | 0 | 0 | 6 | — | — | — | not viable |
| SINAN hanseníase, closed as death → SIM | 3 | 1 | 33.3 | 0 | 0 | 0.0% | cause of death is the disease in 0 of 1 | not viable |
| SINAN Chagas, all → SIM | 7 | 0 | 0 | 2 | — | — | — | not viable |

Radioterapia and bariatric surgery are not published for RR. No Chagas case in RR was closed as death.

### SP 2022 (stability check)

| Linkage | Records in A | Pairs kept | % of A linked | Pairs dropped | Control pairs | Chance | Validation | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| SIH deaths → SIM | 141,376 | 129,066 | 91.3 | 0 | 294 | 0.2% | municipality equal in 96.4% | viable |
| SIM infant deaths → SINASC | 5,146 | 3,819 | 74.2 | 435 | 98 | 2.6% | delivery type equal in 97.7% | viable |
| SINASC deliveries → SIH | 358,637 | 285,984 | 79.7 | 0 | 1,516 | 0.5% | diagnosis in chapter XV in 97.4% | viable |
| SIH rejected → RD (`n_aih`) | 187,361 | 114,339 | 61.0 | — | — | — | same birth date in 99.7% (control 1.3%) | viable |
| SIA CNS in another family → PS CNS | 627,640 | 3,313 | 0.5 | — | — | — | sex equal in 98.0% (control 51.1%) | viable |
| SIM → PS people | 354,056 | 0 | 0 | 9,175 | — | — | — | not viable |
| PS people → SIH chapter V | 302,774 | 0 | 0 | 6,315 | — | — | — | not viable |
| AQ → SIH chapter II | 126,642 | 27,063 | 21.4 | 0 | 4,089 | 15.1% | facility equal in 85.3% | use with caution |
| AQ → SIM chapter II | 126,642 | 0 | 0 | 3,103 | — | — | — | not viable |
| ATD → SIH chapter XIV | 34,537 | 0 | 0 | 5,672 | — | — | — | not viable |
| ATD → SIM chapter XIV | 34,537 | 0 | 0 | 951 | — | — | — | not viable |
| DOMAT → SIH (women) | 207 | 114 | 55.1 | 30 | 0 | 0.0% | admission ended in death in 79.9% | use with caution |
| SINAN TB, all cases → SIM | 22,974 | 0 | 0 | 945 | — | — | — | not viable |
| SINAN TB, closed as death → SIM | 2,071 | 0 | 0 | 120 | — | — | — | not viable |
| SINAN hanseníase, all → SIM | 1,476 | 0 | 0 | 161 | — | — | — | not viable |
| SINAN hanseníase, closed as death → SIM | 34 | 0 | 0 | 1 | — | — | — | not viable |
| SINAN Chagas, all → SIM | 68 | 0 | 0 | 3 | — | — | — | not viable |
| APAC bariatric surgery → RD (`ab_numaih`) | 3,941 | 461 | 11.7 | — | — | — | surgery date inside the admission in 92.4% (control 32.8%) | viable where found |

Radioterapia is published for SP, but its dictionary has no `x-decode` for `ap_coidade`, so the age key could not be built. SP skipped the professional-service file, BPA-I and AM (`PULAR`).

The three linkages of the first report are stable in SP, with chance at 0.2% to 2.6%. SIH → SIM is "use with caution" in RR only because residence municipality, the validation that report chose, agrees in 85.9% of RR pairs against 96.4% in SP. In RR, 99.9% of those pairs have place of death "Hospital". SIM → SINASC keeps only its birth-weight pass under the pre-set rule. The mother's-age pass had 21.7% chance in RR and 28.0% in SP, so it is dropped. Its link rate therefore reads 59.7% in RR, not the 72.4% of the first report.

## Pair by pair

### SIH professional services → AIH reduzida

The SP file has one row per professional act, with `sp_naih` but no birth date or sex. Grouped by AIH, its 46,613 AIHs are exactly the 46,613 RD AIHs of RR 2022. No AIH has two facilities or two discharge dates across its rows.

| Variable | Real pairs | Neighbour-AIH control |
| --- | ---: | ---: |
| facility (CNES) | 100% | 99.9% |
| admission date | 100% | 6.8% |
| discharge date | 100% | 13.7% |
| principal diagnosis | 100% | 15.6% |
| procedure | 100% | 15.8% |
| sum of `sp_valato` = `val_tot` (±0.01) | 100% | 3.7% |

The control shows why the facility is not a validation. AIH numbers are issued in blocks per hospital, so the neighbouring number almost always belongs to the same hospital.

### SIH rejected AIHs → approved AIHs

RJ holds rejection records, ER their error codes. Every ER AIH is an RJ AIH in RR. In SP, 157,014 of the 157,136 ER AIHs are. The notebook looks for each RJ `n_aih` in RD of the same year and, for RR, the next year.

- **RR.** Of 271 rejected AIHs, 8 have the number in RD. All 8 were approved **1 or 2 competências before** the rejection, and all carry ER error `040006`. Birth date agrees in 4 of 8. No rejected RR AIH reappears in RD 2023.
- **SP.** Of 187,361 rejection records, 114,339 have the number in RD 2022 (RD 2023 SP could not be imported). The lag is mostly positive:
  - 81,724 one competência later;
  - 14,548 two competências later;
  - 6,587 at three or more competências later (3,631 of them at three);
  - 708 in the same competência;
  - 10,772 with RD before RJ, 3,829 of them one competência earlier.

  | Variable | Real pairs | Neighbour-AIH control |
  | --- | ---: | ---: |
  | birth date | 99.7% | 1.3% |
  | sex | 99.8% | 57.6% |
  | admission date | 99.5% | 27.7% |
  | discharge date | 87.8% | 17.7% |
  | CNES | 99.8% | 82.2% |

So in SP a rejected AIH usually comes back approved, with the same number, the next month. In RR it does not. The RR overlaps are re-presentations of already approved AIHs, half with a different patient. This behaviour is not stable across UFs, and the notebook reports both. The ER codes are unlabeled (see [Dictionary gaps](#dictionary-and-library-gaps)).

### SIA: the encrypted CNS

| | RR | SP |
| --- | --- | --- |
| Families checked | BI, PS, AQ, ATD, AM, AD, ACF | PS, AQ, AR, ATD, ABO, AD, ACF, AMP |
| Length | 15 (BPA-I also 14, 13 and 12, in 96 records) | 15 |
| Symbol alphabet | 10 bytes, `0x7b`–`0x84` | same |
| CNS with more than one sex in its family | 0 to 0.6% | 0 to 0.33% |

The same value in two families belongs to one person, measured against the reference family: BPA-I in RR, PS in SP, where BPA-I was skipped.

| Variable | RR, real | RR, control | SP, real | SP, control |
| --- | --- | --- | --- | --- |
| sex | 96.3–98.8% | 48.6–57.4% | 95.5–100% | 38.5–75.8% |
| age ±1 (APAC) | 93.5–98.3% | 4.6–6.2% | 90.9–99.3% | 6.5–12.1% |
| birth date (PS vs BPA-I, RR) | 91.5% | 0.0% | — | — |

Inside SIA the encrypted value is a stable person identifier. The fixed length, the 10-symbol alphabet and the consistency across families describe how it is encoded. The notebook does not try to invert the encoding, and neither does this report.

### BPA-I and RAAS → SIM and SIH

Birth date + sex + municipality with no shared event behaves as the first report found for SIM → BPA-I:

| Linkage | RR, chance | SP, chance |
| --- | --- | --- |
| SIM → BPA-I | 58.3% | — (skipped) |
| SIM → PS | 56.2% | 78.1% |
| BPA-I → SIH | 57.4% | — (skipped) |
| PS → SIH | 13.0% (23 pairs) | 32.3% |

Restricting the SIH side to psychiatric admissions (chapter V) was the attempt at a shared event. In RR it leaves 23 pairs with weak validation, and in SP it is noise.

### APAC → SIH and SIM on age

APAC has no birth date, only an age. The key is CEP + sex + age for SIH and municipality + sex + age for SIM. SIH is restricted to the same ICD-10 chapter as the APAC: chapter II for quimioterapia, chapter XIV for dialysis. The control shifts age by **2** years, not 1:

| AQ → SIH chapter II, age + k | RR pairs | SP pairs |
| --- | ---: | ---: |
| k = 0 (real) | 84 | 27,063 |
| k = 1 | 51 | 9,391 |
| k = 2 | 26 | 4,089 |
| k = 3 | 33 | 4,110 |

A true pair can differ by one year of age between two events, so k = 1 still finds true pairs. From k = 2 the count stops falling.

With that control:

- **AQ → SIH:** 31.0% chance in RR (dropped) and 15.1% in SP, where facility agrees in 85.3% and municipality in 99.8%. Use with caution, and only in a large UF.
- **ATD → SIH:** 30.6% (RR) and 25.2% (SP). Facility agrees in 0% (RR) and 36.7% (SP), because dialysis clinics are not the admitting hospitals.
- **APAC → SIM:** 50% to 120% chance. Municipality + sex + age is unique for 18.4% of RR deaths and 6.2% of SP deaths.

**An age-only key does not identify a person.** Even with CEP, it identifies a person only in a small population, and then the counts are too small to use.

### SIM subsets → SIM by UF

Each subset, filtered to residents of the UF, was joined to DO on all 87 shared columns compared as text:

| Subset | RR rows | equal to exactly 1 DO | SP rows | equal to exactly 1 DO |
| --- | ---: | ---: | ---: | ---: |
| DOFET | 122 | 0 | 4,820 | 0 |
| DOINF | 246 | 246 | 5,795 | 5,795 |
| DOMAT | 19 | 19 | 207 | 207 |
| DOEXT | 611 | 611 | 24,332 | 24,332 |

- DOFET holds only `tipobito = 1` (fetal) and DO only `tipobito = 2`, so they are disjoint registers.
- Seen from DO:
  - every death under 365 days of life is in DOINF (RR 246 of 246; SP 5,774 of 5,774 with a birth date);
  - every chapter-XX cause is in DOEXT;
  - chapter XV is in DOMAT **except `O96`** (late maternal death), which is in 2 RR and 34 SP declarations.

### Maternal deaths → admissions

The brief asked for obstetric admissions (chapter XV). The data rule that out: of RR's 19 maternal deaths, only 1 links to a chapter-XV admission. Indirect maternal deaths (`O98`, `O99`) are admitted under the underlying disease. So B became all admissions of women:

| | RR | SP |
| --- | --- | --- |
| Pass 1: birth date + death date = discharge + facility | 9 pairs, 0 control | 114 pairs, 0 control |
| Pass 2: birth date + date | 0 pairs | 20 pairs, 13 control (dropped) |
| Pass 3: birth date + municipality + facility | 0 pairs, 1 control (dropped) | 10 pairs, 8 control (dropped) |
| Admission ended in death (SIH) | 100% | 79.9% |
| Admission diagnosis in chapter XV | 1 of 9 | 66 of 144 (all passes) |

### SINAN → SIM

SINAN has only birth year, sex and municipality of residence, plus the death date for Chagas, which is empty in RR and in SP. Birth year + sex + municipality is unique for:

| Base | RR | SP |
| --- | ---: | ---: |
| SIM deaths | 18.7% | 6.3% |
| tuberculose cases | 28.3% | 23.1% |
| hanseníase cases | 84.6% | 75.1% |
| Chagas cases | 100% | 100% |

| Linkage (SP) | Pairs | Control | Chance |
| --- | ---: | ---: | ---: |
| TB, all cases | 945 | 876 | 92.7% |
| TB, closed as death | 120 | 88 | 73.3% |
| hanseníase, all cases | 161 | 145 | 90.1% |
| Chagas, all cases | 3 | 8 | — |

Restricting to cases closed as death reduces the pool but not the coincidences. Among the 68 SP TB pairs whose closure does not say "outras causas", the SIM underlying cause is tuberculosis (A15–A19) in 60.3%. **SINAN → SIM on these fields is not viable.**

### APAC bariatric surgery → AIH of the surgery (SP)

ABO carries `ab_numaih`. Grouped by that number, SP 2022 has 3,941 surgeries, dated from 2003 to 2022. The RD search covers 2022 only, because RD SP 2023 does not import:

| Surgery year | AIHs in ABO | found in RD 2022 |
| --- | ---: | ---: |
| 2022 | 1,617 | 446 |
| 2021 | 955 | 14 |
| 2019 | 449 | 1 |
| 2003–2020, other years | 920 | 0 |

| Variable (461 pairs) | Real | Neighbour-AIH control |
| --- | ---: | ---: |
| sex | 99.6% | 76.8% |
| facility | 99.8% | 90.7% |
| age ±1 | 98.5% | 9.1% |
| surgery date inside the admission | 92.4% | 32.8% |

The found pairs are right. But 72.4% of 2022 surgeries are not in RD SP 2022, and why is open. Candidates are surgeries in another UF, AIHs paid in 2023, or numbers that are not SIH AIHs. RD SP 2023, which the next defect blocks, would answer the second.

## Two import defects found on SP

Both stop `odb.load` for a whole batch because of one byte in one free-text field. The dictionaries declare `encoding: cp1252`, and the bytes below are undefined in cp1252:

| File | SHA-256 | Field | Byte | Value |
| --- | --- | --- | --- | --- |
| `CNES/200508_/Dados/ST/STSP2212.dbc` | `dba6fff68657a6c3272d5be2a12266ee190f5be7355451d71d3ca1c5503bd285` | `ALVARA` | `0x8F` | `.\x8f6018202200448734` |
| `SIHSUS/200801_/Dados/RDSP2308.dbc` | `eb5d97e8e834b7bc4342bfa28eb00eaa20055490b688f466906d6bc7f42f3ebb` | `AUD_JUST` | `0x90` | `PACIENTE REC\x90M NASCIDO ENCONTRADO NA ESTRADA RURAL` |

- `RDSP2308` fails with `'charmap' codec can't decode byte 0x90`. The other 11 months of RD SP 2023 are rolled back with it: RDSP2301 imports alone into an empty lake.
- In CP850, `0x90` is `É`, which would give "RECÉM", so this one record looks CP850-encoded.
- CNES ST SP 2022-12 fails the same way on its single `0x8F`.

The SP run therefore skips both through `PULAR`. This is a library question, how one undecodable byte in a free-text field should be handled, and it is a follow-up here.

## Method changes since the first report

- **Pre-set verdict rule**, and passes dropped by it (see [Linkage results](#linkage-results)). The first report kept every pass.
- **Control for exact keys: the neighbouring identifier** in sort order. The pair is certainly two different records, so its agreement is the chance baseline. It showed that facility cannot validate an AIH link.
- **Age control shifted by 2 years**, as measured above. Birth year (SINAN) keeps a 1-year shift, because it does not drift between events.
- **Results that do not depend on row order.** A first SP run gave 27,054 pairs for AQ → SIH and a rerun 27,065, because `mode()` and `unique(keep="first")` broke ties differently. After the rebase, the fresh lake returned rows in another order and moved three more numbers through `first()`. Aggregates now use the smallest value, the first admission by date, or a full sort key. A delivery counts as twins only if **all** its birth records say "Dupla/Tripla" (tutorial 6 took the first record). The notebook was run with every loaded base shuffled: every linkage, uniqueness, validation and summary table came out identical. Only the illustrative "exemplo" columns of the column check changed.
- **`ligar_em_passos`** takes the shifted column and delta (`deslocar`, `delta`); the default is unchanged. New helpers: `vizinho`, `pares_por_chave`, `comparar`, `resumo`, `veredito`.
- Validation is computed over all pairs of the cascade, including dropped passes. The verdict uses it together with the chance estimate of the kept passes.

Limits the first report listed still hold: one year, deterministic keys only, and a control that measures coincidence, not shared data-entry errors. Two limits are added here:

- The SP run lacks BPA-I, professional services, AM, CNES and RD 2023.
- The rejected-AIH result differs between the two UFs, so it should not be generalised from either.

## Dictionary and library gaps

Opened as GitHub issues on 2026-09-23:

1. **Import fails on one undecodable byte** (CNES ST SP 2022-12 `ALVARA`, RD SP 2023-08 `AUD_JUST`), and one failure rolls back the whole batch.
2. **`sia_psicossocial`: column `tippre` loads as `tippre  `** (trailing spaces), so the dictionary never matches it.
3. **`sia_psicossocial.tp_droga`**: combined codes (`AC`, `ACO`, `AO`, `A O`, `CA`) have no label; 362,613 rows in SP.
4. **APAC `ap_coidade = 5`** (AQ, ATD, AD), **`ap_tpapac = 4`**, **AR `ar_finali = 7`**, **SIH `espec = 17`**, **RJ `financ = 00`**: codes with no label.
5. **AR, ACF and AMP have no `x-decode` on `ap_coidade`** (and AMP none on `ap_sexo`), unlike the curated APAC dictionaries.
6. **SIH ER `co_erro` has no labels**, and RJ's raw dictionary has no code maps on sex and the other fields RD decodes.
7. **SIM subsets have raw dictionaries** although their rows are identical to DO rows on 87 columns. Whether the curated DO dictionary can serve them needs its own evidence.
8. **Impossible dates** in APAC (years 0009 to 9202), PS (1366) and SINASC (0980). This extends the first report's open item.
9. **Staging overwrites file columns named like partitions** (ER `ano`/`mes`). The values are equal on RR 2022; documenting or guarding it is open.

## Follow-ups

- Rerun the rejected-AIH and bariatric linkages with RD SP 2023 once the undecodable-byte fix lands: done, see the [addendum](#addendum-2026-09-23-rd-sp-2023-after-the-undecodable-byte-fix).
- Tutorial 6 still uses its own `rotulo`, first-letter `sexo` and `verificar_colunas`. v0.3.1 adds `odb.label`, `odb.check_columns` and `sexo_categoria`, which replace them. This branch only adapts to what v0.3.1 changed: `resolve_target`, and `decode` returning `None`. Switching to the library functions is one mechanism instead of two, and it is left for a separate change.
- The age-key linkage in a mid-size UF, between RR and SP, would show where CEP + sex + age stops working.
- Keep linkage helpers in the notebook until a second consumer exists, as the helpers session agreed.

## Provenance

Every file came from `ftp.datasus.gov.br`. The hashes below are read from the lake's `_omnisus_sources` table, identical in the first lake and in the `data/raw/` lake of the rebased runs: RR 2022 and RD RR 2023 (145 files), the 7 national files, and SP 2022 (134 files). The two failed SP files and the 12 raw ER files are hashed above or were read outside the lake (the ER files match the lake hashes).

### RR

| Dataset | File | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `cnes_estabelecimentos` | STRR2212.dbc | 5a3700a98a1e4eec7d8f1e6d0a5b942b5fffde82bd9b4240f90266c88e665c97 | 40,527 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2201.dbc | 16a2be14785bf96b574d5414474c6add029f34b87a0c292e73a4edbf4178136f | 2,348 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2202.dbc | 2dfa22a9a90ebe62535cff72f14499551e1e6004fc15b9e3f7e8cb6165453279 | 2,271 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2203.dbc | 022c005a937057731bab263e2ad62173c26a2b8005ed7110626c72eb2bdc0beb | 2,644 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2204.dbc | 2a04893aba4ae2642e441ba186aa0ac745a5375a4512bef6a6bb2de6c435590c | 2,524 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2205.dbc | 54535d22ae5e375b6b66447c9c557e964c59fb228548128f1c0e6b86dd7f0394 | 2,596 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2206.dbc | 24d5eebe08dff22f7f83b9b01b25608760712acedb77e7529d137a956fd925c6 | 2,368 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2207.dbc | cac652231f91b16509129d9eb48ac9bc362dee7ed52572e3bb442c44ee581315 | 2,530 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2208.dbc | bb9d7ace2e6c41edb08205f5d826533dd5306999b05755697d2b1813525aa142 | 2,447 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2209.dbc | a610680a54acaf64a76189803380f404b2dc0114074f83f15aaf0e70cb1d696b | 2,661 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2210.dbc | b317724e5d77c2314c611ea7d6dc7b9a2ef369936ac35b316be7dbb11ab55c2e | 2,530 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2211.dbc | c5558ce584da15fc7ff57559277401655a7d9b5cfe2a511861119922ccadef19 | 2,254 |
| `sia_apac_fistula_arteriovenosa` | ACFRR2212.dbc | 3115334daa5adc2d593e4d6eab65c0ff0ed5b0ef683d44cf0b6a500949978bf5 | 2,710 |
| `sia_apac_laudos_diversos` | ADRR2201.dbc | a539ff1e77545d5039f8d89aa6925fb35c99b96dead3ff234fdfe342b6f32c03 | 13,243 |
| `sia_apac_laudos_diversos` | ADRR2202.dbc | d76bb78868b511016f78b4d13b59b1d9312343ba058fd15197e28d385fffea2e | 11,809 |
| `sia_apac_laudos_diversos` | ADRR2203.dbc | 08f331439c987895ed06c3666a7959d024840a3e669d99778adb729b5079ead6 | 26,270 |
| `sia_apac_laudos_diversos` | ADRR2204.dbc | 1e24be3dae8252c5ed807f94e8df2ceff928b3de3b730ad07f2d5cd0adbe3e4a | 18,279 |
| `sia_apac_laudos_diversos` | ADRR2205.dbc | c98ba3a2f7e583d6c169de1783eb17409f6c1f37629b89cc92b6f6eda8846c43 | 26,832 |
| `sia_apac_laudos_diversos` | ADRR2206.dbc | e34127bbf1180f97ceb12b71f07dc946d8a5c5e4aef9e7f013d48ca70ccba69a | 21,268 |
| `sia_apac_laudos_diversos` | ADRR2207.dbc | 778cb50bcc287b38e0064be8f9834418f83d4a84c57de5df6f59887b709f81dd | 28,299 |
| `sia_apac_laudos_diversos` | ADRR2208.dbc | d20d3d7d5915db7baf3202493a293ae67f85f7a5e7d205410586fcf9e37c1cee | 42,725 |
| `sia_apac_laudos_diversos` | ADRR2209.dbc | a32a07856ab9594bd629a542c3d1b8459ec85b1e1795a3c432ddccc7105c590a | 63,445 |
| `sia_apac_laudos_diversos` | ADRR2210.dbc | 89aa7c2d91b12c3880f242bd5f02d094bf6e815628f3993a98298f14f680d045 | 44,726 |
| `sia_apac_laudos_diversos` | ADRR2211.dbc | 78738689f698280e61a39310b491e4c45fecaaa892de8f65e97629f22b336547 | 28,691 |
| `sia_apac_laudos_diversos` | ADRR2212.dbc | 099b6a058abd2506938a413b30e0699eae2bca93147f8e42464671e371befb6f | 12,648 |
| `sia_apac_medicamentos` | AMRR2201.dbc | 74ecf6fbb1f8335a15a1c014a64e1dac69e16f2ebdf377536596481113ac1dd4 | 62,418 |
| `sia_apac_medicamentos` | AMRR2202.dbc | 793efa6c7e3a14e3a06ab888301db043d9088e3c64985a7bef2e5f39ec9f11d7 | 60,210 |
| `sia_apac_medicamentos` | AMRR2203.dbc | 51ecd670c755437857e6105bbda6a0248c74d99af9112cdb21ca93ffbf896882 | 61,766 |
| `sia_apac_medicamentos` | AMRR2204.dbc | 14d34af284a17c3e9f886cdd1630d6c593461d57b1353ee6fbd9ece799ab6f6f | 63,770 |
| `sia_apac_medicamentos` | AMRR2205.dbc | a3fa38ce38661aeb23434824db12b065196a83c406717b7a9c76f3403cd7767e | 66,680 |
| `sia_apac_medicamentos` | AMRR2206.dbc | 0f2ca938cb22ff6a4c7f475f74955fca2cdafe6564a03fedb64ae9cdc5af33a3 | 67,613 |
| `sia_apac_medicamentos` | AMRR2207.dbc | 1755691dec29f3264b5f3b7cfde12acf7ca2029b2f1be91febc5aecb8c33aeaa | 69,489 |
| `sia_apac_medicamentos` | AMRR2208.dbc | 3ed8f35d8b7c9746308e67c34d2944ca17c146b0d31096bf2120ec335e806f29 | 69,460 |
| `sia_apac_medicamentos` | AMRR2209.dbc | 3573fb562057f6c5cdc612e5ea6a6d1acbc0ad9da65479d3005a707dfa0fd8c9 | 66,223 |
| `sia_apac_medicamentos` | AMRR2210.dbc | 1112fcf4d4cda1ab9797df26d4dbe1561e67694f0a03d2055725271b55266c22 | 71,483 |
| `sia_apac_medicamentos` | AMRR2211.dbc | 7820d88d5770bc91b6a25b7350037f4b75e3b3c6c65e68da3861b80a2fb77e64 | 71,260 |
| `sia_apac_medicamentos` | AMRR2212.dbc | 6a925302d2c780f88ced4a05a7f17844c9091e1520865da9c8ac877b2a9b39e9 | 73,785 |
| `sia_apac_quimioterapia` | AQRR2201.dbc | 5d23f54f0ca61d3e1c1ae68d9a64e56b0620da910901af3ccd76e5e1aca3c7bb | 25,982 |
| `sia_apac_quimioterapia` | AQRR2202.dbc | 323efb8b73955a7390806cadb63f756cf8d69598f051d81bfc2070df92cf0a86 | 27,452 |
| `sia_apac_quimioterapia` | AQRR2203.dbc | 4942aee9bfb29ce5240f2ebc9e22449d8e4246471d79f71544c0199f46fbc03b | 20,490 |
| `sia_apac_quimioterapia` | AQRR2204.dbc | 8d1c4ea200199a71b31a604bac20c3570bbbb947994881217d3160be0c696871 | 30,401 |
| `sia_apac_quimioterapia` | AQRR2205.dbc | 2dbc306d6a6432bf2e57fb12ddb092cf189f981517dbe81f50dfd6117949c99e | 21,968 |
| `sia_apac_quimioterapia` | AQRR2208.dbc | 02bc3b094f9bc131dd6aea5b5157fa5c1c94319e10c68273cb602736070c0cf8 | 20,149 |
| `sia_apac_quimioterapia` | AQRR2209.dbc | feab4a8860899865bfd9a675e9f0e3370c345aba6cb014de23be7cb315f77942 | 20,780 |
| `sia_apac_quimioterapia` | AQRR2210.dbc | 135918f047b568f777e34907f81ee4f107e23fc013c4fbaadd799cb0d2b0c5d0 | 21,276 |
| `sia_apac_quimioterapia` | AQRR2211.dbc | 1b1d217ad07271e3c722c077bb1a04cc202a0b756185d7e8996eb7cc1a18c525 | 19,996 |
| `sia_apac_quimioterapia` | AQRR2212.dbc | f5a0f6774f67961c08952101aa2b2e995e9d8786c2a11144707129a05f8b7b72 | 18,540 |
| `sia_apac_tratamento_dialitico` | ATDRR2201.dbc | 93ef8bb3afd46206ee3d11705e311631940681b2ede846f64fb989e0a3f760c2 | 18,096 |
| `sia_apac_tratamento_dialitico` | ATDRR2202.dbc | dc261f77d858bc396a3099f9cffed71f1841d99e337b9f39ffaf94f76bda7a92 | 18,341 |
| `sia_apac_tratamento_dialitico` | ATDRR2203.dbc | 0f2ac7c552067e7d21d15a5836e9876222ac05eda2dcb5d1cc5c1f0950a24402 | 18,326 |
| `sia_apac_tratamento_dialitico` | ATDRR2204.dbc | b45a3582fb58f8ff35919279822088349dc48274ef45b8400df1377287ca47cd | 18,044 |
| `sia_apac_tratamento_dialitico` | ATDRR2205.dbc | 01dc80b1250b1be4f04a1169be4dd4f1a5ab27695fc97b9b67a9a4bebb777b38 | 18,896 |
| `sia_apac_tratamento_dialitico` | ATDRR2206.dbc | be757f73db877645eef37e9b4d11859482a8cc3e8bbc185f8efb40ad7238392b | 18,488 |
| `sia_apac_tratamento_dialitico` | ATDRR2207.dbc | c48464374d1ef6882a0587a6bc390c2b2ca109ef70daf97f65af60feec22b7fb | 18,155 |
| `sia_apac_tratamento_dialitico` | ATDRR2208.dbc | aa64f5f188d6bca108c5cbddacf7a0c1bb1edba6f852a1f8e40c16777625a2ac | 19,913 |
| `sia_apac_tratamento_dialitico` | ATDRR2209.dbc | 3fa44c145ad7a3d4c1c8ef8849633139117a38b995edfadeb5706c03225d48a8 | 19,315 |
| `sia_apac_tratamento_dialitico` | ATDRR2210.dbc | bd5d8071587f23dbccbc633d67c3082001529e45694af97898b2fe998a1602a8 | 20,210 |
| `sia_apac_tratamento_dialitico` | ATDRR2211.dbc | 3f8809704587c42dd8f8871a1db7649b52ee6360329f6ba33b0cbfe6744ecf7f | 20,306 |
| `sia_apac_tratamento_dialitico` | ATDRR2212.dbc | 1e4c841260cd634bfb41a052218033c4896c0312c3200929cba7c2c30549d905 | 20,759 |
| `sia_bpa_individualizado` | BIRR2201.dbc | 03d41d139dd970f25a565471053a5459f7cd77ef7d2633a63f33db2f8725340a | 766,384 |
| `sia_bpa_individualizado` | BIRR2202.dbc | e9d359f1422add2c1b2cf0be707c9a88ffba7c2290d0e7fec9edf5bfffce2b7a | 763,985 |
| `sia_bpa_individualizado` | BIRR2203.dbc | 0b6ef6b20ab1754d42a1ee6c0f0a2ee08814f4f32ecfbcd3c899bf3edcd47c82 | 940,207 |
| `sia_bpa_individualizado` | BIRR2204.dbc | 1f84e042c436e5cdeee724e8e81f2dba3e7d26b3aad22b67b076baffca0c0c63 | 854,400 |
| `sia_bpa_individualizado` | BIRR2205.dbc | 99cfc5ebf78e25000632e9428d2bad463ab4c6e5fbea1e7ff00721e9d50ba300 | 1,178,856 |
| `sia_bpa_individualizado` | BIRR2206.dbc | eb6ab2df7c137c2b0c3f323f6a6a38e029b861d39956691749ec2b7089d25616 | 342,523 |
| `sia_bpa_individualizado` | BIRR2207.dbc | bf1c0d7196639f707fe8a49229426d7798a03b845626e318eb66a238112f1eda | 1,141,592 |
| `sia_bpa_individualizado` | BIRR2208.dbc | d5e88dcbfdbd75a5a04adfa14c8fb12fa888a41fe3c72dacdf94eb5a32e1fedc | 1,352,697 |
| `sia_bpa_individualizado` | BIRR2209.dbc | 28e0c18eb2e12deba6ab378d14e22e257d22aa956f6f8b5304df506ac487e4b4 | 1,128,514 |
| `sia_bpa_individualizado` | BIRR2210.dbc | a9c234f7bbe36e545a6a14db36a16e89dc86d790f6c349ae3bd3a1bccd07c195 | 983,373 |
| `sia_bpa_individualizado` | BIRR2211.dbc | a3335858c684feb66dba96b48f913784085b8953ac23a4a16f539c54bb96fb4e | 1,091,595 |
| `sia_bpa_individualizado` | BIRR2212.dbc | 0045b4d3929ccf5960aa5aa16f0ba0b9eae4ba7d0ed0a7c7d92e9858deee4e83 | 938,791 |
| `sia_psicossocial` | PSRR2201.dbc | ec112c52f64e247c6ce9ea0cab0967fbea89d12ca399583d250ef633a16dcb7b | 32,577 |
| `sia_psicossocial` | PSRR2202.dbc | 20aed048b3ce4b0a822254b8d482abd471d7963ec32ea7cf263f32436bc7f665 | 41,538 |
| `sia_psicossocial` | PSRR2203.dbc | ea01d254219010757891d3ec95adfe839815082a4836fb4fc1e6dbec2182b604 | 51,566 |
| `sia_psicossocial` | PSRR2204.dbc | 7df8935e01be3f3a0132b46314d27971829f0f2d5734cf8c9e59911f11f5bf0e | 23,389 |
| `sia_psicossocial` | PSRR2205.dbc | b7365a2337572bcdcfee9ddbae3644aced941cfb2dce1153c93fb951198f552f | 49,766 |
| `sia_psicossocial` | PSRR2206.dbc | 31b7452bef46da244253ed1ee2f17ec4536e285a61e60303311b63a60021a24d | 44,833 |
| `sia_psicossocial` | PSRR2207.dbc | a6f6cf6350012793f73fcd6b9a932dab35011ec995cc62ec8298af85691fce6f | 33,130 |
| `sia_psicossocial` | PSRR2208.dbc | af22b4bce3e91e1fba86efc549abc84a7c99e5fb4499e5a48f9cd0cc4ca48d64 | 32,643 |
| `sia_psicossocial` | PSRR2209.dbc | b8f5ee04c728d2496fb3f02d93b643e2d65b8b3f539c51fc7cda61791b9dccd4 | 36,487 |
| `sia_psicossocial` | PSRR2210.dbc | 77dfb1a403937d1ddf98b158b3a1cff0c37b805641610f0ac66c2d90822ee0b6 | 29,605 |
| `sia_psicossocial` | PSRR2211.dbc | 0c7373f4e2970de6dae78f74973e2f8766fc4cd9712971ef62c391e5368a8c4f | 36,289 |
| `sia_psicossocial` | PSRR2212.dbc | 33ab10fbb8a3619d39516a0046e3ecd613173586d4581fc3aaf0a82249f95b23 | 31,538 |
| `sih_aih_reduzida` | RDRR2201.dbc | 00c5ee1079dca6d947892b221851693c0c1f13d60ee14d3ec1be3a8932dc7d55 | 265,559 |
| `sih_aih_reduzida` | RDRR2202.dbc | e6207cbeaad1d20dfc6ec5a3dcd6070bfe4dd58e0dff25fdd4041945cd671832 | 252,712 |
| `sih_aih_reduzida` | RDRR2203.dbc | 5ccab0c5af5bf25e69e97d91beb16637d9db1ed8ca944d74f435e380db6334f3 | 309,582 |
| `sih_aih_reduzida` | RDRR2204.dbc | 433b97deeb0fe0a74a481d1e6377bff66178f9eba06bc9cf992d486917fc2cab | 292,263 |
| `sih_aih_reduzida` | RDRR2205.dbc | e7f867bcfd4c51feb0c79ab322e3f613ab4c07baff36fb31b57f93c7177a00e6 | 325,659 |
| `sih_aih_reduzida` | RDRR2206.dbc | 22fea9cb1c5517d2c79de4d620cbf234be9715c2c78fcad54d7c68c38e9c2b77 | 50,318 |
| `sih_aih_reduzida` | RDRR2207.dbc | 246f920bbd2f9a7f5b98597a280d75108d6276eccf5967e2b73b0f22092db80a | 308,161 |
| `sih_aih_reduzida` | RDRR2208.dbc | adffac19f16c5e98cb3ef543ea2bb18c86dbc7443dd0baeb8aa09672bac80954 | 368,638 |
| `sih_aih_reduzida` | RDRR2209.dbc | fe2b8399c0743c82050743bf1b293c1e3ffa1dacd3d2e095889cbf49b12b858d | 300,510 |
| `sih_aih_reduzida` | RDRR2210.dbc | 6f18774b0c19491ecf31cab908d47b5ddb862282edc6a21441eee5dc50dcb2e9 | 352,598 |
| `sih_aih_reduzida` | RDRR2211.dbc | 9e0d65d02a140e03afe6c6c35b4076ca2a8b8cb9c658ae7da2625dae35bb1662 | 334,610 |
| `sih_aih_reduzida` | RDRR2212.dbc | 4a665f136f34c2a8a4eccc317af4593a4999e624d24ccce2b359b42b6e8582e9 | 329,543 |
| `sih_aih_reduzida` | RDRR2301.dbc | e9f717ff378477a883d19f733efe8409aee7f7795a027584b9f383364264d8e4 | 349,244 |
| `sih_aih_reduzida` | RDRR2302.dbc | 2a5ef1d64ab304643d78ba017bfcf2743045ca59b409878f5e2bbb151bfa50e2 | 297,649 |
| `sih_aih_reduzida` | RDRR2303.dbc | 867568bf115de612649900cb0768171d6aae11ea5721a1ff6dd6625d6cfb49c6 | 338,974 |
| `sih_aih_reduzida` | RDRR2304.dbc | 9630ae623f67ae1b048ed7a5a8b4611b45fdf2cb363bb3f1511662b33cff08a5 | 334,342 |
| `sih_aih_reduzida` | RDRR2305.dbc | 070095ba8dfb7eae48fd32151827ebd1ac1a08880d248ee9f11135f524f86432 | 295,832 |
| `sih_aih_reduzida` | RDRR2306.dbc | 276950c6e444be8c7dbd4db0bb4c72102af9acd99c301d018ee9622133363942 | 292,318 |
| `sih_aih_reduzida` | RDRR2307.dbc | 554c7fe24595ddd67995426cf2e56540aa502b8470ef8e896ea59c1a581ed64c | 321,728 |
| `sih_aih_reduzida` | RDRR2308.dbc | df1511b117a712f4812947e9ab79714cf3e1e87177efe9b717ebe31a4e49e8a5 | 347,846 |
| `sih_aih_reduzida` | RDRR2309.dbc | 76575dee8d2168dc5022bf46b420ca93e41109711e972e7527e39380c93dbd1b | 119,285 |
| `sih_aih_reduzida` | RDRR2310.dbc | ca61a398b9ec92afeec48e2dfe9f85012f0a9e928c0ccb9877ec7ec34ebe29ff | 166,954 |
| `sih_aih_reduzida` | RDRR2311.dbc | bdf3d83ba5d51966f051980b4a0df2d14b2adc58695888e280d44eedd14ba199 | 275,988 |
| `sih_aih_reduzida` | RDRR2312.dbc | 89aa6c94bf266f3952c4dee9a16f0181602c533f8d6426a7f95f6a0fd0a16e1b | 259,816 |
| `sih_aih_rejeitada` | RJRR2201.dbc | 6dd3650dbbf200565b8ed097e6b6d8aded062fd7bc53bca4399703c8652e4ce9 | 3,858 |
| `sih_aih_rejeitada` | RJRR2202.dbc | 655216303f19917b7ab89118f49c4627cd9ab1ac7732e89bd58047e28da25add | 4,067 |
| `sih_aih_rejeitada` | RJRR2203.dbc | 597d0be524f23859d9461de219049be5c92108cc2c06f92155029c382b889dcf | 5,030 |
| `sih_aih_rejeitada` | RJRR2204.dbc | 6346c2d723b8e12eda205b2442274c78046614ec1fcc85c1836b13e712ec4552 | 4,585 |
| `sih_aih_rejeitada` | RJRR2205.dbc | 77729422fd7b11b89201bd5992d8a2b3a4c55bb34785850c7d1177e2c4bf2058 | 4,345 |
| `sih_aih_rejeitada` | RJRR2206.dbc | 44764ca9b0490a5ed2e8a04671fb676f04e2b36a326932212a747ebdd8a37ef0 | 3,844 |
| `sih_aih_rejeitada` | RJRR2207.dbc | 7d6d7466479a72d1383235fae58dd5672d9f48ca216324c1a13b06575bc2d76e | 4,674 |
| `sih_aih_rejeitada` | RJRR2208.dbc | ea99dc2a8aad67490d09eda285f964e3fa7e764d3909af34d15fe43b040f6ec6 | 5,052 |
| `sih_aih_rejeitada` | RJRR2209.dbc | f38f54a8ae2741632939b8ae3123e45a857fb6456585c594092b02810c352877 | 4,011 |
| `sih_aih_rejeitada` | RJRR2210.dbc | 6618097b1ea346cdf42af335abf7df97e75a379f698c6c97a92aad2908ef13d3 | 4,621 |
| `sih_aih_rejeitada` | RJRR2211.dbc | adda9a55950023b223967729920042ce6d14397f06b11388320d8b26f55f2534 | 4,581 |
| `sih_aih_rejeitada` | RJRR2212.dbc | 4e18352041e06ff53fdd4264d34e660ac47b8b9acf9e95a57a9a1b516007da6e | 4,814 |
| `sih_aih_rejeitada_erro` | ERRR2201.dbc | c0aaf6fd53f80a4e50ad6e280770162e593a06f6103fa08c5268769f4e170316 | 837 |
| `sih_aih_rejeitada_erro` | ERRR2202.dbc | 048672358d5ad0714f20918a546f580854266dbe524db94926698c06b584e80f | 882 |
| `sih_aih_rejeitada_erro` | ERRR2203.dbc | 5622c27428bb776790dbd736a56180205e3b04611f56fdc2b7636d0fe52ea4a0 | 1,270 |
| `sih_aih_rejeitada_erro` | ERRR2204.dbc | 99435115d62ebe747c731a2ca2bac0521801fe8bc8e8dbba5b32943e239038fc | 1,086 |
| `sih_aih_rejeitada_erro` | ERRR2205.dbc | 79cb846c1032863b982fc9f788decf7c9c6ed854d93eec2d6b027833ab13a3c0 | 1,009 |
| `sih_aih_rejeitada_erro` | ERRR2206.dbc | 8c1c6e64dc8ca72e013ba83ffa9cbcb0009b5af6f9f6708f7379f6723f1e46ac | 784 |
| `sih_aih_rejeitada_erro` | ERRR2207.dbc | 0fb326aa1f0c0abd0297b7256632acbaa3535910d07d412f1936ed2f820c4e58 | 1,124 |
| `sih_aih_rejeitada_erro` | ERRR2208.dbc | 4d05a4ff38491cbce2c6e22ac784aa5a80bba9c741422da2bb52b884640ea1e2 | 1,270 |
| `sih_aih_rejeitada_erro` | ERRR2209.dbc | e9794b7fc3b5012c9cab074fe084c10e7272a9a27a1dad815e56bfdcf8eed7bc | 879 |
| `sih_aih_rejeitada_erro` | ERRR2210.dbc | 629077d5b339957498779fe3b3d9bc55d88a04597c2a674356168d8a64da6929 | 1,075 |
| `sih_aih_rejeitada_erro` | ERRR2211.dbc | 64e183a62f87f042b708c9f7c3a659c04cab40cbe73007d370ef8f39c76d1f28 | 1,055 |
| `sih_aih_rejeitada_erro` | ERRR2212.dbc | 213768eae176e3968fe4a81c816604568b92c38e56f2e1cd1e4364d650afca45 | 1,116 |
| `sih_servicos_profissionais` | SPRR2201.dbc | 2fdba7249812f6bdbfe3ddf9f047768c3f7c5b2d9eabb0c77783059351157db0 | 1,095,846 |
| `sih_servicos_profissionais` | SPRR2202.dbc | 9779f90cc0e6709db52aa25fa6741401ebfe8d1ad6c49e68946ce4c81a4de6b2 | 924,748 |
| `sih_servicos_profissionais` | SPRR2203.dbc | 7176a753fb787451bc74f9d87445614cf5c8c0d3b2b773d42347995f780138f1 | 1,119,978 |
| `sih_servicos_profissionais` | SPRR2204.dbc | 6b7843d0acf9326a13af8b18f6fe331557b0f4525b883049d07d3d75e243de49 | 1,098,231 |
| `sih_servicos_profissionais` | SPRR2205.dbc | db285f7f7c955444ec52ba4ac47ea0851c26e97307c868df36bfac09a8e6c313 | 1,176,585 |
| `sih_servicos_profissionais` | SPRR2206.dbc | 08120b932fc5aec106f26d1e37f71cc21f5478d69012683d90a88638b5575f40 | 229,491 |
| `sih_servicos_profissionais` | SPRR2207.dbc | eb2fdfc89594dc0a043c668e8bb0c86af74e7d0d52d27a6e4b77d792f9b995c8 | 1,120,891 |
| `sih_servicos_profissionais` | SPRR2208.dbc | 14f5e95f9f971f6d70bdf544e81a3c3b3c8e5f2a32bd5c79af23768433642712 | 1,327,469 |
| `sih_servicos_profissionais` | SPRR2209.dbc | a2bf38294abaf0233b9a4d7236409b688eccad13a0bedde1be75ed534faf206d | 1,243,739 |
| `sih_servicos_profissionais` | SPRR2210.dbc | d584d787a3d84b107a1f999825e98fa542f865a67b631c5ebcea0965f71bbeed | 1,325,440 |
| `sih_servicos_profissionais` | SPRR2211.dbc | f88eda9961e8954175e149b8d17f7770f49a213c1955593b9d90c514b5e6cf91 | 1,325,182 |
| `sih_servicos_profissionais` | SPRR2212.dbc | ea0bd7285e4caed5ad5b6bcc9edc54c3b89f46278ef39def724e90bc5d264e30 | 1,267,436 |
| `sim_obitos` | DORR2022.dbc | 6643344fe1ab587d648e5e0ea8cf7e3ef9e5b5b7021a12dcbbc54f5724d2ec65 | 275,221 |
| `sinasc_nascidos_vivos` | DNRR2022.dbc | 55edaa6508cb58cc35e8ce7a74d5950198d91dd3c5c4c64d9e0c8199667601db | 641,046 |

### National files

| Dataset | File | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `sim_obitos_externos` | DOEXT22.dbc | b90fc92e0415af8311837271c88daa4068c35ad0775a883310ffe5912c2a5257 | 13,596,870 |
| `sim_obitos_fetais` | DOFET22.dbc | 6ff6b37af75b7f702b544913c67134c00469e00c571cabd82565688c57eb3ef0 | 2,710,646 |
| `sim_obitos_infantis` | DOINF22.dbc | 86af1c7dcf7d6dea2077de3572568023387bf625863cfed1d14114fe6d94a9fd | 3,582,690 |
| `sim_obitos_maternos` | DOMAT22.dbc | 3bb7758c7c70a53669978fc833df5a451616ab92bec6dd966e95dc73e7858f40 | 165,685 |
| `sinan_chagas` | CHAGBR22.dbc | 4dc491ca6904ad48e89d86ab4d794fb8ae6e6074addb5a911d521d73fcb8f60d | 408,082 |
| `sinan_hanseniase` | HANSBR22.dbc | 2db872dc3cf6ffa8403f69549d6463e7ff5c165af39e57d96778c60c7292b7c8 | 1,708,109 |
| `sinan_tuberculose` | TUBEBR22.dbc | f1690ddb28aa28687d00ce9a3ce0c6956364c92098acf447ee123d44492a071d | 5,691,427 |

### SP

| Dataset | File | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2201.dbc | 0a9d736c5ee0ac0b6e2fd887a0bbf6738e394b190ade3dbc87a1d33c4fca8e1d | 29,241 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2202.dbc | 6b811bb57a0e89cc5341acc35c1dafe715257dd9294a8dc9429e20b2f50ffeab | 31,657 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2203.dbc | ea846db69d2216eab329ec43d30256a0086bd38d20032f3ff00d503b59cf6028 | 29,548 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2204.dbc | 7745f534ff9f9d06b87c8d65961ac1ab68cd544aa73f9e591db1149150db7370 | 32,982 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2205.dbc | 7b336da65a6d9192d2297f74de13d31131ca8c932bda2e24f51030bf727ef7a1 | 33,226 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2206.dbc | c318e6199f873d51ab8f5cd63b793189f709a44a6dd623101958a48a729eed1d | 33,584 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2207.dbc | afcdae6a48f3a30a80fe1974eea19e864d9182e6f7651bf23b2bf490eccb6ab2 | 34,454 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2208.dbc | 62f180b042c35d537cfdfb528a1ddc1222461a192624710972b53c818b77b89c | 35,350 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2209.dbc | e0c5b8542d1e222a514096f5dba1aba78500c5fe0d261e9ad4e7b98605924c7d | 33,877 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2210.dbc | 881233bd43e93e04260435500a32f4715bd75ae4392fe23e5f9e203b5a9a7b80 | 33,202 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2211.dbc | 956e27dde90a2f8230222757a1b39bdb659403400b3b95f04587862f8cf7e00c | 29,925 |
| `sia_apac_acompanhamento_multiprofissional` | AMPSP2212.dbc | 95aeb3c38fd012db3ca83c035037913ae5df9a18029a5e356a9d65ada14db613 | 34,684 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2201.dbc | fa8ba8b39ec48af8bec86a5d7ce5c30b708491fe7f789cccc08ba16798d07103 | 40,992 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2202.dbc | 4120569b652533ba112998cce880dfbc2dc54ddf1ce0195a5073be4b28c443dd | 47,174 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2203.dbc | 63629789bb0b92488b9740193b4d5963ea427bd1177cc593b503af0af43e51c5 | 49,349 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2204.dbc | 48f3108a60e8e9d8b6f306c744d50e78fe3eb8f396661fee5e0f3aac1c947ed7 | 47,830 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2205.dbc | 96c627118bafa4b33e5a74284ca89fa942e69814100560f86afbc9afd1c8d7f8 | 50,673 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2206.dbc | 39ee171f183bc357af5cbe79f89d401c2ed876c012a8549420a16ddc65b4b978 | 49,201 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2207.dbc | ef0c19f15cd9dc615aad18c1eea27bd94471b21b2e854017331d2e4085da04ac | 48,039 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2208.dbc | 1af036c3fefa755973f237e30748aed461ec9f0e781bd84a5d3a2f99a331e9f9 | 50,997 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2209.dbc | fa1b3e96fd6a53e02645311e743a6fc2602af9adbcb7e6d43dd16f71f7c1d864 | 49,843 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2210.dbc | ab4cff8a32ad68c503edfb69f3fc174b04d8f27233ee7f55c48edceaef6665c1 | 51,154 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2211.dbc | ae05f1f6b63a024d138d97acae2ac9ec58c52a2eceaf7e63f72739a425676593 | 44,852 |
| `sia_apac_cirurgia_bariatrica` | ABOSP2212.dbc | 931b8ddd8ed1ac78dece7d5b0161546034ccd73915f04238a51455ba194613b0 | 49,405 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2201.dbc | df67ac386760ef3e64d91acd7a722be1513ebcbcc7890583e9e7ece22c864e1c | 32,518 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2202.dbc | b9c54de636b4d38f83eff7d9e58fb85b6495c49b63b04a97b82ed2f5479bd969 | 33,688 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2203.dbc | d77183c0650afd16d9170acde5fec7c9774add33fca45765a4e59ba46045d07a | 40,972 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2204.dbc | 7e5d133f6a6ab7aa92db0a57ac9b0bed8c1eeaf1be2b285f0a6cdccdbec4d0fc | 35,767 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2205.dbc | 5d239e0df1d3a9e95a4813be7e1244f00d40350f567abfdaa40f679bd4d7f389 | 38,565 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2206.dbc | 3330812ca4a8658e599486242f3aa6b9e3d1e4aa37109f91ac6cc950f2c7be7e | 35,828 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2207.dbc | e230c14d69247a052bb64d961417a568d02a763eeef08df3195f763c9471fc9e | 38,581 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2208.dbc | 46b6bc2aaae27e22d785c9b917ba439d2a122892cdd774004e50e0e57e0e6962 | 44,942 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2209.dbc | 2814870538da7a7ec749d3bb15ddfd80a0383550effe019f8168f003970b1543 | 36,798 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2210.dbc | db27cb3e3fdf7396a244169fda45c28f7df5c9305bfd4b3b157c377ff640e5ea | 39,417 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2211.dbc | 1dfd682b87ff682e8e3e3f313338dd9e436a32f274194f42bffec224c75e34be | 38,699 |
| `sia_apac_fistula_arteriovenosa` | ACFSP2212.dbc | daf54348c189afdf5bc5d427941f6ee206b35866426ee3c3c0b133295d9dbec9 | 35,140 |
| `sia_apac_laudos_diversos` | ADSP2201.dbc | 90989ad3acd7fe0254cb6038d3899d6fea43068a2a430d9f6a9ff12fc7b6de3f | 3,166,032 |
| `sia_apac_laudos_diversos` | ADSP2202.dbc | c0769f094a9b71d9ec6290c0640c04f8d9b58806c37cba50f55cd3d2584f6b8f | 3,378,091 |
| `sia_apac_laudos_diversos` | ADSP2203.dbc | 02b5d02bd7279a9697f1eeb351bdbbdfda2a47b005d3aa75d1ff2f6d49305a86 | 3,668,199 |
| `sia_apac_laudos_diversos` | ADSP2204.dbc | fb5267213b2970a8f2bcae047db0dc7a5766b77518b19ff51dae545412ff33b2 | 3,580,165 |
| `sia_apac_laudos_diversos` | ADSP2205.dbc | 14beea5148cad2606e677a4afbac8a19ea74a87d97c5cb7e09ed779959a19d56 | 4,076,426 |
| `sia_apac_laudos_diversos` | ADSP2206.dbc | a5064354ad59609425be876755fec5344ae53da8207acac228b36773576fb5ea | 4,158,945 |
| `sia_apac_laudos_diversos` | ADSP2207.dbc | 72cb0c9ea8b27550ac6c4732faf33e61efa098afc5d2cf02be70d07a8eb8c9ec | 4,078,676 |
| `sia_apac_laudos_diversos` | ADSP2208.dbc | 2fcff3c5a87d86208f517aecad5068d8e01adb92627ebaca4812a70e211208c6 | 4,635,883 |
| `sia_apac_laudos_diversos` | ADSP2209.dbc | 9e1d8c9da0b10fe2166a236a291cd52e220dadc8386f0b6f39444c6e19e3c423 | 4,274,213 |
| `sia_apac_laudos_diversos` | ADSP2210.dbc | 50f7d8d7d5a33be9c378aba835ee96c8cef9cca91add16d382626daf9d7b2bfe | 4,098,821 |
| `sia_apac_laudos_diversos` | ADSP2211.dbc | 3cea2f231392e663652c9032a31a9711846dbbdcda7f7ae3934630c777c78799 | 4,145,522 |
| `sia_apac_laudos_diversos` | ADSP2212.dbc | c0e186720cb35f84ab7078330ee1956fbd90c70cbbc8798c56495e4ce7f33bcb | 3,955,288 |
| `sia_apac_quimioterapia` | AQSP2201.dbc | 65d35c42e2f9ca42387777f5eac10a1e6b61d39d38cc5ff5bf9338e6c1b4cc6c | 5,498,577 |
| `sia_apac_quimioterapia` | AQSP2202.dbc | f6d61fb1aec59efcfbf719a750b53294aa851980adf7ac7010c0961e6b35f96a | 6,947,189 |
| `sia_apac_quimioterapia` | AQSP2203.dbc | 2cc491a6b54a836ea7ce2f95ea507e190fb67063ddcadf04e35903b31093c515 | 5,605,348 |
| `sia_apac_quimioterapia` | AQSP2204.dbc | 8de3c2e30b5f3a708368e23f0c285a86fbde1264f63f1535c8398e94328b762f | 7,262,560 |
| `sia_apac_quimioterapia` | AQSP2205.dbc | c8b175c0361bbb9cf05bd44547a002f6f5da38f49f9edcfa0606c4713de5ce43 | 7,874,561 |
| `sia_apac_quimioterapia` | AQSP2206.dbc | b1d77aa3d51addce416cf269be8fe070f8f918b0c1bb76ad45263d6c315fb7e3 | 5,689,578 |
| `sia_apac_quimioterapia` | AQSP2207.dbc | e4cb93428eee18333ce51db5f383d937bb55aea283dd14d73ffc81926874cfa9 | 7,435,857 |
| `sia_apac_quimioterapia` | AQSP2208.dbc | f3fc0024e2cbab82cecd142a6378444e81f336eb5e8bb888ca9c578b4a1be5bf | 7,375,027 |
| `sia_apac_quimioterapia` | AQSP2209.dbc | abed1ef0ecef180ddaacf4f9a68b5861361eadae8f013afaf975ff9bef5f71ca | 6,251,825 |
| `sia_apac_quimioterapia` | AQSP2210.dbc | 2342bd11e2de162497735ae969b0684544f5605aa3d07861ee2e1454391fbd1e | 7,280,698 |
| `sia_apac_quimioterapia` | AQSP2211.dbc | 924cadfe487e0e7fac611fe1e7552c3c7f773945ae4e060cdb0f34bd95c63edc | 7,302,477 |
| `sia_apac_quimioterapia` | AQSP2212.dbc | 9d5fcf26cd9d03f8ca43cccd4e144461481988faff7cf06eabb325b48de3552b | 6,962,851 |
| `sia_apac_radioterapia` | ARSP2201.dbc | ffff38fd87650d67cb2a21d2526d9bea600c03090b266a5a1db6ed894b2c634f | 229,013 |
| `sia_apac_radioterapia` | ARSP2202.dbc | cd98e4152ca13394db5655dd4f77dbd860cde4984fcec5f769929f53149e5bae | 228,144 |
| `sia_apac_radioterapia` | ARSP2203.dbc | 7a89ec3af8c441e5c97d87c57458388a963df096c1163f421bc60c760bc6172d | 262,293 |
| `sia_apac_radioterapia` | ARSP2204.dbc | 37cb64c4095a0a56c388bbf88f26a43322a577a3e6e3ea92fb3d5e43883f00e1 | 237,888 |
| `sia_apac_radioterapia` | ARSP2205.dbc | 3be480b5dbd2cd82d0826cdf5a0fa94c05945076f4b426cfe22114aecad58324 | 264,199 |
| `sia_apac_radioterapia` | ARSP2206.dbc | 0038d88a8f42c010129d56396cde0c15316b760bd2d7f23a8a9c2ebcad716685 | 223,176 |
| `sia_apac_radioterapia` | ARSP2207.dbc | 02e6d4c72be36c415c9cee182d8bcde17ec5af3402f8c63ac511ed09bf54b50c | 262,317 |
| `sia_apac_radioterapia` | ARSP2208.dbc | 8db41ceac92bba94ac7258021ab9d09f6638b06f5b5376e96d6bdc7dc94b3b90 | 302,406 |
| `sia_apac_radioterapia` | ARSP2209.dbc | f21e3956b54fe5f237587e627c05858d012677bf30e92ec3057a92f3337e611c | 280,754 |
| `sia_apac_radioterapia` | ARSP2210.dbc | 040b002c9bc2ce7d2498bb297626df09759267c3fcc34516493657c2c5a63569 | 267,459 |
| `sia_apac_radioterapia` | ARSP2211.dbc | ba36d879e09fc777f1fb1e0085a3d0d421f8d938d289f784fa3aa2bd3eba2ef3 | 262,429 |
| `sia_apac_radioterapia` | ARSP2212.dbc | 12462afcad1e206bb736e138fef880d47c4012cec8c013396c4d267dee38cd3c | 271,155 |
| `sia_apac_tratamento_dialitico` | ATDSP2201.dbc | 6daa43ccd5028d7859b650194881b7f9be76bf34d945b22fcd4d073cb0ad34bd | 1,689,055 |
| `sia_apac_tratamento_dialitico` | ATDSP2202.dbc | fbea4d4b5fea1e8b8b620120fcd0ea0decc485536b5a82bb12c50ced89e75f50 | 1,637,586 |
| `sia_apac_tratamento_dialitico` | ATDSP2203.dbc | 76deba625d62962948459d963b911ead581898e83c787222008663013045a601 | 1,631,232 |
| `sia_apac_tratamento_dialitico` | ATDSP2204.dbc | f27420b8f926b74ce65bb740fb1e1ad094a6518624e88c96a4a87616e8fc777e | 1,658,479 |
| `sia_apac_tratamento_dialitico` | ATDSP2205.dbc | 783e3f4dd7f95211c83e6f07a8b01fd57cfc0af27e6a7a1e896d876e5d13c905 | 1,618,642 |
| `sia_apac_tratamento_dialitico` | ATDSP2206.dbc | f538921281ac72f00bb8155a5ffd0e2594fdd7ff357fcc14a88db4ef76add47d | 1,673,159 |
| `sia_apac_tratamento_dialitico` | ATDSP2207.dbc | 8779e2e9e0715e4eeabb4393f8c728efd98a600e0875fef79a5b817d557f7268 | 1,656,087 |
| `sia_apac_tratamento_dialitico` | ATDSP2208.dbc | 95fa06aaefcf23c1fad172b6d1185b666926b3584bdd36656687e8d60e595f17 | 1,656,453 |
| `sia_apac_tratamento_dialitico` | ATDSP2209.dbc | 7438ba40f960e77f8a9b04d2592c7a7ed08181cda89ac4372d5be462608f35b0 | 1,655,544 |
| `sia_apac_tratamento_dialitico` | ATDSP2210.dbc | 9a246601d88e907bf3c2294df22bdec4ff7b51e304d9121190fd6df54309a6b3 | 1,669,156 |
| `sia_apac_tratamento_dialitico` | ATDSP2211.dbc | 6e7d525b4b8de0a1fdf2674276e636bbd3b255671f429df7dfbe310e14f4876c | 1,620,552 |
| `sia_apac_tratamento_dialitico` | ATDSP2212.dbc | 06a4af1cb3a153d6e534340fd038ea9b139d17eedaa13e1271953fb668e2b5ae | 1,688,975 |
| `sia_psicossocial` | PSSP2201.dbc | 7352c1a8a556a3637c96488ac9531147900283004397549752369a8d70e1c117 | 4,824,408 |
| `sia_psicossocial` | PSSP2202.dbc | a33b2eac0fdf1b46a82d534a4ec7e984a3dd2d06c742657e946fdb437569fd04 | 5,372,119 |
| `sia_psicossocial` | PSSP2203.dbc | d283aa168b4ed4d9ad3ec532827540c3e5583cb9dc946bad7c5eb4becd611e3c | 6,097,342 |
| `sia_psicossocial` | PSSP2204.dbc | 25373635e1f413ce56852aa90b879bac3a5e93535fe26630ac375ed707f620e2 | 5,503,263 |
| `sia_psicossocial` | PSSP2205.dbc | d8f760f96da84008a4cf0f31a29367f46705ba7f5c9a541ee1133f3c20fd45d3 | 6,077,778 |
| `sia_psicossocial` | PSSP2206.dbc | 3df27f08cb5d894d63a4774f76582a4c4813bc3d15b0e492bc7f9b67ab36244c | 5,410,056 |
| `sia_psicossocial` | PSSP2207.dbc | bd75310131e297eaef99cfb71918770ceb1c584a61722da2f36ad21fdf2c12ed | 5,955,207 |
| `sia_psicossocial` | PSSP2208.dbc | 0b0b9c4f0bc18d16e94cbaf25074dfdfde416d22bee6fa69ae0b393bf512f0e3 | 6,432,918 |
| `sia_psicossocial` | PSSP2209.dbc | c2b0541409339281d468fd16038befede1908f210547daa6348b8c801339e935 | 6,242,194 |
| `sia_psicossocial` | PSSP2210.dbc | 5fee3a1712c85cd4359650b662937e17cdc7a0b56025e2fed4cab96dda37379c | 5,915,317 |
| `sia_psicossocial` | PSSP2211.dbc | 09ce62a046a440e15cb7d37cd4bbcff70ab5a58743f2c54819aeb5a95281f096 | 6,285,680 |
| `sia_psicossocial` | PSSP2212.dbc | 9954c25e08ec7f112a56b0db77e4c9c5ddb8b26baa5e573d1bb489ed91e69441 | 5,462,333 |
| `sih_aih_reduzida` | RDSP2201.dbc | 8ae4e3a106dbdd27e7c1a75591f4f692255364d8238044451fb00b7d85346c68 | 15,549,230 |
| `sih_aih_reduzida` | RDSP2202.dbc | adde15599eb92152b61316c86122d4e0f3fa9580dff02a51bd4cec4ccc04d335 | 15,047,971 |
| `sih_aih_reduzida` | RDSP2203.dbc | 9ecc75c9df85dc9bd5cb0dd4d3025ffe9484aabc75de8cb195230b9b4a94aed0 | 16,675,594 |
| `sih_aih_reduzida` | RDSP2204.dbc | 9ba18937432562fa044f15675944ed8f2778b9194056d4c4d9c051fb47e7ebd7 | 15,947,793 |
| `sih_aih_reduzida` | RDSP2205.dbc | d7a658fe3fbc069a7674fe65697bd13749652aa293981b8df137907aa087e424 | 16,059,106 |
| `sih_aih_reduzida` | RDSP2206.dbc | 92ee775903a8e14dbf53fcabaed3f6436db4787bbc6b5d4d5ec1f2095dfb63f0 | 16,211,545 |
| `sih_aih_reduzida` | RDSP2207.dbc | 21d3c46dfba9f78ed5a5a47585242da36a385b87286c2beccab546763efa6318 | 17,003,030 |
| `sih_aih_reduzida` | RDSP2208.dbc | 2f4d602946be16ab3ba847e799e2b826944fc792794a93310a2482914fdbb0d3 | 16,975,493 |
| `sih_aih_reduzida` | RDSP2209.dbc | 15c9afc0b77f0711046c4998ad2cc7f657d08a593b2729aab65fa9b18e09f3e0 | 17,069,931 |
| `sih_aih_reduzida` | RDSP2210.dbc | 35376f83fe05c547ff2628b8cd97cf0318dc98d8a375edb8c92e959673112770 | 17,273,733 |
| `sih_aih_reduzida` | RDSP2211.dbc | b01fd0dffe33e74ba82fbba0f8bf4b0d4f3766d3d36d04ff563bbb9544e74bb0 | 16,449,825 |
| `sih_aih_reduzida` | RDSP2212.dbc | dc05eda6f495d749f4e38e12f19d01488528f1276ce6d6e292b0215573fb01d2 | 16,493,381 |
| `sih_aih_rejeitada` | RJSP2201.dbc | 2ea4a600fec594ce4dfb00075e5ae29a72b378b3375946c3b74c8ff50b76c241 | 621,582 |
| `sih_aih_rejeitada` | RJSP2202.dbc | cadf30eec97f970949f63522171143cbd87f6c0101abaa2f44e1a2d95894d060 | 599,573 |
| `sih_aih_rejeitada` | RJSP2203.dbc | f85760f7cf7befa7507266736e5ae5bda02b9b92cf5a7a020db30dc4e2873100 | 672,103 |
| `sih_aih_rejeitada` | RJSP2204.dbc | 90da75ebfeda732ddea39a5eb990b134a6296fc3f8410f0f8fe4533c3e4de1c1 | 686,470 |
| `sih_aih_rejeitada` | RJSP2205.dbc | 1e7b4e073fc37b6bb05f5be4c74a93988880af56be116b5df387f3412c1a6204 | 1,419,440 |
| `sih_aih_rejeitada` | RJSP2206.dbc | 1f5a4ba9191808d234f70f0f6b6457824c14c86d9e98b52f1066f2941e2c1255 | 1,714,654 |
| `sih_aih_rejeitada` | RJSP2207.dbc | 3de15538f7ac622f691a2341106c2db5826833b701622d9fd04ae3fe872233c3 | 1,214,971 |
| `sih_aih_rejeitada` | RJSP2208.dbc | e98fd333a43f9e699d2de9081086bb93b1f3c7ec4e34d70e15408bed5d0f6e9a | 1,232,885 |
| `sih_aih_rejeitada` | RJSP2209.dbc | d2106405d3dfcd04c30ccce9d937d994f508ca1122be6bac7654417e11bdc1fc | 930,640 |
| `sih_aih_rejeitada` | RJSP2210.dbc | 8d4e289fd750eff533c1c539b8f6f7941f4b3a134ff37892f53dadd5138dcd5b | 889,864 |
| `sih_aih_rejeitada` | RJSP2211.dbc | b68df908da34a7b6e5cc8c7f257d9018c0f720e0912fcd92c26f3f5c11416637 | 728,407 |
| `sih_aih_rejeitada` | RJSP2212.dbc | de0339f9da78aa2295083b7d4d8ce2464060267dcd4505cdc3a1d20d17a79901 | 712,014 |
| `sih_aih_rejeitada_erro` | ERSP2201.dbc | 4dc05c03ab7f3396153a32bb29ba97c92250484a23b0f8d9e6f2e82105c4ae50 | 254,558 |
| `sih_aih_rejeitada_erro` | ERSP2202.dbc | bb19214c2f493004053548e66b03f2fc998ec245e15a806bf08b10d85438199c | 257,353 |
| `sih_aih_rejeitada_erro` | ERSP2203.dbc | a7e8c2907f8b2940718eb9a04d2ea16f2a7c5ac3f4532440d54a907107272816 | 291,091 |
| `sih_aih_rejeitada_erro` | ERSP2204.dbc | a20b69db54f704787f34a7b3dac13e79f7d182cc0f726e5eb0fc15de48fe5625 | 276,972 |
| `sih_aih_rejeitada_erro` | ERSP2205.dbc | b26d0b7fe6c7c40628735cc6ec9fb9c5679e4fbed6ddceabc598f2ee43065fd3 | 558,545 |
| `sih_aih_rejeitada_erro` | ERSP2206.dbc | 5a2f9a3fc763f932a8a75826f5700086127674e805ea971e07b782604c2b9d9f | 687,832 |
| `sih_aih_rejeitada_erro` | ERSP2207.dbc | 710e673f1b33b9739c960c8492fe15dcc2c52513ca9d7d48f9323e2637a99e3c | 484,022 |
| `sih_aih_rejeitada_erro` | ERSP2208.dbc | f629ae6eab98d321bb747f0ab32d663eab21c7c51d741b9d9416f456e15a50ab | 493,740 |
| `sih_aih_rejeitada_erro` | ERSP2209.dbc | 825b74c75760139509950c3d3dc81fae8f27e8285f918917415d6ec3a311ad51 | 372,942 |
| `sih_aih_rejeitada_erro` | ERSP2210.dbc | c1555dd74bc3cd25d33c63ca55839d1a0e901558c75ae9b0e85acf9510b331a3 | 376,691 |
| `sih_aih_rejeitada_erro` | ERSP2211.dbc | dcd50637bb944b3c55c44b5939e7e0d7625353724af5f152471cb64d02bef694 | 306,026 |
| `sih_aih_rejeitada_erro` | ERSP2212.dbc | c09fd902e5ecfee70be3afa1d81b18cdc3ce43911688ea626400722463c9d20d | 285,355 |
| `sim_obitos` | DOSP2022.dbc | 34f6f7aef94545b88748982d0891a2b014c21dd43db8fd3b656643e0d6c17540 | 28,630,082 |
| `sinasc_nascidos_vivos` | DNSP2022.dbc | 09c3eed7c97ae81a5d9e44f697964e17f505c8c7b9693d9fdc408a53d48e6a56 | 25,153,015 |

Files read outside the lake, for the import defects (SP):

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| STSP2212.dbc | dba6fff68657a6c3272d5be2a12266ee190f5be7355451d71d3ca1c5503bd285 | 4,120,637 |
| RDSP2301.dbc | 2b20b418325c62627265ddfc91baad2eca5fd490e11495e77a1a0a1310ddd61e | 16,427,028 |
| RDSP2308.dbc | eb5d97e8e834b7bc4342bfa28eb00eaa20055490b688f466906d6bc7f42f3ebb | 18,583,060 |

ICD-10 chapters and descriptions come from `aux_cid10`, part of the packaged `auxiliares-bootstrap.zip`.

## Verification

- **No red test.** This is a notebook-only change to a notebook already listed in `ESPERADOS`. No library behaviour changed, so no existing test could fail first.
- **Green.** `uv run --locked --extra dev --extra notebooks pytest -q tests/unit/notebooks/`: the notebook opens offline, writes nothing, carries PEP 723 metadata and a molab badge, and uses no `mo.ui` widgets.
- **Executed end to end** on the rebased branch (main 8fd5cdf, v0.3.1): RR 2022 and SP 2022 (with `PULAR`) ran through every cell. A copy with every loaded base shuffled gave identical linkage, uniqueness, validation and summary tables. `marimo export html ... -- --executar true` completed on RR.
- **Linters.** `ruff format --check`, `ruff check` and `pre-commit run --from-ref origin/main --to-ref HEAD` on the branch.

## Addendum, 2026-09-23: RD SP 2023 after the undecodable-byte fix

With the undecodable-byte fix, RD SP 2023 and CNES ST SP 2022-12 import. Tutorial 6 was rerun on SP 2022 with `PULAR` holding only BPA-I, professional services and AM. It ran into a new, empty lake and every cell completed. The RD 2022 half of §4.7 reproduces the numbers above exactly (114,339 pairs, same lag counts), so the rest of the report stands.

**Rejected AIHs (§4.7).** RD SP 2023 adds 21,746 pairs to the 114,339 found in RD 2022. That is 136,085 of 187,361 rejection records, with 94,539 distinct AIH numbers. The 2023 pairs are mostly a long tail, not more next-month returns:

| Lag (competências, RD − RJ) | RD 2022 | RD 2023 |
| --- | ---: | ---: |
| before the rejection | 10,772 | 0 |
| same | 708 | 0 |
| +1 | 81,724 | 4,316 |
| +2 | 14,548 | 2,179 |
| +3 to +11 | 6,587 | 9,563 |
| +12 to +23 | 0 | 5,688 |

"A rejected AIH usually comes back approved the next month" still holds: +1 is 63.2% of all pairs. What RD 2022 hid is a tail. RD 2022 can only show returns within 2022, so a rejection from late 2022 could not appear there. With 2023, 15,251 pairs come back three or more competências later, 5,688 of them a year or more later. Validation over all 136,085 pairs:

| Variable | Real pairs | Neighbour-AIH control |
| --- | ---: | ---: |
| birth date | 99.7% | 1.2% |
| sex | 99.8% | 57.5% |
| admission date | 99.4% | 28.4% |
| discharge date | 80.2% | 16.1% |
| CNES | 99.8% | 81.0% |

Discharge date agrees less than with RD 2022 alone (87.8%). This run did not split the validation by year, so it does not show whether the 2023 pairs cause the drop.

**Bariatric surgery (§4.13).** RD SP 2023 answers the open question: AIHs paid in the next year are not the explanation. Of the 1,617 AIHs of 2022 surgeries, RD 2022 has 446 and RD 2023 adds 2. Coverage goes from 27.6% to 27.7%, and the 1,169 still missing are not in SP's RD for 2022 or 2023. What remains open is surgeries billed in another UF, or `ab_numaih` values that are not SIH AIH numbers. With 463 pairs, the validation is unchanged: surgery date inside the admission 92.4% (control 32.8%), sex 99.4%, facility 99.8%, age ±1 98.5%.

The ER error codes are still unlabeled in this run. `MOTERRO.dbf` in TAB_SIH labels them; that change is its own PR.

Provenance of the files new to this run (downloaded 2026-09-23; the other SP files are as listed above):

| File | Server time | SHA-256 |
| --- | --- | --- |
| `SIHSUS/200801_/Dados/RDSP2301.dbc` | 2024-02-05 22:58 | `2b20b418325c62627265ddfc91baad2eca5fd490e11495e77a1a0a1310ddd61e` |
| `SIHSUS/200801_/Dados/RDSP2302.dbc` | 2024-03-07 18:44 | `744b0977d0c6a4d60ba98f012da5111e449e065ed2898e5e03747d9268a21f9f` |
| `SIHSUS/200801_/Dados/RDSP2303.dbc` | 2024-04-09 14:32 | `e6c920afdb0f432f93724893a731b22cb9303c2bed8a3342ed0c161f2e600b6b` |
| `SIHSUS/200801_/Dados/RDSP2304.dbc` | 2024-06-16 01:17 | `717509473b3c644385bbfcdc2dd7645b759d55ed2da085311b81fbfeb3420c27` |
| `SIHSUS/200801_/Dados/RDSP2305.dbc` | 2024-06-16 01:17 | `fdf092781980fe6673c54736970d516a2dc002735b157ae27b03fa1816e5821e` |
| `SIHSUS/200801_/Dados/RDSP2306.dbc` | 2024-08-05 14:46 | `e9507c7429b4dc8990639b90b70e2ea38d42547dde7594cf1f327aae8587a95b` |
| `SIHSUS/200801_/Dados/RDSP2307.dbc` | 2024-08-05 14:46 | `956e525f34e3d0a38ee473d5c6355dc4b1026acb0ef6b1637fae4f5c3eeb3291` |
| `SIHSUS/200801_/Dados/RDSP2308.dbc` | 2024-09-05 10:32 | `eb5d97e8e834b7bc4342bfa28eb00eaa20055490b688f466906d6bc7f42f3ebb` |
| `SIHSUS/200801_/Dados/RDSP2309.dbc` | 2024-10-08 12:08 | `d7211a3e0822eca3cf948f03c43245800c71beb8a1a15989ecbd223ab83598dd` |
| `SIHSUS/200801_/Dados/RDSP2310.dbc` | 2024-11-07 15:40 | `d57e52a565831f69f35ecfbf16fd83f4c421bd93a16da186e98abb094980b674` |
| `SIHSUS/200801_/Dados/RDSP2311.dbc` | 2025-01-05 18:59 | `176837cc3be751908c6e2958830760877f527dbbb5693382e57d346b8ee6b551` |
| `SIHSUS/200801_/Dados/RDSP2312.dbc` | 2025-01-05 18:59 | `ad9a723ac673f5d9b1e6362c407dcbc3faf83645798e1315106ff6da01801488` |
| `CNES/200508_/Dados/ST/STSP2212.dbc` | 2023-01-11 07:34 | `dba6fff68657a6c3272d5be2a12266ee190f5be7355451d71d3ca1c5503bd285` |
