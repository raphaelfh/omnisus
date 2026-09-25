use crate::{
    arrow,
    decode::Encoding,
    error::{Error, Result},
    header::Header,
};
use arrow_array::RecordBatch;

pub struct Reader {
    data: Vec<u8>,
    header: Header,
    encoding: Encoding,
    batch_rows: usize,
    next_record: usize,
    closed: bool,
}
impl Reader {
    pub fn new(data: Vec<u8>, encoding: Encoding, batch_rows: usize) -> Result<Self> {
        if batch_rows == 0 {
            return Err(Error::Value("batch_rows must be greater than zero".into()));
        }
        let header = Header::parse(&data, encoding)?;
        Ok(Self {
            data,
            header,
            encoding,
            batch_rows,
            next_record: 0,
            closed: false,
        })
    }

    pub fn next_batch(&mut self) -> Result<Option<RecordBatch>> {
        if self.closed {
            return Ok(None);
        }
        let result = self.read_batch();
        if !matches!(&result, Ok(Some(_))) {
            self.close();
        }
        result
    }

    fn read_batch(&mut self) -> Result<Option<RecordBatch>> {
        let capacity = self
            .batch_rows
            .min(self.header.record_count - self.next_record);
        let mut rows = Vec::with_capacity(capacity);
        while rows.len() < self.batch_rows && self.next_record < self.header.record_count {
            let start = self
                .next_record
                .checked_mul(self.header.record_len)
                .and_then(|n| self.header.header_len.checked_add(n))
                .ok_or_else(|| Error::Invalid("record offset overflow".into()))?;
            self.next_record += 1;
            match self.data.get(start) {
                Some(b' ') => rows.push(start),
                Some(b'*') => {}
                _ => {
                    return Err(Error::Invalid(
                        "invalid record marker or premature DBF EOF".into(),
                    ));
                }
            }
        }
        if rows.is_empty() {
            return Ok(None);
        }
        arrow::build(&self.data, &self.header, self.encoding, &rows).map(Some)
    }

    pub fn close(&mut self) {
        self.closed = true;
        self.data = Vec::new();
        self.header.fields = Vec::new();
    }
}
