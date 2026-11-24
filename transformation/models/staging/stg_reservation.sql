select
  {{ int_('id_reservation') }}   as reservation_id,
  {{ int_('id_event') }}         as event_id,
  {{ int_('id_service') }}       as service_id,
  {{ day('reservation_date') }}  as reservation_date,
  lower({{ txt('status') }})     as status,
  {{ num('final_price') }}       as final_price
from {{ source('raw', 'reservation') }}
