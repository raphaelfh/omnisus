# Official IBGE fixtures

Collected from https://servicodados.ibge.gov.br/api/v3/agregados on 2026-09-10.
`{aggregate}-metadados.json` and `-periodos.json` preserve complete JSON content
from `/{aggregate}/metadados` and `/{aggregate}/periodos`.
Population fixtures preserve complete tiny responses requested with
`localidades=N6[1100015,1100023]`: aggregate 202/year 2010/variable 93 with
`classificacao=2[0]|1[0]`, 4714/year 2022/variable 93, 6579/year 2026/variable 9324.
Tests mock a two-municipality universe using these localities. This is a controlled
miniature, not evidence that a national edition contains only two municipalities.

The repository formatter normalizes one trailing newline; these fixture files
are not byte-identical archives of the original HTTP bodies. Production
provenance hashes the received HTTP body bytes before JSON parsing.
