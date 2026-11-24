select
  {{ int_('id_provider') }}      as provider_id,
  {{ txt('name') }}              as provider_name,
  {{ txt('service_type') }}      as service_type,
  {{ txt('city') }}              as city
from {{ source('raw', 'provider') }}
