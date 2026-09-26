# Dicionário de dados e proveniência

O dicionário responde, para **cada campo de uma tabela**: o que significa, como
interpretar os valores, de onde veio essa interpretação, quando foi conferida e a
quais arquivos ela se aplica.

Os YAMLs empacotados em `src/omnisus/data/dicionarios/` são a fonte única das
definições. Cada afirmação sobre um campo cita um documento oficial registrado em
`src/omnisus/data/dicionarios/sources/registry.json`, com URL e SHA-256. Um
rótulo sem essa evidência não é tratado como conferido.

| Página | Para quê |
| --- | --- |
| [Contrato por coluna](contrato.md) | Descrição, códigos, evidência e aplicabilidade de um campo |
| [Consumo e integração](consumo.md) | Ler os metadados pela biblioteca, em JSON ou Arrow |
| [Manutenção e checagem](manutencao.md) | Atualizar um campo, resolver conflitos, critérios de publicação |
| [JSON Schema](schemas/column-metadata.schema.json) | Contrato `1.0.0` dos metadados de coluna |
| [Exemplo SIM / DO / SEXO](exemplos/sim_obitos.sexo.json) | Um campo com evidência oficial localizada |

Pela biblioteca: `sus.describe_dataset`, `sus.label` e `sus.display_row` leem estes
metadados; `sus.analytical_projection` aplica as regras auditadas de SIM, SIH, SINASC, SINAN e SIA.
Veja [Consumo e integração](consumo.md).
