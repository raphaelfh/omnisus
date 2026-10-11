# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.25.1,<0.26",
#     "omnisus==0.2.3",
#     "polars>=1.44.2,<2.0",
#     "sqlglot>=30.18.0",
# ]
# ///

"""Explorar o lake: escolher bases e escopos com widgets, ver as linhas e citar."""

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full", app_title="Explorar o lake")


@app.cell
def _():
    import json
    import os
    import shutil
    import tempfile
    from datetime import date
    from pathlib import Path

    import marimo as mo
    import polars as pl

    import omnisus as sus
    from omnisus.lake.locking import WriterBusyError

    return Path, WriterBusyError, date, json, mo, os, pl, shutil, sus, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Explorar o lake

    [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/explorar.py)

    Escolha nos widgets as bases e os escopos que o lake já tem e veja as linhas numa
    tabela com busca, filtro e ordenação, o perfil de uma coluna e a citação do que
    você escolheu. Os códigos ficam como o DATASUS publicou; o rótulo vem do
    dicionário, ao lado (`sexo_rotulo`).

    **Onde está o lake.** Indique a pasta que tem `omnisus-catalog.sqlite` e
    `omnisus.ducklake/`:

    - neste computador, a pasta onde `sus.load` grava: `$OMNISUS_DATA_DIR`, se
      definida, ou `data/raw`, relativa à pasta em que você abriu o marimo;
    - no Google Drive, a pasta do lake sincronizada no computador ou, no molab (que não
      monta o Drive), uma cópia da pasta no disco do notebook.

    O catálogo guarda a pasta em que o lake foi criado (no Colab,
    `/content/drive/MyDrive/omnisus`); este notebook lê os dados da pasta indicada,
    onde quer que ela esteja agora. Importe só num lake que está na pasta onde foi
    criado.

    **Abrir este notebook não baixa nem grava nada.** A seção *Importar* consulta o
    DATASUS só quando você clica no botão.
    """)
    return


@app.cell
def _(Path, mo, os):
    # Onde `sus.load` grava, resolvido como a biblioteca resolve: um `~` literal não é a home.
    _padrao = Path(os.environ.get("OMNISUS_DATA_DIR") or "data/raw").resolve()
    pasta = mo.ui.text(
        value=mo.cli_args().get("lake") or str(_padrao), label="Pasta do lake", full_width=True
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

    Para pôr escopos no lake: escolha a base e, conforme a base, os anos, as UFs e os
    meses. Cada lista tem *Select all* e *Deselect all* no topo; digitar filtra a lista
    (`201` e depois *Select 10 matching* marca 2010 a 2019). `sus.import_dataset` baixa
    só o que o lake ainda não tem do mesmo arquivo.

    **Limites.** A importação anda em partes de 24 escopos, com um commit no lake por
    parte. O omnisus baixa até 6 arquivos por vez, de propósito: o servidor do DATASUS
    é público e compartilhado. Cada arquivo é descompactado inteiro na memória, e os do
    SIA de SP e MG têm centenas de MB compactados; numa máquina com pouca memória,
    importe-os poucos de cada vez. O disco cresce com o que você escolhe: a linha
    abaixo dos seletores mostra o espaço livre.

    **Falhas.** O relatório diz o que houve com cada escopo. Clique em *Importar* de
    novo para continuar: o que já está no lake é pulado sem baixar. Se o kernel cair
    (por falta de memória, por exemplo), o que as partes anteriores gravaram fica.
    *Interromper* (■, só no modo de edição) para ao fim da parte em curso, que é
    gravada mas não entra no relatório; o resto da página se atualiza no próximo
    *Importar*. Ligue *Substituir* só quando o motivo pedir `replace` (o arquivo foi
    importado por outra versão do omnisus): os escopos escolhidos são baixados e
    gravados de novo.
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
        value=mo.cli_args().get("base") or "sim_obitos",
        label="Base",
        searchable=True,
    )
    return (base_nova,)


@app.cell
def _(base_nova, date, mo, sus):
    _base = sus.resolve(base_nova.value)
    por_uf = _base.geography == "state"
    mensal = _base.monthly

    def _da_linha(nome, padrao):
        """Os valores de `-- --nome a,b` (vírgula ou espaço), ou o padrão."""
        valor = mo.cli_args().get(nome)
        return padrao if valor is None else str(valor).replace(",", " ").split()

    (_primeiro, _), _ultimo = _base.coverage
    _anos = list(range(_primeiro, (_ultimo or (date.today().year,))[0] + 1))
    anos_novos = mo.ui.multiselect(
        options=_anos,
        value=[int(a) for a in _da_linha("anos", [min(2022, _anos[-1])])],
        label="Anos",
    )
    ufs_novas = mo.ui.multiselect(options=sus.ALL_UFS, value=_da_linha("ufs", ["RR"]), label="UFs")
    meses_novos = mo.ui.multiselect(
        options=list(range(1, 13)), value=[int(m) for m in _da_linha("meses", [1])], label="Meses"
    )
    substituir = mo.ui.switch(
        value=bool(mo.cli_args().get("substituir")), label="Substituir o que já está no lake"
    )
    importar = mo.ui.run_button(label="Importar")
    mo.hstack(
        [
            base_nova,
            anos_novos,
            *([ufs_novas] if por_uf else []),
            *([meses_novos] if mensal else []),
        ],
        justify="start",
        wrap=True,
    )
    return (
        anos_novos,
        importar,
        mensal,
        meses_novos,
        por_uf,
        substituir,
        ufs_novas,
    )


@app.cell
def _(
    Path,
    anos_novos,
    base_nova,
    diretorio,
    importar,
    mensal,
    meses_novos,
    mo,
    por_uf,
    shutil,
    substituir,
    sus,
    tempfile,
    ufs_novas,
):
    escopos_novos = sus.scopes_for(
        base_nova.value,
        years=sorted(anos_novos.value),
        ufs=[u for u in sus.ALL_UFS if u in ufs_novas.value] if por_uf else None,
        months=sorted(meses_novos.value) if mensal else None,
    )

    def _livre(pasta):
        """GiB livres no disco de `pasta` ou, se ela ainda não existe, da pasta acima."""
        while not pasta.exists():
            pasta = pasta.parent
        return shutil.disk_usage(pasta).free / 2**30

    _temporaria = Path(tempfile.gettempdir())
    mo.vstack(
        [
            mo.md(
                f"**{len(escopos_novos):,} escopo{'' if len(escopos_novos) == 1 else 's'}.** "
                "Disco livre: "
                f"{_livre(diretorio):.1f} GiB na pasta do lake e "
                f"{_livre(_temporaria):.1f} GiB em `{_temporaria}`, onde a importação "
                "descompacta cada arquivo."
            ),
            mo.hstack([importar, substituir], justify="start"),
        ]
    )
    return (escopos_novos,)


@app.cell
def _(
    WriterBusyError,
    alvo,
    base_nova,
    escopos_novos,
    executar,
    importar,
    mo,
    mudar_versao,
    pl,
    substituir,
    sus,
):
    mo.stop(not (importar.value or executar))
    mo.stop(not escopos_novos, mo.md("Escolha ao menos um ano, uma UF e um mês."))

    _situacoes = {
        None: "importado",
        "unchanged": "já estava no lake",
        "not_listed": "o DATASUS não publica",
        "outside_coverage": "fora da cobertura da base",
        "fetch_failed": "falhou ao baixar",
        "ingest_failed": "falhou ao gravar",
        "rolled_back": "desfeito: outro escopo da parte falhou",
    }
    _ao_abrir = {
        "install": "o DuckDB precisa de internet para baixar a extensão ducklake uma vez",
        "attach": "um lake só recebe importações na pasta onde foi criado (#87)",
        "set_option": "outro programa está lendo este lake; feche-o",
    }
    _resultado = {}  # escopo -> (situação, motivo)

    def _anotar(relatorio):
        for o in relatorio.outcomes:
            _resultado[o.scope] = (_situacoes[o.code], o.reason)

    def _parte(escopos):
        """Importa uma parte e anota cada escopo; devolve por que parar, se for o caso."""
        try:
            _anotar(
                sus.import_dataset(
                    base_nova.value,
                    scopes=escopos,
                    target=alvo,
                    policy="replace" if substituir.value else "skip_same",
                )
            )
        except sus.ImportAbortedError as e:
            _anotar(e.report)
            for _, escopo in e.unresolved:
                _resultado[escopo] = ("sem resultado", str(e.__cause__ or e))
            return f"A gravação no lake parou ({e.__cause__ or e})."
        except sus.FtpUnavailable as e:
            return f"O servidor do DATASUS não respondeu ({e.__cause__ or e})."
        except sus.FtpPathNotFound as e:
            return f"O DATASUS não tem mais um diretório desta base ({e}); atualize o omnisus."
        except sus.CatalogAttachError as e:
            return f"Não deu para abrir o lake para gravar: {_ao_abrir[e.stage]} ({e.__cause__ or e})."
        except WriterBusyError:
            return (
                "Outro processo está gravando neste lake (outra aba deste notebook, outro "
                "notebook ou um terminal). Espere ele terminar."
            )
        return None

    _partes = [escopos_novos[i : i + 24] for i in range(0, len(escopos_novos), 24)]
    parada = None
    with mo.status.progress_bar(
        total=len(escopos_novos), title=f"Importando {base_nova.value}", show_eta=True
    ) as _barra:
        for _escopos in _partes:
            try:
                parada = _parte(_escopos)
            except KeyboardInterrupt:
                for _escopo in _escopos:
                    _resultado.setdefault(_escopo, ("sem resultado", "interrompido"))
                parada = "Interrompido. A parte em curso foi gravada, mas não entra no relatório."
            _barra.update(increment=len(_escopos))
            if parada:
                break

    relatorio = pl.DataFrame(
        [(str(e), *_resultado.get(e, ("não tentado", None))) for e in escopos_novos],
        schema=["escopo", "situacao", "motivo"],
        orient="row",
    )
    importacao = " · ".join(
        f"{s}: {n}" for s, n in relatorio["situacao"].value_counts(sort=True).rows()
    )
    # Reabre o lake mesmo sem escopo novo: depois de uma interrupção, o marimo descarta
    # a mudança de versão, e é este clique que atualiza o resto da página.
    mudar_versao(lambda v: v + 1)
    _falhas = relatorio["situacao"].str.starts_with("falhou").any()
    mo.vstack(
        [
            *(
                [
                    mo.callout(
                        mo.md(f"{parada} Clique em *Importar* para continuar."), kind="danger"
                    )
                ]
                if parada
                else [mo.callout(mo.md("Clique em *Importar* para tentar de novo."), kind="warn")]
                if _falhas
                else []
            ),
            mo.md(importacao),
            mo.ui.table(relatorio, page_size=10, selection=None, wrapped_columns=["motivo"]),
        ]
    )
    return importacao, parada, relatorio


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## O que o lake tem

    Um escopo por linha, lido do catálogo, sem rede: a base, a UF, o ano e o mês, o
    diretório do servidor (`final` ou `prelim`), quantas linhas foram gravadas e quando.
    """)
    return


