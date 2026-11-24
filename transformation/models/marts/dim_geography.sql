-- Where the service is delivered: Tunisia's 24 governorates (scraped from Wikipedia), one per provider city.
select governorate_id, governorate, region, population_2024, area_km2,
       round(population_2024 / nullif(area_km2, 0), 1) as density_per_km2
from {{ ref('stg_tn_governorate') }}
