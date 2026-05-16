select
    sa2_code_2021::text as sa2_code,
    sa2_name_2021 as sa2_name,
    sa3_code_2021::text as sa3_code,
    sa3_name_2021 as sa3_name,
    sa4_code_2021::text as sa4_code,
    sa4_name_2021 as sa4_name,
    gccsa_code_2021::text as gccsa_code,
    gccsa_name_2021 as gccsa_name,
    state_code_2021::text as state_code,
    state_name_2021 as state_name,
    aus_code_2021::text as country_code,
    aus_name_2021 as country_name,
    area_albers_sqkm::numeric as area_albers_sqkm
from {{ source('abs_boundaries', 'sa2_2021_aust_gda94') }}
