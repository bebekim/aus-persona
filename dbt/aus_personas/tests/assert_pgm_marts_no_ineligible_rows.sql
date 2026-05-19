with violations as (
    select
        'mart_pgm__sa2_age_sex' as mart_name,
        *
    from {{ ref('mart_pgm__sa2_age_sex') }}
    where count is null
        or is_total
        or not is_sampler_eligible
        or geography_level != 'sa2'

    union all

    select
        'mart_pgm__sa2_personal_income' as mart_name,
        *
    from {{ ref('mart_pgm__sa2_personal_income') }}
    where count is null
        or is_total
        or not is_sampler_eligible
        or geography_level != 'sa2'
)

select *
from violations
