"""Warehouse access, always as the read-only role analyst_ro, and always inside a locked-down transaction.

Three layers hold every query, so no single mistake upstream reaches the data:
  1. sql_guard         only known tables, functions and shapes (analyst questions); the app's own queries are fixed
  2. the transaction   read-only, 5 s statement timeout, short lock and idle timeouts (set here, per query)
  3. the role          analyst_ro: SELECT on four analytics schemas, nothing else (infra/warehouse/analyst_role.sh)
"""

import datetime as dt
import decimal
import os
from functools import cache

from sqlalchemy import create_engine, text

MAX_ROWS = 1_000          # nothing here ever needs more; the analyst is held to 200 by the guard
MAX_CELL_CHARS = 500


@cache
def engine():
    e = os.environ
    # a hosted warehouse (Neon on Vercel) needs TLS: EVENTZILLA_DB_SSLMODE=require; locally it stays unset
    ssl = {"sslmode": e["EVENTZILLA_DB_SSLMODE"]} if e.get("EVENTZILLA_DB_SSLMODE") else {}
    return create_engine(
        f"postgresql+psycopg2://analyst_ro:{e['ANALYST_DB_PASSWORD']}@{e.get('EVENTZILLA_DB_HOST', 'localhost')}"
        f":{e.get('EVENTZILLA_DB_PORT', '5442')}/{e.get('EVENTZILLA_DB_NAME', 'eventzilla')}",
        pool_pre_ping=True, pool_size=5, pool_recycle=300,
        connect_args={**ssl, "connect_timeout": 10, "application_name": "eventzilla-api"})


def _plain(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, str) and len(value) > MAX_CELL_CHARS:
        return value[:MAX_CELL_CHARS] + "..."
    return value


def run_readonly(sql: str, params: dict | None = None) -> tuple[list[str], list[list]]:
    with engine().connect() as conn, conn.begin():
        # first statements of the transaction: it cannot write, and it cannot run long, whatever the query says
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        conn.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
        conn.exec_driver_sql("SET LOCAL lock_timeout = '1s'")
        conn.exec_driver_sql("SET LOCAL idle_in_transaction_session_timeout = '10s'")
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return columns, [[_plain(v) for v in row] for row in result.fetchmany(MAX_ROWS)]


def records(sql: str, params: dict | None = None) -> list[dict]:
    columns, rows = run_readonly(sql, params)
    return [dict(zip(columns, row, strict=True)) for row in rows]
