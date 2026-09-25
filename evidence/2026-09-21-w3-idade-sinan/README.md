# Idade SINAN (`kind: sinan`) — auditoria de 2026-09-21

| Arquivo (PRELIM, completo) | SHA-256 | Registros | Idade válida | 4088 → 88 anos |
| --- | --- | ---: | ---: | ---: |
| CHAGBR23.dbc | `a0ab9f56…a10f` | 6.253 | 6.253 | 11 linhas |
| HANSBR26.dbc | `2a1d5b69…5a62` | 10.354 | 10.354 | 16 linhas |

`NU_IDADE_N` tem 1 dígito de unidade e 3 de quantidade (Dicionário de Dados
Notificação Individual v5, pp. 3–4, SHA-256 `b3e0561c…3004`, registro
`sinan-b3e0561c7a2d`). CHAGBR23 usa as unidades 2 (dia, 000–029), 3 (mês, 001–011)
e 4 (ano, 001–106); HANSBR26 só a unidade 4 (001–103). A unidade 1 (hora) está no
documento e não aparece em nenhum dos dois arquivos.

A regra do SIM (unidade + 2 dígitos) rejeita `4088` como `invalid`; um recorte de
dois dígitos leria `8`. Os bytes auditados são as fixtures
`tests/fixtures/dbc/sinan_chagas_br_2023.dbc` e `sinan_hanseniase_br_2026.dbc`
(`tests/fixtures/FIXTURES.md`); `manifest.json` aponta cópias com o nome do servidor
porque o script confere nome e escopo. Estados, expressões e consultas em
`acceptance.json`.
