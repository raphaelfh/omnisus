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
    from pathlib import Path

    import marimo as mo
    import polars as pl

    import omnisus as sus

    return Path, mo, pl, sus


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

    - neste computador, `data/raw` (onde `sus.load` grava por padrão), relativo à
      pasta em que você abriu o marimo;
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
def _(mo):
    _argumentos = mo.cli_args()
    pasta = mo.ui.text(
        value=_argumentos.get("lake") or "data/raw", label="Pasta do lake", full_width=True
    )
    linhas = mo.ui.number(
        start=100,
        stop=1_000_000,
        step=100,
        value=int(_argumentos.get("linhas") or 10_000),
        label="Linhas na tabela",
    )
    executar = bool(_argumentos.get("executar"))
    pasta
    return executar, linhas, pasta


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
def _(mo, sus):
    catalogo = sus.describe_datasets()
    base_nova = mo.ui.dropdown(
        options=catalogo["name"].to_list(), value="sim_obitos", label="Base", searchable=True
    )
    return base_nova, catalogo


@app.cell
def _(base_nova, catalogo, mo, sus):
    descricao = catalogo.filter(name=base_nova.value).row(0, named=True)
    ano_novo = mo.ui.number(
        start=int(descricao["coverage_start"][:4]), stop=2100, value=2022, label="Ano"
    )
    ufs_novas = mo.ui.multiselect(options=sus.ALL_UFS, value=["RR"], label="UFs")
    meses_novos = mo.ui.multiselect(
        options=[str(m) for m in range(1, 13)], value=["1"], label="Meses"
    )
    importar = mo.ui.run_button(label="Importar")
    mo.hstack(
        [
            base_nova,
            ano_novo,
            *([ufs_novas] if descricao["geography"] == "state" else []),
            *([meses_novos] if descricao["cadence"] == "monthly" else []),
            importar,
        ],
        justify="start",
    )
    return ano_novo, descricao, importar, meses_novos, ufs_novas


