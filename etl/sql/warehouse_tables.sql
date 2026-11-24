-- Warehouse tables (DW_event), as the committed Talend exports write them (etl/talend/job_master_dw_0.1).
-- Derived from the jobs' generated Java: table names, column lists and the JDBC types of each INSERT.
-- The beneficiary, reservation and evaluation jobs drop and recreate their own tables.
-- scripts/dw_schema.sql describes an earlier design (Fact_Revenues) that the jobs do not use.
-- Used by etl/rebuild_warehouse.sh.

\connect "DW_event"
-- written by benficiary_DWH
CREATE TABLE IF NOT EXISTS "DIM_beneficiary" (
  "id_beneficiary" integer,
  "SK_beneficiary" integer,
  "last_name" varchar,
  "first_name" varchar,
  "email" varchar,
  "phone" varchar
);
-- written by category_dw_1
CREATE TABLE IF NOT EXISTS "DIM_category" (
  "category_id" integer,
  "category_bkey" varchar,
  "category_name" varchar,
  "subcategory_name" varchar
);
-- written by evaluation_DWH
CREATE TABLE IF NOT EXISTS "DIM_evaluation" (
  "id_evaluation" integer,
  "SK_evaluation" integer,
  "comment" varchar
);
-- written by DIM_locations
CREATE TABLE IF NOT EXISTS "DIM_location" (
  "id_local" integer,
  "Code_Postal" varchar,
  "Local" varchar,
  "Ville" varchar,
  "Adresse_Complete" varchar,
  "Pays" varchar
);
-- written by dim_reservation
CREATE TABLE IF NOT EXISTS "DIM_reservation" (
  "reservation_sk" integer,
  "bk_reservation" varchar,
  "status" varchar
);
-- written by dim_reviews
CREATE TABLE IF NOT EXISTS "DIM_reviews" (
  "reviews_sk" integer,
  "bk_reviews" varchar,
  "username" varchar,
  "title" varchar,
  "description" varchar
);
-- written by dim_competitors
CREATE TABLE IF NOT EXISTS "dim_competitor" (
  "sk_competitor" integer,
  "bk_competitor" varchar,
  "brand_name" varchar,
  "top_features" varchar,
  "brand_description" varchar
);
-- written by dim_complaints
CREATE TABLE IF NOT EXISTS "dim_complaint" (
  "bk_complaint" varchar,
  "subject" varchar,
  "description" varchar,
  "status" varchar,
  "id_complaint" integer
);
-- written by DIM_date
CREATE TABLE IF NOT EXISTS "dim_date" (
  "date_id" integer,
  "date" timestamp,
  "month" varchar,
  "year" integer,
  "quarter" integer,
  "semester" integer,
  "day" varchar
);
-- written by dim_events
CREATE TABLE IF NOT EXISTS "dim_event" (
  "event_sk" integer,
  "bk_event" integer,
  "title" varchar,
  "event_date" timestamp,
  "type" varchar
);
-- written by saison_DWH
CREATE TABLE IF NOT EXISTS "dim_saison" (
  "idSaison" varchar,
  "event_date" timestamp,
  "saison" varchar,
  "weather_description" varchar,
  "sk_saison" integer
);
-- written by fact_v3
CREATE TABLE IF NOT EXISTS "fact_suivi_event" (
  "reservation_sk" integer,
  "service_key" integer,
  "event_sk" integer,
  "budget" integer,
  "price" integer,
  "sk_provider" bigint,
  "category_id" bigint,
  "sk_evaluation" integer,
  "rating" integer,
  "sk_beneficiary" integer,
  "id_complaint" integer,
  "final_price" integer,
  "reservation_date_fk" bigint,
  "date_event_fk" bigint,
  "visitors" integer,
  "reservations" integer,
  "marketing_spend" integer,
  "new_beneficiaries" integer
);
