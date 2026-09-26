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

"""SINAN · notificações nacionais de Chagas aguda e hanseníase, em seis etapas."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SINAN · Chagas e hanseníase")


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

    agravos = {"sinan_chagas": "Doença de Chagas aguda", "sinan_hanseniase": "Hanseníase"}
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    return (
        MAX_DOWNLOAD_BYTES,
        agravos,
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
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SINAN · Chagas aguda e hanseníase

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinan.py)

    Notificações do Sistema de Informação de Agravos de Notificação (SINAN),
    publicadas pelo DATASUS em **um arquivo nacional por ano**, com diretório final e
    preliminar. Este notebook percorre as seis etapas do
    [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com
    **Chagas aguda, 2022** (troque `AGRAVO` para `sinan_hanseniase`).

    **Abrir este notebook não baixa nem grava nada.** Ponha `EXECUTAR = True` (ou
    `-- --executar true`) para rede e escrita.

    Uma notificação não é um caso confirmado nem uma pessoa única. Leia os perfis de
    [Chagas](https://raphaelfh.github.io/omnisus/sources/sinan_chagas/) e
    [hanseníase](https://raphaelfh.github.io/omnisus/sources/sinan_hanseniase/).
    """)
    return


@app.cell
def _(agravos, resolve_target, mo, run_without_buttons):
    AGRAVO = "sinan_chagas"
    ANO = 2022
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    assert AGRAVO in agravos, f"agravo desconhecido: {AGRAVO}"
    (AGRAVO, agravos[AGRAVO], ANO, target, executar)
    return AGRAVO, ANO, executar, target


@app.cell(hide_code=True)
def _(AGRAVO, mo):
    mo.md(f"## 1 · O que `{AGRAVO}` registra")
    return


@app.cell
def _(AGRAVO, load_dicionario, pl):
    campos = pl.DataFrame(
        [{"campo": f["name"], "tipo": f["type"]} for f in load_dicionario(AGRAVO).fields]
    )
    campos
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 · Descobrir

    Lista agora os diretórios final e preliminar (`refresh=True`). Um ano preliminar
    pode ser revisado e depois movido para o final com o mesmo nome.
    """)
    return


@app.cell
async def _(AGRAVO, asyncio, executar, mo, odb, pl):
    mo.stop(
        not executar,
        mo.md(
            "Para consultar o DATASUS, defina `EXECUTAR = True` na célula de parâmetros "
            "ou rode com `-- --executar true`."
        ),
    )
    _publicados = await asyncio.to_thread(odb.available_releases, AGRAVO, refresh=True)
    publicados = pl.DataFrame(
        [
            {"ano": e.ano, "abrangencia": "nacional", "diretorio": r}
            for e, r in sorted(_publicados.items(), key=lambda item: -item[0].ano)
        ]
    )
    publicados
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 · Planejar e importar

    O arquivo é nacional: não há filtro de UF na importação. Filtre a geografia dos
    registros depois, na análise. O notebook limita cada download comprimido a 25 MiB.
    """)
    return


@app.cell
def _(AGRAVO, ANO, MAX_DOWNLOAD_BYTES, asdict, executar, mo, odb, save_plan, target):
    mo.stop(
        not executar,
        mo.md("Defina `EXECUTAR = True` para gravar o plano e importar."),
    )
    escopos = odb.scopes_for(AGRAVO, years=[int(ANO)])
    plano, pasta = save_plan(
        target,
        dataset=AGRAVO,
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
    o mesmo arquivo já estava no lake. Um `failed` pedindo `replace` quer dizer que
    o DATASUS publicou outra versão do arquivo.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 · Conferir

    `outdated` lista os anos que o DATASUS moveu entre preliminar e final desde a
    importação; atualize-os com `policy="replace"` e um novo `run_id`.
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
        desatualizados = odb.outdated(plano["dataset"], lake=_leitor)
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

    Os códigos aparecem como publicados; confira no dicionário oficial antes de
    selecionar casos confirmados ou calcular incidência.
    """)
    return


@app.cell
def _(escopos, odb, plano, snapshot_id):
    _tabela = plano["dataset"]
    _recorte = f'FROM lake."{_tabela}" WHERE _source_ano = ?'
    _parametros = [escopos[0].ano]
    consultas = {
        "diretorio_de_origem": {
            "sql": f"""
                SELECT _source_release AS diretorio, count(*) AS notificacoes {_recorte}
                GROUP BY ALL
            """,
            "parameters": _parametros,
        },
        "notificacoes_por_uf_de_notificacao": {
            "sql": f"""
                SELECT trim(CAST(sg_uf_not AS VARCHAR)) AS uf_notificacao_ibge,
                       count(*) AS notificacoes {_recorte}
                GROUP BY ALL ORDER BY notificacoes DESC
            """,
            "parameters": _parametros,
        },
        "notificacoes_por_uf_de_residencia": {
            "sql": f"""
                SELECT left(trim(CAST(id_mn_resi AS VARCHAR)), 2) AS uf_residencia_ibge,
                       count(*) AS notificacoes {_recorte}
                GROUP BY ALL ORDER BY notificacoes DESC
            """,
            "parameters": _parametros,
        },
    }
    if _tabela == "sinan_chagas":
        consultas["classificacao_e_evolucao"] = {
            "sql": f"""
                SELECT trim(CAST(classi_fin AS VARCHAR)) AS classi_fin,
                       trim(CAST(evolucao AS VARCHAR)) AS evolucao,
                       count(*) AS notificacoes {_recorte}
                GROUP BY ALL ORDER BY classi_fin, evolucao
            """,
            "parameters": _parametros,
        }
    else:
        consultas["modo_de_entrada_e_alta"] = {
            "sql": f"""
                SELECT trim(CAST(modoentr AS VARCHAR)) AS modoentr,
                       trim(CAST(tpalta_n AS VARCHAR)) AS tpalta_n,
                       count(*) AS notificacoes {_recorte}
                GROUP BY ALL ORDER BY modoentr, tpalta_n
            """,
            "parameters": _parametros,
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
