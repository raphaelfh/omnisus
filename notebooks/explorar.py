# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25.0,<0.26",
#     "omnisus==0.2.3",
#     "polars>=1.44.2,<2.0",
#     "sqlglot>=30.18.0",
# ]
# ///

"""Explorar o lake: escolher bases e recortes com widgets, ver as linhas e citar."""

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="full", app_title="Explorar o lake")


@app.cell
def _():
    import json
    import os
    from pathlib import Path

    import marimo as mo
    import polars as pl

    import omnisus as sus

    return Path, json, mo, os, pl, sus


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Explorar o lake

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/explorar.py)

    Escolha nos widgets as bases e os recortes que o lake já tem e veja as linhas numa
    tabela com busca, filtro e ordenação, o perfil de uma coluna e a citação do que
    você escolheu. Os códigos ficam como o DATASUS publicou; o rótulo vem do
    dicionário, ao lado (`sexo_rotulo`).

    **Onde está o lake.** Indique a pasta que tem `omnisus-catalog.sqlite` e
    `omnisus.ducklake/`:

    - neste computador, a pasta onde `sus.load` grava (`data/raw/`, ou
      `$OMNISUS_DATA_DIR`), relativa à pasta em que você abriu o marimo;
    - no Google Drive, a pasta do lake sincronizada no computador ou, no molab, a
      pasta copiada do Drive para o disco do notebook.

    O catálogo guarda a pasta em que o lake foi criado (no Colab,
    `/content/drive/MyDrive/omnisus`); este notebook lê os dados da pasta indicada,
    onde quer que ela esteja agora. Importe só num lake que está na pasta onde foi
    criado.

    **Abrir este notebook não baixa nem grava nada.** A seção *Importar* consulta o
    DATASUS só quando você clica no botão.
    """)
    return


@app.cell
def _(mo, os):
    pasta = mo.ui.text(
        value=mo.cli_args().get("lake") or os.environ.get("OMNISUS_DATA_DIR") or "data/raw",
        label="Pasta do lake",
        full_width=True,
    )
    executar = bool(mo.cli_args().get("executar"))
    pasta
    return executar, pasta


@app.cell
def _(Path, pasta):
    diretorio = Path(pasta.value).expanduser().resolve()
    alvo = f"ducklake:{diretorio / 'omnisus.ducklake'}"
    return alvo, diretorio


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Importar

    Para pôr um recorte no lake: escolha a base, o ano e, conforme a base, as UFs e os
    meses. `sus.import_dataset` baixa só o que o lake ainda não tem do mesmo arquivo.
    """)
    return


@app.cell
def _(mo):
    # Uma importação muda a versão, e só ela reabre o lake: mexer nos widgets de
    # importação não refaz as consultas abaixo.
    versao, mudar_versao = mo.state(0)
    return mudar_versao, versao


@app.cell
def _(mo, sus):
    base_nova = mo.ui.dropdown(
        options=sorted(d.name for d in sus.datasets()),
        value="sim_obitos",
        label="Base",
        searchable=True,
    )
    return (base_nova,)


@app.cell
def _(base_nova, mo, sus):
    _base = sus.resolve(base_nova.value)
    por_uf = _base.geography == "state"
    mensal = _base.cadence == "monthly"
    ano_novo = mo.ui.number(start=_base.coverage[0][0], stop=2100, value=2022, label="Ano")
    ufs_novas = mo.ui.multiselect(options=sus.ALL_UFS, value=["RR"], label="UFs")
    meses_novos = mo.ui.multiselect(options=list(range(1, 13)), value=[1], label="Meses")
    importar = mo.ui.run_button(label="Importar")
    mo.hstack(
        [
            base_nova,
            ano_novo,
            *([ufs_novas] if por_uf else []),
            *([meses_novos] if mensal else []),
            importar,
        ],
        justify="start",
    )
    return ano_novo, importar, mensal, meses_novos, por_uf, ufs_novas


