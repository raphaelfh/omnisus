# SIH · AIH reduzida (`sih_aih_reduzida`)

## Em uma frase

Autorizações de Internação Hospitalar (AIH) do Sistema de Informações Hospitalares do
SUS (SIH/SUS), nos arquivos RD que o DATASUS publica um por UF e mês de processamento.

## O que um registro representa

- O dicionário da biblioteca descreve a base como "SIHSUS — AIH Reduzida (RD)" e não
  declara chave primária (`src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`,
  `title`, sem `primaryKey`).
- O documento oficial descreve o layout dos arquivos `RD*.dbf` para janeiro de 2008 em
  diante (Informe SIH 2016-03, p. 1).
- Cada linha traz o número da AIH em `n_aih`, com 13 caracteres, e o tipo da AIH em
  `ident` (Informe SIH 2016-03, p. 1).
- O documento não lista os códigos de `ident` (Informe SIH 2016-03, p. 1); os rótulos
  vêm do pacote oficial `TAB_SIH.zip`, `RD2008.DEF` → `IDENT.CNV`: 1 = Normal,
  5 = Longa permanência, e a faixa `0-9` dá "Outras/ignorado" a qualquer outro código,
  como o 3, que não tem rótulo próprio na tabela
  (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`). O Manual SIH 2012 diz que
  "Existem dois tipos de AIH: Tipo 1: internamento inicial e Tipo 5: continuidade"
  (p. 8). Na fixture de Roraima 2024-01 (`tests/fixtures/dbc/sih_rr_2024_01_mini.dbc`),
  as 3.714 AIH têm `ident` 1.
- `seq_aih5` é o sequencial de longa permanência, da AIH tipo 5
  (Informe SIH 2016-03, p. 3).
- O layout RD não traz o número do Cartão Nacional de Saúde do paciente
  (Informe SIH 2016-03, p. 1–4); `aud_just` e `sis_just` guardam a justificativa para
  aceitar a AIH sem esse número (p. 3).
- `homonimo` indica se o paciente da AIH é homônimo do paciente de outra AIH
  (Informe SIH 2016-03, p. 3). Nenhum documento do RD de 2008 em diante dá os códigos de
  `homonimo` nem de `gestor_tp`, e nenhum DEF empacotado cita os dois campos: eles ficam
  sem rótulo (issues `homonimo-sem-fonte` e `gestor_tp-sem-fonte`, #10). O RD publica
  `homonimo` `0`, `2` e, em poucos arquivos, `1`; o RJ publica `0`, `1`, `2` e `3`. Quatro
  documentos registrados dão `0` não e `1` sim para a marca de homônimo, e nenhum dá `2`
  nem `3`: o layout dos arquivos RD de 2006-04 a 2007-12 (`Layout_REDUZIDA.pdf`, p. 2), o
  dicionário de dados das tabelas `TB_AIH` e `TB_HAIH` (`dicionario_de_dados_AIH.pdf`,
  pp. 8-9), o dicionário de dados do SIHD (`sihd1_dicionario_de_dados.pdf`, pp. 4 e 10)
  e a tabela 66 do pacote de tabelas do SIHD (`Tabelas300.zip`, `DSIHD006.TXT`: "NAO É
  HOMONIMO" e "É HOMONIMO"). Os arquivos RD lidos publicam `2` em todos os anos de 2006 a
  2026, inclusive os 21 de Roraima dos meses do layout que diz 0 e 1; por isso a lista
  dos documentos não virou mapa (`evidence/2026-11-18-sih-codigos-em-outros-documentos/`,
  `evidence/2026-11-18-rd-medidas/`, `evidence/2026-11-28-sih-homonimo/`).
- Os manuais dizem como a marca de homônimo nasce, sem dar os códigos. No sistema do
  gestor, a "pesquisa de duplicidades" "verifica se existem nomes e datas de nascimento
  iguais em registros diferentes e marca os registros como bloqueados ou liberados", e o
  autorizador analisa cada registro bloqueado "para decidir sobre manter o bloqueio ou
  liberá-lo" (Manual SIHD 2006, procedimento "Gerenciar Informações"). O manual do SIHD2
  lista quatro relatórios de duplicidade, "Encontradas", "Bloqueadas", "Canceladas" e
  "Liberadas", e para liberar uma AIH pede o CPF do autorizador (Manual SIHD2 2009,
  pp. 89-90 e 106). Na nova AIH do mesmo paciente na mesma internação, "o sistema
  bloqueia a AIH por “duplicidade” (homônimo), mas o gestor autoriza", e a AIH emitida
  menos de 3 dias depois de outra internação é bloqueada "desde que a outra AIH seja
  emitida pelo mesmo gestor" (Manual SIH 2012, p. 11, itens 5.10 e 5.11). A Nota Técnica
  SIHD2 nº 001/2015 (DATASUS-RJ, 25/08/2015, "Válido a partir da competência 08/2015")
  muda o bloqueio: o gerenciador do SIHD2 passa a "realizar o bloqueio de DUPLICIDADES
  (homônimos) apenas nas AIHs que NÃO POSSUAM número de CNS do paciente", e dois
  bloqueios novos pegam AIH com internações sobrepostas ou com até 3 dias de intervalo:
  entre as AIH do mesmo CNS no próprio movimento e contra o histórico de internações do
  estado. O Manual SIH 2017 traz os dois como bloqueios separados, "DUPLICIDADE DE NOME"
  e "INTERNAÇÃO SOBREPOSTA" (pp. 85-86, itens 58.1 e 58.2). Nenhum documento lido diz que
  código a marca recebe quando a duplicidade é encontrada, bloqueada, liberada ou
  cancelada.
- O que os arquivos lidos mostram sobre `homonimo` é associação, não definição
  (`evidence/2026-11-28-sih-homonimo/`: 175 arquivos `RD`, 58 `RJ` e 14 `ER` de 2008 a
  2025, e 28 `RD` de 2006 e 2007). Nos 30 arquivos `RJ` até 2015-07 (SP, RJ, MG, DF e RR),
  `1` está em 17.618 linhas, 17.612 delas com `st_bloq` 2 (Bloqueio AIH); `2` em 17.190,
  16.448 com `st_bloq` 5 (Liberação bloqueio AIH); `3` em 95, todas com `st_bloq` 4
  (Cancelamento AIH). A associação não é uniforme: em `RJRJ0801`, 542 das 967 linhas com
  `2` têm `st_bloq` 2, e `st_bloq` 5 também cobre liberações por outros motivos (9.089
  linhas com `homonimo` 0). Das 4.225 AIH que os `ER` de SP e RJ de 2012-01, 2014-12 e
  2015-07 trazem com o erro "AIH BLOQUEADA POR DUPLICIDADE", sozinho ou com outros
  motivos, 4.211 têm `1` no `RJ` do mesmo mês. Das 4.219 AIH rejeitadas com `1` em seis
  arquivos `RJ` até 2015-06, 1.823 estão no `RD` do mês seguinte, 1.371 com `2` e 451 com
  `0`. Nos 74 `RD` até 2015-07, as 355.588 AIH com `homonimo` diferente de 0 têm todas
  `gestor_cpf` preenchido (5,5% das com 0) e nenhuma tem `ident` 5; 88,6% delas têm
  `nasc`, `sexo` e `cep` iguais aos de outra AIH do mesmo arquivo (2,0% das com 0). Nos
  três `RDRR` de 2006-01 a 2006-03, `cpf_aut` vem preenchido nas 146 AIH com `2` e em
  nenhuma das 4.418 com `0`. Nos seis arquivos de 2006-04 a 2006-08 (cinco `RDRR` e
  `RDRJ0607`), `cpf_aut` vem preenchido em 635 AIH com `0` e em 36 das 2.162 com `2`; nos
  19 de 2006-09 a 2007-12, em nenhuma. Com os quatro relatórios do manual do SIHD2, isso é
  coerente com `1` para a duplicidade bloqueada, `2` para a liberada e `3` para a
  cancelada, e o RD, que traz as AIH aprovadas, quase não teria `1`; nenhum documento lido
  diz isso, e o campo segue sem rótulo. Ficam fora dessa leitura as 5.309 AIH aprovadas
  com `1` em 8 dos 175 `RD` (5.105 em `RDBA1201` e `RDRS1201`), em cada arquivo todas de
  um só gestor (`uf_zi`), e 746 linhas de `RJ` com `2` e `st_bloq` 2.
- A frequência de `homonimo` diferente de 0 cai em 2015-08, o mês da nota técnica. Nos
  `RDRR`, `2` está em 3.657 das 19.931 AIH de 2015-01 a 2015-07 (18,3%) e em 182 das
  14.903 de 2015-08 a 2015-12 (1,2%); de 2008-01 a 2015-07, em 29.532 de 229.443
  (12,9%), e de 2015-08 a 2026-06, em 3.244 de 452.253 (0,7%)
  (`evidence/2026-11-18-rd-medidas/2008-2026/medidas.csv`). Nos arquivos de SP, RJ, MG,
  RR, DF e PE, a marca está em 109.998 das 891.851 AIH de 2015-06 e 2015-07 (12,3%) e em
  1.183 das 1.298.139 de 2015-08 a 2015-10 (0,1%). De 2015-08 em diante (101 arquivos),
  3.188 das 3.612 AIH marcadas (88,3%) têm em `gestor_cod` um código que a tabela
  `LIBGESTOR.dbf` do `TAB_SIH.zip` rotula "CNS" (0,4% das não marcadas), em linha com a
  nota técnica; até 2015-07 a proporção é a mesma nas marcadas e nas outras (0,4%)
  (`evidence/2026-11-28-sih-homonimo/`). Compare `homonimo` antes e depois de 2015-08
  com essa ressalva.
- `diag_princ` é o código do diagnóstico principal pela CID-10, com 4 caracteres
  (Informe SIH 2016-03, p. 2), e o dicionário o liga à tabela `aux_cid10`
  (`src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`).
- `val_tot` é o valor total da AIH (Informe SIH 2016-03, p. 2).
- A importação grava as colunas do arquivo com nomes em minúsculas e acrescenta `ano`,
  `uf`, `mes` e `_source_release` a cada linha
  (`src/omnisus/sources/datasus_ftp/staging.py`, `dbc_bytes_to_parquet`;
  `src/omnisus/sources/datasus_ftp/_runner.py`, `ingest_raw`).

## Datas e geografia

- `ano_cmpt` e `mes_cmpt` são o ano e o mês de processamento da AIH
  (Informe SIH 2016-03, p. 1), e a data de internação é outro campo (p. 2).
- A data de internação está em `dt_inter` e a data de saída em `dt_saida`, ambas no
  formato aaaammdd no recorte; o Informe SIH 2016-03, p. 2, declara char(8), mas
  grafa o primeiro campo `DI_INTER` e seu formato `aaammdd`, inconsistências
  documentais preservadas na auditoria.
- `nasc` é a data de nascimento do paciente, no formato aaaammdd
  (Informe SIH 2016-03, p. 1).
- `gestor_dt` é a data da autorização dada pelo gestor, no formato aaaammdd
  (Informe SIH 2016-03, p. 3).
- As colunas `ano`, `uf` e `mes` vêm do nome do arquivo (`RDSP2401.dbc` → SP, 2024,
  mês 1) (`tests/unit/sources/datasus_ftp/test_filenames_golden.py`;
  `src/omnisus/sources/datasus_ftp/staging.py`).
- `munic_res` é o município de residência do paciente, com 6 caracteres
  (Informe SIH 2016-03, p. 1).
- `munic_mov` é o município do estabelecimento, com 6 caracteres
  (Informe SIH 2016-03, p. 2).
- `uf_zi` é o gestor da AIH, com 6 caracteres, apesar do nome: o DEF o chama de
  "Município gestor" e o informe de "Município Gestor." (`RD2008.DEF`, linhas 175-176;
  Informe SIH 2016-03, p. 1), mas o código nem sempre é de município. A tabela que o DEF
  liga ao campo, `CNV/br_municgestor.cnv` do `TAB_SIH.zip`, tem para cada um dos 26
  estados uma linha "Gestão estadual" com o código da UF seguido de `0000` (`140000`,
  "140000 Roraima - Gestão estadual"). Em RDRR2401 são 2.920 das 3.714 AIHs com `140000`
  e 794 com `140010` (Boa Vista), e `gestao` vale `2` nas primeiras e `1` nas outras. Os
  rótulos vêm dessa tabela, no RD e no RJ (`RJ2008.DEF`, linhas 177-178). Cada rótulo
  começa pelo código da linha da tabela, e uma chave listada como segundo código ou
  dentro de uma faixa mostra o código da linha: `149999` é "140000 Roraima - Gestão
  estadual" e `530010` (Brasília) é "530000 Distrito Federal". Das 15.731 chaves, 10.087
  vêm de três linhas que escrevem faixas (Rio de Janeiro, São Paulo e Distrito Federal),
  forma que o TabWin.pdf (pp. 90-91) só documenta para códigos de até 4 caracteres; a
  issue `uf_zi-faixa-em-codigo-longo` do campo diz isso, e está resolvida: o mapa segue a
  tabela como publicada e expande as faixas (#182). Uma delas é publicada: `530000`
  está em todos os 76.276 registros dos cinco arquivos `RDDF` lidos (janeiro de 2008,
  2012, 2016, 2020 e 2024, `evidence/2026-11-18-rd-medidas/`), e a tabela só chega a ela
  pela faixa `530000-530009`. Nenhum arquivo `RJ` do Distrito Federal foi lido. O campo não tem referência a `aux_municipios`: lá `140000` é "Município
  ignorado - RR", e a tabela do DEF o chama de "Roraima - Gestão estadual".
- `cnes` é o código CNES do hospital, com 7 caracteres (Informe SIH 2016-03, p. 3).
- O dicionário liga `munic_res` e `munic_mov` a `aux_municipios.codigo_6`.
  `diag_secun`, `cid_asso` e `cid_morte` gravam `0000`, que não é um código CID-10
  ([vocabulários](vocabularios.md)), mas não em todo arquivo: em São Paulo 2014-12,
  `cid_morte` vem em branco nas 184.988 AIH sem óbito
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`), e nenhuma das 193.789 AIH traz `0000` em
  `diag_secun` ou `cid_asso`: `diag_secun` vem em branco em 134.282 e `cid_asso` em
  187.186 (`evidence/2026-11-28-rd-medidas-da-revisao/`). De 2015-02 em diante, nos
  arquivos lidos,
  `cid_asso` e `cid_morte` trazem `0000` em toda AIH, e o informe descreve `diag_secun`
  como "Preenchido com zeros a partir de 201501" (Informe SIH 2016-03, p. 2); ver
  [Armadilhas](#armadilhas). A importação preserva o comprimento dos códigos publicados; não aplica
  preenchimento de zeros guiado pelo YAML.

## Cobertura e modalidade

Arquivos mensais por UF, de janeiro de 2008 em diante, no diretório
`/dissemin/publicos/SIHSUS/200801_/Dados`, sem diretório preliminar; veja
[Bases e argumentos](../datasets.md#onde-fica-no-servidor). O arquivo `SP`, que o mesmo
documento descreve (Informe SIH 2016-03, p. 4–5), e os arquivos `RJ` e `ER`, que ele não
descreve (o sumário, p. 1, lista só `RD` e `SP`), são linhas próprias; veja abaixo.

### Outras linhas do SIH

| Linha | Prefixo | Diretório | Cobertura |
| --- | --- | --- | --- |
| `sih_aih_rejeitada` | `RJ` | `SIHSUS/200801_/Dados` | 2008-01 em diante |
| `sih_servicos_profissionais` | `SP` | `SIHSUS/200801_/Dados` | 2008-01 em diante |
| `sih_aih_rejeitada_erro` | `ER` | `SIHSUS/200801_/Dados` | 2011-01 em diante |
| `sih_aih_reduzida_1992_1997` | `RD` | `SIHSUS/199201_200712/Dados` | 1992-01 a 1997-12; o diretório `Doc` dessa era está vazio no servidor |
| `sih_aih_reduzida_1998_2007` | `RD` | `SIHSUS/199201_200712/Dados` | 1998-01 a 2007-12; mesmo diretório, mesmo prefixo |

Os dicionários dessas linhas partem do inventário físico do descritor DBF de uma fixture real (`scripts/gen_dicionario.py`); os de `sih_aih_reduzida_1992_1997` e `sih_aih_reduzida_1998_2007`, dos descritores de duas fixtures cada um (`uti_total`, de `sih_aih_reduzida_1998_2007`, só existe até 1999-12 e nenhuma fixture da era o traz: o tipo vem do N2.0 que ele tem em todos os layouts) e do censo de layouts descrito abaixo. Os rótulos de categoria vêm do CNV do TabWin quando o DEF liga o campo e todo valor não branco da fixture é chave do mapa (`sources/cnv/vinculos.json`); calendários, cadastros e faixas não são copiados. Em `sih_aih_rejeitada_erro`, o DEF liga a CNV só ano e mês; `co_erro` ele liga a `DBF/MOTERRO.dbf`, de onde vêm os rótulos (`sources/cnv/vinculos.json`). Em `sih_aih_reduzida_1992_1997` (`ident`, `sexo`, `morte`, `natureza` e `semiplen`) e em `sih_aih_reduzida_1998_2007` (`ident`, `sexo`, `morte`, `natureza`, `gestao`, `instru` e `vincprev`), os campos têm os rótulos dos CNV que o `RD.DEF` liga a eles nos três pacotes da era em `SIHSUS/200801_/Auxiliar/` (`TAB_SIH_199201-199712.zip`, `TAB_SIH_199801-200307.zip` e `TAB_SIH_200308-200712.zip`), idênticos byte a byte; os SHA-256 estão em `evidence/2026-09-29-tab-sih-rd-eras/`. Os outros campos categóricos que o `RD.DEF` liga, como `espec`, `car_int`, `cobranca` e `marca_uti`, seguem sem rótulo nessas duas linhas. `CH` e `CM` (nacionais, desde 2019) e as eras antigas de `RJ` e `SP` não têm linha em [Bases e argumentos](../datasets.md#sih).

Em `sih_aih_rejeitada_erro`, `co_erro` tem 398 valores distintos nas 14.656.815 linhas dos 4.931 arquivos `ER` que o servidor listava em 2026-09-23 (2011-01 a 2026-07); 15 deles, em 8.048 linhas, não estão em `DBF/MOTERRO.dbf` do `TAB_SIH.zip` e ficam sem rótulo (`evidence/2026-09-23-er-co-erro/`; issue `co_erro-fora-da-tabela` do campo).

De 1992-01 a 2007-12, os arquivos `RD` lidos (um de RR por mês, AP onde RR falta, e SP e MG nos meses de troca) têm 19 layouts DBF: 7 até 1997-12 e 12 de 1998-01 em diante. O dataset é separado em 1998-01, um dicionário por era (issue #12, decisão 1): `sih_aih_reduzida_1992_1997` declara os 43 campos dos 7 primeiros layouts e `sih_aih_reduzida_1998_2007`, os 80 dos 12 últimos (89 no total). Cada tabela do lake só tem as colunas da sua era; antes da separação, os 46 campos que só os layouts de 1998-01 em diante têm eram colunas vazias da tabela única em 1992-1997. Colunas aparecem e somem: `us_sh`, `us_sp`, `us_sadt`, `us_ortp` e `us_sangue` existem até 1997-12 (`us_rn`, de 1994-01 a 1997-12); `uti_total`, até 1999-12; `cod_arq` e `cont`, até 2006-03, menos em 2001; `semiplen`, de 1995-01 a 1997-12; `diag_sec`, só em 1997; `val_sang`, só em 1994-12, mês que não tem `val_sangue`; `cgc_mant`, só em 2004-07; `cod_seg`, de 2004-07 a 2006-03. Numa tabela com vários meses da mesma era, a coluna que falta num mês fica NULL nas linhas desse mês. O `RD.DEF` dos três pacotes liga `semiplen` ("Gestão (95-97)") a `GESTAO.CNV`, de onde vêm os rótulos, e `diag_sec` a tabelas CID-9; `diag_sec` fica sem rótulo, como `diag_princ`. `num_proc` (era 1992-1997) é numérico (N) de 1996-01 a 1996-07, e `insc_pn` e `seq_aih5` (era 1998-2007), de 2004-07 a 2006-03; nos outros meses em que existem são texto (C), o tipo que o dicionário declara. A importação grava os meses N como texto, o número sem zeros à esquerda ([issue #40](https://github.com/raphaelfh/omnisus/issues/40)): nos 264 registros de `RDRR9602` e nos 5 da fixture de `RDRR9603`, `num_proc` sai `364` e `368`, e nos 794 de `RDRR9709`, `0489`; nos 91 da fixture de `RDRR0407`, `insc_pn` e `seq_aih5` saem `0`, e nos 1.496 de `RDRR0712`, `0000000000` e `000`. Quem quiser unir as duas formas faz isso na consulta; a issue `sem-zeros-a-esquerda` de cada um dos três campos, no dicionário da sua era, lista os meses. Um lake em que uma dessas colunas já é número, porque começou por um mês N numa versão anterior, recusa os arquivos gravados como texto com `UnsafeSchemaError`, também com `replace`; a biblioteca não tem operação que troque o tipo de uma coluna, e a tabela precisa ser importada de novo num lake novo. Os arquivos lidos, com data, tamanho, SHA-256 e layout, estão em `evidence/2026-10-01-rd-1992-2007-layouts/`. O cabeçalho DBF dos 5.165 arquivos `RD` do diretório, lido em 2026-11-19 (`evidence/2026-11-19-sih-cabecalhos/`), tem os mesmos 19 layouts e nenhum outro, em todas as UFs; `num_proc` é N nos 188 arquivos de 1996-01 a 1996-07, e `insc_pn` e `seq_aih5`, nos 567 de 2004-07 a 2006-03.

De 2008-01 em diante, os arquivos `RD` lidos (um de RR por mês, AP onde RR falta, e SP e MG nos meses de troca) têm 6 layouts (`evidence/2026-10-06-rd-2008-layouts/`). O cabeçalho DBF dos 6.072 arquivos `RD` que o servidor listava em 2026-11-19 (`evidence/2026-11-19-sih-cabecalhos/`) tem um desses 6 layouts em 6.071; o outro é `RDAC0909.dbc` (ver "Em aberto"). O layout 6, de 2025-03 em diante, acrescenta `fonte_orc` (C(2)). O `RD2008.DEF` liga o campo a `CNV/fonterem.CNV`, e os rótulos vêm dele: `01` a `04` (também escritos `1` e ` 1`) e a chave literal `  -zz`, "Branco Ignorado" (#24). No excerto de RDRR2503 (`sih_rd_rr_2025_03_excerpt`, 30 registros) ele vale `00` em todas as linhas, e `00` não é chave da tabela: fica sem rótulo, e a issue `fonte_orc-00-sem-fonte` do campo diz isso.

Os arquivos `SP` e `RJ` ganham `FONTE_ORC` (C(2)) no mesmo mês: é o último campo do cabeçalho DBF dos 510 arquivos de cada prefixo, de 2025-03 a 2026-09, e de nenhum anterior (`evidence/2026-11-19-sih-cabecalhos/`, o cabeçalho de todo arquivo `SP` e `RJ` que o servidor listava em 2026-11-19, lido sem nenhum registro). `sih_servicos_profissionais` e `sih_aih_rejeitada` declaram `fonte_orc` sem rótulo e sem mapa: o `SP2008.DEF` e o `RJ2008.DEF` não citam o campo, e a linha do `RD2008.DEF` é do RD. Nos 18 arquivos `RJRR` de 2025-03 a 2026-08, o campo vale `00` nos 1.270 registros, o mesmo valor que o RD publica; dos arquivos `SP`, só o cabeçalho foi lido para este registro. A issue `fonte_orc-sem-def` do campo diz isso.

Em `sih_aih_reduzida` e `sih_aih_rejeitada`, `CONTRAC.CNV` (`contracep1` e `contracep2`), `RACACOR.CNV` (`raca_cor`) e `motbloqueio.cnv` (`st_mot_blo`, só em `RJ`) abrem com a faixa `00-99`, que rotula qualquer código de dois dígitos: um código fora da tabela recebe "Ignorado/não se aplica", "Sem informação" ou "NÃO ESPECIFICADO", e não fica sem rótulo. Do mesmo jeito, `etnia.cnv` (`etnia`) lista os códigos `0001` a `0264` e abre com a faixa `0000-9999`: qualquer outro código de quatro dígitos, `0000` inclusive, recebe "NÃO INFORMADO" só pela faixa (issue `etnia-nao-informado-pela-faixa` no campo). Código que não é dígito fica fora da faixa e sem rótulo: RDRR2501 (RR, 2025-01) publica `X389` em 2 AIHs e `X401` em 3, todas com `raca_cor` 05, e a issue `etnia-x389-x401-sem-fonte` do campo diz isso; o excerto `sih_rd_rr_2025_01_excerpt` traz as duas AIHs com `X389`.

## Armadilhas

- Em `etnia`, o `0000` das fixtures do RD e do RJ (RR 2024-01 e excertos SP de 2022 e
  2023) marca AIH de paciente não indígena, e não etnia desconhecida: nelas, toda linha
  com `0000` tem `raca_cor` de 01 a 04, e toda linha com `raca_cor` 05 (indígena) tem um
  código de `0001` a `0264`. O `etnia.cnv` rotula o `0000` "NÃO INFORMADO" só pela faixa
  `0000-9999`; em RR 2024-01 são 3.303 das 3.714 AIHs do RD. Para contar pacientes
  indígenas, filtre por `raca_cor`. A Portaria SAS/MS nº 508/2010 incluiu o campo no SIH,
  "com efeitos operacionais a partir da competência outubro de 2010" (art. 5º), e o exige
  "somente" quando o usuário é registrado em raça/cor "como Indígena" (art. 2º). Em sete
  arquivos de São Paulo de 2014-12 a 2025-12, nenhuma AIH com `raca_cor` diferente de 05
  traz `etnia` diferente de `0000`, e algumas com 05 trazem `0000` (6 das 35 em 2020-01)
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`).
- `raca_cor` entrou no SIH pela Portaria SAS/MS nº 719/2007, com 01 a 05 e 99 "SEM
  INFORMACAO", "atendendo a classificação expressada pelo próprio usuário ou seu
  responsável" (art. 1º), "com efeitos operacionais a partir de janeiro de 2008" (art.
  8º): os arquivos de 1992 a 2007 não têm o campo (`evidence/2026-11-19-sih-cabecalhos/`).
  Desde a Portaria SAS/MS nº 1.134/2014, com "efeitos operacionais a partir de novembro de
  2014" (art. 6º), quando a AIH traz o Cartão Nacional de Saúde, o SISAIH01 "irá consumir
  as informações cadastrais" do CADSUS WEB, que "não poderão ser alteradas no SISAIH01"
  (art. 1º e § 1º); as informações indispensáveis que faltarem no CADSUS "poderão ser
  registradas manualmente" (§ 3º). A portaria não lista quais informações cadastrais são
  consumidas. O CADSUS guarda raça/cor (informe da CIT citado abaixo, p. 1, de 2023); se
  ela estiver entre as consumidas, a raça/cor da AIH vem do cadastro, e não de uma
  pergunta feita na internação. Nenhum documento registrado diz isso.
- O DATASUS anunciou para abril de 2023 uma mudança na regra de `raca_cor`. O informe do
  DATASUS à 3ª reunião ordinária da Comissão Intergestores Tripartite de 2023 (30/03/2023, "Demanda raça/cor") diz que,
  "a partir da competência de abril/2023", os aplicativos de captação e processamento do
  SIA e do SIH "não mais aceitarão o registro/envio de informações (APAC/BPA/AIH etc) cujo
  campo raça/cor esteja preenchido com o código 99 (não informado)", e que "as
  produções/atendimentos feitos até a competência de março/2023 não sofrerão qualquer
  impacto, mesmo que as produções sejam enviadas após essa competência" (p. 2). O informe não
  diz por qual data se conta a competência de uma produção. O 99 ainda aparece em
  arquivos processados depois de abril de 2023. O `RACACOR.CNV` só dá rótulo ao 99 pela faixa `00-99`,
  "Sem informação"
  (`src/omnisus/data/dicionarios/sources/cnv/sih/CNV/RACACOR.CNV`). Na fixture de Roraima
  2024-01, `raca_cor` traz 01 (120 AIH), 02 (40), 03 (3.134), 04 (9) e 05 (411), e nenhum
  99. Em São Paulo, o 99 está em 32.488 das 193.789 AIH de 2014-12, em 27.436 das 215.766
  de 2020-01, em 4.778 das 233.649 de 2023-03, em 282 de 2023-06 e em 97 de 2025-12; nos
  dois últimos, todas com `dt_inter` até 31/03/2023
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). Numa série da proporção de raça/cor sem
  informação, o informe anuncia o fim do 99 de abril de 2023 em diante; nos dois arquivos
  de São Paulo lidos depois disso o 99 continua, só em AIH com `dt_inter` até
  31/03/2023. Parte das AIH com 99 desses dois arquivos tem `dt_saida` depois de março de
  2023: das 282 de 2023-06, 229 têm `dt_saida` de abril a junho de 2023, e 190 das 282
  têm `ident` 5; as 97 de 2025-12 têm `ident` 5 e `dt_saida` em dezembro de 2025
  (`evidence/2026-11-28-rd-medidas-da-revisao/`). Em São Paulo a maior parte da queda
  veio antes: de 27.436 AIH em 2020-01 para 4.778 em 2023-03.
- Há AIH de tipos diferentes em `ident` (Informe SIH 2016-03, p. 1) e um sequencial
  próprio para a AIH de longa permanência (p. 3).
- Uma internação pode gerar mais de uma AIH. A AIH 5 mantém a data de internação da
  AIH 1, "mesmo que a internação se prolongue por meses (ou anos)", e na permanência é
  "renovada" mensalmente (Manual SIH 2012, p. 8). Além disso, uma nova AIH para o mesmo
  paciente na mesma internação é obrigatória, com motivo 2 (permanência), em casos como
  uma segunda cirurgia, um parto em paciente internada por outro motivo ou a reinternação
  clínica pela mesma doença até 3 dias depois da alta (pp. 10–11; a reinternação é o
  item 5.9, e o item 5.11, na mesma página, manda manter a mesma AIH no retorno com menos
  de 3 dias: o manual não resolve a diferença). Contar AIH não é contar internações nem
  pacientes.
- `n_aih` segue uma regra de numeração: 1º e 2º dígitos, a UF pelo código do IBGE (ou 99
  nas séries da CNRAC); 3º e 4º, os dois últimos algarismos do ano; 5º, "o número 1 (um)
  para identificar que a autorização é de Internação (AIH) - uso geral"; 6º a 12º, um
  sequencial; 13º, o dígito verificador (Manual SIH 2012, p. 8). Na fixture de Roraima
  2024-01, os 3.714 números têm 13 caracteres, são distintos e começam com 14 (Roraima);
  781 têm 23 no 3º e 4º dígitos (o "ano de referência" do manual), em arquivo processado
  em 2024-01. O 5º dígito é 1 em 3.432 e
  5 em 282, embora todas as 3.714 tenham `ident` 1: não deduza o tipo da AIH do
  número. Em São Paulo 2025-12, as 4.488 AIH com `ident` 5 têm o 5º dígito 1, e as com
  `ident` 1 têm 1, 3 ou 5 (`evidence/2026-11-24-rd-sp-uti-cid-raca/`).
- A consulta `aih_distintas` do notebook compara o número de linhas com o número de
  valores distintos de `n_aih` antes de qualquer contagem
  (`notebooks/sih_aih_reduzida.py`).
- Agregar por `mes_cmpt` conta AIH processadas no mês (Informe SIH 2016-03, p. 1); para
  contar internações por mês de ocorrência, use `dt_inter` (p. 2). A validade da AIH é
  de "no máximo 03 competências anteriores à competência de apresentação"; apresentada
  com mais de 4 meses do mês da alta, a AIH é rejeitada em definitivo e, rejeitada dentro
  desse prazo, pode ser reapresentada até o 6º mês contado do mês da alta (Manual SIH
  2012, p. 10). Os arts. 400 e 401 da Portaria de Consolidação SAES/MS nº 1/2022 dizem
  que, no SIH, o mês de produção é o mês da alta, e que o mês de processamento aceita AIH
  "com alta de no máximo 4 (quatro) meses anteriores"; segundo a nota de origem dos dois
  artigos na consolidação, a regra vem da Portaria SAS/MS nº 472/2008. Na fixture de
  Roraima 2024-01, 3.431 das 3.714 AIH têm `dt_saida` de 2023-10 a 2023-12 e 283, de
  2024-01: nessa fixture, o arquivo traz altas de até três meses antes; em São Paulo
  2023-06, 3 das 282 AIH com `raca_cor` 99 têm `dt_saida` de 2023-02, quatro meses antes
  (`evidence/2026-11-28-rd-medidas-da-revisao/`).
- `qt_diarias`, a "Quantidade de diárias" (Informe SIH 2016-03, p. 2), não conta dias de
  permanência. "O sistema paga o último dia de internamento quando o motivo de
  apresentação for: permanência, óbito e transferência" (Manual SIH 2012, p. 13). Em São
  Paulo 2025-12, `qt_diarias` é `dias_perm` mais 1 em 8.659 das 9.869 AIH com motivo de
  transferência (`cobranca` 3x; 87,7%), em 6.877 das 11.595 com óbito (4x; 59,3%) e em
  8.176 das 15.364 com permanência (2x; 53,2%), em que outras 4.269 têm os dois iguais; e
  é igual a `dias_perm` em 131.170 das 170.082 com alta (1x; 77,1%) e em 20.569 das
  20.855 de parto (6x; 98,6%). `dias_perm` é igual a `dt_saida` menos
  `dt_inter` em 226.276 das 230.747 AIH (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). Para
  tempo de internação, use as datas ou `dias_perm`, não `qt_diarias`.
- `morte` "indica óbito", com 1 algarismo, e o documento não lista os códigos
  (Informe SIH 2016-03, p. 2); os códigos e rótulos vêm do pacote oficial
  `TAB_SIH.zip`, republicado pelo DATASUS em 2026-09-15, `RD2008.DEF` →
  `MORTES.CNV` (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`).
- `cid_morte` é a CID da morte (Informe SIH 2016-03, p. 3), e `cobranca` é o motivo de
  saída ou permanência (p. 2); os códigos e rótulos de `cobranca` vêm do mesmo pacote
  `TAB_SIH.zip`, `RD2008.DEF` → `SAIDAPERM.CNV` — por exemplo, 26 = permanência por
  mudança de procedimento e 31 = transferência para outro estabelecimento
  (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`). O motivo de saída ou
  permanência substituiu o "Motivo de Cobrança" com efeitos operacionais a partir de
  janeiro de 2008, pela Portaria SAS/MS nº 719/2007 (arts. 2º e 8º), que define a tabela
  de motivos no art. 5º. A fixture de Roraima 2007-12
  (`tests/fixtures/dbc/sih_rd_rr_2007_12_mini.dbc`) publica códigos fora dela: 33, 35, 37,
  52, 53 e 71. O layout dos
  arquivos de 2006-04 a 2007-12 só dá o nome do campo, "MOTIVO DE COBRANCA"
  (`Layout_REDUZIDA.pdf`, p. 1), e os dicionários de 1992-1997 e de 1998-2007 deixam
  `cobranca` sem tabela.
- Óbitos não estão só em `cobranca` 41 a 43. Os motivos 61 a 67 são "exclusivo[s] para
  as AIH de procedimento principal parto", incluídos pela Portaria SAS/MS n.º 384/2010
  (Manual SIH 2012, p. 13): 63 e 64 registram alta da mãe com óbito do recém-nascido
  ou óbito fetal, e 65 a 67, o óbito da gestante ou da mãe/puérpera (p. 12–13;
  `SAIDAPERM.CNV`). Quem conta óbitos hospitalares por 41 a 43 deixa de fora as mortes
  maternas em AIH de parto; quem conta qualquer código de 61 a 67 com "óbito" no rótulo
  mistura a morte da mãe com a do concepto. Na fixture de Roraima 2024-01, as 90 AIH com
  41 têm `morte` 1 e as 659 com 61 têm `morte` 0. Em sete arquivos de São Paulo de 2014-12
  a 2025-12, nas 25 AIH com 65, 66 ou 67, `morte` é 1, e nas 192.678 AIH com 61 a 64,
  inclusive as 2.029 com 63 ou 64, `morte` é 0: nesses arquivos, `morte` acompanha a
  morte da paciente da AIH, não a do concepto
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`).
- Os complementos federal e do gestor de serviços hospitalares e profissionais
  (`val_sh_fed`, `val_sp_fed`, `val_sh_ges`, `val_sp_ges`) estão incluídos no valor
  total da AIH (Informe SIH 2016-03, p. 4).
- `diar_acom` é a "Quantidade de diárias de acompanhante" (Informe SIH 2016-03, p. 2):
  conta diárias cobradas, não a presença do acompanhante, e `diar_acom` maior que zero
  não indica parto. Duas normas registradas autorizam o prestador a cobrar na AIH
  "despesas previstas com acompanhante". Uma é a do acompanhante "no trabalho de parto,
  parto e pós-parto imediato" (Portaria GM/MS nº 2.418/2005, art. 1º, § 2º); em 2017 o
  texto passou ao art. 92, § 2º, do Anexo II da Portaria de Consolidação GM/MS nº 3/2017
  (texto registrado, anotado até 2018; a vigência depois disso não foi lida), que revogou
  a 2.418/2005 "por consolidação" (art. 6º, VII). A outra é a do acompanhante de
  pacientes "maiores de 60 (sessenta) anos de idade, quando internados" (Portaria de
  Consolidação GM/MS nº 2/2017, Anexo 2 do Anexo XI: o art. 1º obriga o hospital a
  viabilizar a presença do acompanhante, e o § 1º do art. 1º autoriza a cobrança). As
  duas não esgotam o campo: o Manual SIH 2012 diz que "É permitido acompanhante para
  menores de 18 anos", que "Para maiores de 18 o médico assistente deve decidir pela
  necessidade ou não do acompanhante" e que "Essas diárias são remuneradas" (p. 23,
  item 13.1). Nos arquivos de São Paulo de 2014-12 e 2025-12, das AIH com `cobranca` 61 a
  67 (alta ou óbito da mãe/puérpera ou da gestante, `SAIDAPERM.CNV`), 9.499 de 26.207
  (2014-12) e 13.909 de 20.855 (2025-12) trazem `diar_acom` maior que zero
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). Nos mesmos dois arquivos, a maior parte
  das AIH com `diar_acom` maior que zero está fora dessas: das 85.178 de 2025-12, 41.243
  são de pacientes de 60 anos ou mais (de 80.284 AIH dessa idade sem `cobranca` 61 a 67),
  16.916 de menores de 18 (de 29.252) e 13.110 de 18 a 59 anos (de 100.356); das 52.346
  de 2014-12, 21.800 (de 51.449), 15.921 (de 29.007) e 5.126 (de 87.126). Os
  denominadores excluem `cobranca` 61 a 67, e a idade em anos é calculada de `cod_idade`
  e `idade` (`evidence/2026-11-28-rd-medidas-da-revisao/`). Um `diar_acom` zero não mostra que a
  paciente ficou sem acompanhante.
- `us_tot` é o valor total em dólar, não em reais (Informe SIH 2016-03, p. 2).
- Vários campos de valor vêm zerados: `val_sadt`, `val_rn`, `val_acomp`, `val_ortp`,
  `val_sangue`, `val_sadtsr`, `val_transp`, `val_obsang` e `val_ped1ac`
  (Informe SIH 2016-03, p. 2).
- Também vêm zerados `uti_mes_in`, `uti_mes_an`, `uti_mes_al`, `uti_int_in`,
  `uti_int_an` e `uti_int_al` (Informe SIH 2016-03, p. 1); a quantidade de dias de UTI
  no mês está em `uti_mes_to` (p. 1).
- Três portarias mandam tirar a UTI tipo I da tabela de leitos do CNES; o RD segue
  publicando o código 74. `marca_uti` "Indica qual o tipo de UTI
  utilizada pelo paciente" (Informe SIH 2016-03, p. 1), e o `MARCAUTI.CNV` rotula 74 "UTI
  adulto - tipo I" e 77 "UTI infantil - tipo I". A Portaria SAS/MS nº 298/2019
  reclassificou essas UTI como Unidade de Cuidados Intermediários: os leitos "74 - UTI
  Adulto - Tipo I" migram para "95 - Unidade de Cuidados Intermediários Adulto", os "77 -
  UTI Pediátrica - Tipo I" para "94", e os códigos 74 e 77 saem da tabela de leitos do
  CNES (art. 2º). A Portaria SAES/MS nº 1.202/2023 descontinua no CNES os leitos e as
  habilitações de UTI tipo I "no prazo de 120 dias" (art. 1º, § 1º), e a Portaria SAES/MS
  nº 3.511/2025 exclui de novo os leitos 74 e 77, "considerando o fim do prazo de
  reclassificação" (art. 2º, § 1º). Nenhuma das três cita o campo do RD, e o RD segue
  publicando 74: em sete arquivos de São Paulo, 423 AIH em
  2014-12, 272 em 2019-02, 130 em 2023-03 e 29 em 2025-12. O 77 aparece em 14 AIH em
  2014-12, 7 em 2015-02, 4 em 2019-02, 2 em 2020-01, nenhuma em 2023-03, 7 em 2023-06 e
  nenhuma em 2025-12 (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). Na fixture de Roraima
  2024-01, `marca_uti` traz 75 (35 AIH), 78 (34) e 81 (32).
- O código 17 de `espec` vem de uma portaria de 2020, não do `LEITOS.CNV`. O
  `RD2008.DEF` e o `RJ2008.DEF` ligam `espec` ao `CNV/LEITOS.CNV`, que lista 41 códigos e
  não tem o 17. A Portaria SAES/MS nº 245/2020 inclui na Tabela de Especialidade da AIH "o
  código 17 - Estabelecimento Exclusivo UTI SUS" (art. 2º) e restringe o código à AIH do
  procedimento 03.03.01.022-3 (COVID-19) em estabelecimento que só tem leitos de UTI no
  SUS (§ 2º). O rótulo do dicionário, no RD e no RJ, é o texto da portaria na forma
  "NN-texto" que o CNV dá aos outros códigos: "17-Estabelecimento Exclusivo UTI SUS"; os
  outros 41 rótulos são as linhas do CNV. Em São Paulo, os 26 arquivos `RD` de 2020-01 a
  2022-02 trazem o 17 de 2020-07 em diante, em 1.963 AIH de 5 estabelecimentos (692 em
  2020, 1.235 em 2021 e 36 nos dois meses de 2022; o mês com mais AIH é 2020-12, com
  292), e os três arquivos `RJ` de 2022-01 a 2022-03, em 75. Em todas, `proc_rea` é
  0303010223 e `marca_uti` é 51 (`evidence/2026-11-28-sih-espec-17/`). A contagem não leu
  outra UF, nem o RD depois de 2022-02. O art. 2º foi lido em 2026-11-24 no arquivo
  registrado e transcrito na issue `espec-17-sem-fonte` do dicionário; o rótulo foi escrito
  em 2026-11-28 a partir dessa transcrição, sem reabrir a portaria (o Saúde Legis devolveu
  403).
- Nos arquivos lidos, `uti_int_to` e `marca_uci` só trazem UCI neonatal. A UCI não tem
  código no `MARCAUTI.CNV`; o RD tem `uti_int_to`, as diárias em unidade intermediária
  (Informe SIH 2016-03, p. 1), e `marca_uci`, o "Tipo de UCI utilizada pelo paciente"
  (p. 4), cujo `MARCAUCI.cnv` só lista UCI neonatais (01 convencional, 02 canguru, 03
  unidade intermediária neonatal). Em sete arquivos de São Paulo, toda AIH com
  `uti_int_to` maior que zero é de paciente com menos de 1 ano e tem `marca_uci` 01 a 03
  (1.926 em 2025-12), e muitas têm `marca_uti` 00 (1.103 delas). A UCI adulto e a
  pediátrica, que receberam os leitos 74 e 77, ganharam diárias próprias na tabela de
  procedimentos (08.02.01.029-6 e 08.02.01.028-8, Portaria 298/2019, art. 5º e anexo; o
  art. 6º exclui as diárias de UTI I, 08.02.01.010-5 e 08.02.01.014-8). O anexo dá às
  duas diárias o instrumento de registro "04-AIH (Proc. Especial)". Para contar UTI, use
  `uti_mes_to` e `marca_uti`; para UCI neonatal, `uti_int_to` e `marca_uci`.
- `uti_mes_to` passa de 31 e, nos arquivos lidos, não traz `999`. O informe o descreve
  como "Quantidade de dias de UTI no mês." (Informe SIH 2016-03, p. 1). Em 114 arquivos
  RD (as 27 UFs em 2008-01, 2012-01, 2016-01 e 2025-12, e São Paulo em mais seis meses;
  4.939.510 AIH),
  7.105 AIH têm mais de 31 dias, em todos os meses lidos, e o maior valor é 183; nenhuma
  traz `999`. O Manual SIH 2012 diz que "Não há limite máximo de diárias numa mesma AIH."
  e que a diária de UTI é registrada "no mês de competência em que foi utilizada" (p. 24,
  item 13.4); nenhum documento registrado lido diz que `uti_mes_to` soma as diárias de
  todos os meses da AIH. O `RD2008.DEF`
  liga o campo ao `DIARIASUTI.CNV`, que a biblioteca não empacota: nele `999` é só o fim
  da faixa `001-999`, "Sim". Nos mesmos arquivos, `regct` traz nove códigos, todos com
  rótulo no `REGCT.cnv`; `7118` não aparece em nenhum, e o `7118` que o dicionário traz é
  de `etnia`, pela faixa `0000-9999` (`evidence/2026-11-28-rd-uti-mes-to-regct/`).
- `cid_morte` não traz a causa do óbito nos arquivos recentes. A Portaria SAS/MS
  nº 1.324/2014, hoje no art. 308 da Portaria de Consolidação SAES/MS nº 1/2022, excluiu
  do layout da AIH os campos "Diagnóstico da Causa Morte" e "Diagnóstico Causas
  Complementares" e incluiu 8 campos de CID secundário, com efeitos a partir de janeiro
  de 2015 (Portaria nº 1.324/2014, art. 6º). Antes dela, a Portaria SAS/MS nº 718/2006 tornou obrigatória "a
  informação da CID (...) da causa da morte nas AIH (...), sempre que o Motivo da Alta
  for óbito" (art. 1º), a partir da competência setembro de 2006 (art. 2º). A
  consolidação mantém as duas regras: o art. 298 (origem 718/2006) ainda diz que a CID é
  obrigatória, e o art. 308 (origem 1.324/2014) exclui o campo do layout. Nenhum
  documento lido diz que a obrigação acabou; o que os arquivos mostram é o campo sem a
  CID de 2015-02 em diante. Em São Paulo, as 8.801 AIH com `morte` 1 de 2014-12 trazem
  uma CID em `cid_morte`; de 2015-02 em diante, `cid_morte` e `cid_asso` são `0000` em
  todas as AIH dos arquivos lidos (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). Na fixture
  de Roraima 2024-01, `cid_morte` e `cid_asso` são `0000` nas 3.714 AIH, inclusive nas 90
  com `morte` 1; na de Roraima 2007-12, as AIH com `morte` 1 trazem códigos em
  `cid_morte` (por exemplo `J188`). Para a causa do óbito, a fonte é o SIM; no SIH restam
  `diag_princ` e os `diagsec`.
- `diag_secun` vem preenchido com zeros a partir de 201501
  (Informe SIH 2016-03, p. 2), quando entram em vigor os 8 campos de CID secundário da
  Portaria SAS/MS nº 1.324/2014 (art. 1º, III; art. 6º: efeitos a partir de janeiro de
  2015).
  Desde então, o sistema não critica mais a compatibilidade entre procedimento e
  diagnóstico (art. 4º; hoje art. 311 da Portaria de Consolidação SAES/MS nº 1/2022); os
  diagnósticos secundários estão em `diagsec1` a `diagsec9` (Informe SIH 2016-03, p. 4),
  e o dicionário liga `diagsec1` a `diagsec8` à tabela `aux_cid10`,
  como o `diag_princ` (`RD2008.DEF`, linhas 389-406, relaciona `DIAGSEC1` a `DIAGSEC9` a
  `DBF/CID10.DBF`). O `diagsec9` fica sem a ligação: a p. 4 dá `char (4)`, mas os 157
  arquivos RD lidos de 2014-01 a 2026-07 (um de RR ou AP por mês, mais SP e MG nos meses
  de troca de layout) publicam o campo com 1 caractere, curto demais para um código da
  CID-10 (censo em `evidence/2026-10-06-rd-2008-layouts/`). A `aux_cid10` vem do
  `CID10.DBF` do SIM (ver [Vocabulários](vocabularios.md)), não do `DBF/cid10.dbf` de
  `TAB_SIH.zip`, que o repositório não empacota. O tipo de cada um, em `tpdisec1` a
  `tpdisec9`, vem de `RD2008.DEF` → `TP_DIAGSEC.CNV`: 1 = preexistente, 2 = adquirido. O
  `0` que os arquivos publicam não está na tabela e fica sem rótulo. Dois documentos de
  outro arquivo dizem que `0` é o diagnóstico secundário não preenchido: o layout da
  interface texto do SISAIH01 de 09/2015 (p. 7) e o dicionário de dados das tabelas
  `TB_AIH` e `TB_HAIH` (p. 4). Nenhum DEF liga `tpdisec1` a `tpdisec9` a eles, e por
  decisão do mantenedor (#182) o `0` segue sem rótulo
  (`evidence/2026-11-18-sih-codigos-em-outros-documentos/`). Nos arquivos lidos
  (`evidence/2026-11-18-rd-medidas/`), os 12 de 2014, todos de Roraima, publicam
  `tpdisec1` a `tpdisec9` em branco, e os 148 de 2015-01 em diante publicam `0` só com o
  diagnóstico do mesmo número em branco e `1` ou `2` só com ele preenchido (`tpdisec8` e
  `tpdisec9` só trazem `0`). A contagem diz o que os arquivos trazem, não o que o `0`
  quer dizer.
- A causa externa de uma lesão não fica em `diag_princ`. Quando o CID principal é do
  capítulo XIX (S00 a T98), o SISAIH01 exige que o secundário seja do capítulo XX (V01 a
  Y98) ou um de D66, D67, D680, D681 e D684 (Manual SIH 2012, p. 37). A regra do
  capítulo XX no "primeiro campo de CID secundário" é da Portaria SAS/MS nº 1.324/2014
  (art. 3º, § 2º; efeitos pelo art. 6º, a partir de janeiro de 2015), hoje no art. 310,
  § 2º, da
  Portaria de Consolidação SAES/MS nº 1/2022. O tipo de causa externa só passou a ser
  codificado na AIH em 1998: até 1997, os dados de acidentes e violências eram "relativos
  somente à natureza da lesão", e a codificação veio "em decorrência da Portaria
  Ministerial N.º 142, de 13 de novembro de 1997" (Portaria de Consolidação GM/MS
  nº 2/2017, Anexo 1 do Anexo VII, Política Nacional de Redução da Morbimortalidade por
  Acidentes e Violências, seção "I. Introdução", parágrafo que começa "O Sistema de
  Informações Hospitalares (SIH/SUS)"). Na fixture de Roraima 2024-01, as 406 AIH com
  `diag_princ` de S ou T trazem em `diagsec1` um código de V a Y; em São Paulo, 18.320
  das 18.321 em 2015-02 e 25.556 das 25.840 em 2025-12
  (`evidence/2026-11-24-rd-sp-uti-cid-raca/`). De 2015-02 em diante, procure a causa
  externa em `diagsec1`, o único campo medido aqui. Em São Paulo 2014-12, nenhuma das
  19.086 AIH com S ou T traz V a Y em `diagsec1`. Na fixture de Roraima 2007-12
  (`tests/fixtures/dbc/sih_rd_rr_2007_12_mini.dbc`), as 144 AIH com S ou T trazem V a Y
  em `diag_secun`. Nos arquivos de 2008 a 2014 lidos, quase todas as AIH com S ou T
  trazem V a Y em `diag_secun`: 39.073 das 39.931 nas 27 UFs em 2008-01, 82.696 das
  82.992 nas 27 UFs em 2012-01 e 18.726 das 19.086 em São Paulo 2014-12; nas 27 UFs em
  2016-01 e em 2025-12, nenhuma (`evidence/2026-11-28-rd-medidas-da-revisao/`). Os
  outros meses de 2008 a 2014 não foram medidos para esse campo. O caráter de
  atendimento, `car_int`, tem códigos de acidente e lesão (03 a 06; Manual SIH 2012,
  p. 12; tabela do art. 4º da Portaria SAS/MS nº 719/2007), mas não serve para
  contá-los: em São Paulo 2025-12, as 2.588 AIH com 03 a 06 têm `diag_princ` de S ou T, e
  23.252 das 25.840 AIH com S ou T têm caráter 01 (eletivo) ou 02 (urgência).
- `diag_princ` grava CID-9 (6 algarismos, `065099`) em `sih_aih_reduzida_1992_1997` e
  CID-10 (`O800`) em `sih_aih_reduzida_1998_2007`: a separação por era põe cada
  classificação em sua tabela, e só os códigos de 1998 em diante juntam à `aux_cid10`.
  Em 2007-12, `cid_morte` e `cid_asso` gravam categorias com um `0` antes (`0I64`), que
  não juntam. O dicionário de 1992-1997 traz a primeira armadilha como issue aberta
  (`diag-princ-cid9`) e o de 1998-2007, a segunda (`cid-zero-a-esquerda`); as evidências estão em
  [Vocabulários](vocabularios.md#cid-9-e-cid-10-nos-sistemas-do-sus).
- `natureza` tem conteúdo só até maio de 2012; a natureza jurídica pela CONCLA está em
  `nat_jur` (Informe SIH 2016-03, p. 2).
- `idade` depende de `cod_idade` (Informe SIH 2016-03, p. 2). O pacote oficial
  `TAB_SIH.zip`, `CNV/IDADEDET.CNV`, confirma dias, meses, anos e unidade 5 com
  deslocamento de 100 anos no domínio detalhado. Os códigos compostos `000` e
  `999` são classificados como inválidos; isso não define uma sentinela global
  para o campo bruto `idade`.
- O rótulo de `cod_idade` (no RD e no RJ) foi medido, não lido: o `RD2008.DEF` e o
  `RJ2008.DEF` ligam o campo a tabelas que leem 3 caracteres (unidade e idade), e
  nenhuma rotula a unidade sozinha. `2` é "Dias", `3` "Meses", `4` "Anos" e `5`
  "Anos (somar 100)", porque `IDADEDET.CNV` lê 500 a 530 como 100 a 130 anos. `0`
  fica sem rótulo: nenhuma fonte o chama de "Ignorada", e no CNV `000` é "Idade
  inválida". O dicionário registra isso na issue `cod_idade-sem-tabela` (#6).
- `sexo` tem 1 caractere (Informe SIH 2016-03, p. 1). A tabela oficial
  `CNV/SEXO.CNV` define 1 masculino e 2/3 feminino. A aplicação dessas regras
  exige os escopos e hashes confirmados no contrato; códigos não documentados
  permanecem desconhecidos. O layout dos arquivos RD de 2006-04 a 2007-12 dá só
  "1=MASCULINO; 3=FEMININO" (`Layout_REDUZIDA.pdf`, p. 1), e na fixture de Roraima
  2024-01 só aparecem 1 (1.517 AIH) e 3 (2.197), como nos sete arquivos de São Paulo de
  2014-12 a 2025-12 (`evidence/2026-11-24-rd-sp-uti-cid-raca/`).
- Os códigos ficam no lake como publicados: o dicionário decodifica rótulos, datas e
  idade na exibição, não na importação (`src/omnisus/transforms/dictionaries.py`,
  docstring do módulo; `src/omnisus/sources/datasus_ftp/staging.py`, que não
  decodifica).
- O texto é lido como `latin-1`: cada byte vira o caractere de mesmo valor, e
  `valor.encode("latin-1")` devolve os bytes do arquivo. Com `cp1252`,
  um único byte 0x90 em `aud_just` derrubava a importação de `RDSP2308`
  (SHA-256 `eb5d97e8…f3ebb`).
- Em `aud_just` de RD SP de 2022-12 a 2023-12 (13 arquivos, 1.056 valores), os únicos
  bytes de 0x80 a 0x9F são 0x80, 0x87 e 0x90, que em CP850 são Ç, ç e É:
  `DOA\x80AO` é "DOAÇAO", `INFORMA\x87oES` é "INFORMAçoES", `REC\x90M` é "RECÉM".
  Nenhum outro campo desses arquivos tem byte nessa faixa. Para ler em CP850:
  `valor.encode("latin-1").decode("cp850")`. A biblioteca não converte: o dicionário
  declara uma codificação por arquivo, não por campo.

### Em aberto

- O que uma linha representa: o documento traz o número da AIH (`n_aih`,
  Informe SIH 2016-03, p. 1), mas não diz que cada linha é uma AIH distinta, e o layout
  RD não traz o número do Cartão Nacional de Saúde do paciente (p. 1–4). Não trate
  linhas como pacientes, e compare linhas com valores distintos de `n_aih` (consulta
  `aih_distintas`) antes de contar AIH.
- Como juntar as AIH de uma mesma internação: o Manual SIH 2012 diz quando uma
  internação se divide em mais de uma AIH (pp. 8, 10–11; ver Armadilhas) e que, em
  cuidados prolongados, a AIH 5 é usada "com mesmo número da AIH - 1" (p. 48). Para a
  nova AIH aberta na mesma internação (pp. 10–11), nem ele nem o informe dizem qual
  campo do RD liga as AIH entre si, e o layout RD não traz o número do Cartão Nacional
  de Saúde (Informe SIH 2016-03, p. 1–4). Em São Paulo, 3.042 valores de `n_aih` estão
  nos arquivos de 2023-03 e de 2023-06: todos com o mesmo `dt_inter` nos dois e com
  `dt_saida` mais tarde em 2023-06; 2.765 têm `ident` 5 nos dois, 274 têm `ident` 1 em
  2023-03 e 5 em 2023-06, e 3 têm linhas com 1 e com 5 em 2023-03. Um mesmo arquivo
  também repete `n_aih` em mais de uma linha (45 valores em 2023-03, 174 em 2023-06),
  nos sete arquivos de São Paulo lidos com um só `dt_inter` por valor
  (`evidence/2026-11-28-rd-medidas-da-revisao/`). Isso vale para esses arquivos; outros
  meses e outras UFs não foram comparados. `homonimo` não liga as AIH: não diz qual é a
  outra AIH nem se é a mesma internação. Nos 175 arquivos `RD` lidos de 2008 a 2025,
  nenhuma AIH com `ident` 5 tem a marca. Nos 74 até 2015-07, a marca está em 314.977 das
  377.784 AIH que têm `nasc`, `sexo` e `cep` iguais aos de outra AIH do arquivo (83,4%),
  e 198.720 das 355.588 AIH marcadas (55,9%) têm outra AIH de mesmo `nasc`, `sexo` e
  `munic_res` com internação sobreposta ou a até 3 dias; nos 101 de 2015-08 em diante, a
  marca está em 3.087 das 1.407.641 AIH com `nasc`, `sexo` e `cep` iguais aos de outra
  (0,2%) (`evidence/2026-11-28-sih-homonimo/`). Até 2015-07 ela é pista de que o
  movimento do mesmo gestor tem outra AIH de paciente de mesmo nome (Manual SIHD 2006;
  Manual SIH 2012, p. 11); de 2015-08 em diante, só entre AIH sem CNS (Nota Técnica SIHD2
  nº 001/2015), e o bloqueio por internação sobreposta, feito pelo CNS, não tem campo no
  RD (Informe SIH 2016-03, p. 1–4). Três campos iguais não são uma pessoa: duas pessoas
  nascidas no mesmo dia, do mesmo sexo e com o mesmo CEP também os têm. Não conte
  internações como linhas sem olhar `ident`, `seq_aih5`, `cobranca`, `n_aih` e
  `dt_inter` nos seus dados.
- Se o mês do arquivo (`mes`) é sempre igual a `mes_cmpt`: o documento não explica o
  nome do arquivo. Compare as duas colunas antes de supor.
- Os códigos de `ident`: o informe não os lista; o Manual SIH 2012 dá os tipos 1 e 5
  (p. 8), sem dizer o que um 3 seria. Para idade e sexo,
  a auditoria de 2026-09-14 acrescentou o pacote oficial TAB_SIH: unidade 5 usa
  100 + quantidade no domínio confirmado; sexo 1 é masculino e 2/3 feminino. A consulta `campo_morte` do notebook mostra
  os valores publicados.
- O comprimento do código de município nos dados: o documento declara 6 caracteres
  (p. 1–2). Confira nos seus dados antes de juntar com outra base.
- A largura de seis campos de texto. O informe dá `nacional` char(2), `raca_cor` char(4),
  `cbor` char(3), `gestor_cpf` char(11) e `gestor_cod` char(3) (Informe SIH 2016-03,
  p. 2–3), e o último layout lido (2025-03 a 2026-07) publica C(3), C(2), C(6), C(15) e
  C(5). Nos arquivos lidos, `gestor_cod` é C(3) e `insc_pn` C(10) até 2011-12, e C(5) e
  C(12) de 2012-01 em diante; o informe, que diz valer "para janeiro de 2008 em diante",
  dá char(3) e char(12). O censo lê um arquivo de RR (ou AP) por mês, mais SP e MG nos
  meses de troca de layout (`evidence/2026-10-06-rd-2008-layouts/`), não todas as UFs. O
  dicionário declara a largura do último layout lido e traz a divergência na issue
  `largura-difere-do-documento` de cada um dos seis campos.
- Se o layout vale para arquivos processados depois de 2016-03: o documento é o informe
  desse processamento (p. 1).
- `nat_jur` e `cnaer` (no RD e no RJ) e `gestor_cod` (no RJ) ficam sem rótulo: o DEF
  liga cada um a tabelas do `TAB_SIH.zip` que ainda não estão empacotadas (`NATJUR.CNV`,
  `NATJURC.CNV`, `ESFERAJUR.CNV` e `ESFERAJURC.CNV`; `CNAEG.CNV` e `CNAE.CNV`;
  `AUTORIZ.CNV`), e a escolha do vínculo está na issue #7. O `vinculos.json` registra o
  motivo em `sem_cnv`. Nas fixtures, `cnaer` é `000` em todas as linhas e o `gestor_cod`
  do RJ vem em branco; o `gestor_cod` do RD é relacionado a `DBF/LIBGESTOR.DBF`.
- Os demais campos que o `RD2008.DEF` e o `RJ2008.DEF` ligam a um CNV e que ficam sem
  mapa (19 no RD, 18 no RJ) também estão em `sem_cnv`, com as linhas do DEF e o motivo:
  agrupamento do código (capítulo e grupo da CID, ano e mês das datas, região e UF do
  município), coluna inicial diferente de 1 (`dias_perm`, `n_aih`), linhas que trazem um
  nome de campo no lugar da coluna inicial (`proc_rea`) ou tabela não empacotada (os
  demais, #137).
- `faec_tp` (no RD e no RJ) tem os rótulos de `CNV/TP_FINAN.CNV`. O DEF liga o campo à
  tabela com `DS_TPFIN` no lugar da coluna inicial. A linha tem a forma da relação com
  DBF do TabWin.pdf (p. 88), mas nomeia um CNV; `DS_TPFIN` é a coluna de descrição do
  `DBF/TP_FINAN.dbf` do mesmo pacote. O mapa usa o CNV, o arquivo que o DEF nomeia, na
  posição 1, a única que cabe num campo de 6 caracteres com códigos de 6 (decisão na
  #182, registrada em `inicio_revisto` do `vinculos.json`). As duas tabelas diferem em 17
  códigos e 2 rótulos (`evidence/2026-11-18-tp-finan-cnv-e-dbf/`): 3 dos 32 códigos que
  os arquivos medidos publicam não estão no DBF. A primeira linha do CNV traz a faixa
  `000000-999999`, "Não discriminado/Não se aplica", e as outras 100 listam um código
  cada: o mapa rotula os 100 e o branco, e não aplica a faixa, então um código fora da
  lista fica sem rótulo, embora a tabela reserve a ele aquele rótulo. Nos 238 arquivos
  RD medidos, os 32 códigos publicados estão todos entre os 100
  (`evidence/2026-11-18-rd-medidas/`). Os rótulos ficam como a tabela os escreve, com
  erros de digitação (`040080`, "… (antigo Reduçäo das Filas)"). A issue
  `faec_tp-faixa-de-reserva` do campo registra isso.
- `RDAC0909.dbc` (Acre, 2009-09) está fora dos 6 layouts. O servidor o data de
  2024-05-22; os outros `RDAC` de 2009 são de 2013-11-01. O cabeçalho tem 82 campos, não
  86: faltam `qt_diarias`, `etnia`, `sequencia` e `remessa`. Em 17 campos o tipo é outro,
  número inteiro de um dígito: 11 campos de valor (`val_sh`, `val_sp` e mais nove) e 6 de
  texto (`num_proc`, `cpf_aut`, `gestor_cod`, `gestor_dt`, `infehosp`, `faec_tp`).
  `val_sh` e `val_sp` vêm zerados nos 4.540 registros, e `val_tot` vem preenchido; em
  `RDAC0908` os dois estão preenchidos nos 4.379. O escopo é importado como publicado: no
  lake, a soma de `val_sh` e a de `val_sp` do Acre em 2009-09 são zero, e as quatro
  colunas que faltam ficam NULL. A issue `zerado-em-rdac0909` dos dois campos registra
  isso. A importação grava os 17 campos com o tipo que o dicionário declara, e o arquivo
  divide a tabela com os outros `RD`: os 11 de valor saem como número com casas, e os 6
  de texto, vazios nos 4.540 registros, saem como texto, com NULL. Três campos (`val_tot`, `val_uti`, `us_tot`) têm tipo
  `F`, que o leitor Rust não lê; a biblioteca lê o arquivo com o leitor Python. A
  evidência está em `evidence/2026-11-19-sih-cabecalhos/` e a decisão, na
  [issue #219](https://github.com/raphaelfh/omnisus/issues/219).

## Como usar

```python
import omnisus as sus

alvo = "ducklake:./data/raw/omnisus.ducklake"  # o padrão de Lake.local() e load()
escopos = sus.available("sih_aih_reduzida", years=[2024], ufs=["RR"], months=[1], refresh=True)
relatorio = sus.import_dataset(
    "sih_aih_reduzida", scopes=escopos, target=alvo, policy="skip_same", run_id="sih-rr-2024-01"
)
with sus.LakeReader(alvo) as leitor:
    print(leitor.connect().sql("SELECT ano, mes, count(*) AS aih FROM lake.sih_aih_reduzida GROUP BY ALL").pl())
```

Passo a passo com análise e procedência:
[notebooks/sih_aih_reduzida.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py)
[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py).

## Fontes

- Disseminação de Informações do Sistema de Informações Hospitalares (SIH), Informe
  Técnico referente ao processamento 2016-03 (`IT_SIHSUS_1603.pdf`), Ministério da
  Saúde / Secretaria de Gestão Estratégica e Participativa / DATASUS:
  <ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Doc/IT_SIHSUS_1603.pdf>
  — consultado em 2026-09-10; SHA-256
  `1e89d5f2cc41420385d7e30ba5541a387912ab3a0efb167d39def74502076220`, conferido de novo
  em 2026-09-13 e em 2026-11-18. Registro: `src/omnisus/data/dicionarios/sources/registry.json`.
  A Tabela 1 do informe (pp. 1–4) está transcrita linha a linha em
  `evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv`, e a descrição de 110 campos
  no dicionário (`sus.describe_dataset("sih_aih_reduzida")`) é a frase que a tabela traz,
  erros de digitação inclusive; 19 campos são descritos só como "Zerado". O rótulo de 24
  campos também é o texto da tabela, até o primeiro ponto (em `ano_cmpt` e `mes_cmpt`,
  até ", no formato"): os que antes diziam mais do que ela ou outra coisa (por exemplo
  `munic_res`, "Município de Residência do Paciente", sem o "(IBGE)" de antes, e
  `uti_int_to`, "Quantidade de diárias em unidade intermediaria", como o documento
  escreve). Parte do que saiu desses rótulos vinha do `RD2008.DEF`, não do informe
  ("Inscrição pré-natal", "Diárias UCI", a tabela `TB_SIGTAW.DBF` dos procedimentos): a
  claim de rótulo de cada um cita a primeira linha do DEF que nomeia o campo. Ao todo 45
  dos 118 rótulos têm claim verificada; os outros 73 não têm, e nenhum teste os compara
  com o documento.
- Layout do arquivo de REDUZIDA gerado pelo SIHD (`Layout_REDUZIDA.pdf`), Ministério da
  Saúde / DATASUS, que a página de manuais do SIHD lista sob "SIHD (uso até 12/2007)":
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/Layout_REDUZIDA.pdf>
  — consultado em 2026-11-18; SHA-256
  `f6084d22de3011fd9d2f490736e6d0469c45ac3ccc45be56f4e5c0ad564cb13d`. Está transcrito em
  `evidence/2026-11-18-layout-reduzida-sihd/layout.csv`. Os 19 campos que o informe de
  2016 descreve só como "Zerado" levam como rótulo o texto deste layout anterior (por
  exemplo `val_sadtsr`, "Valor de SADT sem rateio"): o rótulo diz o que o campo era em
  2006 e 2007, os meses em que os arquivos RD lidos têm exatamente os 75 campos do
  documento. Nos 238 arquivos RD lidos de 2008-01 a 2026-07 (1.994.690 registros, 222
  dos arquivos de Roraima; `evidence/2026-11-18-rd-medidas/`) nenhum dos 19 vem
  preenchido em registro algum. Nos 21 arquivos de Roraima de 2006-04 a 2007-12, os
  meses desse layout, 13 deles vêm (`val_sadt` em 36.858 dos 36.983 registros);
  `num_proc` não vem em nenhum, só nos três arquivos de 2006-01 a 2006-03. Cada um traz a
  issue `rotulo-do-layout-ate-2007`. Onde o informe de 2016 descreve o campo, vale o
  texto dele, mesmo quando o layout anterior dizia outra coisa (`ano_cmpt` era "ANO
  COMPETÊNCIA" e é "Ano de processamento da AIH").
- Manual Técnico Operacional do Sistema de Informação Hospitalar do SUS, setembro de
  2012, Ministério da Saúde / Secretaria de Atenção à Saúde / Departamento de
  Regulação, Avaliação e Controle (Manual SIH 2012):
  <https://bvsms.saude.gov.br/bvs/publicacoes/manual_tecnico_sistema_informacao_hospitalar_sus.pdf>
  — consultado em 2026-11-24; SHA-256
  `7429b011ee2a7329ffb4084e71bd0ede629985ce3d1bcd9e8e4109a2af85e755`, 1.502.594 bytes.
  A página de manuais do SIHD lista `MANUAL_SIH_SETEMBRO_2012_VERSAO_DIA_30_09_12.pdf`
  com o mesmo tamanho (`evidence/2026-11-18-layout-reduzida-sihd/manuais-listing.txt`),
  e o arquivo do FTP (`ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/`),
  baixado em 2026-11-28, tem o mesmo SHA-256. As páginas citadas são as impressas no
  rodapé, duas a menos que as do PDF (p. 8 é a 10ª página do arquivo).
  O manual descreve o SISAIH01 e o processamento do SIH/SUS, não o arquivo RD: liga-se
  aos campos pelo nome que o informe de 2016 dá a cada um.
- Nota Técnica SIHD2 nº 001/2015, DATASUS-RJ, 25/08/2015, da página de manuais do SIHD:
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/SIHD2_NotaTecnica_2015-001.pdf>
  — consultado em 2026-11-26; SHA-256
  `6de69835fef0be45475182f945a716b7b39354f1eb6fde9a56c095b0be4a9eca`, 262.952 bytes.
- Manual Operacional do Sistema de Informação Hospitalar Descentralizado (SIHD), versão
  atualizada em 19/05/2006, Ministério da Saúde / Secretaria de Atenção à Saúde / DRAC /
  CGSI e DATASUS (Manual SIHD 2006), no arquivo `Manual-SIHD atualizada 19.05.06.doc` de
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/Manual_SIHD_19_05_06.zip>
  — consultado em 2026-11-28; SHA-256 do ZIP
  `13954d36eb2b53bf818cabb61592d70ff89a6cda02ed7c2891d964b51c9b6e37`, 2.026.032 bytes.
  É um arquivo do Word, sem páginas numeradas; os trechos citados estão em
  `evidence/2026-11-28-sih-homonimo/README.md`. Descreve o SIHD, o sistema do gestor, em
  2006, não o arquivo RD.
- SIHD2: Manual de Operação, versão do produto 2.40, edição 1.0, julho de 2009,
  Ministério da Saúde / Secretaria Executiva / DATASUS (Manual SIHD2 2009):
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/MNL-PDOC-SIHD2-ManualOperacao-Edicao1.0.pdf>
  — consultado em 2026-11-28; SHA-256
  `0e6bb434e7f2312e4a67a8ce287dc430a3f44a57b2477a7c4d1ffbda466b0c2f`, 12.898.826 bytes.
  As páginas citadas são as impressas no rodapé, nove a menos que as do PDF (p. 106 é a
  115ª página do arquivo). As figuras do manual são imagens e não foram lidas.
- Manual Técnico Operacional do Sistema de Informação Hospitalar do SUS, janeiro de 2017,
  Ministério da Saúde / Secretaria de Atenção à Saúde / DRAC / CGSI (Manual SIH 2017):
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/MANUAL_SIH_janeiro_2017.pdf>
  — consultado em 2026-11-28; SHA-256
  `b51eb51dde1de7ff8b9d0079dffb4f7a48a0361051649d362419bf8f3ee690d1`, 1.658.142 bytes.
  As páginas citadas são as impressas, uma a menos que as do PDF. Só a seção 58 foi
  lida para esta página.
- Dicionário de Dados SIHD (`sihd1_dicionario_de_dados.pdf`), Ministério da Saúde /
  DATASUS, da página de manuais do SIHD:
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/sihd1_dicionario_de_dados.pdf>
  — consultado em 2026-11-28; SHA-256
  `a3d8bb97b272ef8b2439d6c25bf63b4237aa5be12c1cf2deeb7977ad1534dfb1`, 151.990 bytes.
- Pacote de tabelas do SIHD (`Tabelas300.zip`), Ministério da Saúde / DATASUS, da pasta
  de programas do SIHD:
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Programas/Tabelas300.zip>
  — consultado em 2026-11-28; SHA-256
  `6c97292786735aedd78329dbf5e56a9bc0067755a7251b3c285fdd5e77b9c62e`, 574.429 bytes.
  As linhas da tabela 66 estão no arquivo `DSIHD006.TXT`, linhas 1686 e 1687.
- Portaria SAS/MS nº 1.324, de 27 de novembro de 2014, Ministério da Saúde / Secretaria de
  Atenção à Saúde, na impressão do Saúde Legis hospedada pela SES-DF:
  <https://www.saude.df.gov.br/documents/37101/75753/Portaria+MS+n%C2%BA+1.324_2014_Conceitos+de+diagn%C3%B3stico+utilizados+no+Programa+de+Apoio+%C3%A0+Entrada+de+Dados+das+Autoriza%C3%A7%C3%B5es+de+Interna%C3%A7%C3%A3o+Hospitalar.pdf>
  — consultado em 2026-11-26; SHA-256
  `d3ae36f17dd0815d67f62d0d1f56fe8d3a57d91085082bf4d94f94e96868aaf3`, 252.775 bytes.
- Portaria SAS/MS nº 719, de 28 de dezembro de 2007, Ministério da Saúde / Secretaria de
  Atenção à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/sas/2007/prt0719_28_12_2007.html>
  — consultado em 2026-11-24; SHA-256
  `fe7c64067e022f0f8038f36c9dac0011e4b05746eea76b29e9332e59be2564bb`, 61.948 bytes.
- Portaria de Consolidação SAES/MS nº 1, de 22 de fevereiro de 2022, texto compilado,
  Ministério da Saúde / Secretaria de Atenção Especializada à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/saes/2022/prc0001_31_03_2022_comp.html>
  — consultado em 2026-11-24; SHA-256
  `7ea504980caae5735edfe11b9cab06b07917fd08b2c969b4165fd742fb4d6df6`, 1.823.197 bytes.
- Portaria de Consolidação GM/MS nº 2, de 28 de setembro de 2017, texto compilado,
  Ministério da Saúde / Gabinete do Ministro (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/prc0002_03_10_2017.html>
  — consultado em 2026-11-26; SHA-256
  `047d0dc65b9fe2787e635081bdf45c5af5fc82cca374bb2eab478ab3793d796f`, 5.771.523 bytes.
  O Anexo 2 do Anexo XI traz como origem a Portaria GM/MS nº 280/1999.
- Portaria SAS/MS nº 718, de 28 de setembro de 2006, Ministério da Saúde / Secretaria de
  Atenção à Saúde (portal SIHD):
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Portarias/portaria2006/PT-718.htm>
  — consultado em 2026-11-26; SHA-256
  `6eca467db02d64f7a589385e5214dc0b98e9f07da8ae53d71478bfcb52ccc82f`.
  Registro `sihsus-6eca467db02d` em `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAS/MS nº 298, de 1º de março de 2019, Ministério da Saúde / Secretaria de
  Atenção à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/sas/2019/prt0298_06_03_2019.html>
  — consultado em 2026-11-24; SHA-256
  `b6bf1a4c9851b4d780340de08b54e605a83b06cf7a781802bd6721d94ed6de6c`.
  Registro `sihsus-b6bf1a4c9851` em `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAES/MS nº 1.202, de 29 de dezembro de 2023, Ministério da Saúde / Secretaria
  de Atenção Especializada à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/saes/2023/prt1202_29_12_2023.html>
  — consultado em 2026-11-24; SHA-256
  `6a8cfeccbe3bf7a1b2267c2098190038e00642abd3612b8d1667ce9517ff29fb`.
  Registro `sihsus-6a8cfeccbe3b` em `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAES/MS nº 245, de 24 de março de 2020 (republicada), Ministério da Saúde /
  Secretaria de Atenção Especializada à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/saes/2020/prt0245_15_06_2020_rep.html>
  — consultado em 2026-11-24; SHA-256
  `80babfa3a19724e8da3b66a92f1e93767f1ddfa4fae360c46de8e717435bb6dd`.
  Registro `sihsus-80babfa3a197` em `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAES/MS nº 3.511, de 24 de novembro de 2025, Ministério da Saúde / Secretaria
  de Atenção Especializada à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/saes/2025/prt3511_05_12_2025.html>
  — consultado em 2026-11-24; SHA-256
  `39c190981579b6b523ddfb357f44b9af0e096c773e453dac8faad95b9ee163b1`.
  Registro `sihsus-39c190981579` em `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAS/MS nº 508, de 28 de setembro de 2010, Ministério da Saúde / Secretaria de
  Atenção à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/sas/2010/prt0508_28_09_2010.html> —
  consultado em 2026-11-24; SHA-256
  `f3c9c26255ce7383b78bc21f82b0a7b2bd26fa0ff3bccb468e9dcb26b4e8f5e4`. Registro:
  `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria SAS/MS nº 1.134, de 23 de outubro de 2014, Ministério da Saúde / Secretaria de
  Atenção à Saúde (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/sas/2014/prt1134_23_10_2014.html> —
  consultado em 2026-11-24; SHA-256
  `bb6635f3da715a78621c8d1ca7cbf5aaecb042b7a32e3b963956b1199e63bca4`. Registro:
  `src/omnisus/data/dicionarios/sources/registry.json`.
- Demanda raça/cor, informe do DATASUS à 3ª reunião ordinária da Comissão Intergestores
  Tripartite de 2023 (30/03/2023), Ministério da Saúde / Secretaria de Informação e Saúde
  Digital (SEIDIGI) / DATASUS; o arquivo está hospedado no sítio do CONASS:
  <https://www.conass.org.br/wp-content/uploads/2023/03/4.-c-Demanda-rac%CC%A7a-cor.pdf> —
  consultado em 2026-11-24; SHA-256
  `737abb0473feeddcb9aadeae0f173f1d3e279a67e763b65ce13eb0114052d946`. Registro:
  `src/omnisus/data/dicionarios/sources/registry.json`.
- Portaria GM/MS nº 2.418, de 2 de dezembro de 2005, Ministério da Saúde / Gabinete do
  Ministro (Saúde Legis):
  <https://bvsms.saude.gov.br/bvs/saudelegis/gm/2005/prt2418_02_12_2005.html>
  — consultado em 2026-11-24; SHA-256
  `92c80feb434abfae35b99a84e8501875eb378e9d9737b9caa991d707cf516464`, 4.257 bytes.
- Portaria de Consolidação GM/MS nº 3, de 28 de setembro de 2017, Ministério da Saúde /
  Gabinete do Ministro (Saúde Legis), no arquivo `prc0003_03_10_2017ARQUIVO.html`, que
  anota alterações de 2017 e 2018; nenhuma delas está no art. 6º nem no art. 92 do
  Anexo II:
  <https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/prc0003_03_10_2017ARQUIVO.html>
  — consultado em 2026-11-26; SHA-256
  `a93041ba7d74ebc2f287057147a6f3ae1aab9bf8199e403e918d5d4fb0d1534e`, 2.614.946 bytes.
- [Bases e argumentos](../datasets.md#sih), página gerada do registro da biblioteca.

## Detalhes técnicos

### Linha de comando

```bash
omnisus inventory sih_aih_reduzida --refresh
omnisus import sih_aih_reduzida --plan inventory --years 2020-2024 --ufs RR
```

As importações acrescentam linhas a `lake.sih_aih_reduzida`. Ao terminar, a importação
devolve um `ImportReport`; o estado de uma transação interrompida aparece em
`ImportAbortedError`. Veja
[resultados e transações](../guides/inventory.md#transactions-and-interrupted-imports).

### Dicionário

As definições de campo, os metadados de chave estrangeira e as regras de decodificação
ficam em `src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`. A ingestão preserva os valores e tipos do DBF, normaliza nomes de colunas e
acrescenta as partições e a modalidade de origem. O YAML descreve campos e
apresentação; ele não comanda coerções na ingestão. Colunas não listadas no YAML
também são preservadas. A validação do dicionário, sozinha, não
certifica todos os registros recebidos.

### Auditoria do contrato analítico (2026-09-14)

Regras, divergências, inventário e limites de aplicabilidade estão na
[auditoria reproduzível](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-14-contrato-analitico/regras.md).
Ela registra o snapshot 5, os hashes das publicações, schemas e consultas agregadas.
A aplicabilidade se restringe aos escopos confirmados; uma edição documental não
valida automaticamente toda a série histórica. A procedência de arquivo é
consultada por `LakeReader.publications()` no mesmo snapshot.

### Extensão de escopo (2026-09-14)

A regra 1.1.0 inclui o arquivo final RDRR2301.dbc, identificado pelo SHA-256
`e9f717ff378477a883d19f733efe8409aee7f7795a027584b9f383364264d8e4`.
As 4.734 linhas foram auditadas integralmente para idade, sexo e datas.
Códigos fora do domínio documentado permanecem sem interpretação exata.
Veja [relatório e reprodução](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-14-extensao-regras/README.md).

### Validação em lote (2026-10-07)

A regra 1.3.0 cobre os 1.674 arquivos `RD{UF}{AAMM}.dbc` das 27 UFs, das competências
2020-01 a 2025-02, cada um identificado pelo SHA-256 em `validated_sources`. Os arquivos
foram auditados um a um, com uma regra de aceite escrita (ADR 0003, Consequences), e
nenhum foi bloqueado. Ficam sem idade interpretada 9.158 registros com a composta `230` e
12 com a `000`, como a regra documenta. A partir de 2025-03 o RD está no layout 6, ainda
não validado (#86). Um arquivo republicado depois perde as categorias harmonizadas até
uma nova validação.
Veja [relatório e reprodução](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-10-07-validacao-sih_aih_reduzida-2020-01-2025-02/README.md).
