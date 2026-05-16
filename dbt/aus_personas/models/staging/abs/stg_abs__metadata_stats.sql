select
    trim(sequential_id) as sequential_id,
    lower(trim(sequential_id)) as raw_column,
    trim(short_id) as short_id,
    trim(long_id) as long_id,
    trim(table_number) as source_table_number,
    lower(trim(table_number)) as physical_table_suffix,
    upper(left(trim(table_number), 3)) as logical_table_code,
    left(trim(table_number), 1) as source_profile,
    trim(profile_table) as metadata_profile_table,
    trim(column_heading_description) as source_label
from {{ source('abs_census', 'metadata_stats') }}
