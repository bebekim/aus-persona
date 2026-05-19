with duplicate_age_sex as (
    select
        'mart_pgm__sa2_age_sex' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        null::text as income_band,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_age_sex') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
),

duplicate_income as (
    select
        'mart_pgm__sa2_personal_income' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        income_band,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_personal_income') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
)

select *
from duplicate_age_sex
union all
select *
from duplicate_income
