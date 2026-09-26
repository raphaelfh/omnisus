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

"""SINASC · nascidos vivos: do arquivo do DATASUS a uma tabela citável, em seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SINASC · nascidos vivos")


@app.cell
def _():
    import asyncio
    from dataclasses import asdict

    import marimo as mo
    import polars as pl

    import omnisus as sus
    from omnisus._notebooks import (
        reconcile,
        record_import,
        record_provenance,
        run_without_buttons,
        save_plan,
    )
    from omnisus.lake.catalog import resolve_target
    from omnisus.transforms.dictionaries import load_dicionario

    dataset = "sinasc_nascidos_vivos"
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    return (
        MAX_DOWNLOAD_BYTES,
        asdict,
        asyncio,
        dataset,
        resolve_target,
        load_dicionario,
        mo,
        sus,
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
    # SINASC · nascidos vivos

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinasc_nascidos_vivos.py)

    Base do Sistema de Informações sobre Nascidos Vivos (SINASC), publicada pelo
    DATASUS. Este notebook percorre as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com um
    recorte pequeno: **Roraima, 2022**.

    **Abrir este notebook não baixa nem grava nada.** Edite os parâmetros na célula
    seguinte e ponha `EXECUTAR = True` (ou `-- --executar true`) para rede e escrita.

    Os dados vão para o lake de pesquisa compartilhado (`data/raw/`, ou `$OMNISUS_DATA_DIR`).

    Antes de interpretar números, leia o
    [perfil do SINASC](https://raphaelfh.github.io/omnisus/sources/sinasc_nascidos_vivos/).
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    UF = "RR"
    ANO = 2022
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    (UF, ANO, target, executar)
    return ANO, UF, executar, target


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1 · O que a base registra

    Campos do dicionário que a biblioteca aplica na importação. O significado dos
    códigos está no perfil e no documento oficial citado nele.
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

    Lista agora o FTP do DATASUS (`refresh=True`). A coluna `diretorio` diz se cada
    ano está no diretório final ou no preliminar.
    """)
    return


@app.cell
async def _(asyncio, dataset, executar, mo, sus, pl):
    mo.stop(
        not executar,
        mo.md(
            "Para consultar o DATASUS, defina `EXECUTAR = True` na célula de parâmetros "
            "ou rode com `-- --executar true`."
        ),
    )
    _publicados = await asyncio.to_thread(
        sus.available_releases, dataset, ufs=["RR"], refresh=True
    )
    publicados = pl.DataFrame(
        [
            {"uf": e.uf, "ano": e.ano, "diretorio": r}
            for e, r in sorted(_publicados.items(), key=lambda item: -item[0].ano)
        ]
    )
    publicados
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 · Planejar e importar

    Confira o ano na etapa 2. Gravar o plano cria `plano.json` com um `run_id` antes
    de qualquer download. O notebook limita cada download comprimido a 25 MiB
    (`MAX_DOWNLOAD_BYTES` no próprio notebook).
    """)
    return


@app.cell
def _(
    ANO,
    MAX_DOWNLOAD_BYTES,
    UF,
    asdict,
    dataset,
    executar,
    mo,
    sus,
    save_plan,
    target,
):
    mo.stop(
        not executar,
        mo.md("Defina `EXECUTAR = True` para gravar o plano e importar."),
    )
    escopos = sus.scopes_for(dataset, years=[int(ANO)], ufs=[UF])
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
    sus,
    pasta,
    pl,
    plano,
    record_import,
):
    mo.stop(not executar, mo.md("A importação segue `EXECUTAR` na célula de parâmetros."))
    try:
        relatorio = await asyncio.to_thread(
            sus.import_research,
            plano["dataset"],
            scopes=escopos,
            target=plano["target"],
            run_id=plano["run_id"],
            concurrency=1,
            max_payload_bytes=MAX_DOWNLOAD_BYTES,
            max_inflight_bytes=MAX_DOWNLOAD_BYTES,
        )
        _nao_resolvidos = ()
    except sus.ImportAbortedError as _erro:
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
    o mesmo arquivo já estava no lake: nada foi duplicado. Um arquivo que o DATASUS
    não publica também aparece como `skipped`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir
    """)
    return


@app.cell
def _(dataset, escopos, mo, sus, plano, reconcile, relatorio):
    with sus.LakeReader(plano["target"]) as _leitor:
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
        snapshot_id = sus.latest_snapshot_id(_leitor)
        desatualizados = sus.outdated(dataset, lake=_leitor)
    {
        "linhas_novas": relatorio.rows,
        "publications": desta_execucao,
        "lake_vs_publicado": conferencia,
        "desatualizados": [str(e) for e in desatualizados],
        "snapshot_id": snapshot_id,
    }
    return publicacoes, snapshot_id


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5 · Analisar

    `com_peso_numerico` mostra quantos registros têm peso utilizável antes de
    qualquer proporção. Os códigos aparecem como publicados; o perfil explica cada um.
    """)
    return


@app.cell
def _(escopos, sus, plano, snapshot_id):
    _parametros = [escopos[0].uf, escopos[0].ano]
    consultas = {
        "nascidos_por_municipio_de_residencia": {
            "sql": """
                SELECT trim(CAST(codmunres AS VARCHAR)) AS municipio_residencia,
                       count(*) AS nascidos_vivos
                FROM lake.sinasc_nascidos_vivos WHERE uf = ? AND ano = ?
                GROUP BY ALL ORDER BY nascidos_vivos DESC
            """,
            "parameters": _parametros,
        },
        "peso_ao_nascer": {
            "sql": """
                SELECT count(*) AS nascidos_vivos,
                       count(TRY_CAST(peso AS INTEGER)) AS com_peso_numerico,
                       count(*) FILTER (WHERE TRY_CAST(peso AS INTEGER) < 2500)
                           AS peso_abaixo_de_2500_g
                FROM lake.sinasc_nascidos_vivos WHERE uf = ? AND ano = ?
            """,
            "parameters": _parametros,
        },
        "consultas_pre_natal": {
            "sql": """
                SELECT trim(CAST(consultas AS VARCHAR)) AS consultas_codigo,
                       count(*) AS nascidos_vivos
                FROM lake.sinasc_nascidos_vivos WHERE uf = ? AND ano = ?
                GROUP BY ALL ORDER BY consultas_codigo
            """,
            "parameters": _parametros,
        },
        "tipo_de_parto": {
            "sql": """
                SELECT trim(CAST(parto AS VARCHAR)) AS parto_codigo, count(*) AS nascidos_vivos
                FROM lake.sinasc_nascidos_vivos WHERE uf = ? AND ano = ?
                GROUP BY ALL ORDER BY parto_codigo
            """,
            "parameters": _parametros,
        },
    }
    with sus.LakeReader(plano["target"], snapshot_id=snapshot_id) as _leitor:
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
