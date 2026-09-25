"""DATASUS DBC: a DBF header, a CRC32, then a PKWare DCL imploded body.

The decoder below is an altered port of Mark Adler's blast.c (zlib
contrib/blast, version 1.3). Altered: it reads an in-memory buffer, appends to a
growing output instead of a 4 KiB window, and raises InvalidDbcError instead of
returning codes. ``native/omnisus-dbf/src/dbc.rs`` carries the same port.
Original notice, from blast.h:

    Copyright (C) 2003, 2012, 2013 Mark Adler

    This software is provided 'as-is', without any express or implied
    warranty.  In no event will the author be held liable for any damages
    arising from the use of this software.

    Permission is granted to anyone to use this software for any purpose,
    including commercial applications, and to alter it and redistribute it
    freely, subject to the following restrictions:

    1. The origin of this software must not be misrepresented; you must not
       claim that you wrote the original software. If you use this software
       in a product, an acknowledgment in the product documentation would be
       appreciated but is not required.
    2. Altered source versions must be plainly marked as such, and must not be
       misrepresented as being the original software.
    3. This notice may not be removed or altered from any source distribution.
"""

from __future__ import annotations

import structlog

from omnisus.sources.datasus_ftp.native import Backend, load_native, requested_backend

logger = structlog.get_logger(__name__)

HINT_BYTES = 16 * 1024**2
"""Compressed size above which pure Python (about 10 MB of output per second) earns a hint."""

_MAXBITS = 13

_MIN_HEADER = 33
"""32 bytes of DBF header plus the 0x0D descriptor terminator: the smallest DBF header."""


class InvalidDbcError(ValueError):
    """The DBC payload is malformed or truncated."""


def _huffman(compact: bytes) -> tuple[list[int], list[int]]:
    """Canonical decoding tables (codes per length, symbols by length) from compact lengths.

    Each compact byte is a code length (low four bits) repeated (high four bits + 1) times.
    """
    lengths: list[int] = []
    for byte in compact:
        lengths += [byte & 15] * ((byte >> 4) + 1)
    count = [0] * (_MAXBITS + 1)
    for length in lengths:
        count[length] += 1
    offsets = [0] * (_MAXBITS + 1)
    for length in range(1, _MAXBITS):
        offsets[length + 1] = offsets[length] + count[length]
    symbols = [0] * len(lengths)
    for symbol, length in enumerate(lengths):
        if length:
            symbols[offsets[length]] = symbol
            offsets[length] += 1
    return count, symbols


_LITERAL = _huffman(
    bytes(
        [
            11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
            9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
            7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
            8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
            44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
            44, 173,
        ]
    )
)  # fmt: skip
_LENGTH = _huffman(bytes([2, 35, 36, 53, 38, 23]))
_DISTANCE = _huffman(bytes([2, 20, 53, 230, 247, 151, 248]))
_LENGTH_BASE = (3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264)
_LENGTH_EXTRA = (0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8)
_END = 519


def _explode(data: bytes, start: int) -> bytes:
    """Decode the imploded stream at ``data[start:]``; errors cite absolute offsets."""
    position = start
    buffer = 0
    available = 0

    def bits(need: int) -> int:
        # Bits are packed least significant first.
        nonlocal position, buffer, available
        while available < need:
            if position == len(data):
                raise InvalidDbcError(f"truncated DBC stream at byte {position}")
            buffer |= data[position] << available
            position += 1
            available += 8
        value = buffer & ((1 << need) - 1)
        buffer >>= need
        available -= need
        return value

    def decode(table: tuple[list[int], list[int]]) -> int:
        # Codes are stored bit-reversed and inverted relative to canonical order.
        # The hot path: bits are read inline rather than through bits(1).
        nonlocal position, buffer, available
        count, symbols = table
        code = first = index = 0
        for length in range(1, _MAXBITS + 1):
            if not available:
                if position == len(data):
                    raise InvalidDbcError(f"truncated DBC stream at byte {position}")
                buffer = data[position]
                position += 1
                available = 8
            code |= (buffer & 1) ^ 1
            buffer >>= 1
            available -= 1
            if code < first + count[length]:
                return symbols[index + code - first]
            index += count[length]
            first = (first + count[length]) << 1
            code <<= 1
        raise InvalidDbcError(f"corrupt DBC stream at byte {position}")

    literals_coded = bits(8)
    if literals_coded > 1:
        raise InvalidDbcError(f"corrupt DBC stream at byte {position}")
    dictionary_bits = bits(8)
    if dictionary_bits not in (4, 5, 6):
        raise InvalidDbcError(f"corrupt DBC stream at byte {position}")
    out = bytearray()
    while True:
        if not bits(1):
            out.append(decode(_LITERAL) if literals_coded else bits(8))
            continue
        symbol = decode(_LENGTH)
        length = _LENGTH_BASE[symbol] + bits(_LENGTH_EXTRA[symbol])
        if length == _END:
            return bytes(out)
        shift = 2 if length == 2 else dictionary_bits
        distance = (decode(_DISTANCE) << shift) + bits(shift) + 1
        if distance > len(out):
            raise InvalidDbcError(f"corrupt DBC stream at byte {position}")
        source = len(out) - distance
        if distance >= length:
            out += out[source : source + length]
        else:
            # Overlapping copy: each new byte may be one this copy just wrote.
            for index in range(source, source + length):
                out.append(out[index])


def _python_decompress(raw: bytes) -> bytes:
    if len(raw) < 10:
        raise InvalidDbcError("missing DBC header")
    header_size = int.from_bytes(raw[8:10], "little")
    if header_size < _MIN_HEADER:
        # Below 33 bytes the DBF integrity gates cannot read the record geometry.
        raise InvalidDbcError(f"DBF header size {header_size} is below the 33-byte minimum")
    if header_size + 4 > len(raw):
        raise InvalidDbcError("DBC header size exceeds file size")
    # The 4 bytes after the header are a CRC32 that DATASUS readers ignore.
    return raw[:header_size] + _explode(raw, header_size + 4)


def decompress_bytes(raw: bytes, backend: Backend | None = None) -> bytes:
    """DBF bytes from a DBC payload.

    ``backend``, else ``OMNISUS_DBC_BACKEND``, is ``python``, ``rust`` or ``auto``
    (the native package when installed). Both produce identical bytes.

    Raises:
        InvalidDbcError: the payload is malformed or truncated.
    """
    requested = requested_backend(backend, variable="OMNISUS_DBC_BACKEND", label="DBC")
    native = load_native(requested)
    logger.debug(
        "datasus_ftp.dbc_backend",
        backend="python" if native is None else "rust",
        requested=requested,
        version=None if native is None else native.__version__,
        fallback="extension_not_installed" if native is None and requested == "auto" else None,
    )
    if native is not None:
        try:
            return native.decompress_dbc(raw)
        except native.InvalidDbcError as exc:
            raise InvalidDbcError(str(exc)) from exc
    if requested == "auto" and len(raw) > HINT_BYTES:
        logger.info("datasus_ftp.dbc_python_backend_slow", compressed_bytes=len(raw))
    return _python_decompress(raw)
