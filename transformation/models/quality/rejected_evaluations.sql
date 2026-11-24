-- Rule: an evaluation rating is 1 to 5. The source also holds 6, 9, 12 and 15; those rows are kept here,
-- with the reason, and left out of every average in the marts.
select evaluation_id, reservation_id, rating, 'rating outside 1-5' as reason
from {{ ref('stg_evaluation') }}
where rating not between 1 and 5 or rating is null
