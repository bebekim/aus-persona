{% macro abs_project_alias(logical_code_expr, table_name_expr) %}
case {{ logical_code_expr }}
    when 'G01' then 'selected_person_characteristics_by_sex'
    when 'G04' then 'age_by_sex'
    when 'G05' then 'registered_marital_status_by_age_sex'
    when 'G06' then 'social_marital_status_by_age_sex'
    when 'G07' then 'indigenous_status_by_age_sex'
    when 'G08' then 'ancestry_by_parent_birthplace'
    when 'G09' then 'country_of_birth_by_age_sex'
    when 'G13' then 'language_home_by_english_proficiency_sex'
    when 'G16' then 'school_completion_by_age_sex'
    when 'G17' then 'personal_income_weekly_by_age_sex'
    when 'G27' then 'household_relationship_by_age_sex'
    when 'G29' then 'family_composition'
    when 'G36' then 'dwelling_structure'
    when 'G37' then 'tenure_landlord_by_dwelling_structure'
    when 'G46' then 'labour_force_status_by_age_sex'
    when 'G49' then 'qualification_level_by_age_sex'
    when 'G50' then 'field_of_study_by_age_sex'
    when 'G60' then 'occupation_by_age_sex'
    else lower(regexp_replace(trim(coalesce({{ table_name_expr }}, 'unknown')), '[^a-zA-Z0-9]+', '_', 'g'))
end
{% endmacro %}

{% macro clean_abs_category(category_expr, logical_code_expr) %}
nullif(
    btrim(
        case
            when {{ logical_code_expr }} in ('G54') then regexp_replace({{ category_expr }}, '^Industry:\s*', '', 'i')
            when {{ logical_code_expr }} in ('G60') then regexp_replace({{ category_expr }}, '^Occupation:\s*', '', 'i')
            when {{ logical_code_expr }} in ('G50') then regexp_replace({{ category_expr }}, '^Field of study:\s*', '', 'i')
            when {{ logical_code_expr }} in ('G36') then regexp_replace({{ category_expr }}, '^Dwelling structure:\s*', '', 'i')
            else {{ category_expr }}
        end
    ),
    ''
)
{% endmacro %}
