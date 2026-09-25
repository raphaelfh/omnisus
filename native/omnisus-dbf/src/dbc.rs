//! DATASUS DBC: a DBF header, a CRC32, then a PKWare DCL imploded body.
//!
//! The decoder is an altered port of Mark Adler's blast.c (zlib contrib/blast,
//! version 1.3). Altered: it reads a slice, appends to a growing `Vec` instead
//! of a 4 KiB window, and returns `DbcError` instead of integer codes.
//! `src/omnisus/sources/datasus_ftp/dbc.py` carries the same port; both must
//! produce identical bytes and messages. Original notice, from blast.h:
//!
//!   Copyright (C) 2003, 2012, 2013 Mark Adler
//!
//!   This software is provided 'as-is', without any express or implied
//!   warranty.  In no event will the author be held liable for any damages
//!   arising from the use of this software.
//!
//!   Permission is granted to anyone to use this software for any purpose,
//!   including commercial applications, and to alter it and redistribute it
//!   freely, subject to the following restrictions:
//!
//!   1. The origin of this software must not be misrepresented; you must not
//!      claim that you wrote the original software. If you use this software
//!      in a product, an acknowledgment in the product documentation would be
//!      appreciated but is not required.
//!   2. Altered source versions must be plainly marked as such, and must not be
//!      misrepresented as being the original software.
//!   3. This notice may not be removed or altered from any source distribution.

use std::{fmt, sync::LazyLock};

#[derive(Debug, PartialEq, Eq)]
pub enum DbcError {
    MissingHeader,
    ShortHeader(usize),
    HeaderSize,
    Corrupt(usize),
    Truncated(usize),
}

impl fmt::Display for DbcError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingHeader => f.write_str("missing DBC header"),
            Self::ShortHeader(size) => {
                write!(f, "DBF header size {size} is below the 33-byte minimum")
            }
            Self::HeaderSize => f.write_str("DBC header size exceeds file size"),
            Self::Corrupt(at) => write!(f, "corrupt DBC stream at byte {at}"),
            Self::Truncated(at) => write!(f, "truncated DBC stream at byte {at}"),
        }
    }
}

const MAXBITS: usize = 13;
/// 32 bytes of DBF header plus the 0x0D descriptor terminator: the smallest DBF header.
const MIN_HEADER: usize = 33;
const END: usize = 519;
const LENGTH_BASE: [usize; 16] = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264];
const LENGTH_EXTRA: [u32; 16] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8];

/// Canonical decoding tables: codes per length, and symbols ordered by length.
struct Huffman {
    count: [usize; MAXBITS + 1],
    symbols: Vec<usize>,
}

impl Huffman {
    /// Each compact byte is a code length (low four bits) repeated (high four bits + 1) times.
    fn new(compact: &[u8]) -> Self {
        let lengths: Vec<usize> = compact
            .iter()
            .flat_map(|&byte| {
                std::iter::repeat_n(usize::from(byte & 15), usize::from(byte >> 4) + 1)
            })
            .collect();
        let mut count = [0; MAXBITS + 1];
        for &length in &lengths {
            count[length] += 1;
        }
        let mut offsets = [0; MAXBITS + 1];
        for length in 1..MAXBITS {
            offsets[length + 1] = offsets[length] + count[length];
        }
        let mut symbols = vec![0; lengths.len()];
        for (symbol, &length) in lengths.iter().enumerate() {
            if length != 0 {
                symbols[offsets[length]] = symbol;
                offsets[length] += 1;
            }
        }
        Self { count, symbols }
    }
}

static LITERAL: LazyLock<Huffman> = LazyLock::new(|| {
    Huffman::new(&[
        11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8, 9, 7, 6, 7, 8, 7, 6,
        55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5, 7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7,
        9, 8, 25, 11, 8, 11, 9, 12, 8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24,
        10, 27, 44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45, 44, 173,
    ])
});
static LENGTH: LazyLock<Huffman> = LazyLock::new(|| Huffman::new(&[2, 35, 36, 53, 38, 23]));
static DISTANCE: LazyLock<Huffman> =
    LazyLock::new(|| Huffman::new(&[2, 20, 53, 230, 247, 151, 248]));

