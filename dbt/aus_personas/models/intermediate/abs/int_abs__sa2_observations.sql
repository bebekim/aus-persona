{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['physical_table', 'raw_column']},
      {'columns': ['sa2_code']},
      {'columns': ['physical_table']}
    ]
  )
}}

{{ generate_census_observation_union('abs_census', var('first_pass_sa2_tables')) }}
