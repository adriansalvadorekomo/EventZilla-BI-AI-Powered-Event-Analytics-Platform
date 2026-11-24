select
  {{ txt('governorate') }}                       as governorate,
  {{ geo_key(txt('governorate')) }}              as governorate_id,
  {{ int_('population_2024') }}                  as population_2024,
  {{ num('area_km2') }}                          as area_km2,
  {{ txt('region') }}                            as region,
  {{ txt('source_url') }}                        as source_url
from {{ source('raw', 'tn_governorate') }}
