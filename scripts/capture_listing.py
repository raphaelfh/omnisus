"""Save one DATASUS directory's raw LIST lines as a gzipped test fixture.

    uv run python scripts/capture_listing.py /dissemin/publicos/SIM/CID10/DORES \
        tests/fixtures/listings/sim_cid10_dores.txt.gz [--keep REGEX]

Prints the values for the fixture's row in tests/fixtures/FIXTURES.md: the
SHA-256 of the full listing text, the number of lines kept, and the capture time.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from omnisus.sources.datasus_ftp.inventory import _blocking_list


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory")
    parser.add_argument("output", type=Path)
    parser.add_argument("--keep", help="keep only lines whose file name matches this regex")
    args = parser.parse_args()
    lines = _blocking_list(args.directory, 120.0)
    digest = hashlib.sha256("\n".join(lines).encode("latin-1")).hexdigest()
    if args.keep:
        pattern = re.compile(args.keep)
        lines = [line for line in lines if pattern.search(" ".join(line.split()[3:]))]
    args.output.write_bytes(gzip.compress(("\n".join(lines) + "\n").encode("latin-1"), mtime=0))
    captured = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M")
    print(f"source_sha256={digest} records={len(lines)} captured={captured}")


if __name__ == "__main__":
    main()
