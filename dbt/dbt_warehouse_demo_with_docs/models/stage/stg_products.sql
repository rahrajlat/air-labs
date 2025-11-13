with src as (
    select * from {{ ref('products') }}
)
select
    cast(product_id as int) as product_id,
    initcap(trim(product_name)) as product_name,
    initcap(trim(category)) as category,
    cast(list_price as numeric(10,2)) as list_price
from src