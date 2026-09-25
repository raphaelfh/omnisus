#[derive(Debug, PartialEq)]
pub enum Error {
    Unsupported(String),
    Invalid(String),
    Value(String),
    Type(String),
    Decode {
        encoding: &'static str,
        data: Vec<u8>,
        start: usize,
        end: usize,
    },
}

pub type Result<T> = std::result::Result<T, Error>;
