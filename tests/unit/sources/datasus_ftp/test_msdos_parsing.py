"""MS-DOS LIST parsing.

Every GOLDEN line is verbatim output from ftp.datasus.gov.br captured
2026-09-09. DATASUS answers `500 Command not understood` to MLSD, so LIST
plus this parser is the only way in.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from omnisus.sources.datasus_ftp.inventory import Listing, _parse_msdos_line

PARENT = "/dissemin/publicos/SIM/CID10/DORES"

# fmt: off
GOLDEN: list[tuple[str, str, bool, int, datetime]] = [
    # line,                                                              name,               is_dir, size,        modified
    ("01-31-20  02:48PM                76107 DOAC1996.dbc",              "DOAC1996.dbc",     False,  76107,       datetime(2020, 1, 31, 14, 48)),
    ("12-23-25  03:48PM               874197 DOTO2024.dbc",              "DOTO2024.dbc",     False,  874197,      datetime(2025, 12, 23, 15, 48)),
    ("12-19-24  11:56AM               817587 DOTO2023.dbc",              "DOTO2023.dbc",     False,  817587,      datetime(2024, 12, 19, 11, 56)),
    ("02-24-18  07:38AM       <DIR>          199407_200712",             "199407_200712",    True,   0,           datetime(2018, 2, 24, 7, 38)),
    ("08-18-10  01:24PM       <DIR>          Anteriores_a_1994",         "Anteriores_a_1994", True,  0,           datetime(2010, 8, 18, 13, 24)),
    # 12 GB — exceeds 32 bits
    ("06-07-26  01:54PM          12000440320 base_aih1.duck",            "base_aih1.duck",   False,  12000440320, datetime(2026, 6, 7, 13, 54)),
]
# fmt: on


@pytest.mark.parametrize(
    ("line", "name", "is_dir", "size", "modified"), GOLDEN, ids=[g[1] for g in GOLDEN]
)
def test_parse_golden_lines(
    line: str, name: str, is_dir: bool, size: int, modified: datetime
) -> None:
    entry = _parse_msdos_line(line, PARENT)
    assert entry is not None
    assert entry.name == name
    assert entry.is_dir is is_dir
    assert entry.size_bytes == size
    assert entry.modified == modified
    assert entry.parent == PARENT
    assert entry.path == f"{PARENT}/{name}"


def test_names_with_spaces_are_preserved() -> None:
    """DATASUS directory names contain spaces; naive split()[3] truncates."""
    entry = _parse_msdos_line("02-24-18  07:38AM       <DIR>          Dados Antigos 1994", PARENT)
    assert entry is not None
    assert entry.name == "Dados Antigos 1994"


def test_size_exceeds_32_bits() -> None:
    entry = _parse_msdos_line(GOLDEN[-1][0], PARENT)
    assert entry is not None
    assert entry.size_bytes > 2**32


def test_mtime_two_digit_year_uses_the_posix_pivot_not_the_filename_pivot() -> None:
    """strptime %y maps 00-68 -> 2000s, 69-99 -> 1900s. That is NOT the
    filename codec's pivot (80), and the two must not be conflated."""
    entry = _parse_msdos_line("01-02-98  10:00AM                  123 OLD.dbc", PARENT)
    assert entry is not None
    assert entry.modified.year == 1998


@pytest.mark.parametrize(
    "line",
    [
        "",
        "   ",
        "garbage",
        "01-31-20  02:48PM",  # too few fields
        "01-31-20  02:48PM   NOTANUMBER file.dbc",  # size neither int nor <DIR>
        "99-99-99  02:48PM                123 x.dbc",  # impossible date
    ],
)
def test_malformed_lines_return_none(line: str) -> None:
    assert _parse_msdos_line(line, PARENT) is None


def test_parent_with_trailing_slash_does_not_double_it() -> None:
    entry = _parse_msdos_line(GOLDEN[0][0], "/dissemin/publicos/")
    assert entry is not None
    assert entry.path == "/dissemin/publicos/DOAC1996.dbc"


def test_listing_splits_files_and_dirs_and_is_frozen() -> None:
    entries = tuple(e for e in (_parse_msdos_line(g[0], PARENT) for g in GOLDEN) if e is not None)
    listing = Listing(entries=entries, skipped=2, path=PARENT)
    assert len(listing.files) == 4
    assert len(listing.dirs) == 2
    assert listing.skipped == 2
    with pytest.raises((AttributeError, TypeError)):
        listing.skipped = 0  # type: ignore[misc]


def test_ftp_entry_is_frozen() -> None:
    entry = _parse_msdos_line(GOLDEN[0][0], PARENT)
    assert entry is not None
    with pytest.raises((AttributeError, TypeError)):
        entry.name = "other"  # type: ignore[misc]
