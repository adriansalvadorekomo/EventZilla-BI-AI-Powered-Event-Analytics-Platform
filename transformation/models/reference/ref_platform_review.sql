-- Market reference: reviews of the EventZilla platform itself (no link to a reservation).
select review_id, rating, title from {{ ref('stg_platform_review') }}
