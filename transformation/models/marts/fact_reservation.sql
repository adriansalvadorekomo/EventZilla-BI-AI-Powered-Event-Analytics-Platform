-- The fact of the star. Grain: one reservation (all 18,000 are kept; v1 kept 428).
-- Six dimensions: date (x2: reservation, event), event, service, provider, beneficiary, geography.
-- Each measure answers a business objective of docs/GIMSI.md:
--   BO1 revenue and profitability   revenue, final_price, list_price
--   BO2 reservations and conversion  is_confirmed, is_cancelled, lead_time_days
--   BO3 satisfaction and retention   rating_avg, evaluations (+ dim_beneficiary.is_returning, complaints)
--   BO4 marketing return             revenue by month, joined to marketing spend in reporting.rpt_marketing_monthly
-- Revenue counts confirmed reservations only; ratings use valid evaluations only (quality.rejected_evaluations).
with ratings as (
  select reservation_id, avg(rating)::numeric(4, 2) as rating_avg, count(*) as evaluations
  from {{ ref('stg_evaluation') }}
  where rating between 1 and 5
  group by 1
)
select
  -- keys to the five dimensions
  r.reservation_id,
  r.event_id,
  r.service_id,
  s.provider_id,
  e.beneficiary_id,
  {{ geo_key('p.city') }}                                       as governorate_id,
  r.reservation_date,
  e.event_date,
  -- BO2: where the reservation stands, and how far ahead it was made
  r.status,
  r.status = 'confirmed'                                        as is_confirmed,
  r.status = 'cancelled'                                        as is_cancelled,
  e.event_date - r.reservation_date                             as lead_time_days,
  -- BO1: what was agreed, what was earned, against the service's list price
  r.final_price,
  case when r.status = 'confirmed' then r.final_price else 0 end as revenue,
  s.list_price,
  -- BO3: how the customer rated it
  ra.rating_avg,
  coalesce(ra.evaluations, 0)                                   as evaluations
from {{ ref('stg_reservation') }} r
left join {{ ref('stg_event') }} e using (event_id)
left join {{ ref('stg_service') }} s using (service_id)
left join {{ ref('stg_provider') }} p using (provider_id)
left join ratings ra using (reservation_id)
