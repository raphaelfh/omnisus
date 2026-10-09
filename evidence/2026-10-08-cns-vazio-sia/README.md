# CNS do paciente em branco nos arquivos do SIA — 2026-10-08

Em 2026-10-08, `census.py` leu 443 arquivos de
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados` (7,39 GB, 179.869.457
registros). Em cada um, contou as linhas sem o CNS cifrado do paciente: `ap_cnspcn` nas
APAC e `cns_pac` no BPA-I e na RAAS psicossocial. O CNS conta como em branco quando é
nulo ou só tem espaços. Os arquivos lidos foram:

- APAC de medicamentos (AM): todas as UFs em 2025-08 e no mês mais recente listado
  (2026-07; 2026-06 para MA, PB e RO, que não tinham 2026-07 no servidor); SP e GO em
  todos os meses de 2024-01 a 2026-07;
- BPA-I (BI), RAAS psicossocial (PS) e as APAC de quimioterapia (AQ), tratamento
  dialítico (ATD), laudos diversos (AD) e cirurgia bariátrica (ABO): todas as UFs que
  publicam a família em 2024-10 e 2026-07; SP e GO também em 2024-11 e 2025-08.

`census.csv` tem uma linha por arquivo, com a data do servidor, o tamanho, o SHA-256, o
número de registros e quantos estão com o CNS em branco. `autorizacao.csv` divide as
linhas da AM de SP e GO pelo mês de `ap_dtaut`, a data de autorização da APAC.

## APAC de medicamentos

| UF | Competências | CNS em branco |
| --- | --- | ---: |
| GO | 2024-01 a 2024-10 | 0% |
| GO | 2024-11 a 2026-07 | 99,2% a 99,7% |
| SP | 2024-01 a 2024-10 | 0% |
| SP | 2024-11 a 2025-08 | 1,9% a 7,1% |
| SP | 2025-09 a 2025-12 | 39,2%, 70,7%, 94,7%, 86,8% |
| SP | 2026-01 a 2026-07 | 99,9% |
| Outras 25 UFs | 2025-08 | 0 de 1.916.259 linhas |
| Outras 25 UFs | mais recente | 297 de 2.133.813 linhas; 265 no Amazonas em 2026-07 (1,8%) |

Os dois cortes têm formas diferentes:

- **GO** segue a competência. Em `AMGO2411.dbc`, as APAC autorizadas de 2024-07 a 2024-10
  já vêm 99,2% a 99,4% em branco, embora as mesmas autorizações tivessem CNS nos
  arquivos de até 2024-10.
- **SP** segue a data de autorização. Somando todos os arquivos de SP, o CNS está em
  branco em:
  - 96,9% a 97,2% das linhas de APAC autorizadas de 2024-11 a 2025-02;
  - 5,7% a 15,5% das autorizadas de 2025-03 a 2025-08;
  - 91,1% a 99,9% das autorizadas de 2025-09 em diante.

  Como as APAC de continuidade autorizadas antes de cada corte ainda trazem CNS, a
  parte em branco por arquivo cresce aos poucos.

## Outras famílias

A parte em branco em 2024-10 e em 2026-07:

| Família | Coluna | Outras UFs, 2024-10 | Outras UFs, 2026-07 | SP | GO |
| --- | --- | ---: | ---: | --- | --- |
| BPA-I (BI) | `cns_pac` | 6,0% | 68,4% | 3,3% → 64,6% | 2,6% → 84,0% |
| Tratamento dialítico (ATD) | `ap_cnspcn` | 0,3% | 70,2% | 0,5% → 72,2% | 0,1% → 77,1% |
| Laudos diversos (AD) | `ap_cnspcn` | 2,7% | 45,4% | 2,8% → 51,3% | 0,2% → 33,7% |
| Quimioterapia (AQ) | `ap_cnspcn` | 0,8% | 29,9% | 1,7% → 33,0% | 0,0% → 65,5% |
| Cirurgia bariátrica (ABO) | `ap_cnspcn` | 0,8% | 29,6% | 2,2% → 37,5% | sem arquivo listado |
| RAAS psicossocial (PS) | `cns_pac` | 0% | 0% | 0% → 0% | 0% → 0% |

- "Outras UFs" soma as 25 UFs fora de SP e GO que publicam a família no mês. Exceções:
  AQ tem 24 UFs em 2026-07, sem RO; ABO tem 14 UFs em 2024-10 e 13 em 2026-07.
- Em 2026-07 a parte em branco varia muito entre UFs:
  - BPA-I: de 27,0% (RR e TO) a 84,0% (GO);
  - ATD: de 0,6% (RR) a 100% (TO);
  - AD: de 0% (RO) a 91,0% (SE);
  - AQ: de 0% (MA e TO) a 95,7% (AC).
- Em SP e GO, os meses intermediários (2024-11 e 2025-08) estão em `census.csv`. Nas
  outras UFs, só 2024-10 e 2026-07 foram lidos, então esta leitura não diz quando a
  falta começou nelas.

## O que não se sabe

- Por que o CNS falta. A coluna continua no arquivo e vem em branco. Nenhum documento
  lido explica a mudança.
- Se o DATASUS vai republicar esses meses com o CNS. A data de cada arquivo no
  servidor está em `census.csv`.

## Reprodução

```bash
uv run --locked python evidence/2026-10-08-cns-vazio-sia/census.py SAIDA [CACHE]
```

`SAIDA` recebe os dois CSV. Com `CACHE`, os bytes baixados ficam guardados e são
reaproveitados numa nova execução. Um arquivo já presente em `census.csv` não é lido de
novo, então uma execução interrompida continua de onde parou. Esta execução foi
retomada duas vezes, cada vez com mais arquivos; a seleção final é a do script.
