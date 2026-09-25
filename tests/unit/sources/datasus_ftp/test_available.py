"""crawl (open-world) and available (registry-decoded).

Same primitive underneath; the only difference is whether filenames get
decoded. Patched at _blocking_list. No network.
"""

from __future__ import annotations

import ftplib
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.inventory import (
    available,
    available_releases,
    crawl,
    list_dir_cached,
)

SIM_DIR = REGISTRY["sim_obitos"].ftp_dir
SIA_DIR = REGISTRY["sia_bpa_individualizado"].ftp_dir
SIM_PRELIM_DIR = REGISTRY["sim_obitos"].prelim_dir


def _file(name: str, when: str = "01-31-20  02:48PM", size: int = 76107) -> str:
    return f"{when}         {size:>12} {name}"


def _dir(name: str, when: str = "02-24-18  07:38AM") -> str:
    return f"{when}       <DIR>          {name}"


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMNISUS_CACHE_DIR", str(tmp_path / "cache"))


# --- available -------------------------------------------------------------


def test_available_decodes_scopes_for_the_requested_dataset() -> None:
    lines = [_file("DOAC1996.dbc"), _file("DOAC1997.dbc"), _file("DOSP2024.dbc")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sim_obitos")
    assert ScopeKey(uf="AC", ano=1996) in scopes
    assert ScopeKey(uf="SP", ano=2024) in scopes
    assert len(scopes) == 3


def test_available_filters_out_other_datasets_sharing_the_directory() -> None:
    """SIASUS/200801_/Dados holds BI, AM, AQ, ATD... available('sia_bpa_individualizado') must
    return only BI scopes."""
    lines = [
        _file("BIRR2401.dbc"),
        _file("AMRR2401.dbc"),
        _file("ATDRR2401.dbc"),
        _file("BIRR2402.dbc"),
    ]
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", return_value=lines):
        scopes = available("sia_bpa_individualizado")
    assert scopes == [
        ScopeKey(uf="RR", ano=2024, mes=1),
        ScopeKey(uf="RR", ano=2024, mes=2),
    ]


def test_available_skips_undecodable_names_without_raising() -> None:
    lines = [_file("DOAC1996.dbc"), _file("readme.txt"), _file("PARR2401.dbc"), _dir("OLD")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sim_obitos")
    assert scopes == [ScopeKey(uf="AC", ano=1996)]


def test_available_filters_by_years() -> None:
    lines = [_file("DOAC1996.dbc"), _file("DOAC2020.dbc"), _file("DOAC2024.dbc")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sim_obitos", years=range(2020, 2025))
    assert [s.ano for s in scopes] == [2020, 2024]


def test_available_returns_sorted_scopes() -> None:
    lines = [_file("DOSP2024.dbc"), _file("DOAC1996.dbc"), _file("DOAC2020.dbc")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sim_obitos")
    assert scopes == sorted(scopes, key=lambda s: (s.ano, s.uf, s.mes or 0))


def test_available_empty_directory_returns_empty_list() -> None:
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", return_value=[]):
        assert available("sim_obitos") == []


# --- available_releases -----------------------------------------------------


def _listing_by_path(paths: dict[str, list[str]]):
    def fake(path: str, _timeout: float) -> list[str]:
        return paths[path]

    return fake


def test_available_releases_reads_both_directories() -> None:
    fake = _listing_by_path(
        {SIM_DIR: [_file("DOAC2024.dbc")], SIM_PRELIM_DIR: [_file("DOAC2025.dbc")]}
    )
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        releases = available_releases("sim_obitos")
    assert releases == {
        ScopeKey(uf="AC", ano=2024): "final",
        ScopeKey(uf="AC", ano=2025): "prelim",
    }
    assert list(releases) == [ScopeKey(uf="AC", ano=2024), ScopeKey(uf="AC", ano=2025)]


def test_available_is_the_keys_of_available_releases() -> None:
    fake = _listing_by_path(
        {SIM_DIR: [_file("DOAC2024.dbc")], SIM_PRELIM_DIR: [_file("DOAC2025.dbc")]}
    )
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        assert available("sim_obitos", years=[2025]) == [ScopeKey(uf="AC", ano=2025)]


def test_same_scope_in_both_directories_is_an_error_not_a_preference() -> None:
    fake = _listing_by_path(
        {SIM_DIR: [_file("DOAC2025.dbc")], SIM_PRELIM_DIR: [_file("DOAC2025.dbc")]}
    )
    with (
        patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake),
        pytest.raises(ValueError, match="both final and prelim"),
    ):
        available_releases("sim_obitos")


def test_row_without_prelim_dir_lists_one_directory_only() -> None:
    calls: list[str] = []

    def fake(path: str, _timeout: float) -> list[str]:
        calls.append(path)
        return [_file("BIRR2401.dbc")]

    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        assert available_releases("sia_bpa_individualizado") == {
            ScopeKey(uf="RR", ano=2024, mes=1): "final"
        }
    assert calls == [SIA_DIR]


def test_adhoc_dataset_is_discovered() -> None:
    """ADR 0002: an unregistered Dataset flows through the same path — including discovery."""
    from omnisus.sources.datasus_ftp.datasets import Dataset

    d = Dataset(
        name="pce",
        prefix="PCE",
        ftp_dir="/dissemin/publicos/PCE/DADOS",
        cadence="yearly",
        partition_by=("ano", "uf"),
        coverage=((2000, 1), None),
    )
    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        return_value=[_file("PCEAL2023.dbc")],
    ):
        assert available(d) == [ScopeKey(uf="AL", ano=2023)]


# --- caching ---------------------------------------------------------------


def test_second_call_is_served_from_cache_without_hitting_the_network() -> None:
    fake = _listing_by_path({SIM_DIR: [_file("DOAC1996.dbc")], SIM_PRELIM_DIR: []})
    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        side_effect=fake,
    ) as spy:
        available("sim_obitos")
        available("sim_obitos")
    assert spy.call_count == 2, "one LIST per directory of the row, cached on the second call"


def test_refresh_bypasses_the_cache() -> None:
    fake = _listing_by_path({SIM_DIR: [_file("DOAC1996.dbc")], SIM_PRELIM_DIR: []})
    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        side_effect=fake,
    ) as spy:
        available("sim_obitos")
        available("sim_obitos", refresh=True)
    assert spy.call_count == 4, "refresh re-lists every directory of the row, not just one"


