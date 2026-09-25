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

"""SIA · produção ambulatorial: escolha uma das sete tabelas e siga as seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SIA · produção ambulatorial")


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

    tabelas = {
        "sia_bpa_individualizado": "BPA individualizado",
        "sia_apac_medicamentos": "APAC · medicamentos",
        "sia_apac_quimioterapia": "APAC · quimioterapia",
        "sia_apac_tratamento_dialitico": "APAC · tratamento dialítico",
        "sia_apac_laudos_diversos": "APAC · laudos diversos",
        "sia_apac_cirurgia_bariatrica": "APAC · cirurgia bariátrica",
        "sia_psicossocial": "RAAS · atenção psicossocial",
    }
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    return (
        MAX_DOWNLOAD_BYTES,
        asdict,
        asyncio,
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
        tabelas,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SIA · produção ambulatorial

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sia.py)

    O Sistema de Informações Ambulatoriais do SUS (SIA/SUS) é publicado pelo DATASUS
    em várias tabelas, por UF e mês; a biblioteca importa sete. Escolha uma na célula
    de parâmetros e siga as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/)
    com um recorte pequeno: **Roraima, janeiro de 2024**.

    **Abrir este notebook não baixa nem grava nada.** Ponha `EXECUTAR = True` (ou
    `-- --executar true`) para rede e escrita.

    Cada tabela registra uma coisa diferente. Antes de interpretar números, leia o
    [perfil do SIA](https://raphaelfh.github.io/omnisus/sources/sia/).
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    TABELA = "sia_bpa_individualizado"
    UF = "RR"
    ANO = 2024
    MES = 1
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    (TABELA, UF, ANO, MES, target, executar)
    return ANO, MES, TABELA, UF, executar, target


@app.cell(hide_code=True)
def _(TABELA, mo):
    mo.md(f"## 1 · O que a tabela `{TABELA}` registra")
    return


@app.cell
def _(TABELA, load_dicionario, pl, tabelas):
    assert TABELA in tabelas, f"tabela desconhecida: {TABELA}"
    campos = pl.DataFrame(
        [
            {"campo": f["name"], "tipo": f["type"], "rótulo": f.get("label", "")}
            for f in load_dicionario(TABELA).fields
        ]
    )
    campos
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 · Descobrir

    Lista agora o diretório do SIA no FTP (`refresh=True`) e filtra os arquivos da
    tabela escolhida.
    """)
    return


@app.cell
async def _(TABELA, asyncio, executar, mo, odb, pl):
    mo.stop(
        not executar,
        mo.md(
            "Para consultar o DATASUS, defina `EXECUTAR = True` na célula de parâmetros "
            "ou rode com `-- --executar true`."
        ),
    )
    _publicados = await asyncio.to_thread(odb.available, TABELA, ufs=["RR"], refresh=True)
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

    Confira ano e mês na etapa 2. O plano guarda a tabela escolhida; mudar a tabela
    depois exige gravar um novo plano. O notebook limita cada download comprimido
    a 25 MiB.
    """)
    return


@app.cell
def _(
    ANO,
    MAX_DOWNLOAD_BYTES,
    MES,
    TABELA,
    UF,
    asdict,
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
    escopos = odb.scopes_for(TABELA, years=[int(ANO)], ufs=[UF], months=[int(MES)])
    plano, pasta = save_plan(
        target,
        dataset=TABELA,
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
            concurrency=1,
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
    aparece como `skipped`: nem toda tabela existe para toda UF e mês.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir

    O SIA é publicado num único diretório, então `outdated` não se aplica.
    """)
    return


@app.cell
def _(escopos, mo, odb, plano, reconcile, relatorio):
    with odb.LakeReader(plano["target"]) as _leitor:
        mo.stop(
            plano["dataset"] not in _leitor.tables(),
            mo.md("Nenhuma tabela publicada; veja os desfechos acima."),
        )
        desta_execucao = _leitor.publications(run_id=plano["run_id"])
        conferencia, publicacoes = reconcile(_leitor, plano["dataset"], escopos)
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

    Para tabelas sem consulta específica, a etapa mostra só a contagem. Use o
    dicionário da etapa 1 e o perfil.
    """)
    return


@app.cell
def _(escopos, odb, plano, snapshot_id):
    _tabela = plano["dataset"]
    _recorte = "WHERE uf = ? AND ano = ? AND mes = ?"
    _analises = {
        "sia_apac_medicamentos": {
            "apac_por_procedimento_principal": f"""
                SELECT trim(CAST(ap_pripal AS VARCHAR)) AS procedimento_principal,
                       count(*) AS apac,
                       round(sum(TRY_CAST(ap_vl_ap AS DOUBLE)), 2) AS valor_aprovado
                FROM lake.sia_apac_medicamentos {_recorte}
                GROUP BY ALL ORDER BY apac DESC
            """
        },
        "sia_bpa_individualizado": {
            "quantidade_por_procedimento": f"""
                SELECT trim(CAST(proc_id AS VARCHAR)) AS procedimento,
                       count(*) AS registros,
                       sum(TRY_CAST(qt_aprov AS BIGINT)) AS quantidade_aprovada
                FROM lake.sia_bpa_individualizado {_recorte}
                GROUP BY ALL ORDER BY quantidade_aprovada DESC NULLS LAST
            """
        },
        "sia_psicossocial": {
            "acoes_por_cid_principal": f"""
                SELECT trim(CAST(pa_proc_id AS VARCHAR)) AS acao_realizada,
                       upper(trim(CAST(cidpri AS VARCHAR))) AS cid10_principal,
                       count(*) AS registros
                FROM lake.sia_psicossocial {_recorte}
                GROUP BY ALL ORDER BY registros DESC
            """
        },
    }
    _sql_por_nome = _analises.get(
        _tabela,
        {"registros_no_recorte": f'SELECT count(*) AS registros FROM lake."{_tabela}" {_recorte}'},
    )
    _parametros = [escopos[0].uf, escopos[0].ano, escopos[0].mes]
    consultas = {
        nome: {"sql": sql, "parameters": _parametros} for nome, sql in _sql_por_nome.items()
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
    for _nome, _resultado in resultados.items():
        _resultado.write_csv(pasta / f"{_nome}.csv")
    str(pasta)
    return


if __name__ == "__main__":
    app.run()
