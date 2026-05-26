select
    'mart_pgm__sa2_personal_income' as mart_name,
    sa2_code,
    age_band,
    sex,
    income_band as feature_value
from {{ ref('mart_pgm__sa2_personal_income') }}
where income_band ilike '%not stated%'
    or income_band ilike '%not applicable%'

union all

select
    'mart_pgm__sa2_labour_force_status' as mart_name,
    sa2_code,
    age_band,
    sex,
    labour_force_status as feature_value
from {{ ref('mart_pgm__sa2_labour_force_status') }}
where labour_force_status ilike '%not stated%'
    or labour_force_status ilike '%not applicable%'

union all

select
    'mart_pgm__sa2_country_of_birth' as mart_name,
    sa2_code,
    age_band,
    sex,
    country_of_birth as feature_value
from {{ ref('mart_pgm__sa2_country_of_birth') }}
where country_of_birth ilike '%not stated%'
    or country_of_birth ilike '%not applicable%'
    or country_of_birth in ('Born elsewhere', 'Other')

union all

select
    'mart_pgm__sa2_language_home_english_proficiency' as mart_name,
    sa2_code,
    age_band,
    sex,
    feature_value
from {{ ref('mart_pgm__sa2_language_home_english_proficiency') }}
where language_used_at_home ilike '%not stated%'
    or language_used_at_home ilike '%not applicable%'
    or language_used_at_home in ('Other')
    or english_proficiency ilike '%not stated%'
    or english_proficiency ilike '%not applicable%'

union all

select
    'mart_pgm__sa2_household_relationship' as mart_name,
    sa2_code,
    age_band,
    sex,
    household_relationship as feature_value
from {{ ref('mart_pgm__sa2_household_relationship') }}
where household_relationship ilike '%not stated%'
    or household_relationship ilike '%not applicable%'
