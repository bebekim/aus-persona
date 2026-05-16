select count(*) as actual_count
from {{ ref('int_abs__sa2_observations') }}
where physical_table = 'sa2_g01'
having count(*) != 2472 * 108
