import pytest

from app.sql_guard import MAX_ROWS, UnsafeSQL, guard


def test_plain_select_gets_a_row_limit():
    out = guard("select region, sum(population_2024) from marts.dim_geography group by 1")
    assert f"LIMIT {MAX_ROWS}" in out


def test_existing_small_limit_is_kept():
    assert "LIMIT 5" in guard("select * from marts.dim_date limit 5")


def test_large_limit_is_capped():
    assert f"LIMIT {MAX_ROWS}" in guard("select * from marts.fact_reservation limit 100000")


def test_cte_names_are_allowed():
    guard("with t as (select * from marts.fact_reservation) select count(*) from t")


@pytest.mark.parametrize("sql, reason", [
    ("delete from marts.dim_date", "only SELECT"),
    ("drop table marts.fact_reservation", "only SELECT"),
    ("update marts.dim_event set budget = 0", "only SELECT"),
    ("select 1; drop table marts.dim_date", "exactly one statement"),
    ("select * from raw.beneficiary", "outside the analytics schemas"),
    ("select * from staging.stg_beneficiary", "outside the analytics schemas"),
    ("select * from pg_catalog.pg_user", "outside the analytics schemas"),
    ("select * from dim_date", "outside the analytics schemas"),
    ("select pg_sleep(10)", "pg_sleep"),
    ("select pg_read_file('/etc/passwd')", "pg_read_file"),
    ("select * into marts.copy from marts.dim_date", "only SELECT"),
    ("this is not sql", "only SELECT|could not be parsed"),
])
def test_unsafe_sql_is_refused(sql, reason):
    with pytest.raises(UnsafeSQL, match=reason):
        guard(sql)
