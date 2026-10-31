# CO_STATUS do tb_municip.dbf da base territorial: 2026-10-31

O build da `aux_municipios` lê seis municípios do `tb_municip.dbf` e só os aceita se o
`CO_STATUS` estiver no vocabulário da base. Este registro diz de onde vêm os seis valores.

## Arquivos lidos

| Arquivo | SHA-256 |
| --- | --- |
| `territorio/tabelas/2026/06-base_territorial_jun26.zip` (registrado, `base-territorial-f6e06a674cf7`) | `f6e06a674cf7c83693df6a230b2068ea2e257c27970050ca320353e42688316a` |
| `tb_municip.dbf` desse zip (1.185.941 bytes) | `a99e4594fcfa824212536b589cf6ebe2adec9a9f3c18047b88fb836a6fce20f3` |

## Contagem

Lido com `dbfread2` em cp1252, coluna `CO_STATUS` dos 5.725 registros:

| CO_STATUS | Registros |
| --- | ---: |
| `ATIVO` | 5.571 |
| `REG ADM` | 63 |
| `TRANS` | 60 |
| `IGNR` | 27 |
| `EXTIN` | 2 |
| `IGNOR` | 2 |

O `SITUACAO` do `CADMUN.DBF` só tem `ATIVO`, `EXTIN`, `IGNOR` e `TRANS`: a base escreve
dois valores a mais (`REG ADM`, `IGNR`). Os seis municípios que entram na tabela são
`ATIVO`. `DT_INSTAL` é 2013 em cinco e 2009 em Nazária (`220672`).
