-- A customer who organises events. No personal data: an id, an e-mail domain, their history and complaints.
with events as (
  select beneficiary_id, count(*) as events, min(event_date) as first_event_date
  from {{ ref('stg_event') }} group by 1
), c as (
  select beneficiary_id, count(*) as complaints from {{ ref('stg_complaint') }} group by 1
)
select b.beneficiary_id, b.email_domain, coalesce(e.events, 0) as events, e.first_event_date,
       coalesce(e.events, 0) >= 2 as is_returning, coalesce(c.complaints, 0) as complaints
from {{ ref('stg_beneficiary') }} b
left join events e using (beneficiary_id)
left join c using (beneficiary_id)
