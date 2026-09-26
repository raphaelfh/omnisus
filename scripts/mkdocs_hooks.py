"""MkDocs hook: the site names the package version it documents.

The version has one home, ``src/omnisus/_version.py``; the header and footer read it
at build time, so a release never needs a docs edit to say which version it is.
"""

from __future__ import annotations

import runpy
from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parents[1] / "src" / "omnisus" / "_version.py"


def on_config(config):
    version = runpy.run_path(str(VERSION_FILE))["__version__"]
    config["site_name"] = f"omnisus {version}"
    config["copyright"] = f"omnisus {version} · MIT · (c) 2026 Raphael Federicci"
    return config
