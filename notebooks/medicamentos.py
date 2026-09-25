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

"""Medicamentos: APAC do SIA no lake, uma página de estoque do Hórus e o que não existe."""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Medicamentos · APAC e estoque")


@app.cell
def _():
    import asyncio
    from dataclasses import asdict
    from uuid import uuid4

    import marimo as mo
    import polars as pl

    import omnisus as odb
    from omnisus._notebooks import (
        reconcile,
        record_import,
        record_provenance,
        run_without_buttons,
        save_plan,
        write_json,
    )
    from omnisus.lake.catalog import data_dir, resolve_target
    from omnisus.sources.medicamentos import fetch_stock_page
    from omnisus.transforms.dictionaries import load_dicionario

    dataset = "sia_apac_medicamentos"
    MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
    return (
        MAX_DOWNLOAD_BYTES,
        asdict,
        asyncio,
        data_dir,
        dataset,
        resolve_target,
        fetch_stock_page,
        load_dicionario,
        mo,
        odb,
        pl,
        reconcile,
        record_import,
        record_provenance,
        run_without_buttons,
        save_plan,
        uuid4,
        write_json,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Medicamentos: o que dá para estudar com dados abertos

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/medicamentos.py)

    Três partes:

    - **A · APAC de medicamentos (SIA-AM)** — as seis etapas do
      [guia do pesquisador](https://raphaelfh.github.io/omnisus/pesquisa/) com
      **Roraima, janeiro de 2024**, no lake de pesquisa compartilhado.
    - **B · Estoque BNAFAR/Hórus** — uma página da API pública de posição de estoque,
      guardada com proveniência, sem publicar no lake.
    - **C · O que não existe publicamente** — eventos de dispensação.

    **Abrir este notebook não baixa nem grava nada.** Ponha `EXECUTAR = True` (ou
    `-- --executar true`) para rede e escrita. Leia o
    [perfil de medicamentos](https://raphaelfh.github.io/omnisus/sources/medicamentos/)
    antes de interpretar números: um registro de APAC não é uma dose nem uma dispensação.
    """)
    return


@app.cell
def _(resolve_target, mo, run_without_buttons):
    UF = "RR"
    ANO = 2024
    MES = 1
    CODIGO_UF = "14"
    DATA_ESTOQUE = ""
    EXECUTAR = False
    target = resolve_target(None)
    executar = EXECUTAR or run_without_buttons(mo.cli_args())
    (UF, ANO, MES, CODIGO_UF, DATA_ESTOQUE, target, executar)
    return ANO, CODIGO_UF, DATA_ESTOQUE, MES, UF, executar, target


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A1 · O que a APAC de medicamentos registra
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
    ## A2 · Descobrir
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
    ## A3 · Planejar e importar

    Gravar o plano cria `plano.json` com um `run_id` antes de qualquer download.
    O notebook limita cada download comprimido a 25 MiB.
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
    aparece como `skipped`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A4 · Conferir

    O SIA é publicado num único diretório, então `outdated` não se aplica.
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
    ## A5 · Analisar

    Registros de APAC por procedimento principal e valor aprovado. Não são doses nem
    pacientes únicos.
    """)
    return


@app.cell
def _(escopos, odb, plano, snapshot_id):
    _parametros = [escopos[0].uf, escopos[0].ano, escopos[0].mes]
    consultas = {
        "apac_por_procedimento_principal": {
            "sql": """
                SELECT trim(CAST(ap_pripal AS VARCHAR)) AS procedimento_principal,
                       count(*) AS apac,
                       round(sum(TRY_CAST(ap_vl_ap AS DOUBLE)), 2) AS valor_aprovado
                FROM lake.sia_apac_medicamentos WHERE uf = ? AND ano = ? AND mes = ?
                GROUP BY ALL ORDER BY apac DESC
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
    ## A6 · Guardar
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## B · Estoque BNAFAR/Hórus

    Uma página da API pública de **posição de estoque**. Não publica no lake. Uma
    página vazia não demonstra ausência de estoque, e uma página curta não demonstra
    completude. Filtros: `CODIGO_UF` e `DATA_ESTOQUE` (AAAA-MM-DD, opcional).
    """)
    return


@app.cell
async def _(
    CODIGO_UF,
    DATA_ESTOQUE,
    asyncio,
    data_dir,
    executar,
    fetch_stock_page,
    mo,
    pl,
    uuid4,
    write_json,
):
    mo.stop(
        not executar,
        mo.md("Defina `EXECUTAR = True` para consultar o estoque."),
    )
    _filtros = {"codigo_uf": CODIGO_UF.strip()}
    if DATA_ESTOQUE.strip():
        _filtros["data_posicao_estoque"] = DATA_ESTOQUE.strip()
    pagina = await asyncio.to_thread(fetch_stock_page, filters=_filtros, limit=20)
    pasta_estoque = data_dir() / "estoque" / uuid4().hex
    pasta_estoque.mkdir(parents=True)
    (pasta_estoque / "resposta.json").write_bytes(pagina.raw)
    write_json(pasta_estoque / "proveniencia.json", pagina.provenance())
    {
        "pasta": str(pasta_estoque),
        "sha256": pagina.sha256,
        "registros": pl.DataFrame(pagina.records),
    }
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## C · O que não existe publicamente

    A investigação de 2026-09-12
    ([relatório](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-12-sinan-e-dispensacao.md),
    Parte 2) não encontrou **nenhuma fonte pública de eventos de dispensação**: a
    dispensação enviada à BNAFAR e à RNDS tem envio ou acesso autenticado. Estoque,
    entrega a DSEI e indicadores agregados não substituem dispensação. Para pesquisar
    dispensação, o caminho é uma extração fornecida pelo gestor.
    """)
    return


if __name__ == "__main__":
    app.run()
