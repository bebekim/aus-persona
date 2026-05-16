select *
from (
    select count(*) as row_count
    from {{ ref('int_g01__total_persons_by_sex') }}
) totals
where row_count != 7416
