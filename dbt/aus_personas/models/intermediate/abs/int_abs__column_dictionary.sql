with stats as (
    select * from {{ ref('stg_abs__metadata_stats') }}
),

tables as (
    select * from {{ ref('stg_abs__metadata_tables') }}
),

joined as (
    select
        s.source_profile,
        coalesce(t.profile_family_name, 'Unknown') as profile_family_name,
        s.logical_table_code,
        t.logical_table_name,
        {{ abs_project_alias('s.logical_table_code', 't.logical_table_name') }} as project_alias,
        t.population_universe,
        s.physical_table_suffix,
        '{{ var("geography_level", "sa2") }}_' || s.physical_table_suffix as physical_table,
        s.raw_column,
        s.sequential_id,
        s.short_id,
        s.long_id,
        s.source_label,
        case
            when upper(s.source_label) like '%|MALES' or upper(s.long_id) ~ '(^|_)MALES($|_)' then 'Male'
            when upper(s.source_label) like '%|FEMALES' or upper(s.long_id) ~ '(^|_)FEMALES($|_)' then 'Female'
            when upper(s.source_label) like '%|PERSONS' or upper(s.long_id) ~ '(^|_)PERSONS($|_)' then 'Persons'
        end as sex,
        coalesce(
            replace(substring(s.long_id from 'Age_([0-9]+_[0-9]+)_years'), '_', '-'),
            replace(substring(s.long_id from 'Age_years_([0-9]+_[0-9]+)_years'), '_', '-'),
            replace(substring(s.long_id from 'Age_groups_([0-9]+_[0-9]+)_years'), '_', '-'),
            replace(substring(s.long_id from '[A-Z]+_([0-9]+_[0-9]+)_years'), '_', '-'),
            substring(s.long_id from 'Age_([0-9]+)_years_and_over') || '+',
            substring(s.long_id from 'Age_years_([0-9]+)_years_and_over') || '+',
            substring(s.long_id from 'Age_groups_([0-9]+)_years_and_over') || '+',
            substring(s.long_id from '[A-Z]+_([0-9]+)_years_and_over') || '+',
            substring(s.long_id from 'Age_([0-9]+)($|_)'),
            substring(s.long_id from 'Age_years_([0-9]+)($|_)'),
            substring(s.long_id from '[A-Z]+_([0-9]+)_years($|_)')
        ) as age_band,
        case
            when s.logical_table_code = 'G05' then 'registered_marital_status'
            when s.logical_table_code = 'G06' then 'social_marital_status'
            when s.logical_table_code = 'G07' then 'indigenous_status'
            when s.logical_table_code = 'G08' then 'ancestry'
            when s.logical_table_code = 'G09' then 'country_of_birth'
            when s.logical_table_code = 'G13' then 'language_used_at_home'
            when s.logical_table_code = 'G16' then 'school_completion'
            when s.logical_table_code = 'G17' then 'income_band'
            when s.logical_table_code = 'G22' then 'defence_service_status'
            when s.logical_table_code = 'G27' then 'household_relationship'
            when s.logical_table_code = 'G35' then 'household_composition'
            when s.logical_table_code = 'G36' then 'dwelling_structure'
            when s.logical_table_code = 'G37' then 'tenure_landlord_type'
            when s.logical_table_code = 'G46' then 'labour_force_status'
            when s.logical_table_code = 'G49' then 'qualification_level'
            when s.logical_table_code = 'G50' then 'field_of_study'
            when s.logical_table_code = 'G60' then 'occupation'
        end as category_axis,
        case
            when s.logical_table_code = 'G04' then null
            when s.logical_table_code = 'G09' then nullif(replace(substring(s.long_id from '^(?:MALES|FEMALES|PERSONS)_(.*?)_Age_'), '_', ' '), 'Total')
            when s.logical_table_code = 'G13' then {{ clean_abs_category("nullif(replace((regexp_match(s.long_id, '^(?:MALES|FEMALES|PERSONS)_(.*?)_(Speaks_English_only|Uses_other_language_and_speaks_English_Very_well_or_well|Uses_other_language_and_speaks_English_Not_well_or_not_at_all|Uses_other_language_and_speaks_English_Total|Not_stated|Total)$'))[1], '_', ' '), 'Total')", "s.logical_table_code") }}
            when s.logical_table_code = 'G17' then {{ clean_abs_category("nullif(replace(substring(s.long_id from '^(?:MALES|FEMALES|PERSONS)_(.*?)_Age_'), '_', ' '), 'Total')", "s.logical_table_code") }}
            when s.logical_table_code = 'G27' then {{ clean_abs_category("nullif(replace(regexp_replace(regexp_replace(s.long_id, '^(?:MALES|FEMALES|PERSONS)_', ''), '_Age_[0-9]+(?:_[0-9]+)?_years(?:_and_over)?$', ''), '_', ' '), 'Total')", "s.logical_table_code") }}
            when s.logical_table_code = 'G54' then {{ clean_abs_category("nullif(replace(substring(s.long_id from '^(?:MALES|FEMALES|PERSONS)_(.*?)_Age_'), '_', ' '), 'Total')", "s.logical_table_code") }}
            else {{ clean_abs_category("split_part(s.source_label, '|', 1)", "s.logical_table_code") }}
        end as category,
        case
            when s.logical_table_code = 'G13'
                then coalesce(
                    nullif(
                        btrim(
                            regexp_replace(
                                replace(
                                    (regexp_match(s.long_id, '^(?:MALES|FEMALES|PERSONS)_(.*?)_(Speaks_English_only|Uses_other_language_and_speaks_English_Very_well_or_well|Uses_other_language_and_speaks_English_Not_well_or_not_at_all|Uses_other_language_and_speaks_English_Total|Not_stated|Total)$'))[2],
                                    '_',
                                    ' '
                                ),
                                '^Uses other language and speaks English\s*',
                                '',
                                'i'
                            )
                        ),
                        'Total'
                    ),
                    case
                    when upper(nullif(split_part(s.source_label, '|', 2), '')) in ('MALES', 'FEMALES', 'PERSONS') then null
                    else nullif(split_part(s.source_label, '|', 2), '')
                    end
                )
        end as english_proficiency,
        case
            when s.logical_table_code = 'G35'
                then nullif(
                    split_part(s.source_label, '|', 2),
                    ''
                )
        end as household_size,
        case
            when s.long_id ~* '(^|_)Total($|_)' then true
            when s.source_label ~* '(^|\|)Total($|\|)' then true
            else false
        end as is_total
    from stats s
    left join tables t
        on t.logical_table_code = s.logical_table_code
)

select
    *,
    jsonb_strip_nulls(
        jsonb_build_object(
            'sex', sex,
            'age_band', age_band
        )
        || case
            when category_axis is not null
                then jsonb_build_object(category_axis, category)
            else '{}'::jsonb
        end
        || jsonb_build_object(
            'english_proficiency', english_proficiency,
            'household_size', household_size
        )
    )::text as axes_json
from joined
