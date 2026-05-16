select
    o.physical_table,
    o.raw_column,
    count(*) as missing_rows
from {{ ref('int_abs__sa2_observations') }} o
left join {{ ref('int_abs__column_dictionary') }} d
    on d.physical_table = o.physical_table
    and d.raw_column = o.raw_column
where d.raw_column is null
group by 1, 2
