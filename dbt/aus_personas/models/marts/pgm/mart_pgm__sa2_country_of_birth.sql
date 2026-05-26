with eligible_rows as (
    select
        census_year,
        geography_level,
        sa2_code,
        sa2_name,
        state_name,
        'country_of_birth'::text as feature_name,
        category::text as feature_value,
        age_band,
        sex,
        category::text as country_of_birth,
        count,
        logical_table_code::text as source_logical_table,
        physical_table as source_physical_table,
        raw_column as source_raw_column,
        source_label,
        is_total,
        true as is_sampler_eligible
    from {{ ref('fct_census_observation') }}
    where logical_table_code = 'G09'
        and category_axis = 'country_of_birth'
        and count is not null
        and is_total = false
        and category is not null
        and category not in ('Total', 'Not stated', 'Not applicable')
        and category not in ('Born elsewhere', 'Other')
        and category not ilike '%not stated%'
        and category not ilike '%not applicable%'
        and age_band is not null
        and age_band not in ('Total', 'Not stated', 'Not applicable')
        and sex in ('Male', 'Female')
),

with_denominators as (
    select
        *,
        sum(count) over (
            partition by census_year, sa2_code, age_band, sex
        ) as denominator_count
    from eligible_rows
)

select
    census_year,
    geography_level,
    sa2_code,
    sa2_name,
    state_name,
    feature_name,
    feature_value,
    age_band,
    sex,
    country_of_birth,
    count,
    denominator_count,
    count::numeric / nullif(denominator_count, 0) as probability_within_partition,
    source_logical_table,
    source_physical_table,
    source_raw_column,
    source_label,
    is_total,
    is_sampler_eligible
from with_denominators
where denominator_count > 0
