-- Market reference: competitors' public ratings (not linked to our reservations).
select competitor_id, brand_name, rating_stars, value_for_money, functionality, starting_price
from {{ ref('stg_competitor') }}
