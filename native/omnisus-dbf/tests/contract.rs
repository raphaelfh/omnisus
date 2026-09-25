use _native::decode::{Encoding, Number, number, text};
use _native::error::Error;

#[test]
fn character_preserves_leading_space_empty_and_latin1_controls() {
    assert_eq!(text(b" 001 \0", Encoding::Latin1).unwrap(), " 001");
    assert_eq!(text(b" \0  ", Encoding::Latin1).unwrap(), "");
    assert_eq!(text(b"\x81", Encoding::Latin1).unwrap(), "\u{81}");
}

#[test]
fn strict_encodings_decode_or_return_the_original_invalid_bytes() {
    assert_eq!(text(b"\x80\x93", Encoding::Cp1252).unwrap(), "€“");
    assert!(matches!(
        text(b"\x81", Encoding::Cp1252),
        Err(Error::Decode {
            start: 0,
            end: 1,
            ..
        })
    ));
    assert!(matches!(
        text(b"\xff", Encoding::Ascii),
        Err(Error::Decode { .. })
    ));
    assert!(matches!(
        text(b"\xc3", Encoding::Utf8),
        Err(Error::Decode { .. })
    ));
    assert_eq!(text("café".as_bytes(), Encoding::Utf8).unwrap(), "café");
}

#[test]
fn integer_parsing_never_rounds_through_float() {
    for (raw, value) in [
        (&b"9007199254740993"[..], 9007199254740993),
        (b"1152921504606846977", 1152921504606846977),
        (b"-9223372036854775808", i64::MIN),
        (b"+000_012", 12),
    ] {
        assert_eq!(number(raw).unwrap(), Number::Int(value));
    }
    assert!(matches!(
        number(b"9223372036854775808"),
        Err(Error::Value(_))
    ));
}

#[test]
fn numeric_padding_decimal_specials_and_invalid_syntax_match_python() {
    for raw in [b"".as_slice(), b" \t\r\n", b"**\0", b"* *", b"\0 \0"] {
        assert_eq!(number(raw).unwrap(), Number::Null);
    }
    for (raw, value) in [
        (b" \t*1,5*\n".as_slice(), 1.5),
        (b"-1.5e+2", -150.0),
        (b".5", 0.5),
        (b"1_2.3_4", 12.34),
        (b"1e999", f64::INFINITY),
        (b"-INFINITY", f64::NEG_INFINITY),
    ] {
        assert_eq!(number(raw).unwrap(), Number::Float(value));
    }
    assert!(matches!(number(b"+NaN"), Ok(Number::Float(v)) if v.is_nan()));
    for raw in [
        b"12x".as_slice(),
        b"1__2",
        b"_1",
        b"1_",
        b"1,_2",
        b"+",
        b"1 2",
        b"\x851",
    ] {
        assert!(matches!(number(raw), Err(Error::Value(_))), "{raw:?}");
    }
}

#[test]
fn numeric_whitespace_includes_vertical_tab_and_nan_preserves_sign() {
    assert_eq!(number(b"\x0b42\x0b").unwrap(), Number::Int(42));
    assert_eq!(number(b" \t1.5\x0b").unwrap(), Number::Float(1.5));
    assert_eq!(number(b"\x0b\x0c \t\r\n").unwrap(), Number::Null);
    assert!(matches!(number(b"-NaN"),Ok(Number::Float(v)) if v.is_nan() && v.is_sign_negative()));
}
