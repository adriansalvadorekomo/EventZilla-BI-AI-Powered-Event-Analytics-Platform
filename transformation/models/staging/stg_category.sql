select {{ txt('id_category') }} as category_id, initcap({{ txt('category_name') }}) as category_name
from {{ source('raw', 'category') }}
