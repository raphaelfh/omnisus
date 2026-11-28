# SIH: what documents and files say about `homonimo`

The RD files of the SIH publish `homonimo` with `0` and `2`, and the documents that give
codes say `0` no and `1` yes (issue `homonimo-sem-fonte` of `sih_aih_reduzida`). This
folder records, on 2026-11-28, every DATASUS document within reach that names homonyms
and what 275 files show. No document read gives a meaning to `2`. The files read are
consistent with one reading, stated at the end as a reading and not as a definition.

    uv run --locked python evidence/2026-11-28-sih-homonimo/medir.py \
        DIR evidence/2026-11-28-sih-homonimo/medidas.json

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-28-sih-homonimo/buscar.py DOCS \
        > evidence/2026-11-28-sih-homonimo/documentos.csv

`medir.py` reads each file with the repository reader
(`omnisus.sources.datasus_ftp.parse.dbc_bytes_to_lazyframe`) and writes only counts: no
CPF, AIH number, date of birth or other value of a row leaves the files. Two runs wrote
the same bytes. `buscar.py` ran on macOS (it calls `textutil` for `.doc`).

## Files read

275 files, 1,002,615,859 bytes, all listed at the end with SHA-256:

- 175 `RD` of `SIHSUS/200801_/Dados/` (12,662,458 AIH): the 114 of
  `evidence/2026-11-28-rd-uti-mes-to-regct/` (the 27 UFs of 2008-01, 2012-01, 2016-01
  and 2025-12; `RDSP` of 2014-12, 2015-02, 2019-02, 2020-01, 2023-03, 2023-06), `RDSP` of
  every month from 2020-02 to 2022-02, of 2012-02 and of 2012-03, `RDRJ` and `RDMG` of
  2014-12 and 2015-02, and SP, RJ, MG, RR, DF and PE of 2015-06 to 2015-10.
- 58 `RJ` of the same folder (290,261 rows): SP, RJ, MG, RR and DF of 2008-01, 2012-01,
  2014-12, 2015-02, 2015-06 to 2015-10, 2016-01 and 2025-12, and `RJSP` of 2022-01 to
  2022-03.
- 14 `ER` of the same folder (134,926 rows): SP and RJ of 2012-01, 2014-12, 2015-07,
  2015-08, 2015-10, 2016-01 and 2025-12. The folder lists no `ER` file of 2008-01.
- 28 `RD` of `SIHSUS/199201_200712/Dados/` (480,634 AIH): `RDRR` of every month of 2006
  and 2007 (same SHA-256 as `evidence/2026-11-18-rd-medidas/2006-2007/arquivos.csv`),
  `RDRJ` of 2006-07 and 2007-07, `RDMG` and `RDSP` of 2007-07. They are read with the
  layout `sih_aih_reduzida_1998_2007`.

"Marked" below means `homonimo` other than `0`. "To 2015-07" and "from 2015-08" split the
files by the competence in their name: Nota Técnica SIHD2 001/2015 is "Válido a partir da
competência 08/2015".

## What the documents say

`sihd-listing.txt` is the listing of `ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/`
and of its folders on 2026-11-28. `documentos.csv` has the 148 files downloaded from it
(70,896,534 bytes) and the 112 members of the ZIP files among them, each with SHA-256 and
the number of text lines that match `hom[oôó]nim` or `duplicidade`: 226 texts were read
and 28 have a match. The passages:

- **The codes, `0` and `1` only.** `Layout_REDUZIDA.pdf`, p. 2: "MARCA DE HOMONIMO ( 0 =
  não , 1 = sim)" and `CPF_AUT`, "CPF DO AUDITOR QUE AUTORIZOU O HOMONIMO".
  `dicionario_de_dados_AIH.pdf`, pp. 8-9, `AH_ST_DUPLICIDADE`: "Marca de homônimo, onde: 0
  = não. 1 = sim." `sihd1_dicionario_de_dados.pdf` ("Dicionário de Dados SIHD"): p. 4,
  `AH_AIH_HM`, "MARCA DE HOMONIMO ( 0 = não , 1 = sim)", and `AH_CPF_HM`, "CPF DO AUDITOR
  QUE AUTORIZOU O HOMONIMO"; p. 10, `HAH_AIH_HM`, the same; p. 3, the list of code tables
  kept in `TB_C_D` has "66 MARCA DE HOMONIMO". `Programas/Tabelas300.zip`, member
  `DSIHD006.TXT` (SHA-256 in `documentos.csv`; 1,741 lines, each starting with the 4-digit
  code of a table, as the dictionary describes `TB_C_D`): the two lines of table 66 are
  "00660 NAO É HOMONIMO" and "00661 É HOMONIMO" (lines 1686 and 1687); line 1737, of the
  index table 0099, is "MARCA DE HOMONIMO". The member of the same name in
  `Programas/Tabelas740.zip` (June 2013) has no line of table 66 and no line with
  "HOMONIMO".
- **Who sets the mark.** `Manuais/Manual_SIHD_19_05_06.zip`, member `Manual-SIHD
  atualizada 19.05.06.doc` ("Manual Operacional do Sistema de Informação Hospitalar
  Descentralizado (SIHD), versão atualizada (19/05/2006)"; a Word file, so no page
  numbers): on importing AIH, "Se a origem dos dados informados é a Regional [...] as
  marcas de homônimo são mantidas para o processamento posterior, para que as duplicidades
  sejam revistas" and "Se a origem dos dados informada é o Estabelecimento (formato de
  arquivo TXT), as marcas de homônimo são zeradas na importação, e o procedimento de
  verificação de duplicidades será executado automaticamente"; on the terms of "Gerenciar
  Informações", "Quando aparece duplicidade significa que: a AIH foi bloqueada
  automaticamente pelo sistema SIHD por ter outra AIH com o mesmo nome do paciente. Apenas
  o nome é igual, não faz batimento com nenhum outro dado da AIH. O autorizador deve
  “checar” essa duplicidade e liberar ou não a AIH."; on the procedure, "A função de
  pesquisa de duplicidades verifica se existem nomes e datas de nascimento iguais em
  registros diferentes e marca os registros como bloqueados ou liberados
  (pré-processamento). Os autorizadores devem analisar cada registro bloqueado,
  verificando se as duplicidades são coerentes ou não, para decidir sobre manter o
  bloqueio ou liberá-lo." The two sentences differ on the date of birth.
  `Manuais/Manual-SIHD123.zip` has the same passages but the one on the terms. None of the
  SISAIH01 layouts read has a matching line (19 files of `Manuais/` whose name starts with
  `layout_sisaih01`, `Layout_SISAIH01` or `Layout_do_SISAIH01`, whatever the case, from
  the competence 2010-01 to 2026-07 and two undated, in `documentos.csv`): the file the
  hospital sends has no homonym field in them.
- **Four reports.** `MNL-PDOC-SIHD2-ManualOperacao-Edicao1.0.pdf` ("SIHD2 Manual de
  Operação", product version 2.40, July 2009), printed p. 106 (115th of the PDF), lists
  the reports of "Gerenciar Informações": "Duplicidade" with "Encontradas", "Bloqueadas",
  "Canceladas" and "Liberadas". The same page lists the same four reports for the other
  kinds of block ("Solicitação de liberação", "Agravos", "Partos sem VDRL"), so the four
  are not particular to duplicates. Printed pp. 89-90: "Liberar. 1. Selecione o código da
  AIH e clique em Liberar. [...] 2. Selecione o CPF do autorizador e clique em OK. O
  sistema libera a AIH"; the procedure is for any blocked AIH, whatever the reason.
  Printed pp. 91-92: the buttons "Bloquear todas" and "Liberar todas" "são habilitados
  apenas quando a opção “Duplicidade” é selecionada". The figures of the manual are images
  and were not read.
- **Which AIH are blocked.** Manual SIH 2012 (`sihsus-7429b011ee2a`), p. 11, items 5.10
  and 5.11: a new AIH for the same patient in the same stay is blocked "por “duplicidade”
  (homônimo), mas o gestor autoriza", and an AIH issued less than 3 days after another
  stay "vai ser bloqueada por “duplicidade”, desde que a outra AIH seja emitida pelo mesmo
  gestor"; item 63.8, p. 74, is on the same block. The manuals of 2009 to 2011, 2013 and
  2015 in `Manuais/` have matching lines too (`documentos.csv`). `Programas/leiame.txt`
  (release notes of the SIHD), version 2.31, "COMPETENCIA JUNHO/2006": "Acerto no
  Gerenciador de Informacoes para nao realizar verificacao de homonimo entre aihs tipo 1 e
  5 para o mesmo numero de aih".
- **The change of 08/2015.** Nota Técnica SIHD2 001/2015 (`sihsus-6de69835fef0`).
  `Programas/leiame_SIHD2.txt` (release notes of the SIHD2), "VERSÃO 10.10 - 08/09/2015 -
  COMPETENCIA 08/2015", item 04: "Novos Bloqueios por Internação sobreposta ou com
  intervalo de até 3 dias; Alterado o Bloqueio de Duplicidade (homonimo) para ser
  realizado apenas para os pacientes SEM CARTÃO NACIONAL DE SAÚDE (CNS)". The same file,
  "VERSÃO 08.40 - 07/04/2014 - COMPETENCIA 03/2014": "Alterado o termo "DUPLICIDADE" para
  "DUPLICIDADE DE NOME"". `MANUAL_SIH_janeiro_2017.pdf`, printed pp. 85-87 (86th to 88th
  of the PDF), section 58, "AIH BLOQUEADAS PELO SIHD2 PARA ANÁLISE PELO GESTOR": 58.1, "O
  SIHD2 bloqueia como DUPLICIDADE DE NOME apenas as AIH que NÃO POSSUAM número de CNS do
  paciente"; 58.2.1, "As AIH apresentadas são verificadas umas contra as outras observando
  se para um mesmo número de CNS, existem AIH com datas de internação / saída sobrepostas
  ou com intervalo de até 3 dias entre elas. Esta verificação é realizada para as AIH de
  um mesmo gestor apresentadas na competência atual"; 58.2.2, the same against "todo o
  estado em até 3 meses anteriores".
- **Tables of the TabWin package.** `TAB_SIH.zip` (`sih-tab-2491e8d4f2db`):
  `CNV/sitbloqueio.cnv`, the table `RJ2008.DEF` links to `ST_BLOQ`, has "0 AIH
  autorizada", "2 Bloqueio AIH", "4 Cancelamento AIH" and "5 Liberação bloqueio AIH";
  `CNV/motbloqueio.cnv` (`ST_MOT_BLO`) has "01 DUPLICIDADE" and the odd codes up to 15
  with "DUPLICIDADE" and another reason; `DBF/MOTERRO.dbf` (`CO_ERRO` of the `ER` files)
  has "020001 AIH BLOQUEADA POR DUPLICIDADE", "030001 AIH CANCELADA POR DUPLICIDADE",
  "020081 AIH BLOQUEADA POR PERÍODOS DE INTERNAÇÃO SOBREPOSTOS NO MOVIMENTO" and "020082
  [...] NO ESTADO"; `DBF/LIBGESTOR.dbf`, which `RD2008.DEF` links to `GESTOR_COD`, labels
  the codes 134 to 243 "CNS", alone or with other reasons. `Docs/erroebloqueio.xlsx` is
  the dump of tables 0024 and 0027 of `TB_C_D`. No member of the package names `HOMONIMO`
  (issue `homonimo-sem-fonte`).

