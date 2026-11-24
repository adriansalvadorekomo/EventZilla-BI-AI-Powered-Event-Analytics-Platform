select
  {{ txt('bk_competitor') }}     as competitor_id,
  {{ txt('brand_name') }}        as brand_name,
  {{ num('rating_stars') }}      as rating_stars,
  {{ num('value_money') }}       as value_for_money,
  {{ num('functionality') }}     as functionality,
  {{ num('starting_price') }}    as starting_price
from {{ source('raw', 'competitor') }}
