from decimal import Decimal

import polars as pl
import pytest

from omnisus.lake import Lake


@pytest.mark.parametrize("first,second", [(1, 1.5), (1.5, 1), (2**53 + 1, 1.5), ("001", 1)])
def test_incompatible_family_rejected_without_mutation(tmp_path, first, second):
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        lake.ingest("t", pl.DataFrame({"v": [first]}).lazy())
        before = lake.snapshots()
        with pytest.raises(ValueError, match=r"type|schema"):
            lake.ingest("t", pl.DataFrame({"v": [second]}).lazy())
        assert lake.connect().execute("SELECT v FROM lake.t").fetchall() == [(first,)]
        assert lake.snapshots() == before


def test_integer_promotion_preserves_values(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        lake.ingest("t", pl.DataFrame({"v": pl.Series([12], dtype=pl.Int32)}).lazy())
        lake.ingest("t", pl.DataFrame({"v": pl.Series([2**53 + 1], dtype=pl.Int64)}).lazy())
        assert lake.connect().execute("SELECT v FROM lake.t ORDER BY v").fetchall() == [
            (12,),
            (2**53 + 1,),
        ]


def test_decimal_scale_change_rejected(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        lake.ingest(
            "t", pl.DataFrame({"v": pl.Series([Decimal("1.2")], dtype=pl.Decimal(10, 1))}).lazy()
        )
        with pytest.raises(ValueError, match=r"type|schema"):
            lake.ingest(
                "t",
                pl.DataFrame({"v": pl.Series([Decimal("1.23")], dtype=pl.Decimal(10, 2))}).lazy(),
            )
        assert lake.connect().execute("SELECT v FROM lake.t").fetchall() == [(Decimal("1.2"),)]


def test_cnes_latest_row_preserves_null(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        con = lake.connect()
        con.execute(
            "CREATE TABLE lake.cnes_estabelecimentos(cnes VARCHAR,tp_unid VARCHAR,codufmun VARCHAR,ano INTEGER,mes INTEGER)"
        )
        con.execute(
            "INSERT INTO lake.cnes_estabelecimentos VALUES ('1234567','05','355030',2024,1),('1234567',NULL,'330455',2024,2)"
        )
        lake.ensure_aux_cnes_view()
        assert con.execute("SELECT tp_unid,codufmun,yyyymm_max FROM lake.aux_cnes").fetchall() == [
            (None, "330455", 202402)
        ]


def test_cnes_conflicting_latest_rows_rejected(tmp_path):
    with Lake.local(f"ducklake:{tmp_path}/s.ducklake") as lake:
        con = lake.connect()
        con.execute(
            "CREATE TABLE lake.cnes_estabelecimentos(cnes VARCHAR,tp_unid VARCHAR,codufmun VARCHAR,ano INTEGER,mes INTEGER)"
        )
        con.execute(
            "INSERT INTO lake.cnes_estabelecimentos VALUES ('1234567','05','355030',2024,1),('1234567','07','355030',2024,1)"
        )
        with pytest.raises(Exception, match=r"conflict|ambig"):
            lake.ensure_aux_cnes_view()
            con.execute("SELECT * FROM lake.aux_cnes").fetchall()
