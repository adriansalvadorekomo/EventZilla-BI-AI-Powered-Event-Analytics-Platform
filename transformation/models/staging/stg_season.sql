select {{ day('event_date') }} as day, {{ txt('saison') }} as season_fr
from {{ source('raw', 'season') }}
