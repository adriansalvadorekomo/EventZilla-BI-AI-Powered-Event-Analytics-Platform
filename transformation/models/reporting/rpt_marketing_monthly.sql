-- Reporting table (monthly grain, not a fact of the star): marketing spend per valid month, with the
-- confirmed revenue booked that month from fact_reservation.
with revenue as (
  select date_trunc('month', reservation_date)::date as month_start, sum(revenue) as confirmed_revenue,
         count(*) filter (where status = 'confirmed') as confirmed_reservations
  from {{ ref('fact_reservation') }} group by 1
)
select m.month_start, m.spend_type, m.marketing_spend, m.new_beneficiaries,
       round(m.marketing_spend / nullif(m.new_beneficiaries, 0), 2) as cost_per_new_beneficiary,
       r.confirmed_revenue, r.confirmed_reservations,
       round(r.confirmed_revenue / nullif(m.marketing_spend, 0), 2)  as revenue_per_spend
from {{ ref('stg_marketing_spend') }} m
left join revenue r using (month_start)
where m.month_start is not null
