"""Fetch verified IBGE product metadata, edition universe and original data bytes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from omnisus.sources.ibge.parse import municipal_codes
from omnisus.sources.ibge.products import PopulationProduct, resolve_product

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"


@dataclass(frozen=True)
class PopulationPublication:
    spec: PopulationProduct
    payload: object
    expected_codes: frozenset[str]
    sha256: str
    url: str
    collected_at: str
    revision: str
    evidence_json: str


def _validate_metadata(metadata: object, spec: PopulationProduct) -> None:
    if not isinstance(metadata, dict):
        raise ValueError("malformed population metadata")
    try:
        if (
            metadata["id"] != spec.aggregate
            or "N6" not in metadata["nivelTerritorial"]["Administrativo"]
        ):
            raise ValueError("unexpected aggregate or municipal level in metadata")
        variables = [v for v in metadata["variaveis"] if v["id"] == spec.variable]
        if len(variables) != 1 or variables[0]["unidade"] != "Pessoas":
            raise ValueError("unexpected variable or unit in metadata")
        categories = metadata["classificacoes"]
        if len(categories) != len(spec.classifications):
            raise ValueError("unexpected metadata classifications")
        actual = {}
        for category in categories:
            key = str(category["id"])
            totals = [c for c in category["categorias"] if c["id"] == 0 and c["nome"] == "Total"]
            if key in actual or len(totals) != 1:
                raise ValueError("metadata lacks unique Total category")
            actual[key] = "0"
        if actual != dict(spec.classifications):
            raise ValueError("unexpected metadata classification identifiers")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("malformed population metadata") from exc


def _period(periods: object, year: int) -> tuple[str, int]:
    if not isinstance(periods, list) or not periods:
        raise ValueError("requested year unavailable: empty periods response")
    try:
        ids = [p["id"] for p in periods]
        if any(
            not isinstance(p, str) or len(p) != 4 or not p.isascii() or not p.isdecimal()
            for p in ids
        ) or len(set(ids)) != len(ids):
            raise ValueError("malformed or duplicate periods")
        selected = [p for p in periods if p["id"] == str(year)]
        if len(selected) != 1:
            raise ValueError(f"year {year} unavailable for selected population product")
        revision = selected[0]["modificacao"]
        datetime.strptime(revision, "%d/%m/%Y")
        return revision, max(map(int, ids))
    except (KeyError, TypeError) as exc:
        raise ValueError("malformed population periods or revision") from exc


async def fetch_pop_by_year(year: int, *, product: str) -> PopulationPublication:
    """Only latest aggregate editions have a verified territorial universe today.

    Census aggregates end in 2010/2022. Historical estimates require an archived,
    independently sourced edition universe; the API locality endpoint is timeless.
    """
    spec = resolve_product(product, year)
    base = f"{BASE}/{spec.aggregate}"
    evidence: dict[str, dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:

        async def get(url: str, *, params: dict | None = None, role: str):
            response = await client.get(url, params=params)
            response.raise_for_status()
            content = response.content
            try:
                body = json.loads(content)
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f"invalid JSON in IBGE {role}") from exc
            evidence[role] = {
                "url": str(response.url),
                "sha256": hashlib.sha256(content).hexdigest(),
                "collected_at": datetime.now(UTC).isoformat(),
            }
            return body

        metadata = await get(f"{base}/metadados", role="metadata")
        _validate_metadata(metadata, spec)
        periods = await get(f"{base}/periodos", role="periods")
        revision, latest = _period(periods, year)
        if year != latest:
            raise ValueError(
                f"no verified edition universe for {product}/{year}; "
                f"only latest aggregate edition {latest} is supported; "
                "historical estimates require an archived territorial universe"
            )
        localities = await get(f"{base}/localidades/N6", role="universe")
        expected_codes = municipal_codes(localities)
        params = {"localidades": "N6"}
        if spec.classifications:
            params["classificacao"] = "|".join(f"{c}[{v}]" for c, v in spec.classifications)
        payload = await get(
            f"{base}/periodos/{year}/variaveis/{spec.variable}", params=params, role="population"
        )
        # A revision observed changing during collection cannot certify this publication.
        after = await get(f"{base}/periodos", role="periods_after")
        if _period(after, year) != (revision, latest):
            raise ValueError("population revision changed during collection; retry")
    evidence["metadata"]["document"] = metadata
    evidence["periods"]["document"] = periods
    evidence["universe"]["codes"] = sorted(expected_codes)
    data = evidence["population"]
    return PopulationPublication(
        spec,
        payload,
        expected_codes,
        data["sha256"],
        data["url"],
        data["collected_at"],
        revision,
        json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    )
