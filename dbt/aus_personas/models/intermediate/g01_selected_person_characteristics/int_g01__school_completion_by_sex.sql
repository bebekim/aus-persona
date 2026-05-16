select
    {{ var('census_year', 2021) }}::integer as census_year,
    '{{ var("geography_level", "sa2") }}'::text as geography_level,
    o.sa2_code,
    g.sa2_name,
    g.state_name,
    d.physical_table,
    d.raw_column,
    'school_completion'::text as feature_name,
    case
        when d.long_id like 'Highest_year_of_school_completed_Year_12_or_equivalent_%' then 'Year 12 or equivalent'
        when d.long_id like 'Highest_year_of_school_completed_Year_11_or_equivalent_%' then 'Year 11 or equivalent'
        when d.long_id like 'Highest_year_of_school_completed_Year_10_or_equivalent_%' then 'Year 10 or equivalent'
        when d.long_id like 'Highest_year_of_school_completed_Year_9_or_equivalent_%' then 'Year 9 or equivalent'
        when d.long_id like 'Highest_year_of_school_completed_Year_8_or_below_%' then 'Year 8 or below'
        when d.long_id like 'Highest_year_of_school_completed_Did_not_go_to_school_%' then 'Did not go to school'
    end as school_completion,
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
    and {{ classify_g01_section('o.raw_column') }} = 'school_completion_by_sex'
