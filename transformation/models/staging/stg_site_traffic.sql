select
  {{ day('date') }}              as traffic_date,
  {{ int_('visitors') }}         as visitors,
  {{ int_('reservations') }}     as reservations
from {{ source('raw', 'site_traffic') }}
