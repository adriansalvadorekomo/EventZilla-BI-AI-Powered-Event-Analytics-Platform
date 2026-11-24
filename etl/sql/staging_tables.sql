-- Staging tables, as the committed Talend exports write them (etl/talend/job_master_sa_0.1).
-- Derived from the jobs' generated Java: table names, column lists and JDBC types of each tDBOutput.
-- scripts/staggin_area.sql describes an earlier design (stg_* tables) that the jobs do not use.
-- Used by etl/rebuild_staging.sh.

\connect "SA_event"
-- written by SAbeneficiary
CREATE TABLE IF NOT EXISTS "beneficiary_sa" (
  "id_beneficiary" varchar,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar,
  "phone" varchar
);
-- written by SAcategory
CREATE TABLE IF NOT EXISTS "category_sa" (
  "id_category" varchar,
  "category_name" varchar
);
-- written by SAcomplaint
CREATE TABLE IF NOT EXISTS "complaint_sa" (
  "id_complaint" varchar,
  "description" varchar,
  "status" varchar,
  "id_beneficiary" varchar,
  "id_provider" varchar,
  "subject" varchar
);
-- written by SAevaluation
CREATE TABLE IF NOT EXISTS "evaluation_sa" (
  "id_evaluation" varchar,
  "id_reservation" varchar,
  "rating" varchar,
  "comment" varchar
);
-- written by SAevent
CREATE TABLE IF NOT EXISTS "event_sa" (
  "id_event" varchar,
  "title" varchar,
  "event_date" varchar,
  "budget" varchar,
  "type" varchar,
  "id_beneficiary" varchar
);
-- written by SA_location
CREATE TABLE IF NOT EXISTS "local" (
  "Code_Postal" varchar,
  "Local" varchar,
  "Ville" varchar,
  "Adresse_Complete" varchar,
  "Pays" varchar
);
-- written by SAmarketing
CREATE TABLE IF NOT EXISTS "marketing_spend_sa" (
  "id" varchar,
  "month" varchar,
  "marketing_spend" varchar,
  "new_beneficiaries" varchar
);
-- written by SAprovider
CREATE TABLE IF NOT EXISTS "provider_sa" (
  "id_provider" varchar,
  "name" varchar,
  "service_type" varchar,
  "email" varchar,
  "phone" varchar,
  "city" varchar
);
-- written by SAreservation
CREATE TABLE IF NOT EXISTS "reservation_sa" (
  "id_reservation" varchar,
  "id_service" varchar,
  "id_event" varchar,
  "reservation_date" varchar,
  "status" varchar,
  "final_price" varchar
);
-- written by SAreviews
CREATE TABLE IF NOT EXISTS "reviews_sa" (
  "User" varchar,
  "Title" varchar,
  "Rating" varchar,
  "Description" varchar,
  "BK_COMMENT" varchar
);
-- written by SA_saison
CREATE TABLE IF NOT EXISTS "saison_sa" (
  "idSaison" varchar,
  "event_date" varchar,
  "saison" varchar,
  "weather_description" varchar
);
-- written by SAservice
CREATE TABLE IF NOT EXISTS "service_sa" (
  "id_service" varchar,
  "price" varchar,
  "description" varchar,
  "id_provider" varchar,
  "id_subcategory" varchar,
  "title" varchar
);
-- written by SAsubcategory
CREATE TABLE IF NOT EXISTS "subcategory_sa" (
  "id_subcategory" varchar,
  "name" varchar,
  "id_category" varchar
);
-- written by SAvisitors
CREATE TABLE IF NOT EXISTS "visitors_sa" (
  "id" varchar,
  "date" varchar,
  "visitors" varchar,
  "reservations" varchar
);

\connect "sa_auto"
-- written by SA_competitor
CREATE TABLE IF NOT EXISTS "competitor_sa" (
  "brand_id" varchar,
  "BK_COMPETITOR" varchar,
  "brand_name" varchar,
  "rating_stars" varchar,
  "top_features" varchar,
  "brand_description" varchar,
  "value_money" varchar,
  "starting_price" varchar,
  "functionality" varchar
);
-- written by SA_category_service
CREATE TABLE IF NOT EXISTS "sa_category_service" (
  "id_category" varchar,
  "id_subcategory" varchar
);

