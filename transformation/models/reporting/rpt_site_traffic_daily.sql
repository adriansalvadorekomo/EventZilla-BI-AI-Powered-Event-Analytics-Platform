-- Reporting table (daily grain, not a fact of the star): the website funnel; the source covers 2022 only.
-- Days with more reservations than visitors are impossible for a funnel: kept, flagged, conversion left empty
-- (quality.flagged_traffic_days).
select traffic_date, visitors, reservations,
       reservations <= visitors as is_valid,
       case when reservations <= visitors then round(reservations::numeric / nullif(visitors, 0), 4) end
         as conversion_rate
from {{ ref('stg_site_traffic') }}
