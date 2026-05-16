with observations as (
    select
        raw_column,
        count
    from {{ ref('int_abs__sa2_observations') }}
    where physical_table = 'sa2_g01'
),

modes as (
    select
        raw_column,
        count as mode_count,
        count(*) as mode_frequency,
        row_number() over (
            partition by raw_column
            order by count(*) desc, count asc nulls last
        ) as mode_rank
    from observations
    group by raw_column, count
),

profile as (
    select
        raw_column,
        count(*) as sa2_count,
        count(*) filter (where count is null) as null_count,
        count(*) filter (where count = 0) as zero_count,
        min(count) as min_count,
        percentile_cont(0.25) within group (order by count) as p25_count,
        percentile_cont(0.5) within group (order by count) as median_count,
        avg(count)::numeric(18, 2) as mean_count,
        percentile_cont(0.75) within group (order by count) as p75_count,
        max(count) as max_count
    from observations
    group by raw_column
)

select
    d.physical_table,
    p.raw_column,
    d.short_id,
    d.long_id,
    d.source_label,
    {{ classify_g01_section('p.raw_column') }} as g01_section,
    d.sex,
    case
        when d.long_id like '%85_years_and_over%' then '85+'
        when d.long_id like '%25_years_and_over%' then '25+'
        else nullif(d.age_band, '-')
    end as age_band,
    d.is_total,
    p.sa2_count,
    p.null_count,
    p.zero_count,
    p.min_count,
    p.p25_count,
    p.median_count,
    p.mean_count,
    p.p75_count,
    p.max_count,
    m.mode_count,
    m.mode_frequency
from profile p
join {{ ref('int_abs__column_dictionary') }} d
    on d.physical_table = 'sa2_g01'
    and d.raw_column = p.raw_column
left join modes m
    on m.raw_column = p.raw_column
    and m.mode_rank = 1