@app.cell
def _(
    alvo,
    ano_novo,
    base_nova,
    descricao,
    executar,
    importar,
    meses_novos,
    mo,
    sus,
    ufs_novas,
):
    importados = None
    if importar.value or executar:
        _escopos = sus.scopes_for(
            base_nova.value,
            years=[ano_novo.value],
            ufs=ufs_novas.value if descricao["geography"] == "state" else None,
            months=[int(m) for m in meses_novos.value]
            if descricao["cadence"] == "monthly"
            else None,
        )
        with mo.status.spinner(title=f"Importando {base_nova.value}…"):
            _relatorio = sus.import_dataset(
                base_nova.value, scopes=_escopos, target=alvo, policy="skip_same"
            )
        importados = len(_relatorio.ok)
        mo.output.replace(
            mo.md(
                f"Importados: {importados}. Já no lake: {len(_relatorio.skipped)}. "
                f"Falharam: {[str(o.scope) for o in _relatorio.failed] or 'nenhum'}."
            )
        )
    return (importados,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## O que o lake tem

    Um recorte por linha, lido do catálogo, sem rede: a base, o escopo, o diretório
    do servidor (`final` ou `prelim`), quantas linhas foram gravadas e quando.
    """)
    return


@app.cell
def _(alvo, diretorio, importados, mo, sus):
    importados  # depois de uma importação, o lake é reaberto
    try:
        leitor = sus.LakeReader(alvo)
    except sus.CatalogAttachError:
        leitor = None
    mo.stop(
        leitor is None,
        mo.md(f"Não há lake em `{diretorio}`. Indique outra pasta ou importe uma base acima."),
    )
    snapshot = sus.latest_snapshot_id(leitor)

    def _texto(caminho):
        return "'" + str(caminho).replace("'", "''") + "'"

    # O catálogo guarda a pasta onde o lake foi criado. Reabrir com OVERRIDE_DATA_PATH lê os
    # Parquet desta pasta, fixa o snapshot e deixa abrir uma cópia vinda do Google Drive.
    _con = leitor.connect()
    _con.execute(f"DETACH {leitor.alias}")
    _con.execute(
        f"ATTACH {_texto('ducklake:sqlite:' + str(diretorio / 'omnisus-catalog.sqlite'))} "
        f"AS {leitor.alias} (READ_ONLY, DATA_PATH {_texto(diretorio / 'omnisus.ducklake')}, "
        f"OVERRIDE_DATA_PATH true, SNAPSHOT_VERSION {snapshot})"
    )
    return leitor, snapshot


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
    return (bases,)


@app.cell
def _(bases, leitor, linhas, mo, pl, recortes):
    _das_bases = recortes.filter(pl.col("base").is_in(bases.value))

    def _opcoes(coluna):
        return [str(v) for v in _das_bases[coluna].drop_nulls().unique().sort()]

    ufs = mo.ui.multiselect(options=_opcoes("uf"), value=_opcoes("uf"), label="UFs")
    anos = mo.ui.multiselect(options=_opcoes("ano"), value=_opcoes("ano"), label="Anos")
    meses = mo.ui.multiselect(options=_opcoes("mes"), value=_opcoes("mes"), label="Meses")
    _colunas = {
        _base: [
            nome
            for nome, *_ in leitor.connect()
            .execute(f'DESCRIBE {leitor.alias}."{_base}"')
            .fetchall()
        ]
        for _base in bases.value
    }
    colunas = mo.ui.dictionary(
        {
            _base: mo.ui.multiselect(options=c, value=c, label=_base)
            for _base, c in _colunas.items()
        }
    )
    rotulos = mo.ui.switch(value=True, label="Rótulos do dicionário")
    mo.vstack(
        [
            mo.hstack([bases, ufs, anos, meses], justify="start"),
            colunas,
            mo.hstack([linhas, rotulos]),
        ]
    )
    return anos, colunas, meses, rotulos, ufs


@app.cell
def _(anos, bases, meses, publicacoes, ufs):
    def _escolhida(p):
        escopo = p["scope"]
        return (
            p["dataset"] in bases.value
            and (escopo.uf is None or escopo.uf in ufs.value)
            and str(escopo.ano) in anos.value
            and (escopo.mes is None or str(escopo.mes) in meses.value)
        )

    escolhidas = [p for p in publicacoes if _escolhida(p)]
    return (escolhidas,)


@app.cell
def _(escolhidas, leitor, sus):
    def recorte_sql(base):
        """`FROM ... WHERE ...` e parâmetros que selecionam os recortes escolhidos da base.

        Uma base por UF grava `uf`, `ano` e `mes`; uma nacional, `_source_ano` e
        `_source_mes`. O mês fica de fora numa base anual.
        """
        condicoes, parametros = [], []
        for p in escolhidas:
            if p["dataset"] != base:
                continue
            e = p["scope"]
            campos = {"uf": e.uf, "ano": e.ano, "mes": e.mes}
            if e.uf is None:
                campos = {"_source_ano": e.ano, "_source_mes": e.mes}
            campos = {k: v for k, v in campos.items() if v is not None or k == "uf"}
            condicoes.append(" AND ".join(f'"{k}" = ?' for k in campos))
            parametros += campos.values()
        onde = " OR ".join(f"({c})" for c in condicoes) or "false"
        return f'FROM {leitor.alias}."{base}" WHERE {onde}', parametros

    def categorias_sql(base):
        """As categorias harmonizadas que as fontes escolhidas permitem (ADR 0003)."""
        _con = leitor.connect()
        esquema = dict(
            (nome, tipo)
            for nome, tipo, *_ in _con.execute(f'DESCRIBE {leitor.alias}."{base}"').fetchall()
        )
        fontes = [
            sus.SourceContext.from_publication(p) for p in escolhidas if p["dataset"] == base
        ]
        projecao = sus.analytical_projection(base, observed_schema=esquema, scopes=fontes)
        return "".join(f', {c.expression} AS "{c.name}"' for c in projecao.columns)

    return categorias_sql, recorte_sql


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Linhas

    Uma aba por base. A contagem é de todos os recortes escolhidos; a tabela mostra até
    *Linhas na tabela* delas, porque a tabela do marimo guarda na memória tudo o que
    recebe. Para mais linhas, filtre os recortes ou tire colunas.
    """)
    return