@app.cell
def _(alvo, diretorio, mo, sus, versao):
    versao()
    try:
        leitor = sus.LakeReader(alvo)
    except sus.CatalogAttachError:
        mo.stop(
            True,
            mo.md(f"Não há lake em `{diretorio}`. Indique outra pasta ou importe uma base acima."),
        )
    snapshot = sus.latest_snapshot_id(leitor)

    def _literal(valor):
        return "'" + str(valor).replace("'", "''") + "'"

    # O catálogo guarda a pasta onde o lake foi criado. Reabrir com OVERRIDE_DATA_PATH lê os
    # Parquet desta pasta, fixa o snapshot e deixa abrir uma cópia vinda do Google Drive.
    _catalogo = diretorio / "omnisus-catalog.sqlite"
    con = (
        leitor.connect()
        .execute("DETACH lake")
        .execute(
            f"ATTACH {_literal(f'ducklake:sqlite:{_catalogo}')} AS lake "
            f"(READ_ONLY, DATA_PATH {_literal(diretorio / 'omnisus.ducklake')}, "
            f"OVERRIDE_DATA_PATH true, SNAPSHOT_VERSION {snapshot})"
        )
    )
    return con, leitor, snapshot


@app.cell
def _(leitor, mo, pl):
    publicacoes = [p for p in leitor.publications() if p["active"] and p["scope"] is not None]
    mo.stop(not publicacoes, mo.md("O lake ainda não tem nenhuma base importada."))
    escopos = pl.DataFrame(
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
    escopos
    return escopos, publicacoes


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Escolher

    As opções vêm do que o lake tem. Uma base nacional (SINAN, subconjuntos do SIM)
    não tem UF; uma base anual não tem mês.
    """)
    return


@app.cell
def _(escopos, mo):
    _nomes = escopos["base"].unique().sort().to_list()
    bases = mo.ui.multiselect(options=_nomes, value=_nomes[:1], label="Bases")
    bases
    return (bases,)


@app.cell
def _(bases, con, escopos, mo, pl):
    mo.stop(not bases.value, mo.md("Escolha ao menos uma base."))
    _das_bases = escopos.filter(pl.col("base").is_in(bases.value))

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
    def _condicao(publicacoes):
        """`WHERE` e parâmetros que selecionam os escopos destas publicações.

        Cada publicação guarda em `scope_json` as colunas e os valores que gravou
        (`uf`, `ano`, `mes`; `_source_ano` numa base nacional).
        """
        campos = [json.loads(p["scope_json"]) for p in publicacoes]
        if not campos:
            return "false", []
        chaves = list(campos[0])
        colunas = ", ".join(f'"{c}"' for c in chaves)
        listas = ", ".join("unnest(?)" for _ in chaves)
        return f"({colunas}) IN (SELECT {listas})", [[e[c] for e in campos] for c in chaves]

    filtros = {_base: _condicao(_pubs) for _base, _pubs in escolhidas.items()}
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

    Uma aba por base. A contagem é de todos os escopos escolhidos; a tabela mostra até
    *Linhas na tabela* delas, porque a tabela do marimo guarda na memória tudo o que
    recebe. Para mais linhas, filtre os escopos ou tire colunas. As categorias
    harmonizadas (`idade_anos_completos`, `sexo_categoria`...) só aparecem quando todos
    os escopos vêm de fontes validadas (ADR 0003); a aba diz o motivo quando faltam.

    *Baixar o dicionário (CSV)* traz, para cada coluna, o tipo declarado e uma linha por
    código com o rótulo que a tabela mostra. Cada mapa de códigos diz como foi conferido
    (`verified_in_source`, `conflicting`, `unreviewed`) e de qual documento oficial veio
    (URL, SHA-256 e onde ler). O nome do arquivo leva a versão do dicionário, a que se
    cita. Abra a coluna `codigo` como texto na planilha, para não perder o zero de
    `06`. Nomes de CID-10 e de municípios ficam nas tabelas `aux_*` (`sus.read("aux_cid10")`).
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
        debounce=True,
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
def _(esquemas, pl, sus):
    def _juntar(valores):
        return " | ".join(valores) or None

    def _dicionario(base):
        """O dicionário de `base` em CSV: (nome do arquivo, bytes).

        Uma linha por código e uma por coluna sem mapa de códigos. Cada mapa leva a
        conferência (`verified_in_source`, `conflicting`, `unreviewed`...) e o
        documento que a sustenta: URL, SHA-256 e onde ler.
        """
        meta = sus.describe_dataset(base)
        documentos = {d["id"]: d for d in meta["sources"]}
        registros = []
        for item in meta["fields"]:
            campo = item["field"]
            mapa = next(c for c in item["claims"] if c["target"] == "/field/codes")
            provas = mapa["evidence"] if campo["codes"] else []
            comum = {
                "coluna": campo["name"],
                "titulo": campo["label"],
                "descricao": campo["description"],
                "tipo": campo["logical_type"],
                "conferencia": mapa["status"] if campo["codes"] else None,
                "fonte": _juntar(documentos[p["source_id"]]["url"] for p in provas),
                "fonte_sha256": _juntar(documentos[p["source_id"]]["sha256"] for p in provas),
                "onde": _juntar(
                    " ".join([p["locator"] or "", *(f"p. {n}" for n in p["pages"])]).strip()
                    for p in provas
                ),
            }
            for codigo in campo["codes"] or [{"value": None, "label": None}]:
                registros.append({**comum, "codigo": codigo["value"], "rotulo": codigo["label"]})
        colunas = ["coluna", "titulo", "descricao", "tipo", "codigo", "rotulo"]
        colunas += ["conferencia", "fonte", "fonte_sha256", "onde"]
        tabela = pl.DataFrame(registros, schema=dict.fromkeys(colunas, pl.String))
        nome = f"{base}_dicionario_{meta['dictionary_version']}.csv"
        return nome, tabela.write_csv(include_bom=True).encode()

    # Toda base de `sus.datasets()` tem dicionário no pacote; uma tabela importada com
    # um `Dataset` próprio pode não ter, e fica sem botão.
    _no_pacote = {d.name for d in sus.datasets()}
    dicionarios = {_base: _dicionario(_base) for _base in esquemas if _base in _no_pacote}
    return (dicionarios,)


@app.cell
def _(brutas, dicionarios, mo, projecoes, rotulos, sus, totais):
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

    # Todas as colunas: as categorias harmonizadas vêm por último e o marimo mostra só 50.
    mo.ui.tabs(
        {
            _base: mo.vstack(
                [
                    mo.hstack(
                        [
                            mo.md(_resumo(_base)),
                            *(
                                [
                                    mo.download(
                                        dicionarios[_base][1],
                                        filename=dicionarios[_base][0],
                                        label="Baixar o dicionário (CSV)",
                                    )
                                ]
                                if _base in dicionarios
                                else []
                            ),
                        ],
                        justify="space-between",
                        align="center",
                    ),
                    mo.ui.table(_amostra, page_size=20, max_columns=None),
                ]
            )
            for _base, _amostra in amostras.items()
        }
    )
    return (amostras,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Perfil de uma coluna

    Quantas linhas tem cada código, em todos os escopos escolhidos (não só nas da
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
def _(base_perfil, coluna_perfil, con, filtros, sus):
    _onde, _parametros = filtros[base_perfil.value]
    perfil = sus.label(
        base_perfil.value,
        con.execute(
            f'SELECT "{coluna_perfil.value}", count(*) AS registros, '
            "round(100 * count(*) / sum(count(*)) OVER (), 2) AS pct "
            f'FROM lake."{base_perfil.value}" WHERE {_onde} '
            "GROUP BY ALL ORDER BY registros DESC LIMIT 1000",
            _parametros,
        ).pl(),
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
    consulta = mo.sql(
        f"""
        SELECT * FROM lake.{base_perfil.value} LIMIT 100
        """,
        engine=con,
    )
    return (consulta,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Citar

    A citação nomeia o arquivo do servidor, o SHA-256 e o snapshot do lake de cada
    escopo escolhido. Guarde-a junto com o resultado.
    """)
    return


@app.cell
def _(escolhidas, mo, snapshot, sus):
    citacoes = {
        _base: sus.citation_from_publications(_pubs, snapshot_id=snapshot, dataset=_base).text
        for _base, _pubs in escolhidas.items()
        if _pubs
    }
    _texto = "\n\n".join(citacoes.values())
    (
        mo.vstack(
            [
                mo.md(f"```text\n{_texto}\n```"),
                mo.download(_texto.encode(), filename="citacao.txt", label="Baixar citação"),
            ]
        )
        if citacoes
        else mo.md("Nenhum escopo escolhido para citar.")
    )
    return (citacoes,)


if __name__ == "__main__":
    app.run()
