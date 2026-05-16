select *
from {{ ref('int_abs__column_dictionary') }}
where physical_table = 'sa2_g01'
    and raw_column between 'g4' and 'g36'
    and age_band is null