def test_list_dir_cached_writes_the_cache_file() -> None:
    from omnisus.sources.datasus_ftp._cache import cache_path

    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        return_value=[_file("DOAC1996.dbc")],
    ):
        list_dir_cached(SIM_DIR)
    assert cache_path(SIM_DIR).exists()


def test_an_unwritable_cache_does_not_veto_a_good_listing() -> None:
    """Never authoritative, on the write side. The network answer is already in hand; a cache
    that cannot be written must not be able to throw it away."""
    fake = _listing_by_path({SIM_DIR: [_file("DOAC1996.dbc")], SIM_PRELIM_DIR: []})
    with (
        patch(
            "omnisus.sources.datasus_ftp.inventory._blocking_list",
            side_effect=fake,
        ),
        patch(
            "omnisus.sources.datasus_ftp._cache.write_cache",
            side_effect=PermissionError("read-only file system"),
        ),
    ):
        scopes = available("sim_obitos")
    assert scopes == [ScopeKey(uf="AC", ano=1996)]


def test_cache_hit_and_miss_agree_on_the_canonical_path() -> None:
    """list_dir promises Listing.path is canonical (trailing slash stripped)
    regardless of what the caller passed. A miss builds it from list_dir; a
    hit must not silently rebuild it from the raw, un-normalised argument."""
    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        return_value=[_file("DOAC1996.dbc")],
    ):
        miss = list_dir_cached(SIM_DIR + "/")
        hit = list_dir_cached(SIM_DIR + "/")
    assert miss.path == SIM_DIR
    assert hit.path == miss.path


def test_refresh_still_writes_the_cache_it_bypassed() -> None:
    """The other half. A call count proves the read was skipped; only the
    file's mtime proves the write still happened."""
    from omnisus.sources.datasus_ftp._cache import cache_path

    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        return_value=[_file("DOAC1996.dbc")],
    ):
        list_dir_cached(SIM_DIR)
        first = cache_path(SIM_DIR).stat().st_mtime_ns
        os.utime(cache_path(SIM_DIR), ns=(first - 1_000_000_000, first - 1_000_000_000))
        aged = cache_path(SIM_DIR).stat().st_mtime_ns

        list_dir_cached(SIM_DIR, refresh=True)

    assert cache_path(SIM_DIR).stat().st_mtime_ns > aged


# --- crawl -----------------------------------------------------------------


def test_crawl_depth_one_does_not_recurse() -> None:
    lines = [_file("DOAC1996.dbc"), _dir("SUBDIR")]
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", return_value=lines) as spy:
        entries = list(crawl(SIM_DIR, depth=1))
    assert spy.call_count == 1
    assert {e.name for e in entries} == {"DOAC1996.dbc", "SUBDIR"}


def test_crawl_depth_two_descends_once() -> None:
    def by_path(path: str, _timeout: float) -> list[str]:
        if path == SIM_DIR:
            return [_dir("SUB")]
        if path == f"{SIM_DIR}/SUB":
            return [_file("DOAC1996.dbc"), _dir("DEEPER")]
        raise AssertionError(f"crawl went too deep: {path}")

    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=by_path):
        names = {e.name for e in crawl(SIM_DIR, depth=2)}
    assert names == {"SUB", "DOAC1996.dbc", "DEEPER"}


def test_crawl_is_lazy() -> None:
    """A generator, so a huge tree can be interrupted."""
    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        return_value=[_file("DOAC1996.dbc")],
    ) as spy:
        it = crawl(SIM_DIR, depth=1)
        assert spy.call_count == 0
        next(it)
        assert spy.call_count == 1


