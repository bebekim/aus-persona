select *
from {{ ref('int_g01__column_profile') }}
where g01_section is null
