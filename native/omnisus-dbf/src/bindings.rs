use crate::{dbc, decode::Encoding, error::Error, reader::Reader};
use arrow_pyarrow::IntoPyArrow;
use pyo3::{
    create_exception,
    exceptions::{PyLookupError, PyTypeError, PyUnicodeDecodeError, PyValueError},
    prelude::*,
    types::{PyBytes, PyModule},
};

create_exception!(
    omnisus_dbf,
    UnsupportedDbfError,
    PyValueError,
    "DBF format or encoding is outside the native reader contract."
);
create_exception!(
    omnisus_dbf,
    InvalidDbfError,
    PyValueError,
    "DBF is malformed or truncated."
);
create_exception!(
    omnisus_dbf,
    InvalidDbcError,
    PyValueError,
    "DBC is malformed or truncated."
);

fn python_error(py: Python<'_>, error: Error) -> PyErr {
    match error {
        Error::Unsupported(message) => UnsupportedDbfError::new_err(message),
        Error::Invalid(message) => InvalidDbfError::new_err(message),
        Error::Value(message) => PyValueError::new_err(message),
        Error::Type(message) => PyTypeError::new_err(message),
        Error::Decode {
            encoding,
            data,
            start,
            end,
        } => PyUnicodeDecodeError::new_err((
            encoding,
            PyBytes::new(py, &data).unbind(),
            start,
            end,
            "invalid byte sequence",
        )),
    }
}

/// Owns the DBF allocation; all exported Arrow arrays own their own buffers.
#[pyclass(module = "omnisus_dbf._native")]
pub struct DbfBatchReader {
    reader: Reader,
}

#[pymethods]
impl DbfBatchReader {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        if let Err(error) = py.check_signals() {
            self.reader.close();
            return Err(error);
        }
        let batch = py
            .detach(|| self.reader.next_batch())
            .map_err(|e| python_error(py, e))?;
        if let Err(error) = py.check_signals() {
            self.reader.close();
            return Err(error);
        }
        match batch {
            None => Ok(None),
            Some(batch) => match batch.into_pyarrow(py) {
                Ok(value) => Ok(Some(value.unbind())),
                Err(error) => {
                    self.reader.close();
                    Err(error)
                }
            },
        }
    }

    fn close(&mut self, py: Python<'_>) {
        py.detach(|| self.reader.close());
    }
}

#[pyfunction(signature=(data, *, encoding, batch_rows))]
fn open_reader(
    py: Python<'_>,
    data: &Bound<'_, PyBytes>,
    encoding: &str,
    batch_rows: isize,
) -> PyResult<DbfBatchReader> {
    if batch_rows <= 0 {
        return Err(PyValueError::new_err(
            "batch_rows must be greater than zero",
        ));
    }
    // Ask Python once to resolve its full set of codec aliases; decoding itself is native.
    let codec = match PyModule::import(py, "codecs")?.call_method1("lookup", (encoding,)) {
        Ok(codec) => codec,
        Err(error) if error.is_instance_of::<PyLookupError>(py) => {
            return Err(UnsupportedDbfError::new_err(format!(
                "encoding {encoding:?} is not supported"
            )));
        }
        Err(error) => return Err(error),
    };
    let canonical: String = codec.getattr("name")?.extract()?;
    let encoding = Encoding::from_name(&canonical).map_err(|e| python_error(py, e))?;
    // Never hold a borrowed Python buffer across detach().
    let owned = data.as_bytes().to_vec();
    let reader = py
        .detach(move || Reader::new(owned, encoding, batch_rows as usize))
        .map_err(|e| python_error(py, e))?;
    Ok(DbfBatchReader { reader })
}

#[pyfunction]
fn decompress_dbc<'py>(
    py: Python<'py>,
    data: &Bound<'py, PyBytes>,
) -> PyResult<Bound<'py, PyBytes>> {
    // Never hold a borrowed Python buffer across detach().
    let owned = data.as_bytes().to_vec();
    let out = py
        .detach(move || dbc::decompress(&owned))
        .map_err(|e| InvalidDbcError::new_err(e.to_string()))?;
    Ok(PyBytes::new(py, &out))
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("API_VERSION", 2)?;
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add(
        "UnsupportedDbfError",
        module.py().get_type::<UnsupportedDbfError>(),
    )?;
    module.add("InvalidDbfError", module.py().get_type::<InvalidDbfError>())?;
    module.add_class::<DbfBatchReader>()?;
    module.add("InvalidDbcError", module.py().get_type::<InvalidDbcError>())?;
    module.add_function(wrap_pyfunction!(decompress_dbc, module)?)?;
    module.add_function(wrap_pyfunction!(open_reader, module)?)?;
    Ok(())
}
