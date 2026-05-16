select g.*
from {{ ref('stg_abs__sa2_geography') }} g
where exists (
    select 1
    from {{ ref('int_abs__sa2_observations') }} o
    where o.sa2_code = g.sa2_code
)
