# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25.0,<0.26",
#     "omnisus",
#     "polars>=1.44.2,<2.0",
# ]
#
# [tool.uv.sources]
# omnisus = { git = "https://github.com/raphaelfh/omnisus.git", rev = "6df1890e81cbb250306d5d98294b49b73c391a7a" }
# ///

"""IBGE · população: a edição que serve de denominador, com procedência."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="IBGE · população")


@app.cell
def _():
    import asyncio
    from dataclasses import asdict

    import marimo as mo
    import polars as pl

    import omnisus as odb
    from omnisus._notebooks import (
        record_provenance,
        run_without_buttons,
        save_plan,
        write_json,
    )
    from omnisus.lake.catalog import resolve_target
    from omnisus.sources.ibge.products import CENSUS_YEARS, ESTIMATE_UNAVAILABLE_YEARS
    from omnisus.transforms.dictionaries import load_dicionario

    return (
        CENSUS_YEARS,
        ESTIMATE_UNAVAILABLE_YEARS,
        asdict,
        asyncio,
        resolve_target,
        load_dicionario,
        mo,
        odb,
        pl,
        record_provenance,
        run_without_buttons,
        save_plan,
        write_json,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # IBGE · população

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/ibge_populacao.py)

    População municipal publicada pelo IBGE, importada de uma **edição explícita**:
    censo ou estimativa, e um ano. Este notebook percorre as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com o
    **censo de 2022** e, se o SIM estiver no mesmo lake, calcula óbitos por 100 mil.

    **Abrir este notebook não baixa nem grava nada.** Ponha `EXECUTAR = True` (ou
    `-- --executar true`) para rede e escrita.

    Censo e estimativa têm datas de referência diferentes. Leia o
    [perfil da população IBGE](https://raphaelfh.github.io/omnisus/sources/ibge_populacao/)
    e a página [Indicadores](https://raphaelfh.github.io/omnisus/pesquisa/indicadores/).
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    PRODUTO = "census"
    ANO = 2022
    CODIGO_UF = "14"
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    (PRODUTO, ANO, CODIGO_UF, target, executar)
    return ANO, CODIGO_UF, EXECUTAR, PRODUTO, executar, target


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1 · O que a base registra

    Colunas da visão `ibge_populacao`.
    """)
    return


@app.cell
def _(load_dicionario, pl):
    campos = pl.DataFrame(
        [
            {"campo": f["name"], "tipo": f["type"], "rótulo": f.get("label", "")}
            for f in load_dicionario("ibge_populacao").fields
        ]
    )
    campos
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 · Descobrir

    Não há inventário de arquivos: a biblioteca aceita edições conhecidas. Esta
    tabela vem do pacote, sem rede. Uma estimativa só é aceita na edição mais
    recente do agregado; anos recusados não têm universo territorial verificado.
    """)
    return


@app.cell
def _(CENSUS_YEARS, ESTIMATE_UNAVAILABLE_YEARS, pl):
    pl.DataFrame(
        [
            {"produto": "census", "anos": ", ".join(map(str, CENSUS_YEARS))},
            {
                "produto": "estimate",
                "anos_recusados": ", ".join(map(str, ESTIMATE_UNAVAILABLE_YEARS)),
            },
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 · Planejar e importar

    Use o mesmo lake do SIM para poder calcular taxas. Uma edição já importada não
    é importada de novo: a visão `ibge_populacao` falha quando um município e ano
    têm duas publicações. Trocar o código da UF depois de gravar o plano exige um
    novo plano.
    """)
    return


@app.cell
def _(ANO, CODIGO_UF, PRODUTO, executar, mo, save_plan, target):
    mo.stop(
        not executar,
        mo.md("Defina `EXECUTAR = True` para gravar o plano e importar."),
    )
    plano, pasta = save_plan(
        target,
        dataset="ibge_populacao",
        product=PRODUTO,
        ano=int(ANO),
        codigo_uf=CODIGO_UF.strip(),
    )
    plano
    return pasta, plano