/// Least-significant-bit-first reader over a slice; offsets are absolute.
struct Bits<'a> {
    data: &'a [u8],
    position: usize,
    buffer: u32,
    available: u32,
}

impl Bits<'_> {
    fn take(&mut self, need: u32) -> Result<usize, DbcError> {
        while self.available < need {
            let byte = *self
                .data
                .get(self.position)
                .ok_or(DbcError::Truncated(self.position))?;
            self.buffer |= u32::from(byte) << self.available;
            self.position += 1;
            self.available += 8;
        }
        let value = self.buffer & ((1 << need) - 1);
        self.buffer >>= need;
        self.available -= need;
        Ok(value as usize)
    }

    /// Codes are stored bit-reversed and inverted relative to canonical order.
    fn decode(&mut self, table: &Huffman) -> Result<usize, DbcError> {
        let (mut code, mut first, mut index) = (0, 0, 0);
        for length in 1..=MAXBITS {
            code |= self.take(1)? ^ 1;
            let count = table.count[length];
            if code < first + count {
                return Ok(table.symbols[index + code - first]);
            }
            index += count;
            first = (first + count) << 1;
            code <<= 1;
        }
        Err(DbcError::Corrupt(self.position))
    }
}

/// Decode the imploded stream at `data[start..]`.
pub fn explode(data: &[u8], start: usize) -> Result<Vec<u8>, DbcError> {
    let mut bits = Bits {
        data,
        position: start,
        buffer: 0,
        available: 0,
    };
    let literals_coded = bits.take(8)?;
    if literals_coded > 1 {
        return Err(DbcError::Corrupt(bits.position));
    }
    let dictionary_bits = bits.take(8)?;
    if !(4..=6).contains(&dictionary_bits) {
        return Err(DbcError::Corrupt(bits.position));
    }
    let mut out = Vec::new();
    loop {
        if bits.take(1)? == 0 {
            let literal = if literals_coded == 1 {
                bits.decode(&LITERAL)?
            } else {
                bits.take(8)?
            };
            out.push(literal as u8);
            continue;
        }
        let symbol = bits.decode(&LENGTH)?;
        let length = LENGTH_BASE[symbol] + bits.take(LENGTH_EXTRA[symbol])?;
        if length == END {
            return Ok(out);
        }
        let shift = if length == 2 {
            2
        } else {
            dictionary_bits as u32
        };
        let distance = (bits.decode(&DISTANCE)? << shift) + bits.take(shift)? + 1;
        if distance > out.len() {
            return Err(DbcError::Corrupt(bits.position));
        }
        let source = out.len() - distance;
        if distance >= length {
            out.extend_from_within(source..source + length);
        } else {
            // Overlapping copy: each new byte may be one this copy just wrote.
            for _ in 0..length {
                out.push(out[out.len() - distance]);
            }
        }
    }
}

/// DBF bytes from a DBC payload: the header is kept, the CRC32 after it is ignored.
pub fn decompress(raw: &[u8]) -> Result<Vec<u8>, DbcError> {
    let size = raw.get(8..10).ok_or(DbcError::MissingHeader)?;
    let header_size = usize::from(u16::from_le_bytes([size[0], size[1]]));
    if header_size < MIN_HEADER {
        // Below 33 bytes the DBF integrity gates cannot read the record geometry.
        return Err(DbcError::ShortHeader(header_size));
    }
    if header_size + 4 > raw.len() {
        return Err(DbcError::HeaderSize);
    }
    let mut out = raw[..header_size].to_vec();
    out.extend(explode(raw, header_size + 4)?);
    Ok(out)
}
