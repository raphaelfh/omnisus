"""Every committed data fixture has a provenance row (AGENTS.md, policy rule 2)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TABLE = FIXTURES / "FIXTURES.md"
COLUMNS = ["file", "kind", "source", "server_modified", "source_sha256", "records", "note"]
KINDS = {"whole", "excerpt", "listing", "synthetic", "vector", "member"}
PINNED_URL = r"https://github\.com/[^/]+/[^/]+/blob/[0-9a-f]{40}/\S+"
DATA_GLOBS = ["dbc/**/*.dbc", "listings/*.txt.gz", "cnv/*", "sigtap/*"]


def load_fixture_rows() -> list[dict[str, str]]:
    rows = []
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(COLUMNS) or cells[0] in ("file", "") or set(cells[0]) <= {"-"}:
            continue
        rows.append(dict(zip(COLUMNS, cells, strict=True)))
    return rows


def test_every_data_fixture_has_exactly_one_row() -> None:
    files = sorted(
        # as_posix: FIXTURES.md records one separator, the one the repository uses.
        path.relative_to(FIXTURES).as_posix()
        for pattern in DATA_GLOBS
        for path in FIXTURES.glob(pattern)
    )
    recorded = [row["file"] for row in load_fixture_rows()]
    assert sorted(recorded) == files


def test_rows_are_complete() -> None:
    for row in load_fixture_rows():
        assert row["kind"] in KINDS, row
        if row["kind"] == "synthetic":
            assert row["note"], f"{row['file']}: a synthetic fixture must say why"
            continue
        if row["kind"] == "vector":
            assert re.fullmatch(PINNED_URL, row["source"]), row
            assert re.fullmatch("[0-9a-f]{64}", row["source_sha256"]), row
            assert row["note"], f"{row['file']}: a vector must name its licence"
            continue
        assert row["source"].startswith("ftp://"), row
        assert re.fullmatch("[0-9a-f]{64}", row["source_sha256"]), row
        assert row["server_modified"], row


def test_whole_files_are_the_recorded_bytes() -> None:
    for row in load_fixture_rows():
        if row["kind"] in ("whole", "vector", "member"):
            digest = hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest()
            assert digest == row["source_sha256"], row["file"]


def test_excerpts_record_how_many_records_they_keep() -> None:
    for row in load_fixture_rows():
        if row["kind"] in ("excerpt", "listing"):
            assert row["records"].isdigit() and int(row["records"]) > 0, row
