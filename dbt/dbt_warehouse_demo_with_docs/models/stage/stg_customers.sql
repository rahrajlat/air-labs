with src as (
    select * from {{ ref('customers') }}
)
select
    cast(customer_id as int) as customer_id,
    initcap(trim(customer_name)) as customer_name,
    lower(trim(email)) as email,
    cast(signup_date as date) as signup_date,
    upper(country) as country
from src