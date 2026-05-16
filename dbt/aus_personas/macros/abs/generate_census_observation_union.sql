{% macro generate_census_observation_union(source_name, table_names) %}
  {%- set selects = [] -%}

  {%- if execute -%}
    {%- for table_name in table_names -%}
      {%- set relation = source(source_name, table_name) -%}
      {%- set columns = adapter.get_columns_in_relation(relation) -%}
      {%- set value_rows = [] -%}
      {%- for column in columns -%}
        {%- set column_name = column.name | lower -%}
        {%- if column_name != 'region_id' -%}
          {%- do value_rows.append("('" ~ column_name ~ "'::text, t." ~ adapter.quote(column.name) ~ "::integer)") -%}
        {%- endif -%}
      {%- endfor -%}

      {%- if value_rows | length > 0 -%}
        {%- set sql -%}
select
    t.region_id::text as sa2_code,
    '{{ table_name }}'::text as physical_table,
    v.raw_column,
    v.count
from {{ relation }} as t
cross join lateral (
    values
      {{ value_rows | join(',\n      ') }}
) as v(raw_column, count)
        {%- endset -%}
        {%- do selects.append(sql) -%}
      {%- endif -%}
    {%- endfor -%}
  {%- endif -%}

  {%- if selects | length == 0 -%}
select
    null::text as sa2_code,
    null::text as physical_table,
    null::text as raw_column,
    null::integer as count
where false
  {%- else -%}
    {{ selects | join('\nunion all\n') }}
  {%- endif -%}
{% endmacro %}

{% macro generate_declared_census_observation_union(source_name, table_prefix) %}
  {%- set table_names = [] -%}

  {%- for source_node in graph.nodes.values() -%}
    {%- if source_node.resource_type == 'source' and source_node.source_name == source_name and source_node.name.startswith(table_prefix ~ '_g') -%}
      {%- do table_names.append(source_node.name) -%}
    {%- endif -%}
  {%- endfor -%}

  {{ generate_census_observation_union(source_name, table_names | sort) }}
{% endmacro %}
