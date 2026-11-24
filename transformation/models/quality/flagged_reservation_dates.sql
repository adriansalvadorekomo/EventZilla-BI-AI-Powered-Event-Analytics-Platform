-- Rule: a reservation is made before (or on) the day of its event. Half the source breaks it, so these rows are
-- flagged, not removed: their revenue is real, but no lead-time indicator can be built on this dataset.
select reservation_id, event_id, reservation_date, event_date, event_date - reservation_date as lead_time_days,
       'reserved after the event date' as reason
from {{ ref('fact_reservation') }}
where reservation_date > event_date
