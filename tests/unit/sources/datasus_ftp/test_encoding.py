"""One byte a codec leaves undefined must not fail an import.

RDSP2308 (``AUD_JUST``, byte 0x90) and STSP2212 (``ALVARA``, byte 0x8F) failed
under the ``cp1252`` their dictionaries declared. Every DATASUS dictionary now
declares ``latin-1``, which maps each byte to the code point of the same value, so
``value.encode("latin-1")`` gives back the bytes of the file.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario


@pytest.mark.parametrize("dataset", sorted(REGISTRY))
def test_every_datasus_dictionary_decodes_every_byte(dataset: str) -> None:
    bytes(range(256)).decode(load_dicionario(dataset).encoding)


@pytest.mark.parametrize(
    ("dataset", "fixture", "scope", "column", "raw", "cp850"),
    [
        (
            "sih_aih_reduzida",
            "sih_rd_sp_2023_08_excerpt",
            {"ano": 2023, "uf": "SP", "mes": 8},
            "aud_just",
            b"PACIENTE REC\x90M NASCIDO ENCONTRADO NA ESTRADA RURAL",
            "PACIENTE RECÉM NASCIDO ENCONTRADO NA ESTRADA RURAL",
        ),
        (
            "cnes_estabelecimentos",
            "cnes_st_sp_2022_12_excerpt",
            {"ano": 2022, "uf": "SP", "mes": 12},
            "alvara",
            b".\x8f6018202200448734",
            ".Å6018202200448734",
        ),
    ],
)
def test_a_byte_cp1252_leaves_undefined_stages_and_keeps_its_value(
    tmp_path: Path, dbc_fixture, dataset, fixture, scope, column, raw, cp850
) -> None:
    out = tmp_path / "out.parquet"
    result = dbc_bytes_to_parquet(dbc_fixture(fixture).read_bytes(), out, dataset=dataset, **scope)
    assert result.rows == 5
    values = [v for v in pl.read_parquet(out)[column].to_list() if v and not v.isascii()]
    assert [v.encode("latin-1") for v in values] == [raw]
    assert values[0].encode("latin-1").decode("cp850") == cp850
