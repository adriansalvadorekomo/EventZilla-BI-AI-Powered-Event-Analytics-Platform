-- month arrives as 'YYYY-MM' text; invalid months (e.g. '2024-24') get a null month_start and are quarantined
select
  {{ int_('id') }}               as marketing_id,
  {{ txt('month') }}             as month_label,
  case when {{ txt('month') }} ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'
       then to_date({{ txt('month') }} || '-01', 'YYYY-MM-DD') end as month_start,
  {{ num('marketing_spend') }}   as marketing_spend,
  {{ int_('new_beneficiaries') }} as new_beneficiaries,
  {{ txt('spend_type') }}        as spend_type
from {{ source('raw', 'marketing_spend') }}
