select
  {{ int_('id_complaint') }}     as complaint_id,
  {{ int_('id_beneficiary') }}   as beneficiary_id,
  {{ int_('id_provider') }}      as provider_id,
  {{ txt('subject') }}           as subject,
  lower({{ txt('status') }})     as status
from {{ source('raw', 'complaint') }}
