# omnisus

Brings Brazilian public health data (DATASUS, IBGE, CNES) into a local
[DuckLake](https://ducklake.select) lake, with the provenance a researcher needs to cite it.

## What it does

- **Fetches** DBC files from the DATASUS FTP server, population tables from IBGE and
  establishment names from the CNES API.
- **Decodes** DBC and DBF in batches spooled to disk, in Rust when the optional
  decoder is installed and in Python otherwise.
- **Stores** Parquet under a DuckLake catalog (SQLite or PostgreSQL). Each imported
  scope is recorded with its source files and their SHA-256.
- **Labels** codes and checks columns against dictionaries whose every claim cites an
  official document.
- **Inventories** the FTP server, so an import plans from what is published.

## Where to start

| You want to | Read |
| --- | --- |
| Answer a research question with one base | [Guia do pesquisador](pesquisa/index.md) and its notebooks |
| Install and run a first import | [Getting Started](guides/getting-started.md) |
| See every dataset the package imports | [Datasets](datasets.md) |
| Know what a column means and where that comes from | [Dicionário de dados](dicionario/index.md) |
| Recover from failures, reprocess, maintain a lake | [Reprocessing and maintenance](guides/reprocessing-and-maintenance.md) |
| Look up a function | [API reference](api.md) |

```python
import omnisus as odb

dados = odb.load("sim_obitos", years=[2023], ufs=["RR"])
```
