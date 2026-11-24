select event_id, event_title, event_type, event_date, budget, beneficiary_id
from {{ ref('stg_event') }}
