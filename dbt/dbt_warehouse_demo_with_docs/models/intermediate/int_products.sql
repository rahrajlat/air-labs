select
    p.product_id,
    p.product_name,
    p.category,
    p.list_price
from {{ ref('stg_products') }} as p