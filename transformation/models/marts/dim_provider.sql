-- Who delivers the service, with their complaint record (complaints have no date, so they live here as counts).
with c as (
  select provider_id, count(*) as complaints, count(*) filter (where status = 'open') as complaints_open
  from {{ ref('stg_complaint') }} group by 1
)
select p.provider_id, p.provider_name, p.service_type, p.city, {{ geo_key('p.city') }} as governorate_id,
       coalesce(c.complaints, 0) as complaints, coalesce(c.complaints_open, 0) as complaints_open
from {{ ref('stg_provider') }} p
left join c using (provider_id)
