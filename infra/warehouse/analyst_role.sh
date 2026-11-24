#!/bin/sh
# Read-only role for the API and the analyst assistant: the analytics schemas only (never raw, which holds
# personal data), read-only transactions, 5 s per statement. Default privileges cover the tables dbt recreates.
set -e
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d eventzilla <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst_ro') THEN
    CREATE ROLE analyst_ro LOGIN PASSWORD '${ANALYST_DB_PASSWORD}';
  ELSE
    ALTER ROLE analyst_ro PASSWORD '${ANALYST_DB_PASSWORD}';
  END IF;
END \$\$;
ALTER ROLE analyst_ro SET default_transaction_read_only = on;
ALTER ROLE analyst_ro SET statement_timeout = '5s';
REVOKE ALL ON SCHEMA raw, staging FROM analyst_ro;
GRANT USAGE ON SCHEMA marts, reporting, reference, quality TO analyst_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA marts, reporting, reference, quality TO analyst_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE "$POSTGRES_USER" IN SCHEMA marts, reporting, reference, quality
  GRANT SELECT ON TABLES TO analyst_ro;
SQL
