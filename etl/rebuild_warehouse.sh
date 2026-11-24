#!/usr/bin/env bash
# Rebuild the whole warehouse (staging, then the star schema in DW_event) from this repository alone.
# Needs Docker only. Leaves the database running in container eventzilla-etl-pg (PostgreSQL 16, trust auth,
# no published port) so the app stack or a BI tool can be pointed at it; `docker rm -f eventzilla-etl-pg` ends it.
#
#   bash etl/rebuild_warehouse.sh
#
# Steps: etl/rebuild_staging.sh (16 staging jobs), the warehouse tables (etl/sql/warehouse_tables.sql), the
# dimension jobs of job_master_dw one by one in the master's order, the bridges of etl/sql/warehouse_bridge.sql
# (gaps in the exported jobs, explained there), then fact_v3. service_dw is skipped: its input table does not
# exist and the bridge builds the dimension it was meant to produce.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PG=eventzilla-etl-pg
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
sql() { docker exec -i "$PG" psql -U postgres -q -v ON_ERROR_STOP=1 "$@"; }

bash "$ROOT/etl/rebuild_staging.sh" --keep

for db in DW_event dw_auto; do sql -c "CREATE DATABASE \"$db\";"; done
sql < "$ROOT/etl/sql/warehouse_tables.sql"
# placeholders: the beneficiary and evaluation jobs look themselves up in lowercase tables before they write
# "DIM_beneficiary" and "DIM_evaluation"; the bridge replaces them
sql -d DW_event -c 'CREATE TABLE dim_beneficiary (last_name varchar, first_name varchar, email varchar,
  phone varchar, "SK_beneficiary" integer, id_beneficiary integer);'
sql -d DW_event -c 'CREATE TABLE dim_evaluation (comment varchar, "SK_evaluation" integer,
  id_evaluation integer, rating integer);'
# two staging jobs write to sa_auto, but the category, competitor and fact jobs read them from SA_event
for t in sa_category_service competitor_sa; do
  docker exec "$PG" pg_dump -U postgres -d sa_auto -t "$t" | sql -d SA_event
done

cp -r "$ROOT/etl/talend/job_master_dw_0.1" "$WORK/"
JOB="$WORK/job_master_dw_0.1/job_master_dw"
# run one child job with the exported classpath (the run script, with the child's class instead of the master's)
sed 's#automatization.job_master_dw_0_1.job_master_dw --context=Default#"$CHILD" --context=Default#' \
  "$JOB/job_master_dw_run.sh" > "$JOB/run_child.sh"
printf '127.0.0.1 localhost host.docker.internal\n' > "$WORK/hosts"
run() {
  echo "--- $1"
  docker run --rm --network "container:$PG" -v "$WORK:/etl" -e CHILD="automatization.$1" \
    -e JAVA_TOOL_OPTIONS="-Djdk.net.hosts.file=/etl/hosts -Duser.timezone=Africa/Lagos" \
    eclipse-temurin:17-jre sh /etl/job_master_dw_0.1/job_master_dw/run_child.sh 2>&1 \
    | grep -vE '^Picked up|^\[(INFO|statistics)\]' || true
}

for child in benficiary_dwh_0_1.benficiary_DWH category_dw_1_0_1.category_dw_1 dim_competitors_0_1.dim_competitors \
  dim_complaints_0_1.dim_complaints dim_date_0_1.DIM_date dim_events_0_1.dim_events \
  dim_locations_0_1.DIM_locations dim_reservation_0_1.dim_reservation dim_reviews_0_1.dim_reviews \
  evaluation_dwh_0_1.evaluation_DWH saison_dwh_0_1.saison_DWH; do
  run "$child"
done

sql < "$ROOT/etl/sql/warehouse_bridge.sql"
docker exec "$PG" psql -U postgres -d SA_event -c "\copy (select id_provider, name, service_type, email, phone, city,
  row_number() over (order by id_provider::int) from provider_sa) to stdout" \
  | sql -d DW_event -c '\copy dim_provider from stdin'
docker exec "$PG" psql -U postgres -d SA_event -c "\copy (select id_service, title, description,
  row_number() over (order by id_service::int) from service_sa) to stdout" \
  | sql -d DW_event -c '\copy dim_service from stdin'

run fact_v3_0_1.fact_v3

echo "== DW_event"
for t in $(docker exec "$PG" psql -U postgres -d DW_event -tAc \
    "select table_name from information_schema.tables where table_schema = 'public' order by 1"); do
  echo "  $t: $(docker exec "$PG" psql -U postgres -d DW_event -tAc "select count(*) from \"$t\"")"
done
