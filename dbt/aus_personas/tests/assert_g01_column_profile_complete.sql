select *
from (
    select count(*) as row_count
    from {{ ref('int_g01__column_profile') }}
) profile
where row_count != 108
