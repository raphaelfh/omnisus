# Validação em lote do SIM 2020–2024, 27 UFs — 2026-10-07

Os 135 arquivos `DO{UF}{ano}.dbc` que o FTP do DATASUS listava em
`/dissemin/publicos/SIM/CID10/DORES` em 2026-10-07 foram auditados um a um pelo
`scripts/metadados/validar_fonte.py`, com a regra de aceite que o ADR 0003 registra em
Consequences (#85). Os 135 foram aceitos e entraram em `x-analytics.validated_sources`
de `sim_obitos.yaml`: 130 são novos; os 5 que já estavam (RR 2021–2024, SP 2024) têm o
mesmo SHA-256 de 2026-09-14.

## Resultado

| Ano | Escopos | Registros |
| --- | ---: | ---: |
| 2020 | 27 | 1.556.824 |
| 2021 | 27 | 1.832.649 |
| 2022 | 27 | 1.544.266 |
| 2023 | 27 | 1.465.610 |
| 2024 | 27 | 1.532.015 |
| **Total** | **135** | **7.931.364** |

- **Idade (`idade_status`):** 7.920.577 válidas e 10.787 ignoradas, nenhuma
  `unsupported` ou `invalid`. Por isso `idades.csv` só tem o cabeçalho.
- **Sexo (`sexo_status`):** 7.928.388 válidos e 2.976 ignorados, nenhum `unsupported`.
- **Datas:** nenhuma inválida nas 11 colunas de data. `dtobito` está preenchida em todos
  os registros e `dtnasc` falta em 16.151.
- **Idade contra datas** (`datas.csv`, não é autoridade): dos 7.915.210 registros com
  idade e datas comparáveis, 7.915.109 coincidem com os anos completos entre nascimento e
  óbito e 101 divergem. As divergências ficam registradas; a idade publicada não é
  recalculada.

## Regra de aceite

Um escopo é **bloqueado** quando:

- a auditoria levanta exceção;
- o servidor o divide em vários arquivos;
- o schema que a biblioteca grava difere do da referência;
- um código de sexo não é suportado pela regra;
- uma idade traz uma unidade que a regra não declara.

São os sinais de um código que mudou de significado, a falha que o ADR 0003 existe para
evitar. Ficam **reportados, sem bloquear**: idade fora da faixa de uma unidade declarada
(no SIM, meses acima de 11), composta inválida, texto malformado, datas inválidas e
diferenças de idade contra datas. Os harmonizados desses registros ficam nulos.

## O que exclui a mudança de significado

- **Referência:** `RR_2023` (`DORR2023.dbc`, SHA-256 `15b52035…`), validada à mão em
  2026-09-14 (`evidence/2026-09-14-contrato-analitico/`).
- **Schema:** cada um dos 135 arquivos tem o mesmo schema que a biblioteca grava para
  ela, 90 colunas com os mesmos tipos (`referencia.json`, `schema`).
- **Códigos:** os de sexo e de idade de todo arquivo caem na regra do documento de
  estrutura do SIM, já no registro de fontes.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `manifest.json` | URL, SHA-256, tamanho e data no servidor de cada arquivo (654,3 MB no total) |
| `escopos.csv` | Decisão e motivos por escopo |
| `estados.csv` | Contagem de cada estado de cada coluna `*_status`, por escopo |
| `idades.csv` | Códigos de idade que a regra deixa sem interpretação, e por quê (vazio aqui) |
| `datas.csv` | Idade contra datas, por escopo |
| `referencia.json` | Schema, expressões e consultas da referência; versão da biblioteca (0.2.2), SHA-256 do script, do manifesto e backends |

A auditoria rodou com a regra 1.1.0 (`rule_version` em `referencia.json`). O mesmo PR
sobe a regra para 1.2.0 sem mudar fórmulas: a versão nova marca o conjunto novo de
fontes validadas.

## Como reproduzir

```bash
uv run python scripts/metadados/validar_fonte.py sim_obitos --ufs ALL --inicio 2020 --fim 2024
```

Sem `--accept`, não toca no dicionário. Se o DATASUS republicar um arquivo, o SHA-256
muda, e aquele escopo perde as categorias harmonizadas até uma nova validação
(`sus.outdated` aponta o escopo).

## Limites

- A validação não detecta arquivo incompleto: confere significado e forma, não volume.
- O lote não inclui o diretório preliminar (`SIM/PRELIM/DORES`, 2025 e 2026).
