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
),

required_rows as (
    select 'mart_pgm__sa2_age_sex' as mart_name
    union all
    select 'mart_pgm__sa2_personal_income' as mart_name
)

select required_rows.mart_name
from required_rows
left join expected_rows
    on expected_rows.mart_name = required_rows.mart_name
where expected_rows.mart_name is null
