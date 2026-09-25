"""Bounded, read-only observation of the public DEMAS BNAFAR/Hórus stock API.

This endpoint has page-number offsets and no documented snapshot/completeness
contract. Consequently this module cannot publish or replace a lake scope.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

import httpx

ENDPOINT = "https://apidadosabertos.saude.gov.br/daf/estoque-medicamentos-bnafar-horus"
SPECIFICATION = "https://apidadosabertos.saude.gov.br/static/swagger.json"
FILTERS = frozenset(
    {
        "codigo_uf",
        "codigo_municipio",
        "codigo_cnes",
        "anomes_posicao_estoque",
        "data_posicao_estoque",
        "codigo_catmat",
        "sigla_programa_saude",
        "tipo_produto",
        "sigla_sistema_origem",
    }
)


@dataclass(frozen=True)
class StockPage:
    """One observed HTTP response, with its exact JSON bytes and acquisition identity.

    ``complete`` is always false, including empty or short pages. A successful
    request is not evidence of complete municipal/basic dispensing coverage.
    """

    url: str
    acquired_at: str
    raw: bytes
    page: int
    limit: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()

    @property
    def records(self) -> list[dict[str, Any]]:
        # Fresh objects avoid a mutable records list diverging from the hash.
        return json.loads(self.raw)["parametros"]

    @property
    def complete(self) -> Literal[False]:
        return False

    def provenance(self) -> dict[str, Any]:
        return {
            "product": "bnafar_horus_stock_page",
            "url": self.url,
            "acquired_at": self.acquired_at,
            "sha256": self.sha256,
            "bytes": len(self.raw),
            "page": self.page,
            "limit": self.limit,
            "rows": len(self.records),
            "complete": False,
            "publication_supported": False,
            "specification": SPECIFICATION,
        }


def fetch_stock_page(
    *,
    filters: dict[str, str | int],
    page: int = 0,
    limit: int = 100,
    max_bytes: int = 4 * 1024 * 1024,
    client: httpx.Client | None = None,
) -> StockPage:
    """Inspect a filtered page (``offset=page``, NOT ``page * limit``).

    At least one documented filter is required to keep discovery deliberate.
    No automatic pagination, retries or writes. HTTP/transport failures propagate;
    schema changes and responses exceeding the byte budget raise ``ValueError``.
    ``max_bytes`` bounds decoded response bytes; HTTP timeout is 30 seconds.
    Caller-owned clients remain open. Preserve ``raw`` with ``provenance()`` when
    saving an exploratory observation outside the managed lake.
    """
    if type(page) is not int or page < 0:
        raise ValueError("page must be a non-negative integer")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer between 1 and 1000")
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")
    if not filters or set(filters) - FILTERS:
        raise ValueError("provide at least one documented stock filter")
    if any(type(v) not in (str, int) or not str(v).strip() for v in filters.values()):
        raise ValueError("filter values must be non-empty strings or integers")
    params = {**filters, "limit": limit, "offset": page}
    context = nullcontext(client) if client is not None else httpx.Client()
    with (
        context as session,
        session.stream(
            "GET",
            ENDPOINT,
            params=params,
            headers={"Accept": "application/json"},
            timeout=30,
            follow_redirects=False,
        ) as response,
    ):
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_bytes(chunk_size=64 * 1024):
            if len(body) + len(chunk) > max_bytes:
                raise ValueError("stock response exceeds max_bytes")
            body.extend(chunk)
        url = str(response.url)
    raw = bytes(body)
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("stock response must be JSON") from exc
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("parametros"), list)
        or any(not isinstance(row, dict) for row in payload["parametros"])
        or len(payload["parametros"]) > limit
    ):
        raise ValueError("unexpected stock response envelope or page length")
    return StockPage(url, datetime.now(UTC).isoformat(), raw, page, limit)
