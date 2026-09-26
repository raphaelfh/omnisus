# omnisus

Brings Brazilian public health data (DATASUS, IBGE, CNES) into a local
[DuckLake](https://ducklake.select) lake, with the provenance a researcher needs to cite it.

**Status:** pre-1.0; the API may change between minor versions.

## Install

Python 3.12 or newer:

```bash
pip install "omnisus @ git+https://github.com/raphaelfh/omnisus"
```

Each release also attaches an optional Rust decoder for Linux x86_64, macOS (arm64,
x86_64) and Windows x86_64. Install both packages from the release page:

```bash
pip install omnisus omnisus-dbf \
  --find-links https://github.com/raphaelfh/omnisus/releases/expanded_assets/v0.1.0
```

Without it, Python decodes the same files. See
[Getting Started](docs/guides/getting-started.md) for the lake location, Colab and
the decoder settings.

## Quick start

```python
import omnisus as sus

dados = sus.load("sim_obitos", years=[2023], ufs=["RR"])             # download, return rows
dados = sus.label("sim_obitos", dados, columns=["sexo", "racacor"])  # + sexo_rotulo, racacor_rotulo
sus.check_columns("sim_obitos", dados)                               # empties, unlabelled codes, dates
```

The lake lives in `data/raw/` under the working directory. A second `load` of the same
scope downloads nothing. Every function documents its parameters and an example:
`help(sus.load)`.

## Para pesquisadores

O [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) mostra qual
base responde a cada pergunta, o que um registro representa e como citar o resultado.
Cada base tem um [notebook](notebooks/README.md) com as mesmas seis etapas, que abre no
navegador pelo molab:

[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sim_obitos.py)

## Documentation

The [documentation site](https://raphaelfh.github.io/omnisus/) has the guides, the
dataset catalogue and the API reference. Build it locally with
`uv sync --locked --extra docs && uv run mkdocs serve`.

Contributors: read [`AGENTS.md`](AGENTS.md) first. This repository is public, and every
fact in code or docs comes from the DATASUS server or a hashed file.
