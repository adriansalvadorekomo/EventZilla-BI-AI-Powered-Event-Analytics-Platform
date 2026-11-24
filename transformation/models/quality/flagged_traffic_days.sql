-- Rule: a day cannot have more reservations than website visitors.
select traffic_date, visitors, reservations, 'more reservations than visitors' as reason
from {{ ref('stg_site_traffic') }}
where reservations > visitors
