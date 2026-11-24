#!/usr/bin/env bash
# Rebuild the staging area (SA_event, sa_auto) from this repository alone, with the committed Talend
# exports and the source files in data/. Needs Docker only; nothing is installed on the host.
#
#   bash etl/rebuild_staging.sh            # loads, prints the row count of every staging table
#   bash etl/rebuild_staging.sh --keep     # leaves the database running (container eventzilla-etl-pg)
#
# The exported jobs were built on a team member's machine, so they carry fixed settings. None of them
# is edited here; each is met where it is:
#   - inputs at "C:/Users/larry/Desktop/Esprit-PABI-4ERPBI6-2526-EventZella/data/..." (a relative path
#     on Linux) and "/opt/talend/data/...": both resolve to this repo's data/;
#   - PostgreSQL at host.docker.internal:5432 and localhost:5432, user postgres, with a password stored
#     encrypted in the jobs: a throwaway PostgreSQL with trust authentication, reached as both names,
#     accepts it without anyone reading it;
#   - target tables that no committed SQL creates: etl/sql/staging_tables.sql, derived from the jobs.
#   - the time zone of the machine they were built on (WAT, see the jobs' contexts/*.properties): dates are
#     staged as Java date strings ("Tue Jul 15 00:00:00 WAT 2025") and fact_v3 matches them with a literal
#     'WAT', so the jobs run with -Duser.timezone=Africa/Lagos.
# The warehouse step (job_master_dw) does not run from the repo alone: see "Reproducibility" in the README.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PG=eventzilla-etl-pg
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"; [ "${1:-}" = "--keep" ] || docker rm -f "$PG" >/dev/null 2>&1 || true' EXIT

docker rm -f "$PG" >/dev/null 2>&1 || true
docker run -d --name "$PG" -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16 >/dev/null
# over TCP: during initdb the image runs a socket-only server, then restarts
until docker exec "$PG" pg_isready -h 127.0.0.1 -U postgres -q; do sleep 1; done
for db in SA_event sa_auto; do docker exec "$PG" psql -U postgres -qc "CREATE DATABASE \"$db\";"; done
docker exec -i "$PG" psql -U postgres -q -v ON_ERROR_STOP=1 < "$ROOT/etl/sql/staging_tables.sql"

# A copy of the exported job, with the Windows-style input folder pointing at data/
cp -r "$ROOT/etl/talend/job_master_sa_0.1" "$WORK/"
JOB="$WORK/job_master_sa_0.1/job_master_sa"
mkdir -p "$JOB/C:/Users/larry/Desktop/Esprit-PABI-4ERPBI6-2526-EventZella"
ln -s /data "$JOB/C:/Users/larry/Desktop/Esprit-PABI-4ERPBI6-2526-EventZella/data"
printf '127.0.0.1 localhost host.docker.internal\n' > "$WORK/hosts"

docker run --rm --network "container:$PG" \
  -v "$WORK:/etl" -v "$ROOT/data:/data:ro" -v "$ROOT/data:/opt/talend/data:ro" \
  -e JAVA_TOOL_OPTIONS="-Djdk.net.hosts.file=/etl/hosts -Duser.timezone=Africa/Lagos" \
  eclipse-temurin:17-jre sh /etl/job_master_sa_0.1/job_master_sa/job_master_sa_run.sh

for db in SA_event sa_auto; do
  echo "== $db"
  for t in $(docker exec "$PG" psql -U postgres -d "$db" -tAc "select tablename from pg_tables where schemaname = 'public' order by 1"); do
    echo "  $t: $(docker exec "$PG" psql -U postgres -d "$db" -tAc "select count(*) from \"$t\"")"
  done
done
