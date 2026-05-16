"""Dagster code location for local aus-personas orchestration."""

from aus_personas.orchestration.dbt_jobs import build_dbt_definitions


defs = build_dbt_definitions()
