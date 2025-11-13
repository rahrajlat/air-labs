select
    o.order_id,
    o.order_date,
    o.status,
    o.customer_id,
    c.customer_name,
    c.country
from {{ ref('stg_orders') }} as o
left join {{ ref('stg_customers') }} as c
  on c.customer_id = o.customer_id