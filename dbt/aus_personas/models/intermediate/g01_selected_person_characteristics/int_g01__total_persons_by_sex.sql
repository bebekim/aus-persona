select
    {{ var('census_year', 2021) }}::integer as census_year,
    '{{ var("geography_level", "sa2") }}'::text as geography_level,
    o.sa2_code,
    g.sa2_name,
    g.state_name,
    d.physical_table,
    d.raw_column,
    'total_persons'::text as feature_name,
    d.sex as feature_value,
    d.sex,
    o.count,
    d.is_total,
    d.source_label,
    d.short_id,
    d.long_id
from {{ ref('int_abs__sa2_observations') }} o
join {{ ref('int_abs__column_dictionary') }} d
    on d.physical_table = o.physical_table
    and d.raw_column = o.raw_column
join {{ ref('stg_abs__sa2_geography') }} g
    on g.sa2_code = o.sa2_code
where o.physical_table = 'sa2_g01'
    and {{ classify_g01_section('o.raw_column') }} = 'total_persons_by_sex'
