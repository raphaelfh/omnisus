"""Explicit maintenance operations, with safe temporal cutoffs."""

from datetime import UTC, datetime

import duckdb

from omnisus.lake.sql import quote_literal


def run_maintenance(
    con: duckdb.DuckDBPyConnection,
    *,
    alias: str,
    operation: str,
    older_than: datetime | None = None,
    dry_run: bool = True,
    table: str | None = None,
) -> list[dict]:
    if operation == "compact":
        if table is None:
            raise ValueError("compact requires a table")
        cursor = con.execute("CALL ducklake_merge_adjacent_files(?, ?)", [alias, table])
    else:
        functions = {
            "expire": "ducklake_expire_snapshots",
            "cleanup": "ducklake_cleanup_old_files",
        }
        function = functions[operation]
        if older_than is None or older_than.tzinfo is None or older_than.utcoffset() is None:
            raise ValueError("older_than must include a timezone")
        # The extension binds named arguments before execution; constants are
        # rendered from validated datetime/bool values, never raw user SQL.
        cutoff = quote_literal(older_than.astimezone(UTC).isoformat())
        cursor = con.execute(
            f"CALL {function}({quote_literal(alias)}, older_than => TIMESTAMPTZ {cutoff}, dry_run => {str(bool(dry_run)).lower()})"
        )
    return cursor.to_arrow_table().to_pylist()
