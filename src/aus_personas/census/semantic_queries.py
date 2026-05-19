"""SQL builders and runners for semantic ABS Census queries."""

from __future__ import annotations

import csv
import subprocess
from dataclasses import dataclass

from aus_personas.census.semantic_catalog import SemanticSection, SemanticTable


@dataclass(frozen=True)
class QueryOptions:
    schema: str = "aus_personas_dbt"
    container: str = "censusloader-postgres"
    sa2_code: str | None = None
    limit: int | None = 20


def columns_sql(table: SemanticTable, *, schema: str = "aus_personas_dbt") -> str:
    physical_tables = sql_string_list(table.default_physical_tables)
    return f"""
select
  d.logical_table_code,
  d.physical_table,
  d.raw_column,
  d.short_id,
  d.long_id,
  d.source_label,
  d.sex,
  d.age_band,
  d.category_axis,
  d.category,
  d.is_total
from {schema}.int_abs__column_dictionary d
where d.logical_table_code = {sql_quote(table.logical_table)}
  and d.physical_table in ({physical_tables})
order by d.physical_table, substring(d.raw_column from 2)::integer
""".strip()


def decode_column_sql(
    physical_table: str,
    raw_column: str,
    *,
    schema: str = "aus_personas_dbt",
) -> str:
    return f"""
select
  d.physical_table,
  d.raw_column,
  d.source_profile,
  d.logical_table_code as table_number,
  d.logical_table_name as table_name,
  d.population_universe as table_description,
  d.project_alias,
  d.sequential_id,
  d.short_id,
  d.long_id,
  d.source_label as column_heading_description,
  d.sex,
  d.age_band,
  d.category_axis,
  d.category,
  d.is_total,
  d.axes_json
from {schema}.int_abs__column_dictionary d
where d.physical_table = {sql_quote(physical_table)}
  and lower(d.raw_column) = {sql_quote(raw_column.lower())}
order by d.physical_table, substring(d.raw_column from 2)::integer
""".strip()


def profile_sql(table: SemanticTable, *, schema: str = "aus_personas_dbt") -> str:
    physical_tables = sql_string_list(table.default_physical_tables)
    return f"""
with obs as (
  select o.physical_table, o.raw_column, o.count
  from {schema}.int_abs__sa2_observations o
  where o.physical_table in ({physical_tables})
),
modes as (
  select
    physical_table,
    raw_column,
    count as mode_count,
    count(*) as mode_frequency,
    row_number() over (
      partition by physical_table, raw_column
      order by count(*) desc, count asc nulls last
    ) as mode_rank
  from obs
  group by physical_table, raw_column, count
),
stats as (
  select
    physical_table,
    raw_column,
    count(*) as sa2_count,
    count(*) filter (where count is null) as null_count,
    count(*) filter (where count = 0) as zero_count,
    min(count) as min_count,
    percentile_cont(0.25) within group (order by count) as p25_count,
    percentile_cont(0.5) within group (order by count) as median_count,
    avg(count)::numeric(18, 2) as mean_count,
    percentile_cont(0.75) within group (order by count) as p75_count,
    max(count) as max_count
  from obs
  group by physical_table, raw_column
)
select
  d.logical_table_code,
  s.physical_table,
  s.raw_column,
  d.short_id,
  d.long_id,
  d.source_label,
  d.sex,
  d.age_band,
  d.category_axis,
  d.category,
  d.is_total,
  s.sa2_count,
  s.null_count,
  s.zero_count,
  s.min_count,
  s.p25_count,
  s.median_count,
  s.mean_count,
  s.p75_count,
  s.max_count,
  m.mode_count,
  m.mode_frequency
from stats s
join {schema}.int_abs__column_dictionary d
  on d.physical_table = s.physical_table
 and d.raw_column = s.raw_column
left join modes m
  on m.physical_table = s.physical_table
 and m.raw_column = s.raw_column
 and m.mode_rank = 1
order by s.physical_table, substring(s.raw_column from 2)::integer
""".strip()


def long_sql(
    table: SemanticTable,
    section: SemanticSection,
    *,
    schema: str = "aus_personas_dbt",
    sa2_code: str | None = None,
    limit: int | None = 20,
) -> str:
    physical_tables = sql_string_list(table.default_physical_tables)
    where = [
        f"d.logical_table_code = {sql_quote(table.logical_table)}",
        f"o.physical_table in ({physical_tables})",
        section.raw_column_predicate,
    ]
    if sa2_code:
        where.append(f"o.sa2_code = {sql_quote(sa2_code)}")

    limit_sql = "" if limit is None else f"\nlimit {limit}"
    value_expr = semantic_value_expression(section.value_column)
    value_alias_sql = semantic_value_alias_sql(section, value_expr)
    sampling_eligibility_sql = sampling_eligibility_expression(section)
    return f"""
select
  o.sa2_code,
  g.sa2_name,
  g.state_name,
  d.logical_table_code,
  {sql_quote(section.section)} as semantic_section,
  {sql_quote(section.grain)} as grain,
  d.physical_table,
  d.raw_column,
  {sql_quote(section.feature_name)} as feature_name,
  {value_expr} as feature_value,
{value_alias_sql}
  d.sex,
  d.age_band,
  d.category_axis,
  d.category,
  o.count,
  d.is_total,
  {sampling_eligibility_sql} as is_sampling_eligible,
  {sql_quote(section.total_policy)} as total_policy,
  d.source_label,
  d.short_id,
  d.long_id
from {schema}.int_abs__sa2_observations o
join {schema}.int_abs__column_dictionary d
  on d.physical_table = o.physical_table
 and d.raw_column = o.raw_column
join {schema}.dim_sa2 g
  on g.sa2_code = o.sa2_code
where {" and ".join(where)}
order by o.sa2_code, d.physical_table, substring(d.raw_column from 2)::integer{limit_sql}
""".strip()


def semantic_value_expression(value_column: str) -> str:
    if value_column in {"sex", "age_band", "category"}:
        return f"d.{value_column}"
    if value_column in {"english_proficiency", "household_size"}:
        return f"d.axes_json::jsonb ->> {sql_quote(value_column)}"
    return "d.category"


def semantic_value_alias_sql(section: SemanticSection, value_expr: str) -> str:
    aliases: list[str] = []
    if section.value_alias:
        aliases.append(f"  {value_expr} as {section.value_alias},")
    for alias in section.extra_value_aliases:
        aliases.append(f"  {semantic_value_expression(alias)} as {alias},")
    return "\n".join(aliases) + ("\n" if aliases else "")


def sampling_eligibility_expression(section: SemanticSection) -> str:
    conditions = [
        f"{sql_quote(str(section.is_sampler_candidate).lower())}::boolean",
        "not d.is_total",
        "o.count is not null",
        "coalesce(d.sex, '') <> 'Persons'",
        "coalesce(d.category, '') not in ('Not stated', 'Not applicable')",
    ]
    for alias in section.extra_value_aliases:
        alias_expr = semantic_value_expression(alias)
        conditions.append(
            f"coalesce({alias_expr}, '') not in ('Not stated', 'Not applicable')"
        )
    return "\n    and ".join(conditions)


def run_psql_csv(sql: str, *, container: str) -> list[dict[str, str]]:
    copy_sql = f"copy ({sql}) to stdout with csv header"
    completed = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-c",
            copy_sql,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("Failed to run semantic query: " + completed.stderr.strip())
    return list(csv.DictReader(completed.stdout.splitlines()))


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_string_list(values: tuple[str, ...]) -> str:
    return ", ".join(sql_quote(value) for value in values)
