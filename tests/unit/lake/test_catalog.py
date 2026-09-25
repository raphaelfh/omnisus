"""Tests for lake.catalog target URI parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from omnisus.lake.catalog import CatalogURI, parse_target


def test_parse_target_local_default(tmp_path: Path) -> None:
    target = f"ducklake:{tmp_path}/omnisus.ducklake"
    parsed = parse_target(target)

    assert parsed.catalog_uri.startswith("sqlite:")
    assert parsed.catalog_uri.endswith("omnisus-catalog.sqlite")
    assert Path(parsed.storage_root) == tmp_path / "omnisus.ducklake"


def test_parse_target_explicit_postgres() -> None:
    target = "ducklake:postgresql://u:p@h/db?storage=s3://bucket/lake"
    parsed = parse_target(target)

    assert parsed.catalog_uri == "postgresql://u:p@h/db"
    assert parsed.storage_root == "s3://bucket/lake"


def test_parse_target_keeps_a_netloc_less_postgres_dsn_intact() -> None:
    """libpq accepts ``postgresql:///?host=…`` (every parameter in the query).
    ``urlunsplit`` rewrote it as ``postgresql:/?host=…``, which libpq rejects."""
    target = "ducklake:postgresql:///?host=h&dbname=d&storage=s3://bucket/lake&sslmode=require"
    parsed = parse_target(target)

    assert parsed.catalog_uri == "postgresql:///?host=h&dbname=d&sslmode=require"
    assert parsed.storage_root == "s3://bucket/lake"


def test_parse_target_rejects_missing_scheme() -> None:
    with pytest.raises(ValueError, match="must start with 'ducklake:'"):
        parse_target("./omnisus.ducklake")


def test_catalog_uri_is_immutable() -> None:
    uri = CatalogURI(catalog_uri="sqlite:/x.sqlite", storage_root="/y")
    with pytest.raises((AttributeError, TypeError)):
        uri.catalog_uri = "other"  # type: ignore[misc]
