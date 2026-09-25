# Validação da extensão Rust DBF

Data: 2026-09-10. Base: `dd4ccef`. Implementação local concluída, com Rust opcional.

## Entrega e organização

O pacote `native/omnisus-dbf` contém um crate com módulos de cabeçalho,
decodificação C/N, cursor, builders Arrow e bindings PyO3. A versão é 0.1.0 e o
contrato Python usa `API_VERSION = 1`. O pacote principal continua Hatchling e
seu wheel permanece `py3-none-any`; instalar a base não instala a nova extensão.

`dbf_contract.py` centraliza integridade e identidade semântica;
`dbf_batches.py` concentra os adaptadores e a seleção de backend. `staging.py`
continua sendo a única implementação de normalização, reconciliação de schema,
IPC e publicação Parquet. O runner preserva `dbc-staging-v1:<dictionary_hash>`:
trocar Python por Rust não invalida `skip_same`.

Fixtures sintéticas e seu construtor ficam em `tests/fixtures/dbf` e
`tests/support/dbf.py`. A [caracterização do corpus](rust-dbf-corpus.md) descreve
as 11 fixtures DBC existentes, incluindo o cabeçalho FoxPro do SIA ABO e o reparo
CNES. Não foram duplicados os DBCs reais nem incluídos binários de build no Git.

Rust foi escolhido para a conversão DBF → Arrow dentro do processo Python, com
ownership dos buffers e ponte oficial `arrow-pyarrow`. Não foi criado outro
servidor/backend. A API tipada `dbase::FieldValue` foi descartada porque não
preserva o contrato atual de inteiros exatos e texto vazio; o leitor implementa
somente o escopo C/N descrito no contrato.

## Evidência de correção

| Verificação local | Resultado |
|---|---|
| Suíte final Python com extensão obrigatória | **601 passaram**, 55 casos e2e/perf desmarcados; **92,28%** de cobertura, acima do mínimo de 85% |
| Suíte sem extensão instalada, antes dos últimos testes adicionais | 546 passaram, 44 casos nativos pulados explicitamente, 47 desmarcados; 92,27% de cobertura |
| Rust com e sem feature Python | 13 testes passaram em cada configuração; propriedades com 512 casos por propriedade |
| Paridade DBC real | Todas as 11 fixtures, lotes de 7 e 100.000; valores, tipos, nulls e ordem comparados exatamente |
| Paridade sintética | Inteiros int64 exatos, texto vazio, encodings, erros e lotes de 1, 7, 1.024 e 100.000 |
| Instalações isoladas dos wheels nativos | 9 testes por wheel CPython 3.12/3.13, fora do checkout, com PyArrow/pytest binários |
| Reconstrução sdist → wheel | Conteúdo conferido, build isolado com lock e 9 testes de instalação |
| Stack inteira em CPython 3.12, somente wheels | 143 pacotes instalados, dependências consistentes; 325 testes passaram contra os wheels instalados |
| Wheel principal reconstruído após correção de limpeza | 33 testes de staging/parse/adaptadores passaram contra a instalação 3.12 atualizada |
| Checkout principal após aplicação e instalação | **80 testes passaram** em 46,81 s; hashes das fontes e do binário coincidem com os validados; 161 pacotes com dependências consistentes |
| Lint e tipagem | Ruff check/format, mypy (44 módulos), Rust fmt/clippy e git diff --check passaram |
| Workflow nativo | Validado localmente com actionlint 1.7.12; execução remota ainda pendente |

A suíte final teve dois avisos de depreciação preexistentes dos testes de vacuum.
Os testes e2e que acessam serviços externos e os benchmarks não compõem essa
contagem; dez testes de desempenho foram exercitados separadamente como smoke.
O job nativo usa `--require-rust-dbf`, que falha se extensão ou fixtures obrigatórias
estiverem ausentes, evitando aprovação por skip ou fallback acidental.

As verificações cobrem inteiros maiores que 2^53 sem perda de precisão, famílias
incompatíveis sem coerção silenciosa, campos deletados, truncamento, EOF,
encoding estrito e validade dos batches após fechar/destruir o leitor. Os testes
com DuckDB/DuckLake local exercitam publicação, `skip_same` entre backends,
`replace` preservando outra UF, falha tardia e rollback conservando dados e manifesto.

