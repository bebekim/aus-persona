{{ config(materialized='table', tags=['local', 'willoughby', 'hackathon', 'g01']) }}

with willoughby_sa2 as (
    select
        council_name,
        lga_code,
        lga_name,
        sa2_code,
        sa2_name,
        pct_sa2_in_lga
    from {{ ref('dim_willoughby_sa2_overlap') }}
),

total_persons as (
    select
        w.council_name,
        w.lga_code,
        w.lga_name,
        'total_persons_by_sex' as topic,
        'Total persons' as category,
        null::text as subcategory,
        g.sex,
        sum(g.count) as raw_sa2_count,
        sum(g.count * w.pct_sa2_in_lga) as estimated_count,
        count(distinct g.sa2_code) as contributing_sa2_count
    from {{ ref('int_g01__total_persons_by_sex') }} g
    join willoughby_sa2 w on g.sa2_code = w.sa2_code
    group by 1, 2, 3, 4, 5, 6, 7
),

age_group as (
    select
        w.council_name,
        w.lga_code,
        w.lga_name,
        'age_group_by_sex' as topic,
        g.age_band as category,
        null::text as subcategory,
        g.sex,
        sum(g.count) as raw_sa2_count,
        sum(g.count * w.pct_sa2_in_lga) as estimated_count,
        count(distinct g.sa2_code) as contributing_sa2_count
    from {{ ref('int_g01__age_group_by_sex') }} g
    join willoughby_sa2 w on g.sa2_code = w.sa2_code
    group by 1, 2, 3, 4, 5, 6, 7
),

birthplace as (
    select
        w.council_name,
        w.lga_code,
        w.lga_name,
        'birthplace_summary_by_sex' as topic,
        g.birthplace_summary as category,
        null::text as subcategory,
        g.sex,
        sum(g.count) as raw_sa2_count,
        sum(g.count * w.pct_sa2_in_lga) as estimated_count,
        count(distinct g.sa2_code) as contributing_sa2_count
    from {{ ref('int_g01__birthplace_summary_by_sex') }} g
    join willoughby_sa2 w on g.sa2_code = w.sa2_code
    group by 1, 2, 3, 4, 5, 6, 7
),

language as (
    select
        w.council_name,
        w.lga_code,
        w.lga_name,
        'language_summary_by_sex' as topic,
        g.language_summary as category,
        null::text as subcategory,
        g.sex,
        sum(g.count) as raw_sa2_count,
        sum(g.count * w.pct_sa2_in_lga) as estimated_count,
        count(distinct g.sa2_code) as contributing_sa2_count
    from {{ ref('int_g01__language_summary_by_sex') }} g
    join willoughby_sa2 w on g.sa2_code = w.sa2_code
    group by 1, 2, 3, 4, 5, 6, 7
),

school_completion as (
    select
        w.council_name,
        w.lga_code,
        w.lga_name,
        'school_completion_by_sex' as topic,
        g.school_completion as category,
        null::text as subcategory,
        g.sex,
        sum(g.count) as raw_sa2_count,
        sum(g.count * w.pct_sa2_in_lga) as estimated_count,
        count(distinct g.sa2_code) as contributing_sa2_count
    from {{ ref('int_g01__school_completion_by_sex') }} g
    join willoughby_sa2 w on g.sa2_code = w.sa2_code
    group by 1, 2, 3, 4, 5, 6, 7
)

select
    council_name,
    lga_code,
    lga_name,
    topic,
    category,
    subcategory,
    sex,
    raw_sa2_count::numeric as raw_sa2_count,
    estimated_count::numeric as estimated_count,
    contributing_sa2_count,
    'SA2 area overlap weighting against 2021 Willoughby LGA boundary' as weighting_method
from total_persons

union all

select
    council_name,
    lga_code,
    lga_name,
    topic,
    category,
    subcategory,
    sex,
    raw_sa2_count::numeric as raw_sa2_count,
    estimated_count::numeric as estimated_count,
    contributing_sa2_count,
    'SA2 area overlap weighting against 2021 Willoughby LGA boundary' as weighting_method
from age_group

union all

select
    council_name,
    lga_code,
    lga_name,
    topic,
    category,
    subcategory,
    sex,
    raw_sa2_count::numeric as raw_sa2_count,
    estimated_count::numeric as estimated_count,
    contributing_sa2_count,
    'SA2 area overlap weighting against 2021 Willoughby LGA boundary' as weighting_method
from birthplace

union all

select
    council_name,
    lga_code,
    lga_name,
    topic,
    category,
    subcategory,
    sex,
    raw_sa2_count::numeric as raw_sa2_count,
    estimated_count::numeric as estimated_count,
    contributing_sa2_count,
    'SA2 area overlap weighting against 2021 Willoughby LGA boundary' as weighting_method
from language

union all

select
    council_name,
    lga_code,
    lga_name,
    topic,
    category,
    subcategory,
    sex,
    raw_sa2_count::numeric as raw_sa2_count,
    estimated_count::numeric as estimated_count,
    contributing_sa2_count,
    'SA2 area overlap weighting against 2021 Willoughby LGA boundary' as weighting_method
from school_completion
