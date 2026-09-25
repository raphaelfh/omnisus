# Verificação da extensão — 2026-09-14

## Testes

- TDD: os 18 casos novos de anos completos/SINASC falharam antes da implementação
  por ausência de suporte ao tipo de regra e ausência de metadados analíticos.
- Os dois testes dos novos escopos SIM/SIH falharam antes da inclusão de seus hashes.
- Suite focada: **165 passaram**, cobrindo transformações, metadados, consistência
  do registro e geração de dicionários.
- Suite unitária ampliada: **855 passaram**, em 79,04 s; dois avisos de depreciação
  existentes no teste de transações (`vacuum`). Comando:

```bash
OMNISUS_DBC_BACKEND=python OMNISUS_DBF_BACKEND=python .venv/bin/pytest tests/unit \
  --ignore=tests/unit/sources/datasus_ftp/test_dbc.py \
  --ignore=tests/unit/sources/datasus_ftp/test_staging.py \
  --ignore=tests/unit/sources/datasus_ftp/test_dbf_parity.py -q --tb=short
```

A tentativa de executar todos os testes parou na coleta: `Incompatible native
API (expected 2)`. A extensão local `omnisus-db-dbf` é incompatível. Os três
arquivos acima incluem testes nativos e acionam essa checagem. Não se modificou
nem simulou a extensão para obter resultado verde; a suite nativa não foi validada.
Os totais de 165 e 855 se sobrepõem e não devem ser somados.

## Contrato e evidências

- `consultar.py --dataset sinasc_nascidos_vivos --field idademae --json`: documento
  de metadados validado pelo JSON Schema, unidade `year` e fontes resolvidas.
- Ruff check e format check dos cinco arquivos Python alterados/adicionados: sem erros.
- `git -c core.whitespace=cr-at-eol diff --check`: sem erros; a opção respeita o
  CRLF já utilizado nos catálogos CSV gerados.
- `atualizar_catalogo.py --check-local`: catálogo reconstruído e hashes das fontes
  antigas conferidos; datas históricas preservadas.
- `acceptance.json`: hashes de metadados conferem com os três contratos finais;
  todos os valores distintos de idade observados têm paridade SQL/Python.
- Snapshot 5: `bands`, `sex`, `statuses`, publicações, schemas e totais são iguais
  ao aceite anterior; histórico de snapshots inalterado. Só a descrição da
  projeção mudou, incluindo versão da regra e hash de metadados.

Os DBCs e PDFs completos ficam no acervo local ignorado pelo Git; os relatórios
versionáveis contêm apenas metadados, hashes e agregados. Não foi feito release.
