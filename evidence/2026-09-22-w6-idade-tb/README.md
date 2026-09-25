# Idade SINAN (`kind: sinan`) — tuberculose, auditoria de 2026-09-22

| Arquivo (PRELIM, completo) | SHA-256 | Registros | Idade válida | Idade em branco | 4088 → 88 anos |
| --- | --- | ---: | ---: | ---: | ---: |
| TUBEBR20.dbc | `9ecf4873…0edc` | 86.160 | 86.124 | 36 | 52 linhas |

Mesma regra de CHAGBR23 e HANSBR26 (Dicionário Notificação Individual v5, pp. 3–4,
registro `sinan-b3e0561c7a2d`). TUBEBR20 usa as unidades 1 (hora, 000–024), 2 (dia,
000–030), 3 (mês, 001–011) e 4 (ano, 001–112); 36 linhas têm `NU_IDADE_N` em branco e
ficam `missing`. A fixture `tests/fixtures/dbc/sinan_tuberculose_br_2020_excerpt.dbc` são
os 3.000 primeiros registros deste arquivo (`tests/fixtures/FIXTURES.md`); o arquivo
completo fica fora do git em `data/lake/w6-sinan/TUBEBR20.dbc`. Estados, expressões e
consultas em `acceptance.json`.
