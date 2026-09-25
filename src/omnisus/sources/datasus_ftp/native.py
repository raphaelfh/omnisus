"""Optional ``omnisus-dbf`` lookup shared by the DBF reader and DBC decompressor."""

from __future__ import annotations

import os
from importlib import import_module
from types import ModuleType
from typing import Literal

Backend = Literal["python", "rust", "auto"]
API_VERSION = 2


def requested_backend(backend: Backend | None, *, variable: str, label: str) -> str:
    """The explicit backend, else the environment variable, else ``auto``."""
    requested = backend if backend is not None else os.environ.get(variable, "auto")
    if requested not in ("python", "rust", "auto"):
        raise ValueError(f"{label} backend must be python, rust or auto")
    return requested


def load_native(requested: str) -> ModuleType | None:
    """The native module, or None when Python decodes.

    Only ``auto`` tolerates an absent package. A missing transitive dependency or
    an incompatible API is always an error, never a silent fallback.
    """
    if requested == "python":
        return None
    try:
        native = import_module("omnisus_dbf")
    except ModuleNotFoundError as exc:
        if exc.name != "omnisus_dbf":
            raise
        if requested == "rust":
            raise ImportError("Rust backend requires the optional omnisus-dbf package") from exc
        return None
    if getattr(native, "API_VERSION", None) != API_VERSION:
        raise ImportError(f"Incompatible omnisus-dbf API; expected API_VERSION={API_VERSION}")
    return native
