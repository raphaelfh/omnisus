"""Type widening when a lake table's schema changes."""

from __future__ import annotations

import pytest

from omnisus.lake.schema import UnsafeSchemaError, compatible_type


def test_same_family_widens_to_the_larger_type() -> None:
    assert compatible_type("SMALLINT", "BIGINT") == "BIGINT"
    assert compatible_type("DOUBLE", "FLOAT") == "DOUBLE"


def test_signed_and_unsigned_do_not_mix() -> None:
    with pytest.raises(UnsafeSchemaError):
        compatible_type("INTEGER", "UINTEGER")
