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
