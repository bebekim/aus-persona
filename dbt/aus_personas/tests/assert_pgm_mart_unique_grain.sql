with duplicate_age_sex as (
    select
        'mart_pgm__sa2_age_sex' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        null::text as feature_value,
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
        income_band as feature_value,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_personal_income') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
),

duplicate_labour as (
    select
        'mart_pgm__sa2_labour_force_status' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        labour_force_status as feature_value,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_labour_force_status') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
),

duplicate_country_of_birth as (
    select
        'mart_pgm__sa2_country_of_birth' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        country_of_birth as feature_value,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_country_of_birth') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
),

duplicate_language as (
    select
        'mart_pgm__sa2_language_home_english_proficiency' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        concat(language_used_at_home, ' / ', english_proficiency) as feature_value,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_language_home_english_proficiency') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
),

duplicate_household_relationship as (
    select
        'mart_pgm__sa2_household_relationship' as mart_name,
        census_year,
        sa2_code,
        age_band,
        sex,
        household_relationship as feature_value,
        count(*) as row_count
    from {{ ref('mart_pgm__sa2_household_relationship') }}
    group by 1, 2, 3, 4, 5, 6
    having count(*) > 1
)

select *
from duplicate_age_sex
union all
select *
from duplicate_income
union all
select *
from duplicate_labour
union all
select *
from duplicate_country_of_birth
union all
select *
from duplicate_language
union all
select *
from duplicate_household_relationship
