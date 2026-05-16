select
    trim(table_number) as logical_table_code,
    trim(table_number) as source_table_number,
    trim(table_name) as logical_table_name,
    nullif(trim(table_description), '') as population_universe,
    left(trim(table_number), 1) as source_profile,
    case left(trim(table_number), 1)
        when 'G' then 'General Community Profile'
        when 'P' then 'Place of Enumeration Profile'
        when 'W' then 'Working Population Profile'
        when 'I' then 'Indigenous Profile'
        when 'T' then 'Time Series Profile'
        else 'Unknown'
    end as profile_family_name
from {{ source('abs_census', 'metadata_tables') }}
