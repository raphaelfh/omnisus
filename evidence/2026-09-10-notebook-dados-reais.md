# Notebook da API com dados reais

Execução: 10/09/2026. Notebook: [api_dados_reais.py](../notebooks/api_dados_reais.py).

O notebook utiliza arquivos completos do SIM obtidos do FTP público do DATASUS,
via `available`, `browse` e `import_dataset`. Não utiliza fixtures ou dados
sintéticos nas consultas. A demonstração de rollback induz um erro sobre uma
agregação real, em catálogo temporário separado.

| Arquivo | Bytes na listagem FTP | Registros importados |
|---|---:|---:|
| DORR2022.dbc | 275.221 | 3.246 |
| DORR2023.dbc | 288.798 | 3.311 |
| Total | 564.019 | 6.557 |

Diretório remoto: `/dissemin/publicos/SIM/CID10/DORES` em `ftp.datasus.gov.br`.
O inventário atualizado retornou ambos os escopos. A execução com
`concurrency=1, batch_size=2` terminou com **2 ok, 0 failed e 0 skipped**.
Contagens por ano/UF foram reconciliadas com o `ImportReport`, depois de reabrir
o catálogo. Fonte de acesso: [transferência de arquivos DATASUS](https://datasus.saude.gov.br/transferencia-de-arquivos/).

A cópia preparada fica em
`data/lake/marimo-real/bc2d6701cdc24f28ba1be5b2e4f4cb72/`.
O ponteiro `data/lake/marimo-real/latest.json` identifica a última cópia concluída.
Dados, catálogo e manifesto local permanecem fora do Git. O botão do notebook
gera um destino novo; abrir ou alterar filtros não repete a ingestão.

## Validações concluídas

- Execução completa do notebook reutilizando os dados, com chamadas de descoberta
  e importação bloqueadas no teste para detectar reimportação acidental.
- Contagens e histórico de snapshots iguais aos registrados no manifesto.
- Filtro de 2022/não fetal retorna 3.246 linhas; filtro fetal produz seleção vazia.
- Agregações anual e mensal reconciliadas com a seleção.
- Exportação Parquet relida e comparada ao DataFrame agregado.
- Manifesto com histórico divergente rejeitado pela célula de leitura.
- Commit da tabela derivada e rollback da tentativa de duplicação verificados.
- Ruff, formatação, `marimo check --strict`, `git diff --check` e exportação HTML
  real aprovados. HTML de conferência: `/private/tmp/omnisus-real.html`.

A qualidade calculada encontrou zero datas ausentes/inválidas/divergentes do ano
do arquivo, zero causas básicas ou municípios de residência vazios, e dois códigos
de sexo ignorado em 2023. Esses testes não certificam validade clínica, completude
de cobertura ou unicidade de pessoas. O notebook distingue o ano/UF do arquivo
da data do óbito e da residência informadas nos registros; não calcula taxas
populacionais. Interpretação dos campos apoiada no
[dicionário SIM](https://svs.aids.gov.br/download/Dicionario_de_Dados_SIM_tabela_DO.pdf)
e no esquema efetivamente importado.

A revisão independente por subagente levou à comparação do histórico persistido
e à confirmação por identidade do erro induzido no rollback. A revisão foi
estática; o controlador executou os testes e a importação real.

Evidências: [verification.json](evidence/2026-09-10-marimo-real/verification.json)
e [script de aceitação](evidence/2026-09-10-marimo-real/verify_notebook.py).
O script registra esta extração específica e pressupõe o lake preparado. Uma
extração futura pode mudar as contagens. O hash apresentado pelo notebook é do
Parquet agregado exportado, não dos DBC originais.
