# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25.0,<0.26",
#     "omnisus",
#     "polars>=1.44.2,<2.0",
# ]
#
# [tool.uv.sources]
# omnisus = { git = "https://github.com/raphaelfh/omnisus.git", rev = "ee5ff47a4a2649e1e3baf34c8736ead2580bfabc" }
# ///

"""CNES · estabelecimentos: do arquivo do DATASUS a uma tabela citável, em seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="CNES · estabelecimentos")


@app.cell
def _():
    import asyncio
    from dataclasses import asdict

    import marimo as mo
    import polars as pl

    import omnisus as odb
    from omnisus._notebooks import (
        reconcile,
        record_import,
        record_provenance,
        run_without_buttons,
        save_plan,
    )
    from omnisus.lake.catalog import resolve_target
    from omnisus.transforms.dictionaries import load_dicionario

    dataset = "cnes_estabelecimentos"
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    return (
        MAX_DOWNLOAD_BYTES,
        asdict,
        asyncio,
        dataset,
        resolve_target,
        load_dicionario,
        mo,
        odb,
        pl,
        reconcile,
        record_import,
        record_provenance,
        run_without_buttons,
        save_plan,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # CNES · estabelecimentos

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/cnes_estabelecimentos.py)

    Arquivo de estabelecimentos (ST) do Cadastro Nacional de Estabelecimentos de
    Saúde (CNES), publicado pelo DATASUS por UF e competência. Este notebook percorre
    as seis etapas do [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/)
    com um recorte pequeno: **Roraima, janeiro de 2024**.

    **Abrir este notebook não baixa nem grava nada.** Edite os parâmetros e ponha
    `EXECUTAR = True` (ou `-- --executar true`) para rede e escrita.

    O dicionário empacotado declara 12 colunas. Antes de interpretar números, leia o
    [perfil do CNES](https://raphaelfh.github.io/omnisus/sources/cnes_estabelecimentos/).
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    UF = "RR"
    ANO = 2024
    MES = 1
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    (UF, ANO, MES, target, executar)
    return ANO, MES, UF, executar, target


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1 · O que a base registra

    Campos do dicionário que a biblioteca aplica na importação; colunas do arquivo
    fora do dicionário também são preservadas.
    """)
    return


@app.cell
def _(dataset, load_dicionario, pl):
    campos = pl.DataFrame(
        [
            {"campo": f["name"], "tipo": f["type"], "rótulo": f.get("label", "")}
            for f in load_dicionario(dataset).fields
        ]
    )
    campos
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 · Descobrir

    Lista agora o FTP do DATASUS (`refresh=True`).
    """)
    return


@app.cell
async def _(asyncio, dataset, executar, mo, odb, pl):
    mo.stop(
        not executar,
        mo.md(
            "Para consultar o DATASUS, defina `EXECUTAR = True` na célula de parâmetros "
            "ou rode com `-- --executar true`."
        ),
    )
    _publicados = await asyncio.to_thread(odb.available, dataset, ufs=["RR"], refresh=True)
    publicados = pl.DataFrame(
        [
            {"uf": e.uf, "ano": e.ano, "mes": e.mes}
            for e in sorted(_publicados, key=lambda e: (-e.ano, -(e.mes or 0)))
        ]
    )
    publicados
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 · Planejar e importar

    Confira ano e mês na etapa 2. Gravar o plano cria `plano.json` com um `run_id`
    antes de qualquer download. Toda importação do CNES-ST também atualiza a visão
    `aux_cnes`. O notebook limita cada download comprimido a 25 MiB.
    """)
    return


@app.cell
def _(
    ANO,
    MAX_DOWNLOAD_BYTES,
    MES,
    UF,
    asdict,
    dataset,
    executar,
    mo,
    odb,
    save_plan,
    target,
):
    mo.stop(
        not executar,
        mo.md("Defina `EXECUTAR = True` para gravar o plano e importar."),
    )
    escopos = odb.scopes_for(dataset, years=[int(ANO)], ufs=[UF], months=[int(MES)])
    plano, pasta = save_plan(
        target,
        dataset=dataset,
        scopes=[asdict(e) for e in escopos],
        policy="skip_same",
        max_download_bytes=MAX_DOWNLOAD_BYTES,
    )
    plano
    return escopos, pasta, plano


