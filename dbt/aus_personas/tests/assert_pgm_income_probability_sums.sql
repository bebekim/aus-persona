with probability_sums as (
    select
        census_year,
        sa2_code,
        age_band,
        sex,
        sum(probability_within_partition) as probability_sum
    from {{ ref('mart_pgm__sa2_personal_income') }}
    group by 1, 2, 3, 4
)

select *
from probability_sums
where abs(probability_sum - 1.0) > 0.000001
