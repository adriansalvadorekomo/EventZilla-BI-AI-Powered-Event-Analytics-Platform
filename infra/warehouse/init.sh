#!/bin/sh
# One PostgreSQL server, one database per application: the warehouse never holds another tool's tables.
set -e
for db in airflow metabase n8n; do
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE $db;"
done
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
CREATE SCHEMA raw;        -- Airbyte writes here (one table per landed entity)
CREATE SCHEMA staging;    -- dbt: typed, cleaned views
CREATE SCHEMA marts;      -- dbt: the star schema (fact_reservation + dimensions)
CREATE SCHEMA reporting;  -- dbt: reporting tables at other grains
CREATE SCHEMA reference;  -- dbt: market reference data
CREATE SCHEMA quality;    -- dbt: rows quarantined by the quality rules
SQL
