select
  {{ int_('id_service') }}       as service_id,
  {{ txt('title') }}             as service_title,
  {{ num('price') }}             as list_price,
  {{ int_('id_provider') }}      as provider_id,
  {{ int_('id_subcategory') }}   as subcategory_id
from {{ source('raw', 'service') }}
