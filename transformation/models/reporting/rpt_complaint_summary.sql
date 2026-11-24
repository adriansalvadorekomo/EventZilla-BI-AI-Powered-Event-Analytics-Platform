-- Reporting table: complaints per provider, subject and status (complaints carry no date, so they are not a
-- fact of the star; their counts also sit on dim_provider and dim_beneficiary).
select provider_id, subject, status, count(*) as complaints
from {{ ref('stg_complaint') }}
group by 1, 2, 3
