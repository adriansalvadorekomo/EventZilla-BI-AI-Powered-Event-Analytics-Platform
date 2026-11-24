select reservation_id, revenue from {{ ref('fact_reservation') }} where revenue < 0
