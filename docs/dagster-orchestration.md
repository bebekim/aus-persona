# Dagster Orchestration

This project uses a small config-driven Dagster layer inspired by the KHC
repository pattern, but without plugin discovery or enterprise deployment
machinery.

The orchestration source of truth is:

```text
configs/orchestration/dbt_jobs.yml
```

Each entry declares one dbt command and selector. Dagster turns those entries
into jobs.

Current jobs:

| Dagster job | dbt selector | Purpose |
| --- | --- | --- |
| `dbt_census_core_job` | `int_abs__column_dictionary int_abs__sa2_observations dim_sa2 fct_census_observation` | Shared decoded Census foundations |
| `dbt_g01_semantic_job` | `tag:g01` | Interpreted G01 semantic views |

Local entrypoint:

```text
src/aus_personas/orchestration/definitions.py
```

Dagster workspace:

```text
workspace.yaml
```

Run a job from the CLI:

```bash
DAGSTER_HOME="$PWD/dagster_home" uv run dagster job execute \
  -m aus_personas.orchestration.definitions \
  -j dbt_g01_semantic_job
```

Open the UI:

```bash
DAGSTER_HOME="$PWD/dagster_home" uv run dagster dev -w workspace.yaml
```

Run Dagster in a separate Docker container:

```bash
docker compose up --build abs-persona-orchestrator
```

The Dagster container connects to the existing `censusloader-postgres` database
through the host-exposed Postgres port:

```text
host.docker.internal:5433
```

That keeps the Census/Postgres image unchanged. The Docker split is:

```text
censusloader-postgres  -> database only
abs-persona-orchestrator -> Dagster + dbt + aus-personas code
```

Raw Census tables remain untouched. These jobs only run dbt transformations into
the dbt target schema.
