select *
from (
    select count(*) as row_count
    from {{ ref('int_g01__age_group_by_sex') }}
) age_groups
where row_count != 81576
