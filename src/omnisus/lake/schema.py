"""Lossless type widening for schema evolution."""

from __future__ import annotations


class UnsafeSchemaError(ValueError):
    """A schema change has no verified lossless conversion."""


def compatible_type(existing: str, incoming: str) -> str:
    """Return a common lossless SQL type, or reject before implicit SQL casts.

    Families are deliberately narrow. Decimal scale changes, signed/unsigned
    mixing and numeric/string conversions require a domain migration.
    """
    if existing == incoming:
        return existing
    families = (
        ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"),
        ("UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT"),
        ("FLOAT", "DOUBLE"),
    )
    for family in families:
        if existing in family and incoming in family:
            return family[max(family.index(existing), family.index(incoming))]
    raise UnsafeSchemaError(
        f"unsafe schema type change: {existing} versus {incoming}; explicit migration required"
    )
