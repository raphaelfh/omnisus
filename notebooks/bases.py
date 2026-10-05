# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25.0,<0.26",
#     "omnisus==0.2.2",
#     "polars>=1.44.2,<2.0",
# ]
# ///

"""Bases do DATASUS: a lista de todas e qualquer uma delas até a citação, em seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Bases do DATASUS")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl

    import omnisus as sus

    return Path, mo, sus, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Bases do DATASUS

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/bases.py)

    Todas as bases do FTP do DATASUS que o omnisus importa, numa tabela, e o caminho
    de qualquer uma delas até a citação. Escolha a base em `BASE` na célula de
    parâmetros e siga as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com um
    recorte pequeno: **Roraima, janeiro de 2024**, em `cnes_leitos`.

    Os notebooks de cada sistema (`sim_obitos.py`, `sia.py`, `sinan.py`...) põem
    rótulos e analisam a base; este só conta os registros do recorte, e por isso
    serve para qualquer base.

    **Abrir este notebook não baixa nem grava nada.** Edite os parâmetros e ponha
    `EXECUTAR = True` (ou exporte com `-- --executar true`) para consultar a rede e
    gravar no lake (`data/raw/`, ou `$OMNISUS_DATA_DIR`).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Que bases existem

    `sus.describe_datasets()` devolve uma linha por base, sem rede: o nome que vai em
    `BASE` (`name`), o sistema (`category`), o que é (`title`), como é publicada e
    desde quando. `geography` diz se `sus.load` pede `ufs` (`state`) ou se o arquivo é
    nacional (`national`), e `cadence` se aceita `months` (`monthly`). A cobertura é a
    janela declarada na biblioteca, não o que o servidor publica hoje; isso, só
    `sus.available` responde. `labelled_fields` conta as colunas que `sus.label`
    rotula. A tabela tem busca, filtro e ordenação; a mesma lista, por sistema, está
    em [Bases e argumentos](https://raphaelfh.github.io/omnisus/datasets/).
    """)
    return


@app.cell
def _(sus):
    bases = sus.describe_datasets()
    bases
    return (bases,)


@app.cell
def _(bases, pl):
    bases.group_by(sistema="category").agg(
        bases=pl.len(),
        por_uf=(pl.col("geography") == "state").sum(),
        mensais=(pl.col("cadence") == "monthly").sum(),
        com_preliminar=pl.col("prelim_dir").is_not_null().sum(),
    ).sort("sistema")
    return


@app.cell
def _(mo):
    # Parâmetros: edite e reexecute. BASE é um `name` da tabela acima. UF vale só para
    # base por UF e MES só para base mensal; a etapa 1 mostra a chamada sem eles.
    BASE = "cnes_leitos"
    UF = "RR"
    ANO = 2024
    MES = 1
    EXECUTAR = False
    executar = EXECUTAR or bool(mo.cli_args().get("executar"))
    return ANO, BASE, MES, UF, executar


@app.cell
def _(ANO, BASE, MES, UF, bases, sus):
    _dataset = sus.resolve(BASE)
    argumentos = {"years": [ANO]}
    if _dataset.geography == "state":
        argumentos["ufs"] = [UF]
    if _dataset.monthly:
        argumentos["months"] = [MES]
    linha = bases.filter(name=BASE).row(0, named=True)
    return argumentos, linha


@app.cell(hide_code=True)
def _(BASE, argumentos, linha, mo):
    _fim = "em diante" if linha["coverage_end"] is None else f"a {linha['coverage_end']}"
    _publicacao = "um arquivo por UF" if linha["geography"] == "state" else "um arquivo nacional"
    _cadencia = "por mês" if linha["cadence"] == "monthly" else "por ano"
    _preliminar = (
        " O DATASUS publica também arquivos preliminares; `sus.load` lê os dois e cada"
        " linha diz `final` ou `prelim` em `_source_release`."
        if linha["prelim_dir"]
        else ""
    )
    _sistema = linha["category"]
    _secao = f"https://raphaelfh.github.io/omnisus/datasets/#{_sistema.lower()}"
    _chamada = ", ".join([repr(BASE)] + [f"{k}={v!r}" for k, v in argumentos.items()])
    mo.md(f"""
    ## 1 · A base escolhida: `{BASE}`

    **{linha["title"]}.** Cobertura declarada: {linha["coverage_start"]} {_fim};
    {_publicacao}, {_cadencia}.{_preliminar}

    Com os parâmetros acima, a etapa 3 chama:

    ```python
    sus.load({_chamada})
    ```

    Abaixo, os campos do dicionário da biblioteca (`sus.describe_dataset`), sem rede;
    `mapa de códigos` marca os que `sus.label` rotula. As outras bases do sistema estão
    em [Bases e argumentos · {_sistema}]({_secao}).
    """)
    return


@app.cell
def _(BASE, sus, pl):
    pl.DataFrame(
        [
            {
                "campo": f["name"],
                "tipo": f["type"],
                "rótulo": f.get("label", ""),
                "mapa de códigos": bool(f.get("x-decode")),
            }
            for f in sus.describe_dataset(BASE)["schema"]["fields"]
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 · Descobrir

    `sus.available` lista agora os arquivos da base no FTP do DATASUS, na UF escolhida
    (todas as publicações, numa base nacional).
    """)
    return


@app.cell
def _(BASE, argumentos, executar, mo, sus, pl):
    mo.stop(not executar, mo.md("Defina `EXECUTAR = True` na célula de parâmetros."))
    publicados = sus.available(BASE, ufs=argumentos.get("ufs"), refresh=True)
    pl.DataFrame(publicados).sort("ano", "mes", descending=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 · Baixar e ler

    `sus.load` importa o recorte para o lake e devolve as linhas, com os códigos como
    o DATASUS publicou. Rodar de novo não baixa nem duplica nada.
    """)
    return


@app.cell
def _(BASE, argumentos, executar, mo, sus):
    mo.stop(not executar, mo.md("Defina `EXECUTAR = True` na célula de parâmetros."))
    dados = sus.load(BASE, **argumentos)
    dados
    return (dados,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir

    `sus.check_columns` mostra, por coluna, vazios, códigos sem rótulo e datas fora
    do esperado. Numa base com preliminar, `sus.outdated` lista também os escopos que
    o DATASUS republicou desde a importação.
    """)
    return


@app.cell
def _(BASE, dados, sus):
    sus.check_columns(BASE, dados)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5 · Contar

    Aqui, só o número de registros do recorte. Para analisar, use o dicionário da
    etapa 1, `sus.label` e o notebook do sistema, e leia o perfil da base em
    [Bases e argumentos](https://raphaelfh.github.io/omnisus/datasets/).
    """)
    return


@app.cell
def _(dados, pl):
    registros = dados.select(registros=pl.len())
    registros
    return (registros,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6 · Citar e guardar

    `sus.cite` nomeia o arquivo do servidor, o SHA-256 e o snapshot do lake de cada
    publicação da base. A contagem e a citação vão para `resultados/<BASE>/`. Veja
    [Reprodutibilidade](https://raphaelfh.github.io/omnisus/pesquisa/reprodutibilidade/).
    """)
    return


@app.cell
def _(BASE, Path, registros, sus):
    with sus.LakeReader() as _lake:
        citacao = sus.cite(_lake, dataset=BASE)
    pasta = Path("resultados") / BASE
    pasta.mkdir(parents=True, exist_ok=True)
    registros.write_csv(pasta / "registros_no_recorte.csv")
    (pasta / "citacao.txt").write_text(citacao.text, encoding="utf-8")
    print(citacao.text)
    return


if __name__ == "__main__":
    app.run()