@app.cell
def _(
    bases,
    catalogo,
    categorias_sql,
    colunas,
    leitor,
    linhas,
    mo,
    recorte_sql,
    rotulos,
    sus,
):
    _con = leitor.connect()
    _rotulaveis = set(catalogo.filter(catalogo["labelled_fields"] > 0)["name"])
    totais, amostras = {}, {}
    for _base in bases.value:
        _de, _parametros = recorte_sql(_base)
        totais[_base] = _con.execute(f"SELECT count(*) {_de}", _parametros).fetchone()[0]
        _selecao = ", ".join(f'"{c}"' for c in colunas.value[_base]) or "NULL AS sem_colunas"
        _amostra = _con.execute(
            f"SELECT {_selecao}{categorias_sql(_base)} {_de} LIMIT {int(linhas.value)}",
            _parametros,
        ).pl()
        if rotulos.value and _base in _rotulaveis:
            _amostra = sus.label(_base, _amostra)
        amostras[_base] = _amostra
    mo.ui.tabs(
        {
            _base: mo.vstack(
                [
                    mo.md(f"**{totais[_base]:,}** linhas; a tabela mostra {_amostra.height:,}."),
                    mo.ui.table(_amostra, page_size=20),
                ]
            )
            for _base, _amostra in amostras.items()
        }
    )
    return amostras, totais


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
def _(bases, mo):
    base_perfil = mo.ui.dropdown(options=bases.value, value=bases.value[0], label="Base")
    return (base_perfil,)


@app.cell
def _(amostras, base_perfil, mo, sus):
    rotulados = [
        f["name"]
        for f in sus.describe_dataset(base_perfil.value)["schema"]["fields"]
        if f.get("x-decode") and f["name"] in amostras[base_perfil.value].columns
    ]
    coluna_perfil = mo.ui.dropdown(
        options=amostras[base_perfil.value].columns,
        value=(rotulados or amostras[base_perfil.value].columns)[0],
        label="Coluna",
        searchable=True,
    )
    mo.hstack([base_perfil, coluna_perfil], justify="start")
    return coluna_perfil, rotulados


@app.cell
def _(base_perfil, coluna_perfil, leitor, pl, recorte_sql, rotulados, sus):
    _de, _parametros = recorte_sql(base_perfil.value)
    _coluna = coluna_perfil.value
    perfil = (
        leitor.connect()
        .execute(
            f'SELECT "{_coluna}", count(*) AS registros {_de} '
            "GROUP BY ALL ORDER BY registros DESC LIMIT 1000",
            _parametros,
        )
        .pl()
        .with_columns(pct=(100 * pl.col("registros") / pl.col("registros").sum()).round(2))
    )
    if _coluna in rotulados:
        perfil = sus.label(base_perfil.value, perfil, columns=[_coluna])
    perfil
    return (perfil,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Transformar e consultar

    Filtre, agrupe e some as linhas da tabela da primeira base com o editor abaixo; ele
    mostra o código polars de cada passo. Para consultar o lake inteiro, use SQL: as
    tabelas estão em `lake.<base>`.
    """)
    return


@app.cell
def _(amostras, bases, mo):
    mo.ui.dataframe(amostras[bases.value[0]], page_size=20)
    return


@app.cell
def _(bases, leitor, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM lake.{bases.value[0]} LIMIT 100
        """,
        engine=leitor.connect(),
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
def _(bases, escolhidas, mo, snapshot, sus):
    citacoes = {
        _base: sus.citation_from_publications(
            [p for p in escolhidas if p["dataset"] == _base],
            snapshot_id=snapshot,
            dataset=_base,
        ).text
        for _base in bases.value
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
