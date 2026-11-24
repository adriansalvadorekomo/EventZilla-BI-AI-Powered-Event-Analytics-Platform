-- ratings use a decimal comma in the source ("5,0")
select
  {{ txt('bk_comment') }}        as review_id,
  {{ num('rating') }}            as rating,
  trim(both '"' from {{ txt('title') }}) as title
from {{ source('raw', 'platform_review') }}
