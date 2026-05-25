with eligible_rows as (
    select
        census_year,
        geography_level,
        sa2_code,
        sa2_name,
        state_name,
        'labour_force_status'::text as feature_name,
        status.labour_force_status::text as feature_value,
        age_band,
        sex,
        null::text as income_band,
        status.labour_force_status::text as labour_force_status,
        count,
        logical_table_code::text as source_logical_table,
        physical_table as source_physical_table,
        raw_column as source_raw_column,
        source_label,
        is_total,
        true as is_sampler_eligible
    from {{ ref('fct_census_observation') }}
    cross join lateral (
        select btrim(
            replace(
                regexp_replace(
                    regexp_replace(long_id, '^(MALES|FEMALES)_', ''),
                    '_Age_[0-9]+_[0-9]+_years$',
                    ''
                ),
                '_',
                ' '
            )
        ) as labour_force_status
    ) status
    where logical_table_code = 'G46'
        and category_axis = 'labour_force_status'
        and count is not null
        and is_total = false
        and status.labour_force_status is not null
        and status.labour_force_status not ilike 'Total%'
        and status.labour_force_status not ilike '%not stated%'
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
    income_band,
    labour_force_status,
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