@app.cell
async def _(
    MAX_DOWNLOAD_BYTES,
    asyncio,
    escopos,
    executar,
    mo,
    odb,
    pasta,
    pl,
    plano,
    record_import,
):
    mo.stop(not executar, mo.md("A importação segue `EXECUTAR` na célula de parâmetros."))
    try:
        relatorio = await asyncio.to_thread(
            odb.import_research,
            plano["dataset"],
            scopes=escopos,
            target=plano["target"],
            run_id=plano["run_id"],
            max_payload_bytes=MAX_DOWNLOAD_BYTES,
            max_inflight_bytes=MAX_DOWNLOAD_BYTES,
        )
        _nao_resolvidos = ()
    except odb.ImportAbortedError as _erro:
        relatorio, _nao_resolvidos = _erro.report, _erro.unresolved
    desfechos = pl.DataFrame(record_import(pasta, relatorio, _nao_resolvidos))
    if executar and (relatorio.failed or _nao_resolvidos):
        raise RuntimeError(f"Importação incompleta; veja {pasta / 'resultado.json'}")
    desfechos
    return (relatorio,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `skipped` com *same source and parser version already published* quer dizer que
    o mesmo arquivo já estava no lake. Um arquivo que o DATASUS não publica também
    aparece como `skipped`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir

    O CNES-ST é publicado num único diretório, então `outdated` não se aplica.
    """)
    return


@app.cell
def _(dataset, escopos, mo, odb, plano, reconcile, relatorio):
    with odb.LakeReader(plano["target"]) as _leitor:
        mo.stop(
            dataset not in _leitor.tables(),
            mo.md("Nenhuma tabela publicada; veja os desfechos acima."),
        )
        desta_execucao = _leitor.publications(run_id=plano["run_id"])
        conferencia, publicacoes = reconcile(_leitor, dataset, escopos)
        mo.stop(
            not publicacoes,
            mo.md(
                "Nenhuma publicação ativa para os escopos deste plano; veja os desfechos acima."
            ),
        )
        snapshot_id = odb.latest_snapshot_id(_leitor)
    {
        "linhas_novas": relatorio.rows,
        "publications": desta_execucao,
        "lake_vs_publicado": conferencia,
        "snapshot_id": snapshot_id,
    }
    return publicacoes, snapshot_id


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5 · Analisar

    Compare `linhas` e `estabelecimentos` (códigos CNES distintos) antes de contar
    unidades. Os códigos de tipo aparecem como publicados; o perfil explica cada um.
    """)
    return


@app.cell
def _(escopos, odb, plano, snapshot_id):
    _parametros = [escopos[0].uf, escopos[0].ano, escopos[0].mes]
    consultas = {
        "estabelecimentos_por_tipo": {
            "sql": """
                SELECT trim(CAST(competen AS VARCHAR)) AS competencia,
                       trim(CAST(tp_unid AS VARCHAR)) AS tipo_de_unidade,
                       count(DISTINCT cnes) AS estabelecimentos,
                       count(*) AS linhas
                FROM lake.cnes_estabelecimentos WHERE uf = ? AND ano = ? AND mes = ?
                GROUP BY ALL ORDER BY estabelecimentos DESC
            """,
            "parameters": _parametros,
        },
        "estabelecimentos_por_municipio": {
            "sql": """
                SELECT trim(CAST(codufmun AS VARCHAR)) AS municipio,
                       count(DISTINCT cnes) AS estabelecimentos
                FROM lake.cnes_estabelecimentos WHERE uf = ? AND ano = ? AND mes = ?
                GROUP BY ALL ORDER BY estabelecimentos DESC
            """,
            "parameters": _parametros,
        },
    }
    with odb.LakeReader(plano["target"], snapshot_id=snapshot_id) as _leitor:
        resultados = {
            nome: _leitor.connect().execute(consulta["sql"], consulta["parameters"]).pl()
            for nome, consulta in consultas.items()
        }
    resultados
    return consultas, resultados


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6 · Guardar

    Resultados e `proveniencia.json` na pasta da execução. Veja
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
