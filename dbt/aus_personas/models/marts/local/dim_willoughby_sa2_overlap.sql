{{ config(materialized='table', tags=['local', 'willoughby', 'hackathon']) }}

with willoughby as (
    select
        lga_code_2021::text as lga_code,
        lga_name_2021 as lga_name,
        state_name_2021 as state_name,
        st_transform(st_makevalid(geom), 3577) as geom_3577
    from {{ source('abs_boundaries', 'lga_2021_aust_gda94') }}
    where lga_name_2021 = 'Willoughby'
      and state_name_2021 = 'New South Wales'
      and geom is not null
      and not st_isempty(geom)
),

sa2_boundaries as (
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
        area_albers_sqkm::numeric as sa2_area_sqkm,
        st_transform(st_makevalid(geom), 3577) as geom_3577
    from {{ source('abs_boundaries', 'sa2_2021_aust_gda94') }}
    where geom is not null
      and not st_isempty(geom)
),

intersections as (
    select
        w.lga_code,
        w.lga_name,
        s.sa2_code,
        s.sa2_name,
        s.sa3_code,
        s.sa3_name,
        s.sa4_code,
        s.sa4_name,
        s.gccsa_code,
        s.gccsa_name,
        s.state_code,
        s.state_name,
        s.sa2_area_sqkm,
        st_area(st_intersection(s.geom_3577, w.geom_3577)) as overlap_area_sqm,
        st_area(s.geom_3577) as sa2_area_sqm,
        st_area(w.geom_3577) as lga_area_sqm
    from sa2_boundaries s
    cross join willoughby w
    where st_intersects(s.geom_3577, w.geom_3577)
),

weighted as (
    select
        *,
        overlap_area_sqm / nullif(sa2_area_sqm, 0) as pct_sa2_in_lga,
        overlap_area_sqm / nullif(lga_area_sqm, 0) as pct_lga_from_sa2
    from intersections
    where overlap_area_sqm > 0
)

select
    lga_code,
    lga_name,
    'Willoughby City Council' as council_name,
    sa2_code,
    sa2_name,
    sa3_code,
    sa3_name,
    sa4_code,
    sa4_name,
    gccsa_code,
    gccsa_name,
    state_code,
    state_name,
    sa2_area_sqkm,
    (overlap_area_sqm / 1000000.0)::numeric as overlap_area_sqkm,
    pct_sa2_in_lga::numeric as pct_sa2_in_lga,
    pct_lga_from_sa2::numeric as pct_lga_from_sa2,
    pct_sa2_in_lga >= 0.5 as is_core_sa2,
    case
        when pct_sa2_in_lga >= 0.5 then 'core'
        else 'edge'
    end as overlap_role
from weighted
where pct_sa2_in_lga > 0.001