def test_crawl_rejects_non_positive_depth() -> None:
    with pytest.raises(ValueError, match="depth"):
        list(crawl(SIM_DIR, depth=0))


def test_crawl_skips_unreadable_subdirectories_but_yields_the_rest() -> None:
    """A denied subtree must not truncate the walk: the directory entry is
    still yielded and its siblings are still listed."""

    def by_path(path: str, _timeout: float) -> list[str]:
        if path == SIA_DIR:
            return [_dir("OK"), _dir("DENIED")]
        if path == f"{SIA_DIR}/OK":
            return [_file("BIRR2401.dbc")]
        raise ftplib.error_perm("550 denied")

    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=by_path):
        names = {e.name for e in crawl(SIA_DIR, depth=2)}
    assert names == {"OK", "DENIED", "BIRR2401.dbc"}


def test_crawl_raises_when_the_root_itself_is_missing() -> None:
    def boom(*_a: object, **_k: object) -> list[str]:
        raise ftplib.error_perm("550 nope")

    from omnisus.sources.datasus_ftp.inventory import FtpPathNotFound

    with (
        patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=boom),
        pytest.raises(FtpPathNotFound),
    ):
        list(crawl("/nope", depth=1))


def test_crawl_is_open_world_where_available_is_closed() -> None:
    """The design's central claim, asserted in one place: given identical
    server output, ``crawl`` yields what ``available`` refuses to. If someone
    ever teaches ``crawl`` to decode, this fails — every other test in this
    file would still pass."""
    lines = [_file("DOAC1996.dbc"), _file("readme.txt"), _file("PARR2401.dbc")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        crawled = {e.name for e in crawl(SIM_DIR)}
        scopes = available("sim_obitos", refresh=True)

    assert crawled == {"DOAC1996.dbc", "readme.txt", "PARR2401.dbc"}
    assert scopes == [ScopeKey(uf="AC", ano=1996)]
    assert len(crawled) > len(scopes)


def test_crawl_refresh_propagates_into_recursion() -> None:
    """``refresh`` must reach every level, not just the root — a stale cached
    subdirectory would otherwise survive a refresh that claimed to be total."""
    by_path = {
        SIM_DIR: [_dir("SUBDIR")],
        f"{SIM_DIR}/SUBDIR": [_file("DOAC1996.dbc")],
    }

    with patch(
        "omnisus.sources.datasus_ftp.inventory._blocking_list",
        side_effect=lambda path, _timeout: by_path[path],
    ) as spy:
        list(crawl(SIM_DIR, depth=2))
        assert spy.call_count == 2
        list(crawl(SIM_DIR, depth=2))
        assert spy.call_count == 2, "second crawl should be fully cached"
        list(crawl(SIM_DIR, depth=2, refresh=True))

    assert spy.call_count == 4, "refresh must refetch the subdirectory too, not only the root"


def test_available_filters_by_ufs_and_months_like_scopes_for() -> None:
    """``available`` takes the same selectors as ``scopes_for`` so a caller can
    ask "what exists for SP in 2024" without post-filtering the listing."""
    lines = [_file("DOSP2024.dbc"), _file("DORJ2024.dbc"), _file("DOSP2023.dbc")]
    fake = _listing_by_path({SIM_DIR: lines, SIM_PRELIM_DIR: []})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sim_obitos", years=[2024], ufs=["sp"])
    assert scopes == [ScopeKey(uf="SP", ano=2024)]

    sih = [_file("RDSP2401.dbc"), _file("RDSP2402.dbc"), _file("RDRJ2401.dbc")]
    sih_dir = REGISTRY["sih_aih_reduzida"].ftp_dir
    fake = _listing_by_path({sih_dir: sih})
    with patch("omnisus.sources.datasus_ftp.inventory._blocking_list", side_effect=fake):
        scopes = available("sih_aih_reduzida", ufs=["SP"], months=[2])
    assert scopes == [ScopeKey(uf="SP", ano=2024, mes=2)]


def test_available_rejects_uf_or_month_selectors_on_a_national_row() -> None:
    """A national row has no uf/month; filtering by them would silently return
    nothing, so it raises like the CLI does."""
    with pytest.raises(ValueError, match="national"):
        available("sinan_chagas", ufs=["SP"])


def test_tuberculose_spans_both_sinan_directories(monkeypatch: pytest.MonkeyPatch) -> None:
    """Real listings of 2026-09-22: TUBEBR01-19 in FINAIS, TUBEBR20-25 in PRELIM."""
    from tests.support.listings import serve_listings

    row = REGISTRY["sinan_tuberculose"]
    serve_listings(
        monkeypatch,
        {row.ftp_dir: "sinan_dados_finais", row.prelim_dir: "sinan_dados_prelim"},
    )
    releases = available_releases("sinan_tuberculose")
    assert releases == {
        **{ScopeKey(uf=None, ano=y): "final" for y in range(2001, 2020)},
        **{ScopeKey(uf=None, ano=y): "prelim" for y in range(2020, 2026)},
    }