No document read says which code the mark takes when a duplicate is found, blocked,
released or cancelled, nor which column of the SIHD2 the RD field is written from.

Not read: the three files the server answered 550 for
(`Manuais/SIHD-TABELASeCAMPOS-7.doc`, linked by the manuals page;
`Manuais/INFORME_TECNICO_SOBRE_A_PORTARIA _203FINAL.pdf`;
`SiteArquivos/documentosPORTARIAS.txt`); `Portarias/portaria2008/PT_SAS_007.rar`; the
videos, presentations, installers, schedules and installation guides of `Manuais/`,
`Outros/`, `Programas/` and `Transmissores/`; the two Portaria archives above 2.1 MB;
`Arquivos/` (monthly `Tabela_Unificada` and `laih66` archives); the `.xls` and `.DBF`
members of the ZIP files; and the images inside the PDF files.

## Measures

All numbers are in `medidas.json`: key `files`, one entry per file, with one profile per
value of `homonimo` (`by_homonimo`), and key `links`.

### (a) RD from 2008: the values

`homonimo` has only `0`, `1` and `2` in the 175 files (key `homonimo` of each file).

| Competence | Files | AIH | `0` | `1` | `2` | not `0` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2008-01 | 27 | 651,615 | 617,022 | 0 | 34,593 | 5.31% |
| 2012-01 | 27 | 918,846 | 832,248 | 5,105 | 81,493 | 9.42% |
| 2012-02 | 1 | 198,234 | 176,852 | 0 | 21,382 | 10.79% |
| 2012-03 | 1 | 215,670 | 191,602 | 0 | 24,068 | 11.16% |
| 2014-12 | 3 | 344,989 | 305,276 | 0 | 39,713 | 11.51% |
| 2015-02 | 3 | 347,024 | 307,788 | 95 | 39,141 | 11.31% |
| 2015-06 | 6 | 444,379 | 390,218 | 0 | 54,161 | 12.19% |
| 2015-07 | 6 | 447,472 | 391,635 | 0 | 55,837 | 12.48% |
| 2015-08 | 6 | 437,952 | 437,542 | 0 | 410 | 0.09% |
| 2015-09 | 6 | 431,385 | 430,995 | 0 | 390 | 0.09% |
| 2015-10 | 6 | 428,802 | 428,419 | 0 | 383 | 0.09% |
| 2016-01 | 27 | 919,331 | 917,891 | 77 | 1,363 | 0.16% |
| 2019-02 | 1 | 203,599 | 203,572 | 0 | 27 | 0.01% |
| 2020-01 | 1 | 215,766 | 215,761 | 0 | 5 | 0.00% |
| 2020-02 | 1 | 205,588 | 205,567 | 0 | 21 | 0.01% |
| 2020-03 | 1 | 208,684 | 208,662 | 0 | 22 | 0.01% |
| 2020-04 | 1 | 158,154 | 158,139 | 0 | 15 | 0.01% |
| 2020-05 | 1 | 163,154 | 163,147 | 0 | 7 | 0.00% |
| 2020-06 | 1 | 172,034 | 172,013 | 0 | 21 | 0.01% |
| 2020-07 | 1 | 186,658 | 186,650 | 0 | 8 | 0.00% |
| 2020-08 | 1 | 184,527 | 184,507 | 0 | 20 | 0.01% |
| 2020-09 | 1 | 190,926 | 190,908 | 0 | 18 | 0.01% |
| 2020-10 | 1 | 196,014 | 195,995 | 0 | 19 | 0.01% |
| 2020-11 | 1 | 195,262 | 195,241 | 0 | 21 | 0.01% |
| 2020-12 | 1 | 188,128 | 188,120 | 0 | 8 | 0.00% |
| 2021-01 | 1 | 195,978 | 195,959 | 0 | 19 | 0.01% |
| 2021-02 | 1 | 191,120 | 191,102 | 0 | 18 | 0.01% |
| 2021-03 | 1 | 199,489 | 199,484 | 0 | 5 | 0.00% |
| 2021-04 | 1 | 192,501 | 192,485 | 0 | 16 | 0.01% |
| 2021-05 | 1 | 202,051 | 202,031 | 0 | 20 | 0.01% |
| 2021-06 | 1 | 201,017 | 201,001 | 0 | 16 | 0.01% |
| 2021-07 | 1 | 200,591 | 200,568 | 0 | 23 | 0.01% |
| 2021-08 | 1 | 201,312 | 201,297 | 0 | 15 | 0.01% |
| 2021-09 | 1 | 196,878 | 196,858 | 0 | 20 | 0.01% |
| 2021-10 | 1 | 195,013 | 195,001 | 0 | 12 | 0.01% |
| 2021-11 | 1 | 197,590 | 197,572 | 0 | 18 | 0.01% |
| 2021-12 | 1 | 203,150 | 203,134 | 0 | 16 | 0.01% |
| 2022-01 | 1 | 199,070 | 199,057 | 0 | 13 | 0.01% |
| 2022-02 | 1 | 191,763 | 191,755 | 0 | 8 | 0.00% |
| 2023-03 | 1 | 233,649 | 233,629 | 0 | 20 | 0.01% |
| 2023-06 | 1 | 232,263 | 232,250 | 0 | 13 | 0.01% |
| 2025-12 | 27 | 1,174,830 | 1,174,305 | 32 | 493 | 0.04% |

To 2015-07 (74 files, 3,568,229 AIH), 355,588 AIH are marked: 350,388 with `2` and 5,200
with `1`. From 2015-08 (101 files, 9,094,229 AIH), 3,612 are marked: 3,503 with `2` and
109 with `1`.

`1` is in 8 of the 175 files, and in each of them all its AIH are of one manager
(`uf_zi_distinct` 1) and, in 7 of the 8, have one `gestor_cpf` (`gestor_cpf_distinct`);
`cnes_distinct` is the last column:

| File | AIH | `1` | `2` | Managers (`uf_zi`) in the file | Hospitals (`cnes`) with `1` |
| --- | ---: | ---: | ---: | ---: | ---: |
| RDBA1201 | 68,584 | 2,289 | 1,662 | 67 | 101 |
| RDRS1201 | 55,459 | 2,816 | 2,577 | 30 | 166 |
| RDSP1502 | 195,822 | 95 | 22,442 | 292 | 1 |
| RDAP1601 | 2,607 | 52 | 0 | 2 | 6 |
| RDBA1601 | 64,985 | 25 | 8 | 75 | 12 |
| RDAP2512 | 4,900 | 12 | 0 | 1 | 5 |
| RDBA2512 | 77,304 | 18 | 2 | 223 | 7 |
| RDRS2512 | 70,967 | 2 | 0 | 67 | 2 |

`RDBA1601` has two `gestor_cpf` among its 25 AIH with `1`.

### (b) RD from 2008: fields that come with the mark

- `gestor_cpf` is filled (something other than spaces and zeros) in every marked AIH of
  the 175 files: 355,588 of 355,588 to 2015-07 and 3,612 of 3,612 from 2015-08. Of the
  unmarked, 175,453 of 3,212,641 (5.5%) and 1,780,415 of 9,090,617 (19.6%).
- `ident`: no marked AIH has `5`, in any file; 111,397 and 222,441 unmarked AIH have it.
  No marked AIH has `seq_aih5` other than zero.
- `cpf_aut` is blank or zero in every AIH of the 175 files.
- `gestor_tp` is `1` in every marked AIH but the 34,593 of 2008-01, where every AIH of
  the 27 files has `0`.
- `cobranca`, first digit, to 2015-07: `5` in 15,871 marked AIH (4.5%) and 13,089
  unmarked (0.4%), so 54.8% of the AIH with it are marked; `2` in 67,190 (18.9%) and
  157,583 (4.9%).

### (c) RD from 2008: another AIH with the same birth date, sex and residence

A row has `other` on a key when another `n_aih` of the same file has the same values in
the fields of the key; it is `near` when another `n_aih` of the same `nasc`, `sexo` and
`munic_res` has a stay that overlaps its own or is up to 3 days apart (`dt_inter`,
`dt_saida`). The keys are not a person: two people born on the same day share them.

| Files | Rows | `other` on `nasc`, `sexo`, `cep` | on `nasc`, `sexo`, `munic_res` | `near` |
| --- | --- | ---: | ---: | ---: |
| to 2015-07 | 355,588 marked | 314,977 (88.6%) | 333,837 (93.9%) | 198,720 (55.9%) |
| to 2015-07 | 3,212,641 unmarked | 62,807 (2.0%) | 358,939 (11.2%) | 173,498 (5.4%) |
| from 2015-08 | 3,612 marked | 3,087 (85.5%) | 3,313 (91.7%) | 2,729 (75.6%) |
| from 2015-08 | 9,090,617 unmarked | 1,404,554 (15.5%) | 2,447,115 (26.9%) | 1,468,699 (16.2%) |

- To 2015-07, of the 377,784 AIH with `other` on `nasc`, `sexo` and `cep`, 314,977 are
  marked (83.4%); from 2015-08, 3,087 of 1,407,641 (0.2%).
- The mark comes in groups: to 2015-07, 314,445 marked AIH have another marked row with
  the same `nasc`, `sexo` and `cep` (`other_marked_nasc_sexo_cep`), and 3,747 unmarked AIH
  have one (0.1% of the unmarked).
- The same six UFs before and after (SP, RJ, MG, RR, DF, PE): in 2015-06 and 2015-07,
  115,242 of 891,851 AIH have `other` on `nasc`, `sexo` and `cep` (12.9%), 99,649 of them
  marked (86.5%); in 2015-08 to 2015-10, 173,252 of 1,298,139 (13.3%), 1,035 of them
  marked (0.6%). The share of AIH with such a pair did not fall; the share of them that
  is marked did.
- To 2015-07, 156,868 marked AIH (44.1%) have no `near` row, and 40,611 (11.4%) have no
  `other` on `nasc`, `sexo` and `cep`.

### (d) RD from 2015-08: AIH released without the card number

The RD layout has no field that says whether the AIH has the patient's CNS. Two things
in it name the CNS: the codes of `gestor_cod` that `LIBGESTOR.dbf` labels "CNS" (134 to
243, class `cns` in `medidas.json`) and `aud_just`, the justification of the auditor for
accepting the AIH without it.

| Files | Rows | `gestor_cod` "CNS" | `aud_just` filled |
| --- | --- | ---: | ---: |
| to 2015-07 | 355,588 marked | 1,263 (0.4%) | 1,260 |
| to 2015-07 | 3,212,641 unmarked | 13,968 (0.4%) | 13,967 |
| from 2015-08 | 3,612 marked | 3,188 (88.3%) | 3,180 (88.0%) |
| from 2015-08 | 9,090,617 unmarked | 32,366 (0.4%) | 33,860 (0.4%) |

From 2015-08, 375 marked AIH have `gestor_cod` zero and 49 another code. The files of
2008-01 have no `aud_just` and a blank `gestor_cod`.

### (e) RJ: `homonimo` and `st_bloq`

The 58 files have `homonimo` `0`, `1`, `2` and `3`. `st_mot_blo` is in three classes:
`00`, the eight codes of `motbloqueio.cnv` that start with "DUPLICIDADE" (01, 03, ... 15)
and the others.

