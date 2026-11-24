select
  {{ txt('code_postal') }}       as postal_code,
  {{ txt('local') }}             as venue,
  {{ txt('ville') }}             as city,
  {{ txt('pays') }}              as country
from {{ source('raw', 'location') }}
