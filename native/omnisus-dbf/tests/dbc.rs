use _native::dbc::{DbcError, decompress, explode};
use proptest::prelude::*;

// zlib contrib/blast/test: test.pk decompresses to test.txt.
const VECTOR: [u8; 8] = [0x00, 0x04, 0x82, 0x24, 0x25, 0x8f, 0x80, 0x7f];
const TEXT: &[u8] = b"AIAIAIAIAIAIA";
const HEADER: usize = 33;

/// A minimal DBC: a 33-byte DBF header declaring its own size, a CRC32, the body.
fn framed(body: &[u8]) -> Vec<u8> {
    let mut raw = vec![0; 8];
    raw.extend_from_slice(&(HEADER as u16).to_le_bytes());
    raw.extend_from_slice(&[0; HEADER - 10]);
    raw.extend_from_slice(&[0; 4]);
    raw.extend_from_slice(body);
    raw
}

#[test]
fn zlib_blast_vector() {
    assert_eq!(explode(&VECTOR, 0).unwrap(), TEXT);
    let mut expected = framed(&[])[..HEADER].to_vec();
    expected.extend_from_slice(TEXT);
    assert_eq!(decompress(&framed(&VECTOR)).unwrap(), expected);
}

#[test]
fn malformed_input_names_the_problem() {
    let short = [&[0u8; 8][..], &32u16.to_le_bytes()].concat();
    let too_big = [&[0u8; 8][..], &100u16.to_le_bytes()].concat();
    let cases: [(&[u8], &str); 6] = [
        (b"", "missing DBC header"),
        (&[0; 9], "missing DBC header"),
        (&short, "DBF header size 32 is below the 33-byte minimum"),
        (&too_big, "DBC header size exceeds file size"),
        (&framed(&[2, 4]), "corrupt DBC stream at byte 38"),
        (&framed(&[0, 7]), "corrupt DBC stream at byte 39"),
    ];
    for (raw, message) in cases {
        assert_eq!(decompress(raw).unwrap_err().to_string(), message);
    }
}

#[test]
fn every_truncation_is_reported_where_input_ends() {
    let raw = framed(&VECTOR);
    for end in HEADER + 4..raw.len() {
        assert_eq!(decompress(&raw[..end]), Err(DbcError::Truncated(end)));
    }
}

proptest! {
    #[test]
    fn arbitrary_bytes_never_panic(body in proptest::collection::vec(any::<u8>(), 0..2048)) {
        let _ = decompress(&body);
        let _ = decompress(&framed(&body));
    }
}
