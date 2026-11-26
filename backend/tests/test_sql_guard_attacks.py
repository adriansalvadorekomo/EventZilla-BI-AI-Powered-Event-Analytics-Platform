"""Attacks on the analyst's SQL guard. Every payload here got through (or crashed) an earlier, blocklist-based guard."""

import pytest

from app import sql_guard
from app.sql_guard import MAX_ROWS, UnsafeSQL, guard

ATTACKS = {
    # functions that were not on the old blocklist, or were spelled so the blocklist missed them
    "quoted function name": 'select "pg_sleep"(5) from marts.dim_date',
    "schema-qualified": "select pg_catalog.pg_sleep(5) from marts.dim_date",
    "pg_sleep_for": "select pg_sleep_for('5 seconds') from marts.dim_date",
    "quoted set_config": "select \"set_config\"('default_transaction_read_only','off',false) from marts.dim_date",
    "qualified set_config": "select pg_catalog.set_config('statement_timeout','0',false) from marts.dim_date",
    "query_to_xml runs a string": "select query_to_xml('select * from pg_authid', true, false, '') from marts.dim_date",
    "table_to_xml": "select table_to_xml('pg_authid'::regclass, true, false, '') from marts.dim_date",
    "dblink_exec": "select dblink_exec('host=x','drop table y') from marts.dim_date",
    "large objects": "select lo_create(0) from marts.dim_date",
    "advisory lock": "select pg_advisory_lock(1) from marts.dim_date",
    "sequence": "select nextval('marts.s') from marts.dim_date",
    "txid": "select txid_current() from marts.dim_date",
    "read a file": "select pg_read_file('/etc/passwd') from marts.dim_date",
    # information about the server
    "version": "select version() from marts.dim_date",
    "server address": "select inet_server_addr() from marts.dim_date",
    "current user": "select current_user, current_database() from marts.dim_date",
    "catalog through a cast": "select 'pg_authid'::regclass::text from marts.dim_date",
    # tables outside the allow-list
    "pg_catalog": "select * from pg_catalog.pg_tables",
    "information_schema": "select * from information_schema.tables",
    "raw schema": "select * from raw.reservation",
    "staging schema": "select * from staging.stg_beneficiary",
    "unqualified table": "select * from fact_reservation",
    "other catalog": "select * from otherdb.marts.fact_reservation",
    "internal quality table": "select * from quality.gate_runs",
    "table function": "select count(*) from generate_series(1, 1000000000)",
    "values list": "select * from (values (1),(2)) v(a)",
    "unnest": "select * from unnest(array[1,2,3])",
    # denial of service
    "cartesian join": "select count(*) from marts.fact_reservation a, marts.fact_reservation b, marts.dim_date c",
    "cross join": "select count(*) from marts.fact_reservation a cross join marts.fact_reservation b",
    "recursive CTE": "with recursive r(n) as (select 1 union all select n+1 from r) select count(*) from r",
    "huge string": "select repeat('x', 1000000000) from marts.dim_date",
    "regex (ReDoS)": "select * from marts.dim_event where event_title ~ '(a+)+$'",
    "similar to": "select * from marts.dim_event where event_title similar to '(a|aa)+'",
    # not a read
    "insert": "insert into marts.dim_date select * from marts.dim_date",
    "delete": "delete from marts.dim_date",
    "drop": "drop table marts.fact_reservation",
    "select into": "select * into marts.copy from marts.dim_date",
    "for update": "select * from marts.dim_date for update",
    "data-modifying CTE": "with d as (delete from marts.dim_date returning *) select * from d",
    "two statements": "select 1; drop table marts.dim_date",
    "set": "set statement_timeout = 0",
    "copy": "copy marts.dim_date to program 'id'",
    "explain": "explain select * from marts.dim_date",
    "parameter": "select * from marts.dim_date where date_day = $1",
    # shapes
    "empty": "   ",
    "too long": "select 1 from marts.dim_date where " + " or ".join(["1=1"] * 800),
    "deeply nested": "select " + "(" * 3000 + "1" + ")" * 3000,
    "many unions": "select 1 from marts.dim_date " + "union select 1 from marts.dim_date " * 60,
}


@pytest.mark.parametrize("name", ATTACKS)
def test_attack_is_refused(name):
    with pytest.raises(UnsafeSQL):
        guard(ATTACKS[name])


LEGIT = [
    ("select event_type, sum(f.revenue) as revenue from marts.fact_reservation f "
     "join marts.dim_event e using (event_id) group by 1 order by 2 desc"),
    ("select to_char(date_trunc('month', reservation_date), 'YYYY-MM') as month, sum(revenue) "
     "from marts.fact_reservation group by 1 order by 1"),
    ("select d.year, round(100.0 * avg(is_confirmed::int), 1) from marts.fact_reservation f "
     "join marts.dim_date d on f.reservation_date = d.date_day group by 1"),
    "with t as (select region, sum(population_2024) as pop from marts.dim_geography group by 1) select * from t",
    "select spend_type, corr(marketing_spend, new_beneficiaries) from reporting.rpt_marketing_monthly group by 1",
    "select percentile_cont(0.5) within group (order by final_price) from marts.fact_reservation",
    "select event_date, lag(revenue) over (order by event_date) from marts.fact_reservation",
    "select case when status = 'confirmed' then 'ok' else 'no' end, count(*) from marts.fact_reservation group by 1",
    "select coalesce(nullif(rating_avg, 0), 3)::numeric(5,2) from marts.fact_reservation",
    "select count(*) from quality.rejected_evaluations",
    "select region from marts.dim_geography union select region from marts.dim_geography",
    "select * from marts.dim_date limit 5 offset 10",
]


@pytest.mark.parametrize("sql", LEGIT)
def test_ordinary_analysis_still_passes(sql):
    assert guard(sql).upper().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize("tail", ["limit all", "limit 99999", "limit (select 5)", "fetch first 99999 rows only",
                                  "limit 1 + 1"])
def test_every_form_of_limit_is_bounded(tail):
    assert f"LIMIT {MAX_ROWS}" in guard("select * from marts.dim_date " + tail)


def test_a_small_literal_limit_is_kept():
    assert "LIMIT 7" in guard("select * from marts.dim_date limit 7")


@pytest.mark.parametrize("offset", ["offset 999999", "offset (select 1)"])
def test_a_huge_or_computed_offset_is_refused(offset):
    with pytest.raises(UnsafeSQL):
        guard("select * from marts.dim_date " + offset)


def test_the_guard_fails_closed(monkeypatch):
    """If the parser or generator ever breaks, the query is refused: never passed, never a 500."""
    def boom(_sql):
        raise RuntimeError("parser bug")
    monkeypatch.setattr(sql_guard, "_guard", boom)
    with pytest.raises(UnsafeSQL, match="could not be checked"):
        guard("select 1 from marts.dim_date")


def test_what_runs_is_the_regenerated_query_not_the_received_text():
    out = guard("select /* comment */ 1 from marts.dim_date -- tail")
    assert "comment" not in out and "tail" not in out


@pytest.mark.parametrize("sql", [
    "select 1 from marts.dim_date /* x */ ; drop table marts.dim_date -- */",
    "select 1 from marts.dim_date -- */ ; delete from marts.dim_date",
    "select /*+ evil */ 1 from marts.dim_date",
])
def test_comments_cannot_carry_text_into_the_query(sql):
    try:
        out = guard(sql)
    except UnsafeSQL:
        return
    assert "/*" not in out and "--" not in out and "drop" not in out.lower() and "delete" not in out.lower()