@app.cell
def _(
    alvo,
    ano_novo,
    base_nova,
    executar,
    importar,
    mensal,
    meses_novos,
    mo,
    mudar_versao,
    por_uf,
    sus,
    ufs_novas,
):
    if importar.value or executar:
        _escopos = sus.scopes_for(
            base_nova.value,
            years=[ano_novo.value],
            ufs=ufs_novas.value if por_uf else None,
            months=meses_novos.value if mensal else None,
        )
        with mo.status.spinner(title=f"Importando {base_nova.value}…"):
            _relatorio = sus.import_dataset(
                base_nova.value, scopes=_escopos, target=alvo, policy="skip_same"
            )
        mudar_versao(lambda v: v + 1)
        mo.output.replace(
            mo.md(
                f"Importados: {len(_relatorio.ok)}. Já no lake: {len(_relatorio.skipped)}. "
                f"Falharam: {[str(o.scope) for o in _relatorio.failed] or 'nenhum'}."
            )
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## O que o lake tem

    Um recorte por linha, lido do catálogo, sem rede: a base, o escopo, o diretório
    do servidor (`final` ou `prelim`), quantas linhas foram gravadas e quando.
    """)
    return


@app.cell
def _(alvo, diretorio, mo, sus, versao):
    versao()
    try:
        leitor = sus.LakeReader(alvo)
    except sus.CatalogAttachError:
        leitor = None
    mo.stop(
        leitor is None,
        mo.md(f"Não há lake em `{diretorio}`. Indique outra pasta ou importe uma base acima."),
    )
    snapshot = sus.latest_snapshot_id(leitor)

    def _texto(valor):
        return "'" + str(valor).replace("'", "''") + "'"

    # O catálogo guarda a pasta onde o lake foi criado. Reabrir com OVERRIDE_DATA_PATH lê os
    # Parquet desta pasta, fixa o snapshot e deixa abrir uma cópia vinda do Google Drive.
    _catalogo = diretorio / "omnisus-catalog.sqlite"
    con = leitor.connect()
    con.execute("DETACH lake")
    con.execute(
        f"ATTACH {_texto(f'ducklake:sqlite:{_catalogo}')} AS lake "
        f"(READ_ONLY, DATA_PATH {_texto(diretorio / 'omnisus.ducklake')}, "
        f"OVERRIDE_DATA_PATH true, SNAPSHOT_VERSION {snapshot})"
    )
    return con, leitor, snapshot


@app.cell
def _(leitor, mo, pl):
    publicacoes = [p for p in leitor.publications() if p["active"] and p["scope"] is not None]
    mo.stop(not publicacoes, mo.md("O lake ainda não tem nenhuma base importada."))
    recortes = pl.DataFrame(
        [
            {
                "base": p["dataset"],
                "uf": p["scope"].uf,
                "ano": p["scope"].ano,
                "mes": p["scope"].mes,
                "diretorio": p["release"],
                "linhas": p["rows"],
                "importado_em": p["published_at"],
            }
            for p in publicacoes
        ],
        schema_overrides={"uf": pl.String, "mes": pl.Int64},
    ).sort("base", "ano", "mes", "uf", nulls_last=True)
    recortes
    return publicacoes, recortes


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Escolher

    As opções vêm do que o lake tem. Uma base nacional (SINAN, subconjuntos do SIM)
    não tem UF; uma base anual não tem mês.
    """)
    return


@app.cell
def _(mo, recortes):
    _nomes = recortes["base"].unique().sort().to_list()
    bases = mo.ui.multiselect(options=_nomes, value=_nomes[:1], label="Bases")
    bases
    return (bases,)


@app.cell
def _(bases, con, mo, pl, recortes):
    mo.stop(not bases.value, mo.md("Escolha ao menos uma base."))
    _das_bases = recortes.filter(pl.col("base").is_in(bases.value))

    def _filtro(coluna, rotulo):
        opcoes = _das_bases[coluna].drop_nulls().unique().sort().to_list()
        return mo.ui.multiselect(options=opcoes, value=opcoes, label=rotulo)

    ufs, anos, meses = _filtro("uf", "UFs"), _filtro("ano", "Anos"), _filtro("mes", "Meses")
    esquemas = {
        _base: {
            nome: tipo for nome, tipo, *_ in con.execute(f'DESCRIBE lake."{_base}"').fetchall()
        }
        for _base in bases.value
    }
    colunas = mo.ui.dictionary(
        {
            _base: mo.ui.multiselect(options=list(e), value=list(e), label=_base)
            for _base, e in esquemas.items()
        }
    )
    mo.vstack([mo.hstack([ufs, anos, meses], justify="start"), colunas])
    return anos, colunas, esquemas, meses, ufs


@app.cell
def _(anos, esquemas, meses, publicacoes, ufs):
    def _escolhido(e):
        return (
            (e.uf is None or e.uf in ufs.value)
            and e.ano in anos.value
            and (e.mes is None or e.mes in meses.value)
        )

    escolhidas = {
        _base: [p for p in publicacoes if p["dataset"] == _base and _escolhido(p["scope"])]
        for _base in esquemas
    }
    return (escolhidas,)


