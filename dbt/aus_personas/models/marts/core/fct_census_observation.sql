select
    {{ var('census_year', 2021) }}::integer as census_year,
    '{{ var("geography_level", "sa2") }}'::text as geography_level,
    o.sa2_code,
    g.sa2_name,
    g.state_name,
    d.source_profile,
    d.profile_family_name,
    d.logical_table_code,
    d.logical_table_name,
    d.project_alias,
    d.population_universe,
    d.physical_table,
    d.raw_column,
    d.sequential_id,
    d.short_id,
    d.long_id,
    d.source_label,
    d.sex,
    d.age_band,
    d.category_axis,
    d.category,
    d.axes_json,
    d.is_total,
    o.count
from {{ ref('int_abs__sa2_observations') }} o
join {{ ref('int_abs__column_dictionary') }} d
    on d.physical_table = o.physical_table
    and d.raw_column = o.raw_column
join {{ ref('dim_sa2') }} g
    on g.sa2_code = o.sa2_code
