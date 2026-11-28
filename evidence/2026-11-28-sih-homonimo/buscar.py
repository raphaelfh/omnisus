"""List every document of a folder with its SHA-256 and the lines that name homonyms.

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-28-sih-homonimo/buscar.py DIR \
        > evidence/2026-11-28-sih-homonimo/documentos.csv

DIR holds the files downloaded from ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/, in
the folders they have there (Manuais/, Outros/, Portarias/portaria2004/ and the other
years, Programas/, SiteArquivos/).
One row per file and per member of a ZIP: SHA-256, bytes, pages (PDF) and the number of
text lines that match `hom[oôó]nim` or `duplicidade`, whatever the case. A file whose text
was not read has that column empty. PDF text comes from pypdf; .doc and .docx from the
macOS `textutil`; .htm loses its tags; .txt is read as Latin-1.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from pypdf import PdfReader

PATTERN = re.compile(r"hom[oôó]nim|duplicidade", re.IGNORECASE)


def text_of(name: str, raw: bytes) -> tuple[str | None, int | None]:
    """The text of a document and, for a PDF, its number of pages."""
    suffix = Path(name).suffix.lower()
    if raw[:5] == b"%PDF-":
        pages = PdfReader(io.BytesIO(raw)).pages
        return "\n".join(page.extract_text() or "" for page in pages), len(pages)
    if suffix in (".doc", ".docx"):
        with tempfile.NamedTemporaryFile(suffix=suffix) as file:
            file.write(raw)
            file.flush()
            command = ["textutil", "-convert", "txt", "-stdout", file.name]
            return subprocess.run(command, capture_output=True, check=True).stdout.decode(), None
    if suffix in (".htm", ".html"):
        return html.unescape(re.sub(r"<[^>]+>", "", raw.decode("latin-1"))), None
    if suffix == ".txt":
        return raw.decode("latin-1"), None
    return None, None


def rows_of(name: str, member: str, raw: bytes) -> list[list[object]]:
    text, pages = text_of(member or name, raw)
    matching = "" if text is None else sum(1 for line in text.splitlines() if PATTERN.search(line))
    rows = [[name, member, hashlib.sha256(raw).hexdigest(), len(raw), pages or "", matching]]
    if not member and name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for info in sorted(archive.infolist(), key=lambda item: item.filename):
                if not info.is_dir():
                    rows += rows_of(name, info.filename, archive.read(info))
    return rows


def main() -> None:
    folder = Path(sys.argv[1])
    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow(["file", "zip_member", "sha256", "bytes", "pdf_pages", "matching_lines"])
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        out.writerows(rows_of(path.relative_to(folder).as_posix(), "", path.read_bytes()))


if __name__ == "__main__":
    main()