To 2015-07, 30 files, 165,518 rows:

| `homonimo` | Rows | `st_bloq` 0 | 2 | 4 | 5 | `st_mot_blo` 00 | "DUPLICIDADE" | other | `gestor_cpf` filled |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 130,615 | 102,563 | 18,943 | 20 | 9,089 | 112,071 | 179 | 18,365 | 19,952 |
| 1 | 17,618 | 0 | 17,612 | 0 | 6 | 6 | 12,104 | 5,508 | 5,226 |
| 2 | 17,190 | 0 | 742 | 0 | 16,448 | 16,528 | 549 | 113 | 17,190 |
| 3 | 95 | 0 | 0 | 95 | 0 | 0 | 23 | 72 | 95 |

From 2015-08, 28 files, 124,743 rows:

| `homonimo` | Rows | `st_bloq` 0 | 2 | 4 | 5 | `st_mot_blo` 00 | "DUPLICIDADE" | other | `gestor_cpf` filled |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 124,613 | 66,469 | 34,938 | 449 | 22,757 | 99,091 | 1,566 | 23,956 | 44,292 |
| 1 | 68 | 0 | 68 | 0 | 0 | 0 | 41 | 27 | 41 |
| 2 | 61 | 0 | 4 | 0 | 57 | 59 | 0 | 2 | 61 |
| 3 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |

- `1` goes with `st_bloq` 2 ("Bloqueio AIH") in 17,680 of 17,686 rows; the other 6 are in
  `RJSP1502`, with 5.
- `2` goes with `st_bloq` 5 ("Liberação bloqueio AIH") in 16,505 of 17,251 rows; 746 have
  `st_bloq` 2, 542 of them in `RJRJ0801` and 119 in `RJSP1507`.
- `3` goes with `st_bloq` 4 ("Cancelamento AIH") in the 96 rows.
- No marked row has `st_bloq` 0. Most rows with `st_bloq` 2, 4 or 5 are unmarked: a block
  has other reasons too.

### (f) ER and RJ of the same month

The AIH numbers an `ER` file has with an error of `MOTERRO.dbf`, by the `homonimo` they
have in the `RJ` of the same UF and month (key `links`, `ER...>RJ...`). "duplicidade":
"AIH BLOQUEADA POR DUPLICIDADE", alone or with the reasons of `motbloqueio.cnv` and with
"SEXO INCOMPATÍVEL C/ PROCEDIMENTO": the 16 codes 020001 to 020015 odd and 020018 to
020032 even. "duplicidade_cancelada": "AIH CANCELADA POR DUPLICIDADE", the same: the 8
codes 030001 to 030015 odd. "sobrepostos": 020081 and 020082. "Mixed" are AIH with rows
of two values.

`MOTERRO.dbf` has six more codes with "AIH BLOQUEADA POR DUPLICIDADE" in the text, and
they were left out because they name another kind of duplicate, not the one of the
patient's name: 020054 ("INT. NO MESMO PERÍODO EM PSIQUIATRIA"), 020055 ("ALTA ADM.
INDEVIDA"), 020077 ("DE CNS DE PACIENTE") and 020078 to 020080 ("DE ACORDO COM PT", the
sequential procedures of oncology, neurosurgery and orthopaedics). The same goes for
030054, 030055 and 030077. Nothing was counted for them.

| ER file | error | AIH | `0` | `1` | `2` | `3` | mixed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ERRJ1201 | duplicidade | 895 | 0 | 889 | 0 | 0 | 6 |
| ERRJ1412 | duplicidade | 890 | 0 | 890 | 0 | 0 | 0 |
| ERRJ1507 | duplicidade | 772 | 1 | 771 | 0 | 0 | 0 |
| ERRJ1508 | duplicidade | 35 | 35 | 0 | 0 | 0 | 0 |
| ERRJ1508 | sobrepostos | 976 | 976 | 0 | 0 | 0 | 0 |
| ERRJ1510 | duplicidade | 2 | 2 | 0 | 0 | 0 | 0 |
| ERRJ1510 | sobrepostos | 1,269 | 1,269 | 0 | 0 | 0 | 0 |
| ERRJ1601 | duplicidade | 5 | 2 | 3 | 0 | 0 | 0 |
| ERRJ1601 | sobrepostos | 985 | 985 | 0 | 0 | 0 | 0 |
| ERRJ2512 | sobrepostos | 374 | 374 | 0 | 0 | 0 | 0 |
| ERSP1201 | duplicidade | 597 | 5 | 592 | 0 | 0 | 0 |
| ERSP1201 | duplicidade_cancelada | 8 | 0 | 0 | 0 | 8 | 0 |
| ERSP1412 | duplicidade | 502 | 0 | 501 | 0 | 0 | 1 |
| ERSP1507 | duplicidade | 569 | 1 | 568 | 0 | 0 | 0 |
| ERSP1507 | duplicidade_cancelada | 4 | 0 | 0 | 0 | 4 | 0 |
| ERSP1508 | duplicidade | 61 | 61 | 0 | 0 | 0 | 0 |
| ERSP1508 | sobrepostos | 1,142 | 1,142 | 0 | 0 | 0 | 0 |
| ERSP1510 | duplicidade | 216 | 216 | 0 | 0 | 0 | 0 |
| ERSP1510 | duplicidade_cancelada | 3 | 3 | 0 | 0 | 0 | 0 |
| ERSP1510 | sobrepostos | 958 | 958 | 0 | 0 | 0 | 0 |
| ERSP1601 | duplicidade | 50 | 47 | 3 | 0 | 0 | 0 |
| ERSP1601 | duplicidade_cancelada | 2 | 2 | 0 | 0 | 0 | 0 |
| ERSP1601 | sobrepostos | 1,053 | 1,053 | 0 | 0 | 0 | 0 |
| ERSP2512 | duplicidade | 55 | 55 | 0 | 0 | 0 | 0 |
| ERSP2512 | duplicidade_cancelada | 238 | 238 | 0 | 0 | 0 | 0 |
| ERSP2512 | sobrepostos | 445 | 445 | 0 | 0 | 0 | 0 |

To 2015-07 (6 files), 4,211 of the 4,225 AIH with "duplicidade" have `1` and the 12 with
"duplicidade_cancelada" have `3`. From 2015-08 (8 files), 418 of 424 with "duplicidade"
have `0`, as do the 243 with "duplicidade_cancelada" and the 7,202 with "sobrepostos".

### (g) From a rejected AIH to the RD of the next months

The `n_aih` of an `RJ` file, by its `homonimo` there, that are in the `RD` of the same UF
one month later, by the `homonimo` they have there (key `links`, `RJ...>RD...`).

| Pairs of files | `homonimo` in RJ | AIH | In the next RD | with `0` | with `2` | both |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RD to 2015-07 (6) | 0 | 29,163 | 13,342 | 12,679 | 660 | 3 |
| RD to 2015-07 (6) | 1 | 4,219 | 1,823 | 451 | 1,371 | 1 |
| RD to 2015-07 (6) | 2 | 3,899 | 1,647 | 976 | 671 | 0 |
| RD to 2015-07 (6) | 3 | 38 | 0 | 0 | 0 | 0 |
| RJ of 2015-07, RD of 2015-08 (5) | 0 | 13,971 | 4,274 | 4,272 | 2 | 0 |
| RJ of 2015-07, RD of 2015-08 (5) | 1 | 2,731 | 1,114 | 1,114 | 0 | 0 |
| RJ of 2015-07, RD of 2015-08 (5) | 2 | 2,165 | 754 | 752 | 2 | 0 |
| RJ from 2015-08 (11) | 0 | 49,229 | 17,578 | 17,575 | 3 | 0 |
| RJ from 2015-08 (11) | 1 | 28 | 4 | 3 | 1 | 0 |
| RJ from 2015-08 (11) | 2 | 33 | 11 | 9 | 2 | 0 |

The six pairs to 2015-07 are `RJSP1201>RDSP1202` and SP, RJ, MG, RR and DF of 2015-06 to
2015-07. Of the 597 AIH `ERSP1201` has with "duplicidade", 305 are in `RDSP1202`, 259 of
them with `2`; of the 569 of `ERSP1507`, 361 are in `RDSP1508`, all with `0`.

### (h) RD of 2006 and 2007: `cpf_aut`

`Layout_REDUZIDA.pdf` describes `CPF_AUT` as "CPF DO AUDITOR QUE AUTORIZOU O HOMONIMO";
it is the layout of the files of 2006-04 to 2007-12 (75 fields), and the three files of
2006-01 to 2006-03 have an earlier layout, of 70 fields
(`evidence/2026-10-01-rd-1992-2007-layouts/`).

| Files | `homonimo` | AIH | `cpf_aut` filled | `gestor_cpf` filled |
| --- | --- | ---: | ---: | ---: |
| `RDRR` 2006-01 to 2006-03 (3) | 0 | 4,418 | 0 | 211 |
| `RDRR` 2006-01 to 2006-03 (3) | 2 | 146 | 146 | 13 |
| `RDRR` 2006-04 to 2006-08, `RDRJ0607` (6) | 0 | 70,395 | 635 | 1,148 |
| `RDRR` 2006-04 to 2006-08, `RDRJ0607` (6) | 1 | 335 | 0 | 335 |
| `RDRR` 2006-04 to 2006-08, `RDRJ0607` (6) | 2 | 2,162 | 36 | 2,162 |
| 2006-09 to 2007-12 (19) | 0 | 373,406 | 0 | 7,721 |
| 2006-09 to 2007-12 (19) | 2 | 29,772 | 0 | 29,772 |

In the three files of 2006-01 to 2006-03, `cpf_aut` is filled in the 146 AIH with `2` and
in no other. From 2006-04 on, every AIH with `1` or `2` has `gestor_cpf`, and `cpf_aut`
is filled mostly in AIH with `0`, until 2006-08. The 335 AIH with `1` are of `RDRJ0607`.

## What the files are consistent with

With the four reports the SIHD2 manual lists, one reading fits the files read: `1` a
duplicate found and blocked, `2` a duplicate whose block an authoriser released, `3` a
duplicate cancelled. It fits (e) and (f) in the rejected files, the manager's CPF in
every marked AIH of the RD (b), the pairs of (c), the drop of 2015-08 with the marked AIH
that remain being those released without the CNS (d), the rejected AIH with `1` that
come back approved with `2` (g) and the auditor's CPF of 2006 (h). It would explain why
the RD, which has the approved AIH, publishes `2` and almost never `1`.

Against it, or left out of it: the 5,309 approved AIH with `1` of (a), in each file all
of one manager, and the 335 of `RDRJ0607`; the 746 rejected rows with `2` and `st_bloq` 2
of (e); the 424 marked AIH from 2015-08 without a "CNS" code in `gestor_cod`; and the 6
rows with `1` and `st_bloq` 5.

This is an association in 275 files, not a published code list: no label enters the
dictionary from it.

## What this does not settle

- The definition of `1`, `2` and `3`, and whether other values exist.
- What makes an approved AIH keep `1`.
- Which column of the SIHD2 the field is written from, and when: the mark is set again in
  each processing ((g): an AIH has `1` in one month and `0` or `2` in the next).
- Whether the search compares the name alone or the name and the date of birth: the 2006
  manual says both, and the RD has no name.
