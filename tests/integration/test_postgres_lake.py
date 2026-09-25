"""Synthetic public-API gate; requires an explicitly supplied disposable server.

OMNISUS_TEST_POSTGRES_URL must allow CREATE DATABASE. Each case creates and drops
only its own UUID-named database; no existing catalog or source data is used.
"""

import hashlib
import os
from urllib.parse import urlencode
from uuid import uuid4

import polars as pl
import pytest

from omnisus import DeletionResult, Lake, LakeReader, ScopeKey

pytestmark = pytest.mark.integration


@pytest.fixture
def postgres_catalog():
    url = os.environ.get("OMNISUS_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("set OMNISUS_TEST_POSTGRES_URL to a disposable PostgreSQL server")
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict

    name = "omnisus_selector_" + uuid4().hex
    info = conninfo_to_dict(url)
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            info["dbname"] = name
            # Percent-encode spaces as %20: libpq does not decode form-style '+'.
            yield "postgresql:///?" + urlencode(info).replace("+", "%20")
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.mark.parametrize("scheme", ["postgresql", "postgres"])
def test_cloud_managed_publication(postgres_catalog, tmp_path, scheme):
    catalog = postgres_catalog.replace("postgresql:", scheme + ":", 1)
    storage = str(tmp_path / "storage")
    staging = tmp_path / "synthetic.parquet"
    pl.DataFrame({"ano": [2024, 2024], "uf": ["SP", "SP"], "value": [11, 22]}).write_parquet(
        staging
    )
    publication = dict(
        scope=ScopeKey(uf="SP", ano=2024),
        source_sha256=hashlib.sha256(staging.read_bytes()).hexdigest(),
        parser_version="synthetic-v1",
        run_id="selector-gate",
    )
    with Lake.cloud(catalog=catalog, storage=storage) as lake:
        before = lake.snapshots()
        result = lake.publish_scope("synthetic", staging, **publication)
        assert result is not None
        assert result.rows == 2
        assert result.publication_id
        assert result.snapshot_id is not None
        snapshots = lake.snapshots()
        assert len(snapshots) == len(before) + 1
        assert result.snapshot_id == snapshots[-1]["snapshot_id"]
        records = lake.publications(run_id="selector-gate")
        assert len(records) == 1
        assert records[0]["publication_id"] == result.publication_id
        assert records[0]["source_sha256"] == publication["source_sha256"]
        assert lake.connect().execute(
            "SELECT value FROM lake.synthetic ORDER BY value"
        ).fetchall() == [(11,), (22,)]
        assert lake.publish_scope("synthetic", staging, policy="skip_same", **publication) is None
        assert lake.snapshots() == snapshots
        assert lake.publications(run_id="selector-gate") == records
        assert lake.connect().execute("SELECT count(*) FROM lake.synthetic").fetchone() == (2,)

    # Persistence and idempotence must survive closing and reopening the public handle.
    with Lake.cloud(catalog=catalog, storage=storage) as lake:
        assert lake.publications(run_id="selector-gate") == records
        assert lake.publish_scope("synthetic", staging, policy="skip_same", **publication) is None
        assert lake.connect().execute("SELECT count(*) FROM lake.synthetic").fetchone() == (2,)
        assert lake.snapshots()[-1]["snapshot_id"] == result.snapshot_id

    # A read-only session sees the same data with no writer lock, DATA_PATH or option
    # calls, and a pin to the pre-publication snapshot does not see the table at all.
    target = f"ducklake:{catalog}&storage={storage}"
    with LakeReader(target) as reader:
        assert reader.publications(run_id="selector-gate") == records
        assert reader.connect().execute("SELECT count(*) FROM lake.synthetic").fetchone() == (2,)
    with LakeReader(target, snapshot_id=before[-1]["snapshot_id"]) as reader:
        assert "synthetic" not in reader.tables()

    # Removal keeps data and manifest coherent, and a reader observes both sides.
    with Lake.cloud(catalog=catalog, storage=storage) as lake:
        deletion = lake.delete_scope("synthetic", ScopeKey(uf="SP", ano=2024))
        assert deletion == DeletionResult(rows_deleted=2, publications_retired=1)
    with LakeReader(target) as reader:
        assert reader.connect().execute("SELECT count(*) FROM lake.synthetic").fetchone() == (0,)
        (record,) = reader.publications(run_id="selector-gate")
        assert record["active"] is False
        assert record["scope"] == ScopeKey(uf="SP", ano=2024)
