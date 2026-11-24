select {{ day('date') }} as day, {{ txt('holiday') }} as holiday, {{ txt('kind') }} as kind,
       {{ txt('wikipedia_check') }} as wikipedia_check
from {{ source('raw', 'tn_holiday') }}