Falhas injetadas na gravação do DBF temporário, no segundo IPC, no primeiro
Parquet e no `os.replace` verificam limpeza e preservação do arquivo anterior.
Cancelamento e falha durante a iteração verificam o fechamento do reader; o
fallback automático só ocorre antes do consumo, para ausência da extensão ou
metadados não suportados. Imports quebrados, versão de API incompatível e dados
corrompidos propagam o erro.

Duas revisões cruzadas independentes examinaram o leitor nativo e a integração
Python/CI. Os achados de limpeza do DBF em falha de escrita e de cobertura das
falhas IPC/Parquet foram resolvidos com regressões. A revisão final não deixou
achados bloqueantes. Testes diferenciais também detectaram e fixaram whitespace
numérico vertical, sinal de NaN e padding após EOF.

A campanha curta de fuzzing com AddressSanitizer completou **995.082 execuções
em 31 segundos**, sem crash ou erro do sanitizer. Ambiente, seed e reprodução
estão no [README do fuzz](../native/omnisus-dbf/fuzz/README.md). Esse resultado
é evidência limitada, não garantia de ausência absoluta de defeitos.

## Desempenho observado

O [relatório JSON completo](rust-dbf-performance.json) registra 192 processos,
um aquecimento e sete medições por backend/corpus/fase, com ordem alternada.
Máquina: Apple M5 Pro, macOS arm64, CPython 3.13.12, PyArrow 25.0.1; Rust release.
As 12 combinações corpus/fase produziram schemas e conteúdo ordenado equivalentes.

| DBF → Arrow, corpus ampliado 4× | Registros | Python, mediana | Rust, mediana | Aceleração |
|---|---:|---:|---:|---:|
| SIM, campos C | 13.244 | 510,612 ms | 19,576 ms | **26,08×** |
| SIH, campos C/N | 14.856 | 857,374 ms | 40,780 ms | **21,02×** |

Para DBC → Parquet nos dois arquivos DBC reais, a soma das medianas caiu de
**447,507 ms para 115,724 ms**, aproximadamente **3,87×**. Nessa medida entram
descompactação, parsing, IPC e Parquet. Os DBFs ampliados não são DBCs recomprimidos;
seu tempo de DBF → Parquet exclui descompactação e não entra nesse agregado.

A razão Rust/Python do RSS mediano ficou entre **0,633 e 0,908** nas fases de
parsing/staging: não houve regressão no corpus medido. Na publicação, medida à
parte num lake novo por rodada, o RSS ficou praticamente igual (0,999–1,0004),
e os tempos permaneceram próximos. Não se atribui ao parser ganho de publicação.

Os gates locais de ≥2× em ambos os DBFs ampliados, ≤10% de regressão agregada
DBC → Parquet e ≤20% de regressão de RSS passaram. A promoção do default continua
condicionada também à distribuição em todas as plataformas previstas.

Os hashes dos seis arquivos medidos correspondem às fontes finais, incluindo a
correção de limpeza em `parse.py`. O hash do wheel CPython 3.13 usado é
`0195faae0a56b4dce8cbf9ecd2efdb29a4ffa70f4256539c561afae676e8fd4a`;
o binário carregado e as chamadas ao leitor nativo estão registrados por worker.
SHA-256 do relatório: `05d3e96981caddcce2e6944de403bd5926b983a65eee867caf9411f0565c9b68`.

A validação de conteúdo ocorre após a captura de tempo/RSS. O RSS inclui imports
e preparação; o disco temporário é amostrado a cada 5 ms e constitui um limite
inferior. Não houve rede nos workers nem limpeza do cache de páginas do sistema.
Repetir registros de fixtures locais não representa a diversidade nacional:
os números descrevem este ambiente e corpus, sem promessa de aceleração geral.
O [baseline anterior](rust-dbf-baseline.json) foi preservado como histórico,
sem misturá-lo às medições finais entre backends.

