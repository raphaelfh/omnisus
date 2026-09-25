import pytest

from omnisus.sources.ibge.products import (
    CENSUS_YEARS,
    ESTIMATE_UNAVAILABLE_YEARS,
    resolve_product,
)


@pytest.mark.parametrize("year", ESTIMATE_UNAVAILABLE_YEARS)
def test_estimate_unavailable_years_are_rejected(year):
    with pytest.raises(ValueError, match=f"estimate unavailable for {year}"):
        resolve_product("estimate", year)


def test_census_years_are_the_verified_editions():
    assert CENSUS_YEARS == (2010, 2022)
    assert all(resolve_product("census", year).name == "census" for year in CENSUS_YEARS)


def test_non_census_year_is_rejected():
    with pytest.raises(ValueError, match="census years: 2010, 2022"):
        resolve_product("census", 2015)
