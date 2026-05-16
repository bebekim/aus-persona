select
    physical_table,
    raw_column,
    count(*) as duplicate_count
from {{ ref('int_abs__column_dictionary') }}
group by 1, 2
having count(*) > 1
