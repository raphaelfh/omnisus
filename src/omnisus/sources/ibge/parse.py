"""Strict IBGE population edition validation before publication."""

from __future__ import annotations

import re
from collections.abc import Collection

import polars as pl

from omnisus.sources.ibge.products import resolve_product


def municipal_codes(localities: object) -> frozenset[str]:
    """Validate the explicit territorial universe returned by the aggregate."""
    if not isinstance(localities, list) or not localities:
        raise ValueError("empty or malformed municipal universe")
    codes = []
    for locality in localities:
        if (
            not isinstance(locality, dict)
            or not isinstance(locality.get("id"), str)
            or not re.fullmatch(r"[1-5][0-9]{6}", locality["id"])
            or not isinstance(locality.get("nivel"), dict)
            or locality["nivel"].get("id") != "N6"
        ):
            raise ValueError("invalid municipal code or territorial level")
        codes.append(locality["id"])
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate municipality in universe or population")
    return frozenset(codes)


def pop_json_to_lazyframe(
    payload: object,
    year: int,
    *,
    product: str | None = None,
    expected_codes: Collection[str] | None = None,
) -> pl.LazyFrame:
    """Reject incomplete, ambiguous or unsupported values; never drop source rows."""
    if not isinstance(payload, list) or len(payload) != 1:
        raise ValueError("population response must contain exactly one variable; empty rejected")
    if product is None or not expected_codes:
        raise ValueError("explicit product and validated edition universe are required")
    spec = resolve_product(product, year)
    try:
        variable = payload[0]
        if variable["id"] != str(spec.variable) or variable["unidade"] != "Pessoas":
            raise ValueError("unexpected population variable or unit")
        results = variable["resultados"]
        if not isinstance(results, list) or len(results) != 1:
            raise ValueError("expected exactly one Total result")
        categories = results[0]["classificacoes"]
        if not isinstance(categories, list) or len(categories) != len(spec.classifications):
            raise ValueError("unexpected classifications")
        actual = {}
        for category in categories:
            key = category["id"]
            if key in actual or category["categoria"] != {"0": "Total"}:
                raise ValueError("expected unique Total categories")
            actual[key] = "0"
        if actual != dict(spec.classifications):
            raise ValueError("unexpected classification identifiers")
        series = results[0]["series"]
        if not isinstance(series, list) or not series:
            raise ValueError("empty population series")
        codes = municipal_codes([item["localidade"] for item in series])
        if codes != frozenset(expected_codes):
            raise ValueError("incomplete or divergent edition municipal universe")
        rows = []
        for item in series:
            values = item["serie"]
            if not isinstance(values, dict) or set(values) != {str(year)}:
                raise ValueError("population period differs from requested year")
            value = values[str(year)]
            if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
                raise ValueError("unsupported population symbol or non-integer value")
            number = int(value)
            if number > 2**64 - 1:
                raise ValueError("population exceeds UInt64 range")
            rows.append((item["localidade"]["id"], year, number))
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("malformed population response") from exc
    return pl.DataFrame(
        rows,
        schema={"codigo_ibge": pl.String, "ano": pl.UInt16, "populacao": pl.UInt64},
        orient="row",
    ).lazy()
