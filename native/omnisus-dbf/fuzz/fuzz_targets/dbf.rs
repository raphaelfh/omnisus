#![no_main]

use _native::{
    decode::{Encoding, number, text},
    reader::Reader,
};
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() > 64 * 1024 {
        return;
    }
    // Arbitrary header mutations and values exercise independent parse surfaces.
    for encoding in [
        Encoding::Latin1,
        Encoding::Cp1252,
        Encoding::Ascii,
        Encoding::Utf8,
    ] {
        if let Ok(mut reader) = Reader::new(data.to_vec(), encoding, 7) {
            while let Ok(Some(_)) = reader.next_batch() {}
            reader.close();
            reader.close();
        }
        let _ = text(data, encoding);
    }
    let _ = number(data);
});
