"""Render dbt configuration from lightweight project YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SOURCE_CONFIG = Path("configs/abs_census_sources.yml")
DEFAULT_DBT_SOURCES = Path("dbt/aus_personas/models/sources/abs_sources.yml")
DEFAULT_DBT_PROJECT = Path("dbt/aus_personas/dbt_project.yml")


@dataclass(frozen=True)
class AbsCensusSourceConfig:
    geography_level: str
    census_source_name: str
    boundary_source_name: str
    census_database: str
    census_schema_var: str
    census_schema_default: str
    boundary_schema_var: str
    boundary_schema_default: str
    boundary_table: str
    metadata_tables: tuple[str, ...]
    profile_tables: tuple[dict[str, Any], ...]

    @property
    def physical_profile_tables(self) -> tuple[str, ...]:
        tables: list[str] = []
        for profile_table in self.profile_tables:
            tables.extend(profile_table["physical_tables"])
        return tuple(tables)


def load_abs_census_source_config(path: Path) -> AbsCensusSourceConfig:
    with path.open() as file:
        raw_config = yaml.safe_load(file)

    return AbsCensusSourceConfig(
        geography_level=raw_config["geography_level"],
        census_source_name=raw_config["census_source_name"],
        boundary_source_name=raw_config["boundary_source_name"],
        census_database=raw_config["census_database"],
        census_schema_var=raw_config["census_schema_var"],
        census_schema_default=raw_config["census_schema_default"],
        boundary_schema_var=raw_config["boundary_schema_var"],
        boundary_schema_default=raw_config["boundary_schema_default"],
        boundary_table=raw_config["boundary_table"],
        metadata_tables=tuple(raw_config["metadata_tables"]),
        profile_tables=tuple(raw_config["profile_tables"]),
    )


def validate_abs_census_source_config(config: AbsCensusSourceConfig) -> None:
    tables = [*config.metadata_tables, *config.physical_profile_tables]
    duplicates = sorted({table for table in tables if tables.count(table) > 1})
    if duplicates:
        msg = f"Duplicate table declarations: {', '.join(duplicates)}"
        raise ValueError(msg)

    expected_prefix = f"{config.geography_level}_g"
    invalid_profile_tables = [
        table
        for table in config.physical_profile_tables
        if not table.startswith(expected_prefix)
    ]
    if invalid_profile_tables:
        msg = (
            f"Profile tables must start with {expected_prefix!r}: "
            + ", ".join(invalid_profile_tables)
        )
        raise ValueError(msg)


def render_abs_sources_yml(config: AbsCensusSourceConfig) -> str:
    validate_abs_census_source_config(config)

    lines = [
        "version: 2",
        "",
        "sources:",
        f"  - name: {config.census_source_name}",
        f"    database: {config.census_database}",
        "    schema: "
        + f"\"{{{{ var('{config.census_schema_var}', '{config.census_schema_default}') }}}}\"",
        "    tables:",
        "      - name: metadata_tables",
        "        columns:",
        "          - name: table_number",
        "            data_tests:",
        "              - not_null",
        "              - unique",
        "      - name: metadata_stats",
        "        columns:",
        "          - name: sequential_id",
        "            data_tests:",
        "              - not_null",
        "              - unique",
    ]

    for table in config.physical_profile_tables:
        lines.append(f"      - name: {table}")

    lines.extend(
        [
            "",
            f"  - name: {config.boundary_source_name}",
            f"    database: {config.census_database}",
            "    schema: "
            + f"\"{{{{ var('{config.boundary_schema_var}', '{config.boundary_schema_default}') }}}}\"",
            "    tables:",
            f"      - name: {config.boundary_table}",
            "        columns:",
            "          - name: sa2_code_2021",
            "            data_tests:",
            "              - not_null",
            "",
        ]
    )
    return "\n".join(lines)


def write_abs_sources_yml(config_path: Path, output_path: Path) -> None:
    config = load_abs_census_source_config(config_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_abs_sources_yml(config))


def write_dbt_project_source_vars(config_path: Path, project_path: Path) -> None:
    config = load_abs_census_source_config(config_path)
    validate_abs_census_source_config(config)

    with project_path.open() as file:
        project = yaml.safe_load(file)

    project.setdefault("vars", {})
    project["vars"]["first_pass_sa2_tables"] = list(config.physical_profile_tables)

    with project_path.open("w") as file:
        yaml.safe_dump(project, file, sort_keys=False)


def render_dbt_config(
    config_path: Path,
    sources_output_path: Path,
    project_path: Path,
) -> None:
    write_abs_sources_yml(config_path, sources_output_path)
    write_dbt_project_source_vars(config_path, project_path)
