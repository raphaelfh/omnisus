"""Tier 3: every registry row, checked against the live server.

Internal agreement is necessary and insufficient — if a row's ftp_dir or
prefix is wrong, every derived surface is consistently wrong. Only this tier
can catch that, and only it detects a DATASUS reorganisation.

Network-bound and upstream-flaky, so it runs on a schedule, never on a PR.

Marked BOTH ``integration`` and ``e2e`` deliberately. CI runs
``-m "not e2e and not perf"``, which does *not* deselect ``integration`` — so
``integration`` alone would put one live FTP listing per registry directory
on every pull request. ``e2e`` is described in pyproject as "slow, manual/cron", which is
exactly this, and it is already deselected. ``probe.yml`` selects with
``-m integration``, which matches regardless of the second marker.

    uv run pytest tests/integration/test_registry_probe.py -m integration

A failure here is a finding about the registry or the server — never a
reason to loosen an assertion.
"""

from __future__ import annotations

from datetime import date

import pytest

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY, Dataset
from omnisus.sources.datasus_ftp.filenames import national_variant, parse_name
from omnisus.sources.datasus_ftp.inventory import Listing, list_dir, sources_for

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

ROWS = [pytest.param(d, id=name) for name, d in sorted(REGISTRY.items())]


@pytest.fixture(scope="module")
def listings() -> dict[str, Listing]:
    """One live LIST per distinct directory — rows share directories (SIA) and
    a row may have two (final + preliminary)."""
    cache: dict[str, Listing] = {}
    for d in REGISTRY.values():
        for directory in d.directories().values():
            if directory not in cache:
                cache[directory] = list_dir(directory, timeout_seconds=120.0)
    return cache


def _scopes(d: Dataset, listings: dict[str, Listing]) -> list[ScopeKey]:
    by_release = {release: listings[directory] for release, directory in d.directories().items()}
    return list(sources_for(d, by_release))


