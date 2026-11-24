select s.service_id, s.service_title, s.list_price, s.provider_id,
       sc.subcategory_name as service_category
from {{ ref('stg_service') }} s
left join {{ ref('stg_subcategory') }} sc using (subcategory_id)
