select
  {{ int_('id_evaluation') }}    as evaluation_id,
  {{ int_('id_reservation') }}   as reservation_id,
  {{ int_('rating') }}           as rating,
  {{ txt('comment') }} is not null as has_comment
from {{ source('raw', 'evaluation') }}
