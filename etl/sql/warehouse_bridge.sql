-- Bridges between the committed warehouse jobs, run by etl/rebuild_warehouse.sh after the dimension jobs and
-- before fact_v3. Each one closes a gap in the exported jobs; the lasting fix is in Talend Studio (re-export).
--
-- 1. The beneficiary and reservation jobs write "DIM_beneficiary" and "DIM_reservation" (quoted, mixed case),
--    but fact_v3 reads dim_beneficiary and dim_reservation (lowercase): two different tables in PostgreSQL.
-- 2. fact_v3 looks up dim_provider, which no job builds.
-- 3. (in the script) two staging jobs write sa_category_service and competitor_sa to sa_auto, but the
--    category, competitor and fact jobs read them from SA_event: the script copies them across.
-- 4. fact_v3 looks up dim_service in DW_event; service_dw writes it to dw_auto, from a sa_auto.service_sa
--    table that no staging job fills.
-- The provider and service dimensions are filled by the script from SA_event.provider_sa and .service_sa,
-- with exactly the columns fact_v3 selects.

\connect "DW_event"
DROP TABLE IF EXISTS dim_beneficiary;   -- empty placeholders the beneficiary and evaluation jobs looked
DROP TABLE IF EXISTS dim_evaluation;    -- themselves up in (fact_v3 reads "DIM_evaluation" directly)
CREATE VIEW dim_beneficiary AS SELECT * FROM "DIM_beneficiary";
CREATE VIEW dim_reservation AS SELECT * FROM "DIM_reservation";

CREATE TABLE dim_provider (
  bk_provider varchar, name_provider varchar, service_type varchar, email varchar, phone varchar, city varchar,
  sk_provider bigint
);
CREATE TABLE dim_service (service_bkey varchar, title varchar, description varchar, service_key integer);
