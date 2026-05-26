with source_rows as (
    select
        *,
        axes_json::jsonb ->> 'english_proficiency' as english_proficiency
    from {{ ref('fct_census_observation') }}
),

eligible_rows as (
    select
        census_year,
        geography_level,
        sa2_code,
        sa2_name,
        state_name,
        'language_home_english_proficiency'::text as feature_name,
        concat(category, ' / ', english_proficiency)::text as feature_value,
        null::text as age_band,
        sex,
        category::text as language_used_at_home,
        english_proficiency::text,
        count,
        logical_table_code::text as source_logical_table,
        physical_table as source_physical_table,
        raw_column as source_raw_column,
        source_label,
        is_total,
        true as is_sampler_eligible
    from source_rows
    where logical_table_code = 'G13'
        and category_axis = 'language_used_at_home'
        and count is not null
        and is_total = false
        and category is not null
        and category not in ('Total', 'Not stated', 'Not applicable')
        and category not in ('Other')
        and category not ilike '%not stated%'
        and category not ilike '%not applicable%'
        and english_proficiency is not null
        and english_proficiency not in ('Total', 'Not stated', 'Not applicable')
        and english_proficiency not ilike '%not stated%'
        and english_proficiency not ilike '%not applicable%'
        and sex in ('Male', 'Female')
),

with_denominators as (
    select
        *,
        sum(count) over (
            partition by census_year, sa2_code, sex
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
    language_used_at_home,
    english_proficiency,
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
