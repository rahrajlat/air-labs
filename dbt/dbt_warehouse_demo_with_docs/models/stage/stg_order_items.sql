with src as (
    select * from {{ ref('order_items') }}
)
select
    cast(order_id as int) as order_id,
    cast(product_id as int) as product_id,
    cast(quantity as int) as quantity,
    cast(unit_price as numeric(10,2)) as unit_price,
    cast(quantity as int) * cast(unit_price as numeric(10,2)) as line_total
from src