from pathlib import Path

from aus_personas.orchestration.dbt_jobs import (
    build_dbt_definitions,
    load_dbt_job_configs,
)


def test_loads_configured_dbt_jobs():
    jobs = load_dbt_job_configs(Path("configs/orchestration/dbt_jobs.yml"))

    assert [job.name for job in jobs] == [
        "census_core",
        "g01_semantic",
    ]
    assert jobs[0].argv()[-2:] == [
        "--select",
        "int_abs__column_dictionary int_abs__sa2_observations dim_sa2 fct_census_observation",
    ]
    assert jobs[1].argv()[-2:] == ["--select", "tag:g01"]


def test_builds_dagster_definitions_from_config():
    defs = build_dbt_definitions(Path("configs/orchestration/dbt_jobs.yml"))
    job_names = sorted(defs.get_repository_def().job_names)

    assert job_names == [
        "dbt_census_core_job",
        "dbt_g01_semantic_job",
    ]