- The months and UFs not read. The `RJ` files are of five UFs and the `ER` files of two.

## Files

| File | SHA-256 | Bytes | Rows | `homonimo` |
| --- | --- | ---: | ---: | --- |
| ERRJ1201.dbc | `780ef6db0625229a6a8cbbfd77dce40f6401b07196a8186b2173a1ba5c2b5e3a` | 173884 | 8623 | – |
| ERRJ1412.dbc | `a3112fa4c3030e28627a235f3b1aebf0170d4728f78c6c02b66201f923ea226c` | 161574 | 8745 | – |
| ERRJ1507.dbc | `b587369303ee39630103b4de3a1a8ce35dd07968c1b54d25ab0724312a548ac8` | 118909 | 5442 | – |
| ERRJ1508.dbc | `8f4515fe17a92cec2955d2fb12c6f05f59b24bb1429f9f7066bd4eba95f9f9e3` | 106441 | 4826 | – |
| ERRJ1510.dbc | `e6fd96ddd335afcdf613acab6cf76cfb67930a91a732fed5c008534d43a5dcc7` | 120999 | 5430 | – |
| ERRJ1601.dbc | `cdbbd51e7e33ed69b99988d05f0b595b54f09e7c99cef57de821f616b936ff77` | 140931 | 6585 | – |
| ERRJ2512.dbc | `a23736f9fd35068263e00f579a1dca3825649e69d586f9089e36401134723f09` | 89967 | 4261 | – |
| ERSP1201.dbc | `b84716ea061c43eac1009d18d0ab38ac20738484440d9f78d84b22632007d62a` | 325618 | 15313 | – |
| ERSP1412.dbc | `d491da1111eef163fa1c4e26d6d60eb41938e57d0b3e8807b8b9cd598a4ffee4` | 268218 | 12526 | – |
| ERSP1507.dbc | `77f075b301ccc275a7653925237f6d24b09bb814015620d68ff700057c1b3a0c` | 286984 | 13147 | – |
| ERSP1508.dbc | `a51598dd9ee3422df33f7c66d7f76e21a1986528510d1195d905af47f2c76ea5` | 308106 | 13729 | – |
| ERSP1510.dbc | `8d68a011bc6fc0276c5d7b1bdef50b8f6558c10b12196e48f39048c732d8c3c3` | 279594 | 12768 | – |
| ERSP1601.dbc | `90d7939673c38f77a2ba01e268ea81d98576b2dd0b9e31b8325aafcfa5cfa303` | 242394 | 10828 | – |
| ERSP2512.dbc | `d480b24fc846fe8545646f2d6d908638a8e805f56dcb696accf5f3d265b257a3` | 271397 | 12703 | – |
| RDAC0801.dbc | `fde119624f5ba8400fdd25f086be6180bb25440c141dbf9ae634b7f417d0f28d` | 114153 | 2087 | `0` 2037, `2` 50 |
| RDAC1201.dbc | `ed1af51e4aa132693c8c652d8173faed293f390d254413dca9ce32b4cb3a4c0b` | 282290 | 3945 | `0` 3700, `2` 245 |
| RDAC1601.dbc | `f65e80451faf6663187f826b66176a45eb0c35b1000f91ea5a4180246f965ac2` | 260204 | 3520 | `0` 3498, `2` 22 |
| RDAC2512.dbc | `0866ca3264e1fef1431de70e0f857b65bccea6c050163f3cfa99871604f68fd8` | 326478 | 4527 | `0` 4527 |
| RDAL0801.dbc | `8b72541b774a0f125905995d88578f1ef8e7bcaf0347836f584ad4d2a1c518cc` | 649292 | 12168 | `0` 11833, `2` 335 |
| RDAL1201.dbc | `d6f36f496e516ba5f65fefdc3d29f9cf4e3fb55d4d1506c1d506216fad2d8cfb` | 986632 | 15179 | `0` 14511, `2` 668 |
| RDAL1601.dbc | `5e2bad3270033b49f1272eae1ef37b76980581d890829c08c48f28df4a1cb20b` | 972093 | 13902 | `0` 13720, `2` 182 |
| RDAL2512.dbc | `e4ef6f7f2a578fccd9909de8e9d56aeb6b6948ed34dc4b02f26c4d45082ba5ca` | 1051577 | 14176 | `0` 14146, `2` 30 |
| RDAM0801.dbc | `70fc4614593552d58e2a0e13858170d8c5babfdeb6fed5bdfc73fb55207bd2f1` | 507103 | 9325 | `0` 9020, `2` 305 |
| RDAM1201.dbc | `0d7c3c186c3867d40d8ea1307b56bd7bb98a85536a6d0e0a947b4db071ab194d` | 836846 | 12944 | `0` 12030, `2` 914 |
| RDAM1601.dbc | `cfe4763cbc5276b7cb086700307be9f5df3f3f25f66252d5dce6197faa527915` | 892456 | 13492 | `0` 13490, `2` 2 |
| RDAM2512.dbc | `b41cf5ca53da64b4481f57662072357327bb9925280e3d0cd73addbb44a201da` | 1547730 | 21768 | `0` 21764, `2` 4 |
| RDAP0801.dbc | `00afc30235fc8ada93c98a4ebe81a583ea9054bfef4198b03ee42502197ae2fc` | 138343 | 2386 | `0` 2286, `2` 100 |
| RDAP1201.dbc | `e84f467afd4871ff4d17fdbba7ffbf5da0c39b9a67075fb33543f28371f9e10d` | 204119 | 3055 | `0` 2844, `2` 211 |
| RDAP1601.dbc | `03ddc29ee17f82b348cecb3c8109bc3624ea2860d89663cae8a9896319266a70` | 167039 | 2607 | `0` 2555, `1` 52 |
| RDAP2512.dbc | `a530c43b1cca7995011c9121fa8be834c0022866c7446bbfd041f0f28b29c79e` | 331879 | 4900 | `0` 4888, `1` 12 |
| RDBA0801.dbc | `3b6a630a91cd958d07ad42d9f02b510f39d54bfd5f5e560cc8bbb27a70078813` | 2442824 | 41659 | `0` 40701, `2` 958 |
| RDBA1201.dbc | `92b8420453f03265916a93c1bc64f1ee104fc6ccb739395991d7cba51e8c7457` | 4488183 | 68584 | `0` 64633, `1` 2289, `2` 1662 |
| RDBA1601.dbc | `1d689f5fd3aaa7a389335a12ca8134a5bb05c9aed2b3fb23566acd16721724a6` | 4635410 | 64985 | `0` 64952, `1` 25, `2` 8 |
| RDBA2512.dbc | `0e7c0ab9b4631c47f5a2f89f84bbc8f4880e9dd1d18392295b9b20647fc50619` | 5706040 | 77304 | `0` 77284, `1` 18, `2` 2 |
| RDCE0801.dbc | `0f28c1f696c373c26ac1e051b827787427cd8c1455167192edb703e99ec0d7f8` | 1717859 | 29823 | `0` 28641, `2` 1182 |
| RDCE1201.dbc | `beaf250bdedf9c30afe75397b91a08f53cbc42023b53207f01e71b19301112bf` | 2523916 | 38134 | `0` 34893, `2` 3241 |
| RDCE1601.dbc | `fd8d7de66376b83d17ee6fcab6641d94f89239973d6970d08db1d5ff88dcf9ae` | 2661764 | 38221 | `0` 38205, `2` 16 |
| RDCE2512.dbc | `c06b42d30e7f0607330e16b3b7229a0b21cfdec1e01623dfe7b36d68c21e0c66` | 3620722 | 48468 | `0` 48440, `2` 28 |
| RDDF0801.dbc | `d8fd2676df3696d9d338f804f931cc538878f3e1b77933caed9ff38e116c704a` | 463062 | 7754 | `0` 6729, `2` 1025 |
| RDDF1201.dbc | `ee24bdfcbd6279ab879141b66bd0aa6a6196963c870fd15dfe7249ecf9733a7e` | 1081971 | 15111 | `0` 12939, `2` 2172 |
| RDDF1506.dbc | `551a579813d31e59514ceb0a39a9a3bc962b8df28b8ce1e5c18b4fbac9790860` | 1132811 | 15412 | `0` 13190, `2` 2222 |
| RDDF1507.dbc | `8c8e2d99b182636fc47498f2bafc19fd5a7e1a0731c176f33c40f54960ad5453` | 1166234 | 15557 | `0` 13116, `2` 2441 |
| RDDF1508.dbc | `0cea53e1bb50aaa16cc80eb13276e4fd7302e0365fc291324611911c99f50658` | 1073135 | 14489 | `0` 14450, `2` 39 |
| RDDF1509.dbc | `593884a1b5616cd2a2af58ac19f1fc42b484e6079fb0a156b834cb36cd4513fa` | 994501 | 13678 | `0` 13629, `2` 49 |
| RDDF1510.dbc | `eafe9c446acac0b872c3f4fcaa868d2f8bfe99ed6137522a2a79fd11eb0dad74` | 936810 | 12829 | `0` 12797, `2` 32 |
| RDDF1601.dbc | `3048ecf0c9147f507725f44d4dfb03a75a2127415a2f154d2009066e34a6d583` | 983353 | 13128 | `0` 13098, `2` 30 |
| RDDF2512.dbc | `d4c111a1fd34debe6b793aeec306e0f38cfd729d8326beba6d162f234c3e8730` | 1632157 | 20360 | `0` 20297, `2` 63 |
| RDES0801.dbc | `18ba01c3ca88b556a208c689d81bf58c19be8e73f949f4b13de1bc93a5bce3d0` | 599540 | 9502 | `0` 9030, `2` 472 |
| RDES1201.dbc | `4f47bc2a6bf69a9fba2ffa9da5b1b9b7262200e729dd4c0e57626ba1c7897c2f` | 1281519 | 17509 | `0` 15674, `2` 1835 |
| RDES1601.dbc | `12111b4880aa7c397a0a43a16d946529ff1efe00a02feb7e378c94f74a99874a` | 1451513 | 18956 | `0` 18909, `2` 47 |
| RDES2512.dbc | `ac8c7142b1133ee6c44adf0fa867fc9335d0d1077d43cd74f1f2a7a6430ff8e3` | 1982866 | 25613 | `0` 25581, `2` 32 |
| RDGO0801.dbc | `f117d0e81ef106ac791c5d5a9e04264c8bb908def51a1d11d4930ab44e2eff9f` | 1565822 | 26465 | `0` 24945, `2` 1520 |
| RDGO1201.dbc | `5b6c23df17c1f49e633e77f059d657ef24ba3d4a477dcdd0a4a7cc8bceb608e0` | 1905518 | 28427 | `0` 26121, `2` 2306 |
| RDGO1601.dbc | `9c07f45d2ef5577dba3b9ca93d3cb605e47e49d4285641a58876fcd38f29989f` | 2008223 | 28199 | `0` 28196, `2` 3 |
| RDGO2512.dbc | `fe36a273314aafd24e755f12e012ea98b16796466e717758c32b07312bcf303d` | 2791654 | 37218 | `0` 37207, `2` 11 |
| RDMA0801.dbc | `4364e04d3ce87e3340195e08fdb36bb0a6e654f05f0ff963882fc320d94ffe27` | 1064563 | 21417 | `0` 21052, `2` 365 |
| RDMA1201.dbc | `155e4e550c8513a80a226231201b719a73b4e2e3bc828f6b4e79128085d99233` | 2078201 | 33818 | `0` 32344, `2` 1474 |
| RDMA1601.dbc | `76cf5327a99f241b7704edb933af3b3f5872bf2ad273624d32733403691114fc` | 2328574 | 35088 | `0` 34723, `2` 365 |
| RDMA2512.dbc | `f63141a68a291ceee339b892790835574c5d388a5b05ffeab6ca5fc4c5491925` | 2758504 | 40293 | `0` 40189, `2` 104 |
| RDMG0707.dbc | `46196689ebb59b8c915a2a7075efc10c6d802131abcb515b5b2ce51a999c780e` | 6825317 | 98408 | `0` 90921, `2` 7487 |
| RDMG0801.dbc | `06ce4974f52e58b1ebade62a7e1e4bc10c87b9ec2bea5498fc16188a4c7ad204` | 4357193 | 67509 | `0` 64832, `2` 2677 |
| RDMG1201.dbc | `a2073e91a6aeb39852cc0467dabe8356c7ab3307220acaf14755dc7466c97012` | 7229369 | 96614 | `0` 85201, `2` 11413 |
| RDMG1412.dbc | `f4f38b21d0b33013583d6cf3e6b438736042e2049ab5e797059739d5d6c8d854` | 7446241 | 97814 | `0` 85533, `2` 12281 |
| RDMG1502.dbc | `025052fdffd2d951fcd7cbd4d33bcb25f276ab2b93112750abccb9cba458db52` | 7551575 | 96126 | `0` 83306, `2` 12820 |
| RDMG1506.dbc | `f4d142377b53a3f6d8140cfef376bb13a3b753736247f6db558185c3e81cd4ad` | 8157788 | 104615 | `0` 90573, `2` 14042 |
| RDMG1507.dbc | `f301baa81190393e70f8bc82ce59cef4c93fbdd818316f90311dd731cf6192bb` | 8106342 | 103890 | `0` 88958, `2` 14932 |
| RDMG1508.dbc | `8d8c421be35d251316e1ba626444541aec189e8b805b3e47af618b4633d6adc0` | 7771783 | 100167 | `0` 100083, `2` 84 |
| RDMG1509.dbc | `eb76ad3007fc4600a528d55ec259ec5878f5209e81d930e0493caedc3eadd248` | 8022017 | 103236 | `0` 103149, `2` 87 |
| RDMG1510.dbc | `68400265cb48352fd586973e45d61e826be901e74b756f43addd8967569a94b2` | 7813864 | 101034 | `0` 100955, `2` 79 |
| RDMG1601.dbc | `e146c2f419fc6394ca21f6ee2864b95cd2fbdaf7592a980c1bb36130f6a34943` | 7605837 | 97833 | `0` 97747, `2` 86 |
| RDMG2512.dbc | `1f8e56e7aee39a4a0e2486f03413386061f197252ecd25000c48a423fc368cd8` | 10040304 | 128022 | `0` 127987, `2` 35 |
| RDMS0801.dbc | `09d6fd890a4b290cb88e12e00c66aaba475964c3f7d13a70388d873305a1c7c0` | 618944 | 9636 | `0` 9146, `2` 490 |
| RDMS1201.dbc | `43fadff2f71290c242d77fafd49e0d734fd9a61c1a3da13cd033c1896d7ddcc2` | 849807 | 11936 | `0` 10839, `2` 1097 |
| RDMS1601.dbc | `b5f29d49154e3e026e291a245961fbfb58d5c9e16ae10b09da280d9899ef5910` | 1041446 | 13732 | `0` 13715, `2` 17 |
| RDMS2512.dbc | `a9956bdae4dd6abaed71e37dfc25eda719571a8c52356fd0f4e021cd17240f50` | 1256472 | 16193 | `0` 16191, `2` 2 |
| RDMT0801.dbc | `b596449d6bc34c53092f2478ee43135fe2204055e6e16fd29f247a9ef5331383` | 623545 | 9975 | `0` 9529, `2` 446 |
| RDMT1201.dbc | `e6ca9867c4a97c17e9332f73a06a9aa01c8252e9fe1fb6b28c45ffcdc75377c6` | 936597 | 13512 | `0` 12468, `2` 1044 |
| RDMT1601.dbc | `86857d02c2ec68fd9910c3a7e725e802b17adc0009874d9abdcdaf8e15f2d949` | 1161922 | 15805 | `0` 15749, `2` 56 |
| RDMT2512.dbc | `c8444a494d944eaabe1f9af9793dc8b7e2057091b9ed2fe667b855f033019c94` | 1540767 | 20653 | `0` 20653 |
| RDPA0801.dbc | `03337aeb2b84a9dbbc7521a1664b43ba4237439fbe7e244a36a55836cb941326` | 2050198 | 38628 | `0` 38042, `2` 586 |
| RDPA1201.dbc | `0f2f00d540e3e5a8468821763728155657bd2b634147ead02af2e9b62806ae31` | 2607609 | 42778 | `0` 41117, `2` 1661 |
| RDPA1601.dbc | `6d9ea813af736595931ae6b6bd13a13398d634bc01343fded0bdf8cb203b261e` | 2420770 | 37348 | `0` 37319, `2` 29 |
| RDPA2512.dbc | `6d5896f3f5f6adf9524166a834500f4789e08792fb0c34bf805f5ad0713d0c51` | 3414115 | 48817 | `0` 48811, `2` 6 |
| RDPB0801.dbc | `88f23e8fca1d3a956e362fc29d6786b30f24403e568ab0bdf7164aa07add7cba` | 1049842 | 17126 | `0` 16217, `2` 909 |
| RDPB1201.dbc | `cbfc84b31b0978fa13b0148f1bbd276dd5d071521d9850726f7368820176e989` | 1141324 | 16259 | `0` 14673, `2` 1586 |
| RDPB1601.dbc | `8ac64383afdc3a71250bf2cbcd13f50951f3585628173ebc635353974fe972cb` | 984103 | 13646 | `0` 13635, `2` 11 |
| RDPB2512.dbc | `989bb9fcaf953703d40269b500f13dd3508604ed92c1f001d4e50be4e1b14546` | 1501361 | 19260 | `0` 19240, `2` 20 |
| RDPE0801.dbc | `a19eee31d7c75c70dcc61d8942da2de3a84c689b3592987cedc3127112b99cc7` | 1489520 | 25390 | `0` 23739, `2` 1651 |
| RDPE1201.dbc | `35dad3dfec6c394e2003a48f6104b956b0101a1b26482b4cd27aca5b8d572772` | 2980539 | 43116 | `0` 37777, `2` 5339 |
| RDPE1506.dbc | `f5355845753d88bced26f49335f73b3bc2c8e32d83bfe9e0809a43deb4305a2a` | 3372778 | 46805 | `0` 39221, `2` 7584 |
| RDPE1507.dbc | `1088fb14bdded08a2fe6e8d1a20832619e43e82f6857887009b25f35608de116` | 3269421 | 45755 | `0` 38576, `2` 7179 |
| RDPE1508.dbc | `507b3c484cfe96bc3018c00d59da91f033316c853f5cd60d30b578b3af3e990c` | 3298973 | 46450 | `0` 46438, `2` 12 |
| RDPE1509.dbc | `68eb8ca75dc73d46ae762cdbbb6452a4be7a9e60d3328c7d7df90f2a235cebf7` | 3187160 | 44514 | `0` 44512, `2` 2 |
| RDPE1510.dbc | `0f61ca79398091fa40b06ae4e6a0009577c8ae32e374648137db46e2a1e0e080` | 3175668 | 44387 | `0` 44383, `2` 4 |
| RDPE1601.dbc | `f68f634da1d45b6bb3f60f989613c0566f7c394f071fa1b7c4a6f3874bbbe674` | 3182632 | 43928 | `0` 43926, `2` 2 |
| RDPE2512.dbc | `6e73e0169857423e23c5c7b2b8634a4c048cdbd019b1ceae61e31bb9a4e69d2b` | 4153035 | 55935 | `0` 55926, `2` 9 |
| RDPI0801.dbc | `1da2d97af82a734078782f10104142035013d9fa68014f44c976c976732107df` | 927125 | 15878 | `0` 15603, `2` 275 |
| RDPI1201.dbc | `38f79bd22a53a781bf7a28b7d26aa491a17594c3312334fb184403f23b62a29a` | 1289545 | 18994 | `0` 18088, `2` 906 |
| RDPI1601.dbc | `2f7ea8f2e0b8e7e6f8a3d0b00b9db2ba0bdf7cacc52a385ba1773fd56657cccb` | 1272221 | 18038 | `0` 18038 |
| RDPI2512.dbc | `3720bb785b33df481d572872e861a9e5625de32747ed257ccf5f937251d2bfce` | 1428355 | 19014 | `0` 19014 |
| RDPR0801.dbc | `be9aec235d3ffd2481cb482a832dd3fa71e8b156352f95fdcc64e9b5574cf825` | 3206594 | 51180 | `0` 46811, `2` 4369 |
| RDPR1201.dbc | `0a935da7c6bb8b11877c571937db4ba305e4aa91997a7c9c02aa3b7860ebc8fc` | 4678129 | 64290 | `0` 56229, `2` 8061 |
| RDPR1601.dbc | `783591a7530ee2cb97c56d434e7d1a40d8dc6e293288466cf084a551a748a3ec` | 4812925 | 63458 | `0` 63435, `2` 23 |
| RDPR2512.dbc | `df5e4ede0d85f9fe7a4605445b11333cec5a6d0b1b4f2680713e16b84a9c8101` | 6875278 | 89610 | `0` 89595, `2` 15 |
| RDRJ0607.dbc | `a1ed7068256ed24ada0d298158e3040c787b48dfe86316302089fb0e9917c282` | 4182442 | 64021 | `0` 61775, `1` 335, `2` 1911 |
| RDRJ0707.dbc | `59e27109f86da7e5a90235d6b9f4d58a9c01363fdfcfb6137b83872a045bd390` | 4255506 | 67136 | `0` 64098, `2` 3038 |
| RDRJ0801.dbc | `6a362242dcb881099929eef7a13f75a92ee1b46cbc1f98ff996354afceb37b49` | 1970037 | 34859 | `0` 33511, `2` 1348 |
| RDRJ1201.dbc | `742d3fd52030906d21a986a86d2b10b5e48c8d19ff5ebcff85db48435e41cd8a` | 3636795 | 53068 | `0` 49702, `2` 3366 |
| RDRJ1412.dbc | `562ade2be97e4b433649bb224a5c5302cb67ddb7c42112a2d981a46ce3e58d35` | 3881820 | 53386 | `0` 49569, `2` 3817 |
| RDRJ1502.dbc | `4751eec8dd4515b84881917d10e5bb8443a580db29c5e3ddd0198d9d7bf840be` | 3984397 | 55076 | `0` 51197, `2` 3879 |
| RDRJ1506.dbc | `738edad25b994c3937c1bb03c789ea14d670e842006a28a3864f7102f41a80ab` | 4472757 | 61764 | `0` 57452, `2` 4312 |
| RDRJ1507.dbc | `c492f5d65f2fbac33e0579601cd5e7fe330a38b1d9c06e29905b49148e2d8470` | 4701652 | 64452 | `0` 59747, `2` 4705 |
| RDRJ1508.dbc | `0655a57bc3591714ef865f0d491dfb97cb4adfd7017187c6d2a0590f442cb9e0` | 4517633 | 61960 | `0` 61754, `2` 206 |
| RDRJ1509.dbc | `3d0dc77f953a5cb6a711d753be7e8b51dbcb5b8c8eb3c39f8ced56d753c7bc41` | 4357324 | 59714 | `0` 59555, `2` 159 |
| RDRJ1510.dbc | `d49bcbf05c0995d531a1544cb558a50b6a33e35a48bcea1692a056d690676657` | 4441898 | 60483 | `0` 60293, `2` 190 |
| RDRJ1601.dbc | `ff0af5d0359ddd7091395eea46e1f01d8f5e27c642a2d739e456c2f4eb727033` | 4187567 | 56877 | `0` 56637, `2` 240 |
| RDRJ2512.dbc | `93d6e196b52c1a5864437e6a97f8a041af71642dfd082179e4247719e61bd36b` | 5909820 | 76232 | `0` 76157, `2` 75 |
| RDRN0801.dbc | `f3e93d1c76123edc4a8c9fb986e9ca9c2e7186bbf82c62b981f38b74f6250cbf` | 573433 | 9916 | `0` 9615, `2` 301 |
| RDRN1201.dbc | `437863e108abb46a879a343ccc9a7d790146b94af1bb1d4f236598f6d0b74880` | 896455 | 13551 | `0` 12399, `2` 1152 |
| RDRN1601.dbc | `8815ac4345f7951e530dff5b50e3593a7572c0eacd62b8f9e1a0de04c80176ca` | 924489 | 12793 | `0` 12684, `2` 109 |
| RDRN2512.dbc | `6453c7d81a3d6b5b24cdc548af3e6323b077803665281b5b481f505e1fd5ea3f` | 1293284 | 17704 | `0` 17693, `2` 11 |
| RDRO0801.dbc | `c50dbfb6239025119bf2eb79e482ebb4284fc2f4e48fc240f37bca979ff6f868` | 223052 | 4142 | `0` 3960, `2` 182 |
| RDRO1201.dbc | `df9b50a9d2142cc7029f7edb6d205f694f3e37ac1c6eaa9db0588ee183400586` | 481274 | 7998 | `0` 7539, `2` 459 |
| RDRO1601.dbc | `baede1b3f33727ff239a2c60a318c23f0adec27eeab1c458c473184eee545b7d` | 612200 | 8956 | `0` 8920, `2` 36 |
| RDRO2512.dbc | `25fdb0528ed640dd9ebfd32dc0c2907dc66ce47212a3c1da1a270235af5b67e4` | 804859 | 11527 | `0` 11511, `2` 16 |
| RDRR0601.dbc | `8a2d386ef611bec916021a6702e8d64b7892197562915081cb4ab55fab39d9ae` | 58284 | 1402 | `0` 1384, `2` 18 |
| RDRR0602.dbc | `58f6f1867b18b0425fe3f6871f82df9d4abc20108ca5ef30c32f4ea8345931e2` | 68848 | 1604 | `0` 1567, `2` 37 |
| RDRR0603.dbc | `38fd6fc225ce4322e7af7c4721d3ae4f25638eb69a3a9340732e063a5825e15e` | 67483 | 1558 | `0` 1467, `2` 91 |
| RDRR0604.dbc | `2c70974f7d49566e804fb64620088d5fc1ada92e715d435a969776d836559c6a` | 99701 | 1774 | `0` 1709, `2` 65 |
| RDRR0605.dbc | `b8290d920c72d46a7f1ed99844617df7380010b255fae1d96a580a9fea098f98` | 103136 | 1814 | `0` 1747, `2` 67 |
| RDRR0606.dbc | `6bef7eb173da28aff61ede45dde27784a5da4bec1b85758a336d47210c3438c1` | 98324 | 1768 | `0` 1731, `2` 37 |
| RDRR0607.dbc | `01d231a19ae9606a8896e6b73fdf1e0b3292b0cd41d9222cdff34fc310acb01b` | 94674 | 1695 | `0` 1657, `2` 38 |
| RDRR0608.dbc | `d8d32cfd4df1556bcdf19a7cdf910c602f515425565f72ad0e692afa031a72f1` | 108826 | 1820 | `0` 1776, `2` 44 |
| RDRR0609.dbc | `eec32aad6999f7a96de86e87ac00ba4052007c2de3ed8de41f09159a38f3e0ad` | 97873 | 1691 | `0` 1631, `2` 60 |
| RDRR0610.dbc | `78bf9f850fb28453e518bc6517e4ed5b91b20457cfcd32cb2872f10a015a7a05` | 108575 | 1984 | `0` 1908, `2` 76 |
| RDRR0611.dbc | `05acea7751e678d7eaa0e7d3be8b7532dab476366d2a80be58c017ca8338b5ae` | 105101 | 1808 | `0` 1743, `2` 65 |
| RDRR0612.dbc | `36fb18481652a718194a02c2fc84d2f60bb15dd9eb4e272f09074c0ab97e0ecc` | 104865 | 1812 | `0` 1742, `2` 70 |
| RDRR0701.dbc | `bbbbf87a999743f76aba404c31adc6c29ecb339e9d7e44b1bad5b544bc2a5afd` | 93165 | 1572 | `0` 1491, `2` 81 |
| RDRR0702.dbc | `4e1d7bbb779fc8f88ef8861f2bc0d0e0a7f6d479d086bd384dfd109ea3901e95` | 99366 | 1703 | `0` 1639, `2` 64 |
| RDRR0703.dbc | `200f47d2f0d530653c2a27e3823ded69e0fee2c7e54934457810c4fbc2c86270` | 95338 | 1730 | `0` 1706, `2` 24 |
| RDRR0704.dbc | `e9ba3bf4ce528995e506bb15b93dc8c94fa955344f43ea11cbf878281e7556e0` | 106194 | 1874 | `0` 1818, `2` 56 |
| RDRR0705.dbc | `43443c457e24e006a6834c84840db2885c546c68de2562d91a2fe001372a36c3` | 106009 | 1777 | `0` 1747, `2` 30 |
| RDRR0706.dbc | `e605f5ff5bf513dc5ef254f93041be7dad4268719eb7a618e512088b0b880a2c` | 104724 | 1936 | `0` 1861, `2` 75 |
| RDRR0707.dbc | `847b56db28fe32a2b89ec3b969685cc32c047975f4a4d36d50d309755302ef54` | 94574 | 1554 | `0` 1514, `2` 40 |
| RDRR0708.dbc | `84c4c24edfc61496a64fc11c4adc2c941cf5793d8d0a1903ef75872957c31343` | 88328 | 1500 | `0` 1450, `2` 50 |
| RDRR0709.dbc | `c2be5de2ee0021db02be8d5be5c89605e33555b459f3ddbf2bf57b49fd503b81` | 120721 | 2045 | `0` 1969, `2` 76 |
| RDRR0710.dbc | `74899f86abb2f9a470566198ab1c578704e6bbe78391fe1a8473f9ee56da67ce` | 100164 | 1737 | `0` 1696, `2` 41 |
| RDRR0711.dbc | `555e1c80f887ac4010f5aabe2e1af9b8f10d6564c64490cf24197e861e2fedff` | 107251 | 1893 | `0` 1822, `2` 71 |
| RDRR0712.dbc | `d6c5838ec19f4cd595f44835cbc3468bf8691299fccdbdbde13ae4d9292d3371` | 93077 | 1496 | `0` 1467, `2` 29 |
| RDRR0801.dbc | `ad3817afbe19f8087415f5204a677893dee767a802de093d84bb193577c2d4e7` | 75358 | 1475 | `0` 1404, `2` 71 |
| RDRR1201.dbc | `3f1ebc51b1e2aca35348d7440a982576c6fdd446762fb9a57373bd3e3e63eb48` | 155584 | 2289 | `0` 1970, `2` 319 |
| RDRR1506.dbc | `9157998eb6aa5a66486a5987a5c2404bce70d94d4d6c979639201bf4eb8c5097` | 179515 | 2531 | `0` 2134, `2` 397 |
| RDRR1507.dbc | `90e7a1b808db97f509e853b1e3013d9974ae618df22bec4a0b233ee0fc7e343b` | 230058 | 3110 | `0` 2537, `2` 573 |
| RDRR1508.dbc | `b23306fe9c64401afe712468023218e3302e86772f9fc393892bc208df269cc9` | 248108 | 3454 | `0` 3422, `2` 32 |
| RDRR1509.dbc | `bc9c80c56347b3fec35b6a42f317ab0172060b57ffa34a27a638959c63d5896a` | 219242 | 3172 | `0` 3121, `2` 51 |
| RDRR1510.dbc | `43451d35beb13a7517a764e8bec0845f2a99fcc7707c75862a4e10837f220302` | 228697 | 3201 | `0` 3140, `2` 61 |
| RDRR1601.dbc | `b5426ef0c50304897e6e92b6615a0b8382f61814ccd78f3b15f12fef1dfb98b5` | 196012 | 2748 | `0` 2712, `2` 36 |
| RDRR2512.dbc | `75988926198221313d854ca8bf80e23007b2a110c3385d3fb64ab2222aff5df9` | 157616 | 2128 | `0` 2123, `2` 5 |
| RDRS0801.dbc | `8d25b1e34bffb60c8abb175ef39af91ff4f5f3327d3bbdf353b9170c118c651a` | 2780100 | 41729 | `0` 38052, `2` 3677 |
| RDRS1201.dbc | `8bd1b90790e4bfd08853185871d635b32bacefac6615f3e3291e2de98ca775e9` | 4268871 | 55459 | `0` 50066, `1` 2816, `2` 2577 |
| RDRS1601.dbc | `f089f0e203ea92992aca2c9aaba774f820254bbc211aba71d2dd5ee3ce58495e` | 4516083 | 58456 | `0` 58437, `2` 19 |
| RDRS2512.dbc | `baa03998fc041c61b3ad2fcb24c91ff0549f85a628c65a5df60ab7a4d871783e` | 5486232 | 70967 | `0` 70965, `1` 2 |
| RDSC0801.dbc | `7757608f37219b9d284dcdbe2f4641d216ed6c13bb6313a03a8f0738affcf7d2` | 1619551 | 23728 | `0` 21854, `2` 1874 |
| RDSC1201.dbc | `a2802efdfe8f508ec767d4674d5769dbce6afc4f26776462f5b03aad564d8bdf` | 2440187 | 32159 | `0` 28420, `2` 3739 |
| RDSC1601.dbc | `f2f89e69f67f2ae87cd4efa7ec44215423448d56d9c338e78f2e4ba47c590a43` | 2825319 | 36944 | `0` 36944 |
| RDSC2512.dbc | `9cc6322a4167d3836a1fc229872a07ae6e8ad20f648bded0052d3242d7349a22` | 4382328 | 55204 | `0` 55204 |
| RDSE0801.dbc | `4abed05e11b06f28275772417f711da7d7cc4d561fafc4d39cb2a57f97ba631f` | 309622 | 5832 | `0` 5704, `2` 128 |
| RDSE1201.dbc | `133fe250bdcfbbca55220da3e7d5024eb004d55e5e0cd0ecb22b3e204bede33c` | 516538 | 7380 | `0` 6643, `2` 737 |
| RDSE1601.dbc | `559316bca769156357476f693ac66713c8e8ad9d715b861de46af67165e975f2` | 496048 | 7203 | `0` 7203 |
| RDSE2512.dbc | `272cb12866dc82443fe21f94ab23699acb60ead0fb223320dabcc66c400f845a` | 797886 | 10417 | `0` 10417 |
| RDSP0707.dbc | `b5dd07099e4bde0330ec4982c2812b3eaa37475035acb3094313818181d1dfc5` | 14312551 | 209522 | `0` 191183, `2` 18339 |
| RDSP0801.dbc | `f2cba06b3b3d4d13d6ed3cfe69f83e46443f3e1700bc694e637fa5847c0671e9` | 7799792 | 125361 | `0` 116519, `2` 8842 |
| RDSP1201.dbc | `3edf83e541c3287df66110c3222092d6f1c98b317a6f09804555d80f7244bf07` | 13891006 | 193264 | `0` 171160, `2` 22104 |
| RDSP1202.dbc | `4c65b4f25102bc1d36046118ec569870d8aa1921e50bcfee4eed57cbcaf6bc45` | 14230401 | 198234 | `0` 176852, `2` 21382 |
| RDSP1203.dbc | `8c33e922ac52f1aad4a8310a153258755b7cdeb45f9afa7e5bad3d76a3cbb9ea` | 15531488 | 215670 | `0` 191602, `2` 24068 |
| RDSP1412.dbc | `c744f524f7a98dc02b30aef346d0efa693dc00d5baeb29a47e378876b808c3ec` | 14214477 | 193789 | `0` 170174, `2` 23615 |
| RDSP1502.dbc | `8011928ad0cb9119ba6ef1c95df8471a44e52a70855624810b3c30ae79b5e8b6` | 14899189 | 195822 | `0` 173285, `1` 95, `2` 22442 |
| RDSP1506.dbc | `0638cb3878a1a9def4f013262335fea02124567ccc0d77692a8479b1ea3f8d7a` | 16277144 | 213252 | `0` 187648, `2` 25604 |
| RDSP1507.dbc | `af743d283211958aeeb981ae7dddcc3c1575b3332be9f5bee8a1ff329ddc145d` | 16273929 | 214708 | `0` 188701, `2` 26007 |
| RDSP1508.dbc | `16c463e68bab5b2cf091f632a77141073b342fc1b9e3e8c7ccb239b13c3f6c1a` | 15990071 | 211432 | `0` 211395, `2` 37 |
| RDSP1509.dbc | `45e2c92479a7aed34253f9d7e0c3a6fcd7a4ef8a190f1fe4e681af50bcc87445` | 15646147 | 207071 | `0` 207029, `2` 42 |
| RDSP1510.dbc | `659facacfb221384961ff89c6289c22013116c2cafc11216d1ee3f47e612d496` | 15701007 | 206868 | `0` 206851, `2` 17 |
| RDSP1601.dbc | `c14bcae03b5adecadd84f7983a30faef0ceaeea0e1a3bdf7d6cfec14f8b3c7f2` | 14818924 | 193621 | `0` 193606, `2` 15 |
| RDSP1902.dbc | `4653fb8f96fefacfb3a47f8f7fc1b1d1591c56be0c9800fbe0fcddf82dc254a0` | 15690982 | 203599 | `0` 203572, `2` 27 |
| RDSP2001.dbc | `ea611bb554aa00062c8aee2c3041d3065b2635938cdd32d6ce6636cb91436478` | 17083017 | 215766 | `0` 215761, `2` 5 |
| RDSP2002.dbc | `78e3493a21d52b6ec5dbb9b02869667b579bcdbccf1e8f1c5d178eb229a00678` | 15807732 | 205588 | `0` 205567, `2` 21 |
| RDSP2003.dbc | `a19bd181d39674213ee5a4238fe950ee486a9bf8df7e0bc990740aabdf68c417` | 16136638 | 208684 | `0` 208662, `2` 22 |
| RDSP2004.dbc | `00511f50e3bcfd6e86724a50d60e9013aea190e1f3f52fa2af86371b95c47aa3` | 12311769 | 158154 | `0` 158139, `2` 15 |
| RDSP2005.dbc | `f2c21020ea246a53039f899b13bc4465d67737d837c519b393cfa0f22b1bc94f` | 12616169 | 163154 | `0` 163147, `2` 7 |
| RDSP2006.dbc | `ad036b4872637ef9e0613a3ac1bebcce6ef5696c9919fd50dda63da6afb9f3a8` | 13217058 | 172034 | `0` 172013, `2` 21 |
| RDSP2007.dbc | `8adcc84f3cff9fdca5510ff02fcfaa6a1cb30e5d76139256af428e861ddd6a17` | 14415177 | 186658 | `0` 186650, `2` 8 |
| RDSP2008.dbc | `a46690ce47cdce0f97b3eae98a524645c1e7c2cdd8d1c7cc6433fb0cfe8c4385` | 14271920 | 184527 | `0` 184507, `2` 20 |
| RDSP2009.dbc | `6704c2ad52186cab31903bea91301d7a4bf2783f5be2dda14981af925bcec7a9` | 14856531 | 190926 | `0` 190908, `2` 18 |
| RDSP2010.dbc | `47960b7bef955ddaceb9a678e9233ec24eba7a467fb99482ea6d12eb49c3f03b` | 15268036 | 196014 | `0` 195995, `2` 19 |
| RDSP2011.dbc | `af54813ccc1ee57cb05a2d676f390f26f4719534bf34cdad25f84901245aa715` | 15181331 | 195262 | `0` 195241, `2` 21 |
| RDSP2012.dbc | `beb0372a2615932adcaf15e809216cc85497ab0a4e5526fd5f175d88a704d125` | 14609333 | 188128 | `0` 188120, `2` 8 |
| RDSP2101.dbc | `226547f04f23b9f18db84b402bcd02b66c47f37ebf366d534ad63abe5c5e7f3c` | 15281896 | 195978 | `0` 195959, `2` 19 |
| RDSP2102.dbc | `c679e2a82871de03fc946682fc34ba5e6f25354f1237ac0248a01da006306291` | 14730967 | 191120 | `0` 191102, `2` 18 |
| RDSP2103.dbc | `f631714d40a47ab461d9e1d219ae05e51e176d929a5c018f1083cd45de163d2b` | 15251695 | 199489 | `0` 199484, `2` 5 |
| RDSP2104.dbc | `3d1586db27ae09be6dfe7e541774a4692998bc2dc9ebd051ddab40a4a03ffbdf` | 14650762 | 192501 | `0` 192485, `2` 16 |
| RDSP2105.dbc | `aa7447a8686b7c24ad699b181bce7225cc5a6ae6b15530d87c68e8258330bfd4` | 15374265 | 202051 | `0` 202031, `2` 20 |
| RDSP2106.dbc | `7e42253f6676ccc70d58ca89ce30912f0356a98deaf2ccb25d3f4b742a9d619b` | 15398229 | 201017 | `0` 201001, `2` 16 |
| RDSP2107.dbc | `429bc327419e28e73728558adf8f83007cc14f7b69bf49a82da6c5662f24cab7` | 15651610 | 200591 | `0` 200568, `2` 23 |
| RDSP2108.dbc | `cf6a9cf0cfeb508aa4e467f892bbdd4aad3a21ea6ce8206ba8cb04471256070e` | 15748366 | 201312 | `0` 201297, `2` 15 |
| RDSP2109.dbc | `1bebbd6a2a72146df2c1465040a63ebe49bd8cc936322e6d29f3c38ac380d59d` | 15398983 | 196878 | `0` 196858, `2` 20 |
| RDSP2110.dbc | `39e252c49cff03f25b1f131b2249070cfabc78ae42fe0843f9f5c453fadc23de` | 15324314 | 195013 | `0` 195001, `2` 12 |
| RDSP2111.dbc | `acf6a9bb25509cb2de0bc494ba29bb9afb642de966cda8f1432d7ad7dda7b938` | 15326784 | 197590 | `0` 197572, `2` 18 |
| RDSP2112.dbc | `7f96f44bd8188eb0f7c3924149830449789343487322c03872c10ad88569317d` | 15969903 | 203150 | `0` 203134, `2` 16 |
| RDSP2201.dbc | `8ae4e3a106dbdd27e7c1a75591f4f692255364d8238044451fb00b7d85346c68` | 15549230 | 199070 | `0` 199057, `2` 13 |
| RDSP2202.dbc | `adde15599eb92152b61316c86122d4e0f3fa9580dff02a51bd4cec4ccc04d335` | 15047971 | 191763 | `0` 191755, `2` 8 |
| RDSP2303.dbc | `e6c920afdb0f432f93724893a731b22cb9303c2bed8a3342ed0c161f2e600b6b` | 18077745 | 233649 | `0` 233629, `2` 20 |
| RDSP2306.dbc | `e9507c7429b4dc8990639b90b70e2ea38d42547dde7594cf1f327aae8587a95b` | 18001348 | 232263 | `0` 232250, `2` 13 |
| RDSP2512.dbc | `976373cd79219b8287dcb3815f5a7b7b85c40ce542dce903e44591bc05159aa5` | 18300555 | 230747 | `0` 230731, `2` 16 |
| RDTO0801.dbc | `ba2e15f2f1b53a42e35c014ddaca4716d7b07651b1460fa5180ff482ed7bc723` | 418955 | 6665 | `0` 6210, `2` 455 |
| RDTO1201.dbc | `bb149fb60ebf4c6cd962c272a585f4713852b5e2c5d37c6b7c78b7ef41acd6a1` | 666210 | 9473 | `0` 8268, `2` 1205 |
| RDTO1601.dbc | `9fdb35647acef42416c6eb1c4de3d3e902c8f8e6325efef36cbcda8fff8709d2` | 438778 | 5847 | `0` 5838, `2` 9 |
| RDTO2512.dbc | `4a21a3a2c3c88ba8e6417eac0147e7f7334e46dd6bfd838d84bd48a1035f4099` | 596933 | 7773 | `0` 7764, `2` 9 |
| RJDF0801.dbc | `73e2baa25434eafa4a79f2ed26dcbadba29e59bf99ff22c03ece51ad79898383` | 11190 | 147 | `0` 114, `1` 3, `2` 30 |
| RJDF1201.dbc | `52f6993ff4a5964eb9d89ba18a0046d8eca6e1fe732e0a695ec8c8e4dc0777ec` | 10417 | 142 | `0` 97, `2` 45 |
| RJDF1412.dbc | `77ea777d73e6061d321cfea3354592e7260e082f101c6f8d9b00cbcace33fbb1` | 20633 | 292 | `0` 178, `1` 1, `2` 113 |
| RJDF1502.dbc | `c62641d2778fdcff27d127d7a9c5543d68d697e2b482d3e6d58109098132c9f0` | 27216 | 399 | `0` 250, `1` 1, `2` 148 |
| RJDF1506.dbc | `4c3320f0e99665fd25361ef9500ad8f4bdc3a86798a55d83d1ae496711ac2e30` | 18345 | 246 | `0` 112, `1` 15, `2` 119 |
| RJDF1507.dbc | `f11492d917230e65d43f7af65f8893b5c3a0e3b3a9429d2a93675b4cb88885e0` | 19393 | 272 | `0` 56, `1` 130, `2` 86 |
| RJDF1508.dbc | `eafb6d63241a8a5b9cbf4b42af459055b0684608571080c87383a7a991f2025e` | 18160 | 236 | `0` 232, `2` 4 |
| RJDF1509.dbc | `9f8400e84a673298a674fc0905fe344192d77033f3c66b8df99f58c6bdb37604` | 17953 | 226 | `0` 224, `1` 1, `2` 1 |
| RJDF1510.dbc | `da7ff369bf8dca6b8498a1f1bfc0c64d7bfe3b83e333337fea9c200ea2b0777f` | 19974 | 265 | `0` 263, `1` 1, `2` 1 |
| RJDF1601.dbc | `3b1fc544a31dbc891b4038fbe89fef9c0f3e9edec914cd5ccdbf4e2b0ea6b61a` | 19404 | 261 | `0` 255, `1` 6 |
| RJDF2512.dbc | `93f007de3556e1245325080fcee412ea58f3d7f189681e48bf6081022c25578d` | 22564 | 289 | `0` 287, `1` 1, `2` 1 |
| RJMG0801.dbc | `84171715db5b8f64e9be8058945996ff2f848e72293e545b30fac8414c8ba487` | 721974 | 12590 | `0` 9393, `1` 2450, `2` 747 |
| RJMG1201.dbc | `b6bfb49de62aa86e43c08acabcf1d38dbf078e900a67d8b7e3a1ff12ae347697` | 198614 | 3147 | `0` 2507, `1` 362, `2` 277, `3` 1 |
| RJMG1412.dbc | `25df2d023b3eada07fad5d1b275b19d2bd76e79db8636c2be01a7f7834a5d929` | 151561 | 2228 | `0` 1618, `1` 321, `2` 284, `3` 5 |
| RJMG1502.dbc | `0bcf82ce2ea2a757541a018ad8602fb3ca00273fe43fef95747f3f2bbb57a64c` | 106914 | 1507 | `0` 1064, `1` 226, `2` 216, `3` 1 |
| RJMG1506.dbc | `f64f6b84789e57712af51e8caaaf27a5e0307c479d332c6ff2e098b75438d10c` | 112415 | 1634 | `0` 1129, `1` 298, `2` 206, `3` 1 |
| RJMG1507.dbc | `510045fa08f58eb72dddb298523c8afa3059f9cf4097248e2d68ba12640e4998` | 118823 | 1778 | `0` 1278, `1` 292, `2` 205, `3` 3 |
| RJMG1508.dbc | `593fb553a39c97b59e888c6a1872520e7f1e29b8855674294d014bc56830c5f1` | 165213 | 2542 | `0` 2537, `1` 4, `2` 1 |
| RJMG1509.dbc | `cbb5282639e72bdb5851bf534e94c580fe3e5f179d0e3be53afb6b67672419f5` | 144119 | 2197 | `0` 2194, `1` 3 |
| RJMG1510.dbc | `4f66f9a46da357084a0b65d27393d45ba3c2e15856fd735a2a2e05df83450e13` | 113394 | 1713 | `0` 1703, `1` 5, `2` 5 |
| RJMG1601.dbc | `a995b5abfb64928f3cdfed2d562975da98f6760f57f6438202f71690038a1f7a` | 119550 | 1718 | `0` 1717, `2` 1 |
| RJMG2512.dbc | `2b1a493dfb49d0dc9b8e1475053cb092ce68181600067e21a8eb5d383480068e` | 253550 | 3984 | `0` 3982, `1` 2 |
| RJRJ0801.dbc | `3d9617ea2862f1aad26b3a660d2c6cf8ce4d0c98598a2f3dc3c328bdc38d3ea0` | 653526 | 12608 | `0` 11080, `1` 560, `2` 967, `3` 1 |
| RJRJ1201.dbc | `3a6b66ed99e0fa3d2ec7452ee2cc629acb44c857c46ae0e139552c19acab566f` | 422253 | 7401 | `0` 6074, `1` 1025, `2` 302 |
| RJRJ1412.dbc | `04ddf713c20a2170ecd3dbf5a6c82ca749151797bae7834a9527d1d60f772288` | 386228 | 7043 | `0` 4246, `1` 1099, `2` 1698 |
| RJRJ1502.dbc | `1a313eb5912e1a9f7db50749291106f528b2f611635c81c15af7a88a742f5df7` | 335385 | 5528 | `0` 3779, `1` 1498, `2` 251 |
| RJRJ1506.dbc | `1fd76fd3df4ab31f1a5cca3d39140259d6f954821b818833b5dcb89852b5ac87` | 373315 | 6139 | `0` 4204, `1` 1539, `2` 396 |
| RJRJ1507.dbc | `969b5ba5e27844c36e0a885c9e918551d19d1252911325660e567c2b71ff079f` | 297689 | 4871 | `0` 3386, `1` 1227, `2` 258 |
| RJRJ1508.dbc | `867d26b3c201b789916dc2fef62aac4451233404d953da16a7df96a5c5aa1bc4` | 270584 | 4305 | `0` 4295, `2` 10 |
| RJRJ1509.dbc | `879ae1caf82d46c062eee16cffd76c6b4ebb380da985b6e368c0392cce54ab00` | 286618 | 4561 | `0` 4542, `1` 16, `2` 3 |
| RJRJ1510.dbc | `e91b9f14f9e131c55a8f0e7231a9c7b197eeb35cb6c208e26c450e58af1c25e5` | 296264 | 4745 | `0` 4740, `1` 3, `2` 2 |
| RJRJ1601.dbc | `761a80a8df7c25f3fe1c246d8fd48387c0dfcc2430fcbfd080278116668c7fd2` | 356966 | 5773 | `0` 5765, `1` 7, `3` 1 |
| RJRJ2512.dbc | `e6d1f78fb39abe8d88cfe4088c0d820c953848ad2069a3d923bfa27429164966` | 235652 | 3747 | `0` 3734, `1` 2, `2` 11 |
| RJRR0801.dbc | `177b02d829ff475fc7567a7f682c7485f42013d538a586f1a8b1ebc435905058` | 4392 | 20 | `0` 18, `2` 2 |
| RJRR1201.dbc | `a4f01596d1577842b8f7b568d6510cdab38329f0b06795c01515d3603de79401` | 6861 | 75 | `0` 72, `2` 3 |
| RJRR1412.dbc | `bb95c28a8e71b51d16d31472eb109b9cfaf8fcdd6570516d4b18cffe53c24b50` | 4654 | 23 | `0` 22, `2` 1 |
| RJRR1502.dbc | `e08300f662f591903ae0458688ad47aaf33c34356d64f6c9c61fa16a59cab3ca` | 4229 | 21 | `0` 21 |
| RJRR1506.dbc | `5cb9ed35ae59dbee3c872eb6859d1354690340beaf9d7a0f474c8a9303c7caaa` | 5968 | 51 | `0` 47, `1` 3, `2` 1 |
| RJRR1507.dbc | `b4f5eb36e03ef8d9ddcdc22ce9bd75c1d4b2ab3d3e7bcde5cb5330c215c82bce` | 4602 | 27 | `0` 24, `1` 2, `2` 1 |
| RJRR1508.dbc | `1c437093840c282916fe42e416ad347b5b6f43f71c00e84813e6bf34639228e4` | 7785 | 87 | `0` 85, `1` 1, `2` 1 |
| RJRR1509.dbc | `74b4ccecfb51f4f85d463b5c328f4396ecef58293bb716123be5ab596d0aac91` | 8399 | 96 | `0` 96 |
| RJRR1510.dbc | `269d63aeec640153fbdfff159f7ca4383a80503f462633346e63209afd8a3326` | 10673 | 141 | `0` 139, `1` 2 |
| RJRR1601.dbc | `e4935070d1a19e5cbb59f055d1c8a4b899faeec87c6db7463b7e57092cbe15d0` | 9707 | 122 | `0` 121, `1` 1 |
| RJRR2512.dbc | `f25f157d2d21f06a7d932301c8b9c408301c899f121297f40c634775fcd7644f` | 9079 | 96 | `0` 96 |
| RJSP0801.dbc | `f2b9beaf7d223c244bb279ea2ef64078341b346434715b60bb219ffcc57026fb` | 1866973 | 34000 | `0` 29614, `1` 878, `2` 3486, `3` 22 |
| RJSP1201.dbc | `c246773c2075113c879b602cfb28779ddae79c994397b206d44c36e142a0a46f` | 858581 | 14235 | `0` 11603, `1` 1191, `2` 1423, `3` 18 |
| RJSP1412.dbc | `edfa3e2bb5827a1f529eeea800d38d4675036894155009db2fcbd1ce7f95b659` | 711738 | 11251 | `0` 8755, `1` 1184, `2` 1303, `3` 9 |
| RJSP1502.dbc | `58b0f38c3b2ae7bb9c3d34d73c3d6e0425952486828900fc5b37eaf35ca9d289` | 674565 | 10740 | `0` 8424, `1` 1060, `2` 1253, `3` 3 |
| RJSP1506.dbc | `c9ad69fdcd18a654871b2eade5cd9833b651d1ab9f490cd520976d957da7c27e` | 925373 | 15052 | `0` 12106, `1` 1173, `2` 1754, `3` 19 |
| RJSP1507.dbc | `fcdd09c2f5502cd40de8f6d7487cc2abdbc7c9f86303feaba03a5216eb871a87` | 752024 | 12051 | `0` 9344, `1` 1080, `2` 1615, `3` 12 |
| RJSP1508.dbc | `d665fafadb402cd8548842619acbca825a779ffe36137a4ba2f8f8fcfb02b296` | 747428 | 11933 | `0` 11921, `1` 1, `2` 11 |
| RJSP1509.dbc | `547f457f04cf165284b4f9c77000914cc597f711b58464a369fb2b5a3e73560b` | 818109 | 13345 | `0` 13344, `2` 1 |
| RJSP1510.dbc | `ff8672d3e10a5e80a2fe1ebd577b8a8b5b581ef2cfb3f6dd366091f80d7d323c` | 679353 | 11040 | `0` 11034, `1` 5, `2` 1 |
| RJSP1601.dbc | `26e0f2b0ca993b728b1030194e5ade911d5cd3ff606259e2b386d2a5869c8034` | 608053 | 9575 | `0` 9571, `1` 4 |
| RJSP2201.dbc | `2ea4a600fec594ce4dfb00075e5ae29a72b378b3375946c3b74c8ff50b76c241` | 621582 | 9912 | `0` 9909, `1` 2, `2` 1 |
| RJSP2202.dbc | `cadf30eec97f970949f63522171143cbd87f6c0101abaa2f44e1a2d95894d060` | 599573 | 9594 | `0` 9590, `1` 1, `2` 3 |
| RJSP2203.dbc | `f85760f7cf7befa7507266736e5ae5bda02b9b92cf5a7a020db30dc4e2873100` | 672103 | 10948 | `0` 10945, `2` 3 |
| RJSP2512.dbc | `de7eb0f5f723decd44ea5194a05fdc5028cb103b03b6f86ae3f795679e7b7db1` | 691782 | 11292 | `0` 11292 |
