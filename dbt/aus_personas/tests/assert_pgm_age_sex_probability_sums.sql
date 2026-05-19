with probability_sums as (
    select
        census_year,
        sa2_code,
        sum(probability_within_partition) as probability_sum
    from {{ ref('mart_pgm__sa2_age_sex') }}
    group by 1, 2
)

select *
from probability_sums
where abs(probability_sum - 1.0) > 0.000001
