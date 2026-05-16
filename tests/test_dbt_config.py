from pathlib import Path

import pytest

from aus_personas.dbt_config import (
    AbsCensusSourceConfig,
    load_abs_census_source_config,
    render_dbt_config,
    render_abs_sources_yml,
    validate_abs_census_source_config,
)


def test_loads_abs_census_source_config():
    config = load_abs_census_source_config(Path("configs/abs_census_sources.yml"))

    assert "sa2_g08" in config.physical_profile_tables
    assert config.physical_profile_tables[0] == "sa2_g01"
    assert config.boundary_table == "sa2_2021_aust_gda94"


def test_renders_abs_sources_from_config():
    config = load_abs_census_source_config(Path("configs/abs_census_sources.yml"))
    rendered = render_abs_sources_yml(config)

    assert "- name: metadata_tables" in rendered
    assert "- name: sa2_g08" in rendered
    assert "- name: sa2_g60b" in rendered
    assert "- name: sa2_2021_aust_gda94" in rendered


def test_rejects_duplicate_source_tables():
    config = AbsCensusSourceConfig(
        geography_level="sa2",
        census_source_name="abs_census",
        boundary_source_name="abs_boundaries",
        census_database="postgres",
        census_schema_var="census_data_schema",
        census_schema_default="census_2021_data",
        boundary_schema_var="census_boundary_schema",
        boundary_schema_default="census_2021_bdys_gda94",
        boundary_table="sa2_2021_aust_gda94",
        metadata_tables=("metadata_tables", "metadata_tables"),
        profile_tables=(),
    )

    with pytest.raises(ValueError, match="Duplicate table declarations"):
        validate_abs_census_source_config(config)


def test_rejects_profile_table_outside_geography_prefix():
    config = AbsCensusSourceConfig(
        geography_level="sa2",
        census_source_name="abs_census",
        boundary_source_name="abs_boundaries",
        census_database="postgres",
        census_schema_var="census_data_schema",
        census_schema_default="census_2021_data",
        boundary_schema_var="census_boundary_schema",
        boundary_schema_default="census_2021_bdys_gda94",
        boundary_table="sa2_2021_aust_gda94",
        metadata_tables=("metadata_tables", "metadata_stats"),
        profile_tables=({"physical_tables": ["poa_g08"]},),
    )

    with pytest.raises(ValueError, match="Profile tables must start"):
        validate_abs_census_source_config(config)


def test_renders_dbt_sources_and_project_vars(tmp_path):
    source_config = Path("configs/abs_census_sources.yml")
    sources_output = tmp_path / "sources.yml"
    project_output = tmp_path / "dbt_project.yml"
    project_output.write_text(
        """
name: aus_personas
vars:
  geography_level: sa2
  first_pass_sa2_tables:
    - sa2_g01
"""
    )

    render_dbt_config(source_config, sources_output, project_output)

    assert "- name: sa2_g08" in sources_output.read_text()
    assert "sa2_g08" in project_output.read_text()
