-- No average outside 1-5 reaches the marts (invalid ratings are quarantined in quality.rejected_evaluations).
select reservation_id, rating_avg from {{ ref('fact_reservation') }} where rating_avg not between 1 and 5
