"""Cut a real DATASUS DBC down to a run of its records, or blank columns, as a valid DBC.

Used to build small real fixtures from files too large to commit
(AGENTS.md, zero-assumption policy, rule 2). The output keeps the original
DBF header (record count changed) and N consecutive records byte for byte,
from record ``--first`` (0-based, default 0). Record every excerpt in
tests/fixtures/FIXTURES.md.

    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --records 200
    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --records 5 --first 152398

``--blank COLUMN`` fills a column with spaces in every record, and
``--blank COLUMN:FLAG=VALUE`` only in the records whose ``FLAG`` column holds
``VALUE``. Fixtures carry no person identifier (AGENTS.md, "Never commit"), so a
column holding CPF or CNS in clear is blanked; every other byte stays as published.

    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --blank GESTOR_CPF
    uv run python scripts/dbc_excerpt.py SOURCE.dbc OUT.dbc --blank CPF_CNPJ:PF_PJ=1

The compressed body is a PKWare DCL stream with uncoded literals and a 4 KiB
window, the variant every blast.c port reads; its bytes differ from DATASUS's
own output. The 4-byte CRC after the header is written as zeros; DBC readers
ignore it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from omnisus.sources.datasus_ftp.dbc import (
    _DISTANCE,
    _END,
    _LENGTH,
    _LENGTH_BASE,
    _LENGTH_EXTRA,
    decompress_bytes,
)

_END_OF_FILE = b"\x1a"

_DICTIONARY_BITS = 6
_WINDOW = 64 << _DICTIONARY_BITS
_MAX_MATCH = _END - 1


def _canonical_codes(table: tuple[list[int], list[int]]) -> dict[int, tuple[int, int]]:
    """Symbol -> (code, bit length), in the canonical order the decoder's tables assume."""
    count, symbols = table
    codes: dict[int, tuple[int, int]] = {}
    first = index = 0
    for length in range(1, len(count)):
        for offset in range(count[length]):
            codes[symbols[index + offset]] = (first + offset, length)
        index += count[length]
        first = (first + count[length]) << 1
    return codes


_LENGTH_CODES = _canonical_codes(_LENGTH)
_DISTANCE_CODES = _canonical_codes(_DISTANCE)
_LENGTH_SYMBOL = {
    base + extra: (symbol, extra)
    for symbol, base in enumerate(_LENGTH_BASE)
    for extra in range(1 << _LENGTH_EXTRA[symbol])
}


def implode(data: bytes) -> bytes:
    """PKWare DCL stream holding ``data``: greedy LZ77 matches of 3 to 518 bytes, then the end."""
    out = bytearray([0, _DICTIONARY_BITS])  # literals not coded; 4 KiB window
    pending = 0
    count = 0

    def put(value: int, bits: int) -> None:
        # Bits are packed least significant first.
        nonlocal pending, count
        pending |= value << count
        count += bits
        while count >= 8:
            out.append(pending & 0xFF)
            pending >>= 8
            count -= 8

    def put_code(code: int, length: int) -> None:
        # The decoder reads a code from its first bit, each bit inverted.
        for shift in range(length - 1, -1, -1):
            put(((code >> shift) & 1) ^ 1, 1)

    def put_length(length: int) -> None:
        symbol, extra = _LENGTH_SYMBOL[length]
        put_code(*_LENGTH_CODES[symbol])
        put(extra, _LENGTH_EXTRA[symbol])

    recent: dict[bytes, list[int]] = {}
    position = 0
    while position < len(data):
        best_length = best_distance = 0
        limit = min(_MAX_MATCH, len(data) - position)
        for candidate in reversed(recent.get(data[position : position + 3], [])[-24:]):
            distance = position - candidate
            if distance > _WINDOW:
                break
            length = 0
            while length < limit and data[candidate + length] == data[position + length]:
                length += 1
            if length > best_length:
                best_length, best_distance = length, distance
                if length == limit:
                    break
        if best_length >= 3:
            put(1, 1)
            put_length(best_length)
            distance = best_distance - 1
            put_code(*_DISTANCE_CODES[distance >> _DICTIONARY_BITS])
            put(distance & ((1 << _DICTIONARY_BITS) - 1), _DICTIONARY_BITS)
            end = position + best_length
        else:
            put(0, 1)
            put(data[position], 8)
            end = position + 1
        for start in range(position, min(end, len(data) - 2)):
            seen = recent.setdefault(data[start : start + 3], [])
            seen.append(start)
            if len(seen) > 64:
                del seen[:32]
        position = end
    put(1, 1)
    put_length(_END)
    if count:
        out.append(pending & 0xFF)
    return bytes(out)


def dbc_from_dbf(dbf: bytes) -> bytes:
    """Wrap a DBF as a DBC: header, four CRC bytes (zeros), compressed body."""
    header_length = int.from_bytes(dbf[8:10], "little")
    return dbf[:header_length] + bytes(4) + implode(dbf[header_length:])


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


def _columns(dbf: bytes) -> dict[str, tuple[int, int]]:
    """Column name -> (offset in the record, width); offset 0 is the deletion flag."""
    header_length = int.from_bytes(dbf[8:10], "little")
    columns: dict[str, tuple[int, int]] = {}
    offset = 1
    for start in range(32, header_length - 1, 32):
        if dbf[start] == 0x0D:
            break
        name = dbf[start : start + 11].split(b"\0")[0].decode("ascii")
        columns[name] = (offset, dbf[start + 16])
        offset += dbf[start + 16]
    return columns


def blank_dbf(dbf: bytes, blanks: list[str]) -> bytes:
    """``dbf`` with each ``COLUMN`` or ``COLUMN:FLAG=VALUE`` of ``blanks`` filled with spaces."""
    columns = _columns(dbf)
    records = int.from_bytes(dbf[4:8], "little")
    header_length = int.from_bytes(dbf[8:10], "little")
    record_length = int.from_bytes(dbf[10:12], "little")
    out = bytearray(dbf)
    for blank in blanks:
        column, _, condition = blank.partition(":")
        flag, _, value = condition.partition("=")
        offset, width = columns[column]
        for record in range(records):
            start = header_length + record * record_length
            if flag:
                flag_offset, flag_width = columns[flag]
                cell = dbf[start + flag_offset : start + flag_offset + flag_width]
                if cell.decode("latin-1").strip() != value:
                    continue
            out[start + offset : start + offset + width] = b" " * width
    return bytes(out)


def excerpt_dbc(dbc: bytes, records: int, first: int = 0) -> bytes:
    """A DBC holding ``records`` records of ``dbc``, from record ``first``."""
    return dbc_from_dbf(excerpt_dbf(decompress_bytes(dbc), records, first))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--records", type=int, help="records to keep; all when omitted")
    parser.add_argument("--first", type=int, default=0, help="0-based index of the first record")
    parser.add_argument(
        "--blank", action="append", default=[], help="COLUMN or COLUMN:FLAG=VALUE to blank"
    )
    args = parser.parse_args()
    if args.records is None and not args.blank:
        parser.error("give --records, --blank or both")
    dbf = decompress_bytes(args.source.read_bytes())
    if args.records is not None:
        dbf = excerpt_dbf(dbf, args.records, args.first)
    args.output.write_bytes(dbc_from_dbf(blank_dbf(dbf, args.blank)))
    print(f"wrote {args.output} ({int.from_bytes(dbf[4:8], 'little')} records)")


if __name__ == "__main__":
    main()
