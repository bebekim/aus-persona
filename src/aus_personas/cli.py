"""Command line entrypoints for aus-personas."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

from aus_personas.abs_metadata import (
    FIRST_PASS_LOGICAL_TABLES,
    fetch_dictionary,
    write_decoded_columns,
)
from aus_personas.census.semantic_catalog import (
    DEFAULT_SEMANTIC_CATALOG,
    load_semantic_catalog,
    normalize_raw_column,
    validate_sa2_physical_table,
)
from aus_personas.census.semantic_queries import (
    QueryOptions,
    columns_sql,
    decode_column_sql,
    long_sql,
    profile_sql,
    run_psql_csv,
)
from aus_personas.dbt_config import (
    DEFAULT_DBT_PROJECT,
    DEFAULT_DBT_SOURCES,
    DEFAULT_SOURCE_CONFIG,
    render_dbt_config,
)
from aus_personas.sample_sizes import (
    DEFAULT_SAMPLE_PRESET,
    SAMPLE_SIZE_PRESETS,
    resolve_sample_size,
)
from aus_personas.sampler.weighted_sampler import generate_seed_profiles


def main() -> None:
    parser = argparse.ArgumentParser(prog="aus-personas")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dictionary_parser = subparsers.add_parser(
        "build-abs-dictionary",
        help="Export a metadata-decoded ABS column dictionary.",
    )
    dictionary_parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/abs_dictionary.csv"),
    )
    dictionary_parser.add_argument(
        "--format",
        choices=("csv", "jsonl", "parquet"),
        default=None,
        help="Defaults to the output file extension.",
    )
    dictionary_parser.add_argument(
        "--container",
        default="censusloader-postgres",
        help="Running Docker container with censusloader Postgres.",
    )
    dictionary_parser.add_argument(
        "--geography",
        default="sa2",
        help="Geography prefix used when deriving physical table names.",
    )
    dictionary_parser.add_argument(
        "--logical-table",
        action="append",
        dest="logical_tables",
        help="Logical ABS table code to include, e.g. G17. Repeatable.",
    )
    dictionary_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all ABS metadata tables instead of the first persona pass.",
    )

    sample_size_parser = subparsers.add_parser(
        "sample-size",
        help="Print a named synthetic persona sample-size preset.",
    )
    sample_size_parser.add_argument(
        "preset",
        nargs="?",
        default=DEFAULT_SAMPLE_PRESET,
        choices=tuple(SAMPLE_SIZE_PRESETS),
        help="Named sample preset. Defaults to the first sampler target.",
    )

    render_dbt_parser = subparsers.add_parser(
        "render-dbt-sources",
        help="Render dbt source declarations from ABS Census source config.",
    )
    render_dbt_parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_SOURCE_CONFIG,
    )
    render_dbt_parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_DBT_SOURCES,
    )
    render_dbt_parser.add_argument(
        "--project",
        type=Path,
        default=DEFAULT_DBT_PROJECT,
    )


    pgm_parser = subparsers.add_parser(
        "pgm",
        help="Run PGM structured seed profile commands.",
    )
    pgm_subparsers = pgm_parser.add_subparsers(
        dest="pgm_command",
        required=True,
    )
    seed_parser = pgm_subparsers.add_parser(
        "seed-profiles",
        help="Generate ABS-backed structured seed profiles from PGM marts.",
    )
    seed_parser.add_argument("--schema", default="aus_personas_dbt")
    seed_parser.add_argument("--container", default="censusloader-postgres")
    seed_parser.add_argument("--sa2", dest="sa2_code", default=None)
    seed_parser.add_argument("--sample-size", type=int, default=10)
    seed_parser.add_argument("--seed", type=int, default=1)
    seed_parser.add_argument(
        "--format",
        choices=("table", "csv", "jsonl"),
        default="csv",
    )

    census_parser = subparsers.add_parser(
        "census",
        help="Run catalog-driven semantic Census queries.",
    )
    census_subparsers = census_parser.add_subparsers(
        dest="census_command",
        required=True,
    )

    tables_parser = census_subparsers.add_parser(
        "tables",
        help="List semantic Census tables in the local catalog.",
    )
    add_catalog_output_arguments(tables_parser)

    sections_parser = census_subparsers.add_parser(
        "sections",
        help="List semantic sections for one Census table.",
    )
    sections_parser.add_argument(
        "logical_table",
        help="Logical ABS table code, e.g. G01 or G17.",
    )
    add_catalog_output_arguments(sections_parser)

    worthy_parser = census_subparsers.add_parser(
        "worthy",
        help="List persona-worthiness guardrails for semantic Census topics.",
    )
    worthy_parser.add_argument(
        "logical_table",
        nargs="?",
        help="Optional logical ABS table code, e.g. G01 or G17.",
    )
    worthy_parser.add_argument(
        "--stage",
        default=None,
        help="Optional persona stage filter. Stage 1 currently means the cataloged topics.",
    )
    worthy_parser.add_argument(
        "--section",
        default=None,
        help="Optional semantic section for a single purpose decision.",
    )
    worthy_parser.add_argument(
        "--purpose",
        default=None,
        choices=("sample", "condition", "validate", "generate"),
        help="Optional purpose for a single guardrail decision.",
    )
    add_catalog_output_arguments(worthy_parser)

    columns_parser = census_subparsers.add_parser(
        "columns",
        help="List decoded columns for one semantic Census table.",
    )
    add_semantic_query_arguments(columns_parser)

    profile_parser = census_subparsers.add_parser(
        "profile",
        help="Profile raw measure columns for one semantic Census table.",
    )
    add_semantic_query_arguments(profile_parser)

    long_parser = census_subparsers.add_parser(
        "long",
        help="Return a long semantic section for one Census table.",
    )
    add_semantic_query_arguments(long_parser)
    long_parser.add_argument(
        "section",
        help="Semantic section name, e.g. age_group_by_sex or personal_income.",
    )
    long_parser.add_argument(
        "--sa2",
        dest="sa2_code",
        default=None,
        help="Optional SA2 code filter.",
    )
    long_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum rows to print. Use 0 for no limit.",
    )

    decode_parser = census_subparsers.add_parser(
        "decode-column",
        help="Decode one raw sa2_* column using metadata-derived labels.",
    )
    decode_parser.add_argument(
        "physical_table",
        help="SA2 physical table, e.g. sa2_g06.",
    )
    decode_parser.add_argument(
        "raw_column",
        help="Raw column, e.g. g743.",
    )
    decode_parser.add_argument(
        "--schema",
        default="aus_personas_dbt",
        help="dbt target schema containing the decoded column dictionary.",
    )
    decode_parser.add_argument(
        "--container",
        default="censusloader-postgres",
        help="Running Docker container with censusloader Postgres.",
    )
    decode_parser.add_argument(
        "--format",
        choices=("table", "csv", "jsonl", "sql"),
        default="table",
        help="Output format. Use sql to print the generated SQL without running it.",
    )

    args = parser.parse_args()

    if args.command == "build-abs-dictionary":
        logical_tables = (
            None if args.all else args.logical_tables or FIRST_PASS_LOGICAL_TABLES
        )
        columns = fetch_dictionary(
            logical_tables=logical_tables,
            geography=args.geography,
            container=args.container,
        )
        write_decoded_columns(columns, args.output, file_format=args.format)
        print(f"Wrote {len(columns)} decoded ABS columns to {args.output}")
    elif args.command == "sample-size":
        print(resolve_sample_size(args.preset))
    elif args.command == "render-dbt-sources":
        render_dbt_config(args.config, args.output, args.project)
        print(f"Rendered dbt sources to {args.output}")
        print(f"Rendered dbt source vars to {args.project}")
    elif args.command == "pgm":
        run_pgm_command(args)
    elif args.command == "census":
        run_census_command(args)


def add_semantic_query_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "logical_table",
        help="Logical ABS table code, e.g. G01 or G17.",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_SEMANTIC_CATALOG,
        help="Semantic catalog YAML path.",
    )
    parser.add_argument(
        "--schema",
        default="aus_personas_dbt",
        help="dbt target schema containing core Census models.",
    )
    parser.add_argument(
        "--container",
        default="censusloader-postgres",
        help="Running Docker container with censusloader Postgres.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "csv", "jsonl", "sql"),
        default="table",
        help="Output format. Use sql to print the generated SQL without running it.",
    )


def add_catalog_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_SEMANTIC_CATALOG,
        help="Semantic catalog YAML path.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "csv", "jsonl"),
        default="table",
        help="Output format.",
    )


def run_census_command(args: argparse.Namespace) -> None:
    if args.census_command == "decode-column":
        physical_table = validate_sa2_physical_table(args.physical_table)
        raw_column = normalize_raw_column(args.raw_column)
        sql = decode_column_sql(
            physical_table,
            raw_column,
            schema=args.schema,
        )
        if args.format == "sql":
            print(sql)
            return
        rows = run_psql_csv(sql, container=args.container)
        write_rows(rows, args.format)
        return

    catalog = load_semantic_catalog(args.catalog)
    if args.census_command == "tables":
        write_rows(catalog.inventory_rows(), args.format)
        return

    if args.census_command == "sections":
        write_rows(catalog.section_rows(args.logical_table), args.format)
        return

    if args.census_command == "worthy":
        if args.stage not in (None, "1"):
            raise ValueError("Only persona stage 1 is currently cataloged")
        if args.section or args.purpose:
            if not args.logical_table or not args.section or not args.purpose:
                raise ValueError(
                    "logical_table, --section, and --purpose are required together"
                )
            write_rows(
                [
                    catalog.guardrail_decision(
                        args.logical_table,
                        args.section,
                        args.purpose,
                    ).as_row()
                ],
                args.format,
            )
            return
        write_rows(catalog.worthiness_rows(args.logical_table), args.format)
        return

    table = catalog.table(args.logical_table)
    if not table.is_sa2_only:
        raise ValueError(
            f"Only sa2_* physical tables are allowed for persona work: "
            f"{', '.join(table.default_physical_tables)}"
        )
    options = QueryOptions(
        schema=args.schema,
        container=args.container,
        sa2_code=getattr(args, "sa2_code", None),
        limit=normalise_limit(getattr(args, "limit", None)),
    )

    if args.census_command == "columns":
        sql = columns_sql(table, schema=options.schema)
    elif args.census_command == "profile":
        sql = profile_sql(table, schema=options.schema)
    elif args.census_command == "long":
        section = catalog.section(args.logical_table, args.section)
        sql = long_sql(
            table,
            section,
            schema=options.schema,
            sa2_code=options.sa2_code,
            limit=options.limit,
        )
    else:
        raise ValueError(f"Unsupported census command: {args.census_command}")

    if args.format == "sql":
        print(sql)
        return

    rows = run_psql_csv(sql, container=options.container)
    write_rows(rows, args.format)



def run_pgm_command(args: argparse.Namespace) -> None:
    if args.pgm_command != "seed-profiles":
        raise ValueError(f"Unsupported pgm command: {args.pgm_command}")

    age_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_age_sex",
            [
                "census_year",
                "sa2_code",
                "sa2_name",
                "state_name",
                "age_band",
                "sex",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    labour_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_labour_force_status",
            [
                "sa2_code",
                "age_band",
                "sex",
                "labour_force_status",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    income_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_personal_income",
            [
                "sa2_code",
                "age_band",
                "sex",
                "income_band",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    country_of_birth_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_country_of_birth",
            [
                "sa2_code",
                "age_band",
                "sex",
                "country_of_birth",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    language_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_language_home_english_proficiency",
            [
                "sa2_code",
                "sex",
                "language_used_at_home",
                "english_proficiency",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    household_relationship_rows = run_psql_csv(
        pgm_mart_sql(
            args.schema,
            "mart_pgm__sa2_household_relationship",
            [
                "sa2_code",
                "age_band",
                "sex",
                "household_relationship",
                "count",
                "probability_within_partition",
            ],
            args.sa2_code,
        ),
        container=args.container,
    )
    profiles = generate_seed_profiles(
        age_sex_rows=age_rows,
        labour_rows=labour_rows,
        income_rows=income_rows,
        country_of_birth_rows=country_of_birth_rows,
        language_rows=language_rows,
        household_relationship_rows=household_relationship_rows,
        sample_size=args.sample_size,
        rng=random.Random(args.seed),
    )
    write_rows(profiles, args.format)


def pgm_mart_sql(
    schema: str,
    mart_name: str,
    columns: list[str],
    sa2_code: str | None,
) -> str:
    quoted_columns = ", ".join(columns)
    sql = f"select {quoted_columns} from {schema}.{mart_name}"
    if sa2_code:
        sql += f" where sa2_code = {sql_quote(sa2_code)}"
    return sql


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

def normalise_limit(limit: int | None) -> int | None:
    if limit == 0:
        return None
    return limit


def write_rows(rows: list[dict[str, str]], output_format: str) -> None:
    if output_format == "jsonl":
        for row in rows:
            print(json.dumps(row, sort_keys=True))
        return

    if output_format == "csv":
        if not rows:
            return
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return

    if output_format == "table":
        write_table(rows)
        return

    raise ValueError(f"Unsupported output format: {output_format}")


def write_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("(0 rows)")
        return

    columns = list(rows[0])
    widths = {
        column: min(
            max(len(column), *(len(row.get(column, "")) for row in rows)),
            48,
        )
        for column in columns
    }
    print("  ".join(column[: widths[column]].ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        print(
            "  ".join(
                row.get(column, "")[: widths[column]].ljust(widths[column])
                for column in columns
            )
        )


if __name__ == "__main__":
    main()
