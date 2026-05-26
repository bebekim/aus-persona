with expected_rows as (
    select 'mart_pgm__sa2_age_sex' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_age_sex') }}
        where sa2_code = '213041359'
    )

    union all

    select 'mart_pgm__sa2_personal_income' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_personal_income') }}
        where sa2_code = '213041359'
            and income_band is not null
    )

    union all

    select 'mart_pgm__sa2_labour_force_status' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_labour_force_status') }}
        where sa2_code = '213041359'
            and labour_force_status is not null
    )

    union all

    select 'mart_pgm__sa2_country_of_birth' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_country_of_birth') }}
        where sa2_code = '213041359'
            and country_of_birth is not null
    )

    union all

    select 'mart_pgm__sa2_language_home_english_proficiency' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_language_home_english_proficiency') }}
        where sa2_code = '213041359'
            and language_used_at_home is not null
            and english_proficiency is not null
    )

    union all

    select 'mart_pgm__sa2_household_relationship' as mart_name
    where exists (
        select 1
        from {{ ref('mart_pgm__sa2_household_relationship') }}
        where sa2_code = '213041359'
            and household_relationship is not null
    )
),

required_rows as (
    select 'mart_pgm__sa2_age_sex' as mart_name
    union all
    select 'mart_pgm__sa2_personal_income' as mart_name
    union all
    select 'mart_pgm__sa2_labour_force_status' as mart_name
    union all
    select 'mart_pgm__sa2_country_of_birth' as mart_name
    union all
    select 'mart_pgm__sa2_language_home_english_proficiency' as mart_name
    union all
    select 'mart_pgm__sa2_household_relationship' as mart_name
)

select required_rows.mart_name
from required_rows
left join expected_rows
    on expected_rows.mart_name = required_rows.mart_name
where expected_rows.mart_name is null
