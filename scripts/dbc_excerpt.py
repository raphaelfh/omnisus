"""Cut a real DATASUS DBC down to a run of its records, as a valid DBC.

Used to build small real fixtures from files too large to commit
(AGENTS.md, zero-assumption policy, rule 2). The output keeps the original
DBF header (record count changed) and N consecutive records byte for byte,
from record ``--first`` (0-based, default 0). Record every excerpt in
tests/fixtures/FIXTURES.md.

    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --records 200
    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --records 5 --first 152398

The compressed body uses only uncoded literals: larger than DATASUS's own
output, but a valid PKWare DCL stream that every blast.c port reads. The
4-byte CRC after the header is written as zeros; DBC readers ignore it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from omnisus.sources.datasus_ftp.dbc import decompress_bytes

_END_OF_FILE = b"\x1a"


def implode_literals(data: bytes) -> bytes:
    """PKWare DCL stream holding ``data`` as uncoded literals, then the end marker."""
    out = bytearray([0, 4])  # literals not coded; dictionary code 4 (unused)
    pending = 0
    count = 0

    def put(value: int, bits: int) -> None:
        nonlocal pending, count
        pending |= value << count
        count += bits
        while count >= 8:
            out.append(pending & 0xFF)
            pending >>= 8
            count -= 8

    for byte in data:
        put(0, 1)  # literal follows
        put(byte, 8)
    put(1, 1)  # length/distance follows
    put(0, 7)  # length symbol 15, stored inverted
    put(0xFF, 8)  # extra bits: 264 + 255 = 519, the end marker
    if count:
        out.append(pending & 0xFF)
    return bytes(out)


def dbc_from_dbf(dbf: bytes) -> bytes:
    """Wrap a DBF as a DBC: header, four CRC bytes (zeros), compressed body."""
    header_length = int.from_bytes(dbf[8:10], "little")
    return dbf[:header_length] + bytes(4) + implode_literals(dbf[header_length:])


def excerpt_dbf(dbf: bytes, records: int, first: int = 0) -> bytes:
    """The DBF header (record count set to ``records``) and ``records`` records from ``first``."""
    available = int.from_bytes(dbf[4:8], "little")
    if records < 1 or first < 0 or first + records > available:
        raise ValueError(
            f"asked for records {first}..{first + records - 1}; the file has only {available}"
        )
    header_length = int.from_bytes(dbf[8:10], "little")
    record_length = int.from_bytes(dbf[10:12], "little")
    header = dbf[:4] + records.to_bytes(4, "little") + dbf[8:header_length]
    start = header_length + first * record_length
    body = dbf[start : start + records * record_length]
    return header + body + _END_OF_FILE


def excerpt_dbc(dbc: bytes, records: int, first: int = 0) -> bytes:
    """A DBC holding ``records`` records of ``dbc``, from record ``first``."""
    return dbc_from_dbf(excerpt_dbf(decompress_bytes(dbc), records, first))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--records", type=int, required=True)
    parser.add_argument("--first", type=int, default=0, help="0-based index of the first record")
    args = parser.parse_args()
    args.output.write_bytes(excerpt_dbc(args.source.read_bytes(), args.records, args.first))
    print(f"wrote {args.output} ({args.records} records from record {args.first})")


if __name__ == "__main__":
    main()
