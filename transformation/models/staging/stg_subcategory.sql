select {{ int_('id_subcategory') }} as subcategory_id, {{ txt('name') }} as subcategory_name,
       {{ txt('id_category') }} as category_id
from {{ source('raw', 'subcategory') }}
