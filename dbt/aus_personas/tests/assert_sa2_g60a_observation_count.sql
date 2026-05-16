select count(*) as actual_count
from {{ ref('int_abs__sa2_observations') }}
where physical_table = 'sa2_g60a'
having count(*) != 2472 * 200