@app.cell
async def _(asdict, asyncio, executar, mo, odb, pasta, pl, plano, write_json):
    mo.stop(not executar, mo.md("A importação segue `EXECUTAR` na célula de parâmetros."))
    _sql = (
        "SELECT publication_id, product, ano, sha256, url, collected_at "
        "FROM lake.ibge_population_manifest WHERE product = ? AND ano = ?"
    )
    try:
        with odb.LakeReader(plano["target"]) as _leitor:
            existentes = (
                _leitor.connect().execute(_sql, [plano["product"], plano["ano"]]).pl().to_dicts()
                if "ibge_population_manifest" in _leitor.tables()
                else []
            )
    except odb.CatalogAttachError:
        existentes = []
    if existentes:
        importadas = []
    else:
        importadas = await asyncio.to_thread(
            odb.import_ibge_populacao,
            years=[plano["ano"]],
            census=plano["product"] == "census",
            target=plano["target"],
        )
    write_json(
        pasta / "resultado.json",
        {"ja_publicadas": existentes, "importadas": [asdict(r) for r in importadas]},
    )
    pl.DataFrame(existentes or [asdict(r) for r in importadas])
    return (importadas,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir

    O manifesto guarda URL, SHA-256 e data de coleta de cada publicação; a contagem
    lê a visão, que falharia se houvesse publicações ambíguas.
    """)
    return


@app.cell
def _(importadas, odb, plano):
    with odb.LakeReader(plano["target"]) as _leitor:
        publicacoes = (
            _leitor.connect()
            .execute(
                "SELECT * EXCLUDE (evidence_json) FROM lake.ibge_population_manifest "
                "WHERE product = ? AND ano = ?",
                [plano["product"], plano["ano"]],
            )
            .pl()
            .to_dicts()
        )
        resumo = (
            _leitor.connect()
            .execute(
                "SELECT count(*) AS municipios, sum(populacao) AS populacao_total "
                "FROM lake.ibge_populacao WHERE ano = ?",
                [plano["ano"]],
            )
            .pl()
        )
        snapshot_id = odb.latest_snapshot_id(_leitor)
    {
        "edicoes_importadas_nesta_execucao": len(importadas),
        "manifesto": publicacoes,
        "resumo": resumo,
        "snapshot_id": snapshot_id,
    }
    return publicacoes, snapshot_id


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5 · Analisar

    A taxa junta os municípios pelos **6 primeiros dígitos**. Óbitos entram pelo
    município de residência (`codmunres`) e só os arquivos do SIM presentes no lake
    são contados.
    """)
    return


@app.cell
def _(odb, plano, snapshot_id):
    _ano, _uf = plano["ano"], plano["codigo_uf"]
    _mun_obito = odb.municipality_join_key_sql("codmunres")
    _mun_pop = odb.municipality_join_key_sql("codigo_ibge")
    _consultas = {
        "populacao_por_municipio": (
            "SELECT codigo_ibge, populacao FROM lake.ibge_populacao "
            "WHERE ano = ? AND left(codigo_ibge, 2) = ? ORDER BY populacao DESC",
            [_ano, _uf],
        ),
        "digitos_codigo_ibge": (
            "SELECT length(codigo_ibge) AS digitos, count(*) AS municipios "
            "FROM lake.ibge_populacao WHERE ano = ? GROUP BY ALL",
            [_ano],
        ),
    }
    with odb.LakeReader(plano["target"], snapshot_id=snapshot_id) as _leitor:
        _tem_sim = "sim_obitos" in _leitor.tables()
        if _tem_sim:
            _consultas["digitos_codmunres_sim"] = (
                "SELECT length(trim(CAST(codmunres AS VARCHAR))) AS digitos, count(*) AS obitos "
                "FROM lake.sim_obitos WHERE ano = ? GROUP BY ALL",
                [_ano],
            )
            _consultas["obitos_por_100_mil"] = (
                f"""
                WITH obitos AS (
                    SELECT {_mun_obito} AS municipio,
                           count(*) AS obitos
                    FROM lake.sim_obitos WHERE ano = ? GROUP BY ALL
                ), populacao AS (
                    SELECT {_mun_pop} AS municipio, populacao
                    FROM lake.ibge_populacao WHERE ano = ? AND left(codigo_ibge, 2) = ?
                )
                SELECT municipio, obitos, populacao,
                       round(100000.0 * obitos / populacao, 1) AS obitos_por_100_mil
                FROM populacao JOIN obitos USING (municipio)
                ORDER BY municipio
                """,
                [_ano, _ano, _uf],
            )
        resultados = {
            nome: _leitor.connect().execute(sql, parametros).pl()
            for nome, (sql, parametros) in _consultas.items()
        }
    consultas = {
        nome: {"sql": sql, "parameters": parametros}
        for nome, (sql, parametros) in _consultas.items()
    }
    resultados
    return consultas, resultados


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6 · Guardar

    Resultados e `procedencia.json` na pasta da execução. Veja
    [Reprodutibilidade](https://raphaelfh.github.io/omnisus/pesquisa/reprodutibilidade/).
    """)
    return


@app.cell
def _(consultas, pasta, plano, publicacoes, record_provenance, resultados, snapshot_id):
    record_provenance(
        pasta, plan=plano, publications=publicacoes, snapshot_id=snapshot_id, queries=consultas
    )
    for _nome, _tabela in resultados.items():
        _tabela.write_csv(pasta / f"{_nome}.csv")
    str(pasta)
    return


if __name__ == "__main__":
    app.run()