@pytest.mark.parametrize("d", ROWS)
def test_every_directory_exists_and_parses_cleanly(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    for release, directory in d.directories().items():
        listing = listings[directory]
        assert listing.entries, f"{d.name}: {release} directory {directory} listed empty"
        assert listing.skipped == 0, (
            f"{d.name}: {listing.skipped} unparseable LIST lines in {directory}"
        )


@pytest.mark.parametrize("d", ROWS)
def test_some_directory_holds_files_with_this_prefix(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    assert _scopes(d, listings), (
        f"{d.name}: no file in {list(d.directories().values())} decodes to this row"
    )


@pytest.mark.parametrize("d", ROWS)
def test_no_scope_is_published_in_two_directories(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    """``sources_for`` raises when a scope is listed in both the final and the
    preliminary directory — the real check is letting that exception surface,
    not deduplicating keys of a dict it already built without duplicates."""
    by_release = {release: listings[directory] for release, directory in d.directories().items()}
    sources_for(d, by_release)


@pytest.mark.parametrize("d", ROWS)
def test_coverage_matches_the_earliest_published_file(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    """coverage[0] must be what the server actually publishes first.

    If this fails, fix the row (or investigate a DATASUS reorganisation) —
    do not widen the assertion.
    """
    scopes = _scopes(d, listings)
    assert scopes, f"{d.name}: nothing decoded"
    earliest = min((s.ano, s.mes or 1) for s in scopes)
    assert earliest == d.coverage[0], (
        f"{d.name}: registry says coverage starts {d.coverage[0]}, "
        f"server's earliest file is {earliest}"
    )


# A monthly dataset silent for 18 months is dead. A yearly one 18 months
# behind is just yearly: DATASUS publishes SIM and SINASC definitive data
# years in arrears. One grace period cannot serve both, and the row already
# declares which it is. This covers publication lag only — a final directory
# that stops publishing years early (SINASC NOV/DNRES did, in 2022) is caught
# by test_final_and_prelim_leave_no_year_gap below, not by this grace period.
_ONGOING_GRACE_MONTHS = {"monthly": 18, "yearly": 48}


@pytest.mark.parametrize("d", ROWS)
def test_coverage_end_is_not_a_stale_claim(d: Dataset, listings: dict[str, Listing]) -> None:
    """coverage[1] is a claim too; a row must not lie.

    A closed window must not be contradicted by newer files on the server. An
    open window — ``None``, meaning "still published" — is the stronger claim,
    and it goes stale silently: nothing else in this suite would notice a
    dataset DATASUS quietly stopped publishing. The grace period is wide
    because DATASUS publishing lag is normal and this runs weekly on a cron,
    where a false alarm costs a notification rather than a blocked pull
    request.
    """
    scopes = _scopes(d, listings)
    assert scopes, f"{d.name}: nothing decoded"
    latest = max((s.ano, s.mes or 12) for s in scopes)

    declared_end = d.coverage[1]
    if declared_end is not None:
        assert latest <= declared_end, (
            f"{d.name}: registry closes coverage at {declared_end}, "
            f"but the server publishes {latest}"
        )
        return

    today = date.today()
    months_stale = (today.year - latest[0]) * 12 + (today.month - latest[1])
    grace = _ONGOING_GRACE_MONTHS[d.cadence]
    assert months_stale <= grace, (
        f"{d.name}: registry claims coverage is open-ended, but the server's "
        f"newest file is {latest}, {months_stale} months old "
        f"(grace for a {d.cadence} dataset is {grace})"
    )


@pytest.mark.parametrize("d", [p for p in ROWS if p.values[0].prelim_dir is not None])
def test_final_and_prelim_leave_no_year_gap(d: Dataset, listings: dict[str, Listing]) -> None:
    """A final directory that stops early (SINASC NOV/DNRES stopped at 2022) leaves
    a gap before the first preliminary year. The gap is the finding."""
    years = {
        release: {
            p.scope.ano
            for e in listings[directory].files
            if (p := parse_name(d, e.name)) is not None
        }
        for release, directory in d.directories().items()
    }
    if years["final"] and years["prelim"]:
        assert min(years["prelim"]) <= max(years["final"]) + 1, (
            f"{d.name}: final ends {max(years['final'])}, prelim starts {min(years['prelim'])}"
        )


@pytest.mark.parametrize("d", ROWS)
def test_parts_are_newer_than_the_whole_file_they_replace(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    """Parts supersede the whole file, which holds only while parts are the later revision."""
    for directory in d.directories().values():
        named = [(parse_name(d, e.name), e) for e in listings[directory].files]
        wholes = {p.scope: e for p, e in named if p is not None and p.part is None}
        for p, e in named:
            if p is not None and p.part is not None and p.scope in wholes:
                assert e.modified >= wholes[p.scope].modified, (d.name, e.name)


# Families the server publishes that no registry row models yet, found while
# running this probe live. Each entry is a note, not a directory to trust
# blindly — test_known_unmodelled_families_are_still_there below checks the
# family still has a .dbc file somewhere the probe lists, so a stale entry
# (the family stopped publishing) gets caught rather than silently ignored
# forever.
KNOWN_UNMODELLED = {
    # CNES/200508_/Dados/{EF,GM,HB,IN,RC}: a template name, 0 records, mtime 2020-12-18
    # (read 2026-09-22).
    "EFUFAAMM": "CNES/200508_/Dados/EF/EFufAAmm.dbc, 0-record template",
    "GMUFAAMM": "CNES/200508_/Dados/GM/GMufAAmm.dbc, 0-record template",
    "HBUFAAMM": "CNES/200508_/Dados/HB/HBufAAmm.dbc, 0-record template",
    "INUFAAMM": "CNES/200508_/Dados/IN/INufAAmm.dbc, 0-record template",
    "RCUFAAMM": "CNES/200508_/Dados/RC/RCufAAmm.dbc, 0-record template",
}


@pytest.mark.parametrize("d", ROWS)
def test_every_name_with_this_prefix_is_understood(
    d: Dataset, listings: dict[str, Listing]
) -> None:
    """Only ``.dbc`` names are checked: the codec reads only DBC, so a stray
    non-DBC file such as ``RDAC2017.zip`` is not something any row could claim."""
    others = [r for r in REGISTRY.values() if r is not d]
    for directory in d.directories().values():
        for e in listings[directory].files:
            if not e.name.lower().endswith(".dbc"):
                continue
            if not e.name.upper().startswith(d.prefix.upper()):
                continue
            if parse_name(d, e.name) or national_variant(d, e.name):
                continue
            if any(e.name.upper().startswith(family) for family in KNOWN_UNMODELLED):
                continue
            assert any(parse_name(r, e.name) for r in others), f"{d.name}: {e.name}"


def test_known_unmodelled_families_are_still_there(listings: dict[str, Listing]) -> None:
    """A ``KNOWN_UNMODELLED`` entry documents server noise the probe is told to
    ignore; if the family stopped publishing, the entry is stale and must be
    removed or updated, not left to silently mask a future, different file."""
    files = [e for listing in listings.values() for e in listing.files]
    for family in KNOWN_UNMODELLED:
        assert any(
            e.name.upper().startswith(family) and e.name.lower().endswith(".dbc") for e in files
        ), (
            f"{family}: no .dbc file found in any probed directory; remove or update KNOWN_UNMODELLED"
        )
