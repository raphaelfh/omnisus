mod arrow;
pub mod dbc;
pub mod decode;
pub mod error;
pub mod header;
pub mod reader;

#[cfg(feature = "python")]
mod bindings;

#[cfg(feature = "python")]
#[pyo3::pymodule]
fn _native(module: &pyo3::Bound<'_, pyo3::types::PyModule>) -> pyo3::PyResult<()> {
    bindings::register(module)
}
