with src as (
    select * from {{ ref('orders') }}
)
select
    cast(order_id as int) as order_id,
    cast(customer_id as int) as customer_id,
    cast(order_date as date) as order_date,
    lower(status) as status
from src