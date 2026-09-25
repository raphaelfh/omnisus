"""Publish a validated population edition and its provenance atomically."""

from __future__ import annotations

from uuid import uuid4

import polars as pl

from omnisus.lake import Lake
from omnisus.lake.sql import qualified
from omnisus.sources._base import ImportResult
from omnisus.sources.ibge.fetch import fetch_pop_by_year
from omnisus.sources.ibge.parse import pop_json_to_lazyframe

_VIEW_ERROR = "ambiguous IBGE population publication; select a publication_id from ibge_population"


async def import_pop_year(*, year: int, lake: Lake, product: str) -> ImportResult:
    """Append one explicit edition. Repeated loads remain distinct publications.

    The compatibility view fails on ambiguous municipality/year population values.
    Existing legacy tables or unrecognized views require explicit migration.
    """
    publication = await fetch_pop_by_year(year, product=product)
    lf = pop_json_to_lazyframe(
        publication.payload, year=year, product=product, expected_codes=publication.expected_codes
    )
    publication_id = str(uuid4())
    data = lf.with_columns(
        pl.lit(product).alias("product"), pl.lit(publication_id).alias("publication_id")
    )
    manifest = pl.DataFrame(
        {
            "publication_id": [publication_id],
            "product": [product],
            "ano": [year],
            "source": ["IBGE SIDRA"],
            "aggregate": [publication.spec.aggregate],
            "variable": [publication.spec.variable],
            "sha256": [publication.sha256],
            "url": [publication.url],
            "collected_at": [publication.collected_at],
            "period": [str(year)],
            "revision": [publication.revision],  # Compatibility alias for source_revision.
            "source_revision": [publication.revision],
            "population_reference_date": [publication.spec.population_reference_date],
            "population_reference_source_url": [publication.spec.population_reference_source_url],
            "population_reference_note": [publication.spec.population_reference_note],
            "territorial_reference_date": [None],
            "publication_date": [None],
            "temporal_metadata_note": [
                "territorial_reference_date and publication_date are unknown: selected "
                "aggregate metadata/periods do not establish these dates. "
                "source_revision preserves period.modificacao; collected_at is retrieval UTC. "
                "Neither is used to infer population reference or publication date."
            ],
            "expected_rows": [len(publication.expected_codes)],
            "accepted_rows": [len(publication.expected_codes)],
            "rejected_rows": [0],
            "parser_version": ["ibge-population-v2"],
            "evidence_json": [publication.evidence_json],
        },
        schema_overrides={
            "population_reference_date": pl.Date,
            "territorial_reference_date": pl.Date,
            "publication_date": pl.Date,
        },
    ).lazy()
    con = lake.connect()
    with lake.transaction():
        existing = con.execute(
            "SELECT table_type FROM information_schema.tables "
            "WHERE table_catalog = ? AND table_schema = ? AND table_name = ?",
            [lake.alias, "main", "ibge_populacao"],
        ).fetchone()
        if existing:
            if existing[0] != "VIEW":
                raise ValueError("legacy ibge_populacao table exists; explicit migration required")
            view = con.execute(
                "SELECT sql FROM duckdb_views() WHERE database_name = ? "
                "AND schema_name = ? AND view_name = ?",
                [lake.alias, "main", "ibge_populacao"],
            ).fetchone()
            if not view or _VIEW_ERROR not in view[0]:
                raise ValueError(
                    "unrecognized ibge_populacao view exists; explicit migration required"
                )
        result = lake.ingest("ibge_population", data, partition_by=("ano",))
        result.publication_id = publication_id
        lake.ingest("ibge_population_manifest", manifest)
        if not existing:
            # Static SQL; names are quoted and all source values travel through ingest.
            con.execute(
                f"CREATE VIEW {qualified(lake.alias, 'ibge_populacao')} AS "
                "SELECT codigo_ibge, ano, CASE WHEN "
                "count(*) OVER (PARTITION BY codigo_ibge, ano) = 1 "
                f"THEN populacao ELSE error('{_VIEW_ERROR}') END AS populacao "
                f"FROM {qualified(lake.alias, 'ibge_population')}"
            )
    return result