@app.cell
def _(escolhidas, esquemas, json, sus):
    def _onde(publicacoes):
        """`WHERE` e parâmetros que selecionam os recortes destas publicações.

        Cada publicação guarda em `scope_json` as colunas e os valores que gravou
        (`uf`, `ano`, `mes`; `_source_ano` numa base nacional).
        """
        escopos = [json.loads(p["scope_json"]) for p in publicacoes]
        if not escopos:
            return "false", []
        chaves = list(escopos[0])
        colunas = ", ".join(f'"{c}"' for c in chaves)
        listas = ", ".join("unnest(?)" for _ in chaves)
        return f"({colunas}) IN (SELECT {listas})", [[e[c] for e in escopos] for c in chaves]

    filtros = {_base: _onde(_pubs) for _base, _pubs in escolhidas.items()}
    projecoes = {
        _base: sus.analytical_projection(
            _base,
            observed_schema=esquemas[_base],
            scopes=[sus.SourceContext.from_publication(p) for p in _pubs],
        )
        for _base, _pubs in escolhidas.items()
    }
    totais = {_base: sum(p["rows"] for p in _pubs) for _base, _pubs in escolhidas.items()}
    return filtros, projecoes, totais


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Linhas

    Uma aba por base. A contagem é de todos os recortes escolhidos; a tabela mostra até
    *Linhas na tabela* delas, porque a tabela do marimo guarda na memória tudo o que
    recebe. Para mais linhas, filtre os recortes ou tire colunas. As categorias
    harmonizadas (`idade_anos_completos`, `sexo_categoria`...) só aparecem quando todos
    os recortes vêm de fontes validadas (ADR 0003); a aba diz o motivo quando faltam.
    """)
    return


@app.cell
def _(mo):
    linhas = mo.ui.number(
        start=100,
        stop=1_000_000,
        step=100,
        value=int(mo.cli_args().get("linhas") or 10_000),
        label="Linhas na tabela",
    )
    rotulos = mo.ui.switch(value=True, label="Rótulos do dicionário")
    mo.hstack([linhas, rotulos], justify="start")
    return linhas, rotulos


@app.cell
def _(colunas, con, filtros, linhas, projecoes):
    brutas = {}
    for _base, (_onde, _parametros) in filtros.items():
        _selecao = ", ".join(f'"{c}"' for c in colunas.value[_base]) or "NULL AS sem_colunas"
        _categorias = "".join(f', {c.expression} AS "{c.name}"' for c in projecoes[_base].columns)
        brutas[_base] = con.execute(
            f'SELECT {_selecao}{_categorias} FROM lake."{_base}" '
            f"WHERE {_onde} LIMIT {int(linhas.value)}",
            _parametros,
        ).pl()
    return (brutas,)


@app.cell
def _(brutas, mo, projecoes, rotulos, sus, totais):
    amostras = {
        _base: sus.label(_base, _bruta) if rotulos.value else _bruta
        for _base, _bruta in brutas.items()
    }

    def _resumo(base):
        fora = [
            f"`{u.field}` ({u.reason})"
            for u in projecoes[base].unavailable
            if u.reason != "unsupported_dataset"
        ]
        return f"**{totais[base]:,}** linhas; a tabela mostra {amostras[base].height:,}." + (
            f" Categorias harmonizadas fora: {', '.join(fora)}." if fora else ""
        )

    mo.ui.tabs(
        {
            _base: mo.vstack([mo.md(_resumo(_base)), mo.ui.table(_amostra, page_size=20)])
            for _base, _amostra in amostras.items()
        }
    )
    return (amostras,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Perfil de uma coluna

    Quantas linhas tem cada código, em todos os recortes escolhidos (não só nas da
    tabela acima), com o rótulo do dicionário. Começa no primeiro campo que o
    dicionário rotula.
    """)
    return


@app.cell
def _(esquemas, mo):
    base_perfil = mo.ui.dropdown(options=list(esquemas), value=next(iter(esquemas)), label="Base")
    return (base_perfil,)


@app.cell
def _(base_perfil, esquemas, mo, sus):
    _colunas = list(esquemas[base_perfil.value])
    _rotuladas = [
        f["name"]
        for f in sus.describe_dataset(base_perfil.value)["schema"]["fields"]
        if f.get("x-decode") and f["name"] in _colunas
    ]
    coluna_perfil = mo.ui.dropdown(
        options=_colunas, value=(_rotuladas or _colunas)[0], label="Coluna", searchable=True
    )
    mo.hstack([base_perfil, coluna_perfil], justify="start")
    return (coluna_perfil,)


@app.cell
def _(base_perfil, coluna_perfil, con, filtros, pl, sus):
    _onde, _parametros = filtros[base_perfil.value]
    perfil = sus.label(
        base_perfil.value,
        con.execute(
            f'SELECT "{coluna_perfil.value}", count(*) AS registros '
            f'FROM lake."{base_perfil.value}" WHERE {_onde} '
            "GROUP BY ALL ORDER BY registros DESC LIMIT 1000",
            _parametros,
        )
        .pl()
        .with_columns(pct=(100 * pl.col("registros") / pl.col("registros").sum()).round(2)),
    )
    perfil
    return (perfil,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Consultar em SQL

    Para ir além das linhas da tabela, consulte o lake inteiro: as tabelas estão em
    `lake.<base>`. A consulta abaixo começa na base do perfil.
    """)
    return


@app.cell
def _(base_perfil, con, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM lake.{base_perfil.value} LIMIT 100
        """,
        engine=con,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Citar

    A citação nomeia o arquivo do servidor, o SHA-256 e o snapshot do lake de cada
    recorte escolhido. Guarde-a junto com o resultado.
    """)
    return


@app.cell
def _(escolhidas, mo, snapshot, sus):
    citacoes = {
        _base: sus.citation_from_publications(_pubs, snapshot_id=snapshot, dataset=_base).text
        for _base, _pubs in escolhidas.items()
    }
    _texto = "\n\n".join(citacoes.values())
    mo.vstack(
        [
            mo.md("\n\n".join(f"```text\n{t}\n```" for t in citacoes.values())),
            mo.download(_texto.encode(), filename="citacao.txt", label="Baixar citação"),
        ]
    )
    return (citacoes,)


if __name__ == "__main__":
    app.run()
