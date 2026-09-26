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

"""SIM · óbitos: do arquivo do DATASUS a uma tabela citável, em seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SIM · óbitos")


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

    dataset = "sim_obitos"
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
    # SIM · óbitos

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sim_obitos.py)

    Base de óbitos do Sistema de Informações sobre Mortalidade (SIM), publicada
    pelo DATASUS. Este notebook percorre as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com um
    recorte pequeno: **Roraima, 2022**.

    **Abrir este notebook não baixa nem grava nada.** Edite os parâmetros na célula
    seguinte e ponha `EXECUTAR = True` (ou exporte com `-- --executar true`) para
    consultar a rede e gravar no lake.

    Os dados vão para o lake de pesquisa compartilhado (`data/raw/`, ou `$OMNISUS_DATA_DIR`), o
    mesmo dos outros notebooks de `bases/`.

    Antes de interpretar números, leia o
    [perfil do SIM](https://raphaelfh.github.io/omnisus/sources/sim_obitos/):
    o que um registro representa, datas, geografia e armadilhas, com as fontes.
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    # Parâmetros: edite e reexecute, como num Jupyter.
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

    Lista agora o FTP do DATASUS (`refresh=True`). O SIM tem um diretório final e um
    preliminar; a coluna `diretorio` diz onde cada ano está.
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
    de qualquer download: é o `run_id` que permite reconciliar uma importação
    interrompida. O notebook limita cada download comprimido a 25 MiB
    (`MAX_DOWNLOAD_BYTES` no próprio notebook); um arquivo maior (por exemplo outra
    UF) termina como `failed`, e pode ser importado subindo esse limite ou com a
    chamada direta `sus.import_dataset` no perfil desta base ("Como usar").
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

    Publicações desta execução, contagem no lake contra o manifesto e escopos que o
    DATASUS moveu de diretório desde a importação (`outdated`).
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
        # refresh=False usa a listagem em cache do FTP, preenchida pela etapa 2 ou
        # pela própria importação: não faz um novo crawl do servidor público.
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

    Consultas sobre o snapshot fixo: com o mesmo número, a consulta devolve as
    mesmas linhas mesmo depois de novas importações. Os códigos aparecem como
    publicados; o perfil explica cada um, e a diferença entre residência e ocorrência.
    """)
    return


@app.cell
def _(escopos, sus, plano, snapshot_id):
    _parametros = [escopos[0].uf, escopos[0].ano]
    consultas = {
        "obitos_por_mes": {
            "sql": """
                WITH obitos AS (
                    SELECT COALESCE(
                        TRY_CAST(dtobito AS DATE),
                        TRY_STRPTIME(trim(CAST(dtobito AS VARCHAR)), '%d%m%Y')::DATE
                    ) AS data_obito
                    FROM lake.sim_obitos WHERE uf = ? AND ano = ?
                )
                SELECT coalesce(strftime(data_obito, '%Y-%m'), 'sem data válida') AS mes,
                       count(*) AS obitos
                FROM obitos GROUP BY ALL ORDER BY mes
            """,
            "parameters": _parametros,
        },
        "obitos_por_sexo_e_causa": {
            "sql": """
                SELECT trim(CAST(sexo AS VARCHAR)) AS sexo_codigo,
                       left(upper(trim(CAST(causabas AS VARCHAR))), 3) AS causa_basica_cid10_3,
                       count(*) AS obitos
                FROM lake.sim_obitos WHERE uf = ? AND ano = ?
                GROUP BY ALL ORDER BY obitos DESC
            """,
            "parameters": _parametros,
        },
        "residencia_e_ocorrencia": {
            "sql": """
                SELECT left(trim(CAST(codmunres AS VARCHAR)), 2) AS uf_residencia_ibge,
                       left(trim(CAST(codmunocor AS VARCHAR)), 2) AS uf_ocorrencia_ibge,
                       count(*) AS obitos
                FROM lake.sim_obitos WHERE uf = ? AND ano = ?
                GROUP BY ALL ORDER BY obitos DESC
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

    Resultados e `proveniencia.json` na pasta da execução. Para citar: arquivo e
    SHA-256 de cada publicação, `snapshot_id`, versão do omnisus e data de
    acesso — veja
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
