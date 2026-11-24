-- Rule: a marketing row needs a real calendar month (YYYY-MM, month 01-12). '2024-24' and the like stay here.
select marketing_id, month_label, marketing_spend, new_beneficiaries, 'not a calendar month' as reason
from {{ ref('stg_marketing_spend') }}
where month_start is null