## Distribuição e rollout

O default continua **python**. `rust` seleciona a extensão estritamente; `auto`
permite Python apenas se o módulo opcional estiver ausente ou o formato for
recusado no preflight. A disponibilidade de `auto` não altera o default.

A validação local cobre macOS arm64 e CPython normal 3.12/3.13. O workflow
`.github/workflows/native.yml` configura oito combinações desses Pythons com
Linux x86_64 manylinux, Windows x86_64 e macOS arm64/x86_64. **Linux, Windows e
macOS Intel ainda não foram executados neste trabalho.** O CI gera artefatos e
bloqueia falhas de instalação nativa; não publica no PyPI.

Os gates locais de tempo e RSS passaram no benchmark acima. Promover o
default para `auto` ainda exige que toda a matriz externa de distribuição passe.
Também continuam fora do escopo a publicação PyPI, tags, push e o extra `rust`
no pacote principal: esse extra só pode apontar para uma versão já disponível.
A lacuna de wheels CPython 3.13 do descompactador `datasus-dbc` é preexistente;
o CI nativo isolado é obrigatório independentemente dela.

Versões pinadas: Rust 1.98.1 (piso efetivamente testado), PyO3 0.29.0,
Arrow/arrow-pyarrow 59.2.0 e Maturin 1.12.6. `Cargo.lock` inclui dependências
transitivas; não foi validada uma toolchain Rust anterior. O leitor mantém uma
cópia própria do DBF; a ingestão ainda carrega DBC/DBF completos. O trabalho não
promete memória constante nem aceleração de rede ou do motor DuckLake.

## Estado do checkout entregue

As alterações foram aplicadas ao projeto principal preservando o trabalho
concorrente dos notebooks. O wheel nativo CPython 3.13 está instalado na `.venv`;
leitura real confirmou o inteiro `1152921504606846977` sem perda de precisão.
Os wheels locais CPython 3.12 e 3.13 estão em `dist/native/`, e o wheel principal
Python puro em `dist/`. Esses artefatos são ignorados pelo Git. Não houve push,
tag, publicação ou commit das alterações concorrentes.

## Reprodução

Na raiz do repositório, com a toolchain pinada disponível:

```bash
uv sync --locked --extra dev
uv build native/omnisus-dbf --wheel --out-dir dist/native
uv pip install --python .venv --no-deps dist/native/omnisus_db_dbf-<tag-do-seu-python-e-plataforma>.whl
uv run --no-sync pytest -m 'not e2e and not perf' --require-rust-dbf --cov=omnisus_db --cov-fail-under=85
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy src
cargo test --locked --manifest-path native/omnisus-dbf/Cargo.toml
cargo test --locked --no-default-features --manifest-path native/omnisus-dbf/Cargo.toml
cargo fmt --manifest-path native/omnisus-dbf/Cargo.toml -- --check
cargo clippy --locked --all-targets --manifest-path native/omnisus-dbf/Cargo.toml -- -D warnings
```

Substituir o nome ilustrativo pelo wheel correspondente ao Python/plataforma.
Um `uv sync` pode remover a extensão local por ela ainda não fazer parte do lock
principal; reinstalar o wheel e usar `uv run --no-sync` nos testes nativos.

```bash
OMNISUS_DBF_BACKEND=rust uv run --no-sync python seu_script.py
OMNISUS_DBF_BACKEND=python uv run --no-sync python seu_script.py
```

O modo de benchmark padrão compara os dois backends. As extensões DuckDB/DuckLake
precisam estar disponíveis localmente antes da medição, sem download no worker.
Usar o wheel release correspondente ao ambiente e uma descrição de CPU conferida:

```bash
uv run --no-sync python scripts/benchmark_resources.py \
  --repeat 4 --rounds 7 --warmups 1 --rust-build-profile release \
  --rust-wheel dist/native/omnisus_dbf-<tag-do-seu-python-e-plataforma>.whl \
  --cpu-description 'CPU verificada' --output evidence/rust-dbf-performance.json
```

A [ADR 0001](../docs/decisions/0001-rust-dbf.md) registra a decisão.
