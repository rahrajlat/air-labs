select
    c.customer_id,
    c.customer_name,
    c.email,
    c.signup_date,
    c.country,
    case when c.country in ('UK','US') then 'EN' else 'EN' end as locale
from {{ ref('stg_customers') }} as c