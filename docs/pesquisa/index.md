# Comece aqui

## O que é

O omnisus importa bases abertas do DATASUS e do IBGE para um lake local, uma base de
dados em arquivos no seu computador. Cada importação fica registrada num manifesto, com
o arquivo de origem, o SHA-256 dele e a execução que o publicou; é isso que permite
dizer de onde veio cada linha.

## Preparar

A partir de uma cópia do repositório:

```bash
git clone https://github.com/raphaelfh/omnisus.git
cd omnisus
uv sync --locked --extra notebooks
uv run --locked --extra notebooks marimo edit notebooks/sim_obitos.py
```

Sem clonar, o notebook instala `omnisus` do GitHub (cabeçalho PEP 723):

```bash
uvx marimo edit --sandbox notebooks/sim_obitos.py
```

`--sandbox` e o molab instalam `omnisus` do GitHub no **commit pinado** no
cabeçalho PEP 723 do notebook, não o checkout local. Abra os notebooks a partir
da raiz do repositório (ou defina `OMNISUS_DATA_DIR`) para SIM e IBGE
gravarem no mesmo lake. Use a prévia em **servidor**, não WebAssembly. Para
desenvolver a biblioteca, use `uv sync --locked --extra notebooks`.

No [molab](https://molab.marimo.io) o mesmo notebook abre no navegador, sem
instalar o ambiente local:

[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sim_obitos.py)

## Qual base responde minha pergunta?

| Pergunta | Base | Perfil | Notebook |
| --- | --- | --- | --- |
| Quantas pessoas morreram, de quê, onde moravam? | SIM · óbitos | [perfil](../sources/sim_obitos.md) | [sim_obitos.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sim_obitos.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sim_obitos.py) |
| Quantos nasceram, com que peso, com quantas consultas de pré-natal? | SINASC · nascidos vivos | [perfil](../sources/sinasc_nascidos_vivos.md) | [sinasc_nascidos_vivos.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sinasc_nascidos_vivos.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinasc_nascidos_vivos.py) |
| Quantas internações hospitalares foram registradas, por qual diagnóstico? | SIH · AIH reduzida | [perfil](../sources/sih_aih_reduzida.md) | [sih_aih_reduzida.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py) |
| Que produção ambulatorial foi registrada (sete tabelas: BPA-I, APAC, RAAS)? | SIA · produção ambulatorial | [perfil](../sources/sia.md) | [sia.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sia.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sia.py) |
| Quais estabelecimentos de saúde existem, onde, de que tipo? | CNES · estabelecimentos | [perfil](../sources/cnes_estabelecimentos.md) | [cnes_estabelecimentos.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/cnes_estabelecimentos.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/cnes_estabelecimentos.py) |
| Qual população usar como denominador de uma taxa? | IBGE · população | [perfil](../sources/ibge_populacao.md) | [ibge_populacao.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/ibge_populacao.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/ibge_populacao.py) |
| Quantas notificações de doença de Chagas aguda? | SINAN · Chagas aguda | [perfil](../sources/sinan_chagas.md) | [sinan.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sinan.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinan.py) |
| Quantas notificações de hanseníase, e como terminou o tratamento? | SINAN · hanseníase | [perfil](../sources/sinan_hanseniase.md) | [sinan.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sinan.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinan.py) |
| Quantas notificações de tuberculose, e como terminou o tratamento? | SINAN · tuberculose | [perfil](../sources/sinan_tuberculose.md) | passo a passo genérico do SINAN, sem exemplo de tuberculose: [sinan.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sinan.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinan.py) |
| Que medicamentos o SUS registrou em APAC, e que estoque aparece? | Medicamentos | [perfil](../sources/medicamentos.md) | [medicamentos.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/medicamentos.py) [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/medicamentos.py) |

Leia o perfil antes de contar: ele diz o que uma linha representa, de onde vêm as datas
e os municípios e o que ainda está em aberto.

## As seis etapas

Todo notebook de `notebooks/` segue as mesmas etapas. Rede e escrita só
correm com `EXECUTAR = True` na célula de parâmetros, ou com `-- --executar true`
na exportação.

**1 · O que a base registra.** Mostra os campos da base a partir do dicionário da
biblioteca, sem rede.

**2 · Descobrir.** Pergunta ao FTP do DATASUS o que existe agora:
`odb.available_releases(dataset, ufs=[...], refresh=True)` diz se cada ano está no
diretório final ou no preliminar, e `odb.available(...)` devolve os escopos que podem
ser importados. A população do IBGE não tem inventário: o notebook mostra as edições que
a biblioteca aceita.

**3 · Planejar e importar.** Gravar o plano cria `plano.json` com um `run_id` antes de
qualquer download. A importação usa esse `run_id` e
`odb.import_research`, que usa `policy="skip_same"`, para que repetir a etapa não
duplique linhas. A população usa
`odb.import_ibge_populacao`. Nos notebooks com download por FTP, esta etapa limita o
arquivo comprimido a 25 MiB (`MAX_DOWNLOAD_BYTES` no próprio notebook); um arquivo
maior (por exemplo outra UF) termina como `failed`, e pode ser importado subindo esse
limite ou com a chamada direta `odb.import_dataset` no perfil da base ("Como usar"). A
população do IBGE não baixa pelo FTP, então esse limite não se aplica a ela.

**4 · Conferir.** Lê o manifesto com `LakeReader.publications(run_id=...)`, compara as
linhas no lake com as linhas publicadas e anota o `snapshot_id` mais recente.
`odb.outdated(dataset, lake=...)` é usado quando a base tem diretório preliminar (SIM,
SINASC, SINAN); as demais bases do DATASUS são publicadas num único diretório, e o
notebook não chama `outdated` para elas.

**5 · Analisar.** Roda as consultas SQL num leitor preso a esse snapshot,
`LakeReader(alvo, snapshot_id=odb.latest_snapshot_id(...))`, para que o resultado
não mude se outra importação acontecer depois.

**6 · Guardar.** Grava os resultados em CSV e um `proveniencia.json` com o plano, as
publicações, o `snapshot_id`, o parágrafo de `odb.cite`, as consultas e a versão da
biblioteca. Veja [Reprodutibilidade](reprodutibilidade.md).

## O lake de pesquisa

Os notebooks gravam no mesmo lake, `data/raw/omnisus.ducklake`, e cada execução
ganha uma pasta própria em `data/raw/execucoes/<run_id>/`, com `plano.json`,
`resultado.json`, os CSVs e `proveniencia.json`
(`omnisus.lake.catalog.data_dir` e `save_plan`). A variável de ambiente
`OMNISUS_DATA_DIR` troca essa pasta.

O lake é um só porque uma taxa precisa de duas bases: óbitos por 100 mil habitantes
lê `sim_obitos` e `ibge_populacao` na mesma consulta
(`notebooks/ibge_populacao.py`, consulta `obitos_por_100_mil`). Veja
[Indicadores](indicadores.md).

## Cuidados gerais

- **Arquivos preliminares mudam.** O DATASUS publica anos preliminares que depois são
  revistos; para o SINAN Chagas, veja a nota citada no
  [perfil](../sources/sinan_chagas.md#armadilhas). Guarde o SHA-256 do arquivo e o
  `snapshot_id` e siga [Reprodutibilidade](reprodutibilidade.md).
- **Um registro não é uma pessoa.** Uma linha do SIM é uma declaração de óbito; uma
  linha do SINAN é uma notificação, não um caso confirmado nem um caso novo. Leia as
  Armadilhas de cada perfil, por exemplo as do
  [SINAN Chagas](../sources/sinan_chagas.md#armadilhas) e as do
  [SINAN hanseníase](../sources/sinan_hanseniase.md#armadilhas).
- **Uma data que passa no formato pode ser impossível.** `odb.check_columns` mostra
  `date_min` e `date_max` de cada campo de data; `*_data_status = 'valid'` só diz que o
  texto é uma data. Nos arquivos de RR e SP de 2022 lidos pelo notebook de linkage há
  autorizações de APAC em 9202, nascimentos em 1366 (RAAS) e mães nascidas em 0980
  (SINASC)
  ([relatório](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-23-linkage-ampliado.md#column-check-of-the-new-bases)).
  Defina a regra de exclusão no seu protocolo, a partir da data do evento
  ([consumo](../dicionario/consumo.md#projecoes-para-analise)).
- **Um escritor por lake de cada vez.** Uma importação local segura uma trava de
  escrita, e uma segunda importação no mesmo lake falha com `WriterBusyError`; um
  `LakeReader` não pega a trava e pode ler durante uma importação
  ([reprocessing and maintenance](../guides/reprocessing-and-maintenance.md#coordinate-writers-and-bound-downloads);
  [getting started](../guides/getting-started.md#4-query)).
- **Abrir um notebook não baixa nada.** Um teste abre cada notebook e falha se houver
  conexão de rede ou escrita no lake de pesquisa
  (`tests/unit/notebooks/test_notebooks_abrem_offline.py`).
