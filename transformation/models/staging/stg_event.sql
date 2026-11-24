select
  {{ int_('id_event') }}         as event_id,
  {{ txt('title') }}             as event_title,
  {{ txt('type') }}              as event_type,
  {{ day('event_date') }}        as event_date,
  {{ num('budget') }}            as budget,
  {{ int_('id_beneficiary') }}   as beneficiary_id
from {{ source('raw', 'event') }}
