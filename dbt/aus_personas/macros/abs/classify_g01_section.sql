{% macro classify_g01_section(raw_column_expr) %}
case
    when substring({{ raw_column_expr }} from 2)::integer between 1 and 3 then 'total_persons_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 4 and 36 then 'age_group_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 37 and 42 then 'census_night_location_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 43 and 54 then 'indigenous_summary_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 55 and 60 then 'birthplace_summary_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 61 and 66 then 'language_summary_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 67 and 69 then 'citizenship_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 70 and 84 then 'education_attendance_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 85 and 102 then 'school_completion_by_sex'
    when substring({{ raw_column_expr }} from 2)::integer between 103 and 108 then 'dwelling_residence_summary_by_sex'
end
{% endmacro %}
