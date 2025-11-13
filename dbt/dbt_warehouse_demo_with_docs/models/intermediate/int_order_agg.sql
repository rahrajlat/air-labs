with items as (
  select
    oi.order_id,
    sum(oi.line_total) as order_total,
    sum(oi.quantity) as item_count
  from {{ ref('stg_order_items') }} as oi
  group by oi.order_id
)
select
  i.order_id,
  o.order_date,
  o.status,
  o.customer_id,
  o.customer_name,
  o.country,
  i.item_count,
  i.order_total
from items i
join {{ ref('int_orders') }} o on o.order_id = i.order_id