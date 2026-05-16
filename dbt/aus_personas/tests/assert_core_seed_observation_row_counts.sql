with expected(physical_table) as (
    values
        ('sa2_g04a'),
        ('sa2_g04b'),
        ('sa2_g05'),
        ('sa2_g06'),
        ('sa2_g07'),
        ('sa2_g08'),
        ('sa2_g09a'),
        ('sa2_g09b'),
        ('sa2_g09c'),
        ('sa2_g09d'),
        ('sa2_g09e'),
        ('sa2_g09f'),
        ('sa2_g09g'),
        ('sa2_g09h'),
        ('sa2_g13a'),
        ('sa2_g13b'),
        ('sa2_g13c'),
        ('sa2_g13d'),
        ('sa2_g13e'),
        ('sa2_g16a'),
        ('sa2_g16b'),
        ('sa2_g17a'),
        ('sa2_g17b'),
        ('sa2_g17c'),
        ('sa2_g22'),
        ('sa2_g27a'),
        ('sa2_g27b'),
        ('sa2_g29'),
        ('sa2_g35'),
        ('sa2_g36'),
        ('sa2_g37'),
        ('sa2_g46a'),
        ('sa2_g46b'),
        ('sa2_g49a'),
        ('sa2_g49b'),
        ('sa2_g50a'),
        ('sa2_g50b'),
        ('sa2_g50c'),
        ('sa2_g54a'),
        ('sa2_g54b'),
        ('sa2_g54c'),
        ('sa2_g54d'),
        ('sa2_g60a'),
        ('sa2_g60b')
),

sa2 as (
    select count(*) as sa2_rows
    from {{ ref('dim_sa2') }}
),

dictionary as (
    select
        physical_table,
        count(*) as dictionary_columns
    from {{ ref('int_abs__column_dictionary') }}
    group by 1
),

observed as (
    select
        physical_table,
        count(*) as observation_rows
    from {{ ref('int_abs__sa2_observations') }}
    group by 1
)

select
    e.physical_table,
    coalesce(o.observation_rows, 0) as observation_rows,
    coalesce(d.dictionary_columns, 0) * sa2.sa2_rows as expected_rows
from expected e
cross join sa2
left join dictionary d
    on d.physical_table = e.physical_table
left join observed o
    on o.physical_table = e.physical_table
where coalesce(o.observation_rows, 0) != coalesce(d.dictionary_columns, 0) * sa2.sa2_rows
