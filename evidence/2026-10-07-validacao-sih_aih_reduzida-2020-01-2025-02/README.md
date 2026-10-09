# Validação em lote do SIH RD 2020-01 a 2025-02, 27 UFs — 2026-10-07

Os 1.674 arquivos `RD{UF}{AAMM}.dbc` que o FTP do DATASUS listava em
`/dissemin/publicos/SIHSUS/200801_/Dados` em 2026-10-07, das competências 2020-01 a
2025-02, foram auditados um a um pelo `scripts/metadados/validar_fonte.py`, com a regra de
aceite que o ADR 0003 registra em Consequences (#85). Os 1.674 foram aceitos e entraram em
`x-analytics.validated_sources` de `sih_aih_reduzida.yaml`: 1.666 são novos; os 8 que já
estavam (RR 2023-01, SP 2024-01 a 2024-05, SP 2025-01 e 2025-02) têm o mesmo SHA-256 de
2026-09-14.

A janela termina em 2025-02 porque, a partir de 2025-03, o RD está no layout 6, que
acrescenta `FONTE_ORC` (`evidence/2026-10-06-rd-2008-layouts/README.md`), e o
dicionário ainda não declara esse campo (#86).

## Resultado

| Ano | Escopos | Registros |
| --- | ---: | ---: |
| 2020 | 324 | 10.688.203 |
| 2021 | 324 | 11.629.005 |
| 2022 | 324 | 12.520.914 |
| 2023 | 324 | 13.355.814 |
| 2024 | 324 | 14.171.364 |
| 2025 (jan e fev) | 54 | 2.295.628 |
| **Total** | **1.674** | **64.660.928** |

- **Idade (`idade_status`):** 64.651.758 válidas, 9.158 `unsupported` e 12 `invalid`.
  - As 9.158 são a composta `230` (`cod_idade` 2, `idade` 30), em 1.393 escopos. O
    `IDADEDET.CNV` a dá como "1 mês", não 30 dias, e a regra a deixa `unsupported` desde a
    1.2.0 (nota em `x-analytics.age`). É a faixa da unidade dia (0 a 29) que a recusa; a
    unidade é declarada, então o escopo não é bloqueado.
  - As 12 são a composta `000` (`cod_idade` 0, `idade` 0), em 8 escopos, que a regra lista
    em `invalid_composites`.
  - O detalhe por escopo está em `idades.csv`.
- **Sexo (`sexo_status`):** os 64.660.928 válidos.
- **Datas:** `nasc`, `dt_inter` e `dt_saida` válidas em todos os registros. `gestor_dt`
  está ausente em todos.
- **Idade contra datas** (`datas.csv`, não é autoridade): dos 64.651.758 registros
  comparáveis, 64.324.252 coincidem com os anos completos entre nascimento e internação e
  327.506 divergem (0,5%). A idade publicada não é recalculada.

## Regra de aceite

Um escopo é **bloqueado** quando:

- a auditoria levanta exceção;
- o servidor o divide em vários arquivos;
- o schema que a biblioteca grava difere do da referência;
- um código de sexo não é suportado pela regra;
- uma idade traz uma unidade (`cod_idade`) que a regra não declara.

São os sinais de um código que mudou de significado, a falha que o ADR 0003 existe para
evitar. Ficam **reportados, sem bloquear**: idade fora da faixa de uma unidade declarada
(compostas `230` e `312`), compostas inválidas (`000` e `999`), texto malformado, datas
inválidas e diferenças de idade contra datas. Os harmonizados desses registros ficam
nulos.

## O que exclui a mudança de significado

- **Referência:** `RR_2023_01` (`RDRR2301.dbc`, SHA-256 `e9f717ff…`), validada à mão em
  2026-09-14 (`evidence/2026-09-14-extensao-regras/`).
- **Schema:** cada um dos 1.674 arquivos tem o mesmo schema que a biblioteca grava para
  ela, 117 colunas com os mesmos tipos (`referencia.json`, `schema`). É o layout 5, que o
  censo `evidence/2026-10-06-rd-2008-layouts/` mostra de 2014-01 a 2025-02.
- **Códigos:** os de sexo e de idade vêm do `RD2008.DEF` e dos CNV do `TAB_SIH.zip`
  (`SEXO.CNV`, `IDADEDET.CNV`), registrados com SHA-256, que valem para o RD de 2008 em
  diante.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `manifest.json` | URL, SHA-256, tamanho e data no servidor de cada arquivo (4.845,8 MB no total) |
| `escopos.csv` | Decisão e motivos por escopo |
| `estados.csv` | Contagem de cada estado de cada coluna `*_status`, por escopo |
| `idades.csv` | Códigos de idade que a regra deixa sem interpretação, e por quê |
| `datas.csv` | Idade contra datas, por escopo |
| `referencia.json` | Schema, expressões e consultas da referência; versão da biblioteca (0.2.2), SHA-256 do script, do manifesto e backends |

A auditoria rodou com a regra 1.2.0 (`rule_version` em `referencia.json`). O mesmo PR
sobe a regra para 1.3.0 sem mudar fórmulas: a versão nova marca o conjunto novo de
fontes validadas.

## Como reproduzir

```bash
uv run python scripts/metadados/validar_fonte.py sih_aih_reduzida --ufs ALL --inicio 2020-01 --fim 2025-02
```

Sem `--accept`, não toca no dicionário. Levou cerca de 1 h, com um download por vez. Se
o DATASUS republicar um arquivo, o SHA-256 muda, e aquele escopo perde as categorias
harmonizadas até uma nova validação (`sus.outdated` aponta o escopo).

## Limites

- A validação não detecta arquivo incompleto: confere significado e forma, não volume.
  `RDRR2206` tem 668 registros, contra 3.340 a 4.863 nos outros meses de 2022
  (`evidence/2026-10-06-rd-2008-layouts/census.csv`), e foi aceito.
- O layout 6 (2025-03 em diante) fica para o #86.
