select {{ txt('id_category') }} as category_id, {{ int_('id_subcategory') }} as subcategory_id
from {{ source('raw', 'category_service') }}
