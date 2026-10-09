"""Tests for Lake.bootstrap_auxiliares over the packaged zip.

The zip is built by ``scripts/build_bootstrap_zip.py`` from hashed DATASUS files in
``SIM/CID10/TABELAS`` and the ``CBO2002.CNV`` and ``CID10GRUPOS.CNV`` members;
its ``manifest.json`` names each digest.
"""

from __future__ import annotations

import io
import json
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest

from omnisus.lake import Lake
from omnisus.metadata import sources_registry

TABLES = {"aux_uf", "aux_municipios", "aux_cid10", "aux_ocupacoes", "aux_paises"}


@pytest.fixture(scope="module")
def lake(tmp_path_factory: pytest.TempPathFactory):
    path = tmp_path_factory.mktemp("bootstrap")
    lake = Lake.local(f"ducklake:{path}/x.ducklake")
    lake.bootstrap_auxiliares()
    yield lake
    lake.close()


def one(lake: Lake, sql: str, *args: object) -> tuple:
    row = lake.connect().execute(sql, list(args)).fetchone()
    assert row is not None, sql
    return row


def test_bootstrap_loads_the_five_vocabularies(lake: Lake) -> None:
    assert set(lake.tables()) >= TABLES
    counts = {t: one(lake, f"SELECT count(*) FROM lake.{t}")[0] for t in sorted(TABLES)}
    assert counts == {
        "aux_cid10": 14257,
        "aux_municipios": 5652,
        "aux_ocupacoes": 2458 + 3564,
        "aux_paises": 264,
        "aux_uf": 27,
    }


def test_municipalities_carry_coordinates_and_successors(lake: Lake) -> None:
    assert one(
        lake,
        "SELECT codigo_6, nome, uf_codigo, latitude, longitude, altitude, area, "
        "regiao_saude, situacao FROM lake.aux_municipios WHERE codigo_ibge = '1100205'",
    ) == ("110020", "Porto Velho", "11", -8.762, -63.904, 85, 34082.366, "1104", "ATIVO")
    assert one(
        lake,
        "SELECT situacao, ano_extincao, sucessor FROM lake.aux_municipios "
        "WHERE codigo_ibge = '4314530'",
    ) == ("EXTIN", 2002, "4302105")
    # 0°, 0° lies in the Atlantic: the rows CADMUN fills with zeros carry NULL.
    assert lake.connect().execute(
        "SELECT situacao, count(*) FROM lake.aux_municipios WHERE latitude IS NULL "
        "GROUP BY 1 ORDER BY 1"
    ).fetchall() == [("ATIVO", 4), ("IGNOR", 27), ("TRANS", 60)]


def test_cid10_is_complete_with_chapters(lake: Lake) -> None:
    assert one(lake, "SELECT descricao, capitulo FROM lake.aux_cid10 WHERE codigo = 'B571'") == (
        "Form aguda doenc de Chagas s/compr cardiaco",
        1,
    )
    assert one(lake, "SELECT descricao FROM lake.aux_cid10 WHERE codigo = 'G904'") == (
        "Disreflexia autonômica",
    )
    assert one(lake, "SELECT count(DISTINCT capitulo) FROM lake.aux_cid10") == (22,)


def test_cid10_has_blocks_from_the_official_sih_group_table(lake: Lake) -> None:
    """AGENTS.md rule 2: real DATASUS CID-10 rows and the hashed TAB_SIH CNV."""
    assert one(
        lake,
        "SELECT bloco, bloco_descricao FROM lake.aux_cid10 WHERE codigo = 'B571'",
    ) == ("B50-B64", "Doenças devidas a protozoários")
    assert one(
        lake,
        "SELECT bloco, bloco_descricao FROM lake.aux_cid10 WHERE codigo = 'E119'",
    ) == ("E10-E14", "Diabetes mellitus")
    assert one(
        lake,
        "SELECT bloco, bloco_descricao FROM lake.aux_cid10 WHERE codigo = 'O930'",
    ) == (None, None)
    assert one(
        lake,
        "SELECT bloco, bloco_descricao FROM lake.aux_cid10 WHERE codigo = 'U071'",
    ) == (None, None)
    assert one(
        lake,
        "SELECT count(*), count(*) FILTER (WHERE bloco IS NULL), "
        "count(DISTINCT bloco) FROM lake.aux_cid10",
    ) == (14257, 15, 263)


def test_occupations_keep_both_schemes(lake: Lake) -> None:
    assert one(
        lake,
        "SELECT count(*), count(DISTINCT codigo) FROM lake.aux_ocupacoes "
        "WHERE esquema = 'cbo2002'",
    ) == (2458, 2458)
    assert one(
        lake,
        "SELECT descricao FROM lake.aux_ocupacoes WHERE esquema = 'cbo2002' AND codigo = '10105'",
    ) == ("Oficial General da Aeronáutica",)
    # TABOCUP lists several titles per code: a title index, not a join key.
    assert one(
        lake,
        "SELECT count(*), count(DISTINCT codigo) FROM lake.aux_ocupacoes "
        "WHERE esquema = 'tabocup'",
    ) == (3564, 383)
    assert one(
        lake,
        "SELECT descricao FROM lake.aux_ocupacoes WHERE esquema = 'tabocup' "
        "AND descricao LIKE 'COLOCADOR DE LI%'",
    ) == ("COLOCADOR DE LIÇOS",)


def test_uf_and_countries_come_from_the_dbf_verbatim(lake: Lake) -> None:
    assert one(lake, "SELECT sigla, nome FROM lake.aux_uf WHERE codigo_ibge = '11'") == (
        "RO",
        "RONDONIA",
    )
    assert one(lake, "SELECT count(*) FROM lake.aux_paises WHERE codigo = '044'") == (2,)


def test_manifest_names_registered_sources() -> None:
    raw = (files("omnisus.data") / "auxiliares-bootstrap.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        parquet = {n.removesuffix(".parquet") for n in zf.namelist() if n.endswith(".parquet")}
    assert set(manifest) == parquet == TABLES
    registry = {s["sha256"]: s for s in sources_registry()["sources"]}
    for table, entry in manifest.items():
        for source in entry["sources"]:
            assert registry[source["sha256"]]["url"] == source["url"], table


def test_cid10_manifest_cites_the_official_group_member() -> None:
    """AGENTS.md rule 1: the derived block labels must identify their source bytes."""
    raw = (files("omnisus.data") / "auxiliares-bootstrap.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        sources = json.loads(zf.read("manifest.json"))["aux_cid10"]["sources"]
    assert {
        "url": "ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Auxiliar/TAB_SIH.zip",
        "sha256": "f05b32f32908bfb31c4999774600d72bb77c32e22b751bd28e557bb3236276df",
        "member": "CNV/CID10GRUPOS.CNV",
        "member_sha256": "8a40729b61e1b7bd86ffd0aa1d7e91c1effaa08252dc4381e3db17e42bd86dfb",
    } in sources


def test_bootstrap_idempotent(tmp_path: Path) -> None:
    lake = Lake.local(f"ducklake:{tmp_path}/x.ducklake")
    lake.bootstrap_auxiliares()
    lake.bootstrap_auxiliares()
    n = lake.connect().execute("SELECT count(*) FROM lake.aux_uf").fetchone()[0]
    assert n == 27
    lake.close()
