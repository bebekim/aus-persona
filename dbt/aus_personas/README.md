# aus_personas dbt

Lightweight dbt project for normalizing ABS Census `censusloader` tables into
sampler-ready observations.

## Local Setup

Start the existing local Postgres container:

```sh
docker start censusloader-postgres
```

Create a local profile from the example if you want to run dbt directly from
this directory:

```sh
cp profiles.yml.example profiles.yml
```

The default profile expects:

```text
host: 127.0.0.1
port: 5433
user: dbt_user
database: postgres
schema: aus_personas_dbt
```

Run:

```sh
uv run dbt debug --profiles-dir dbt/aus_personas --project-dir dbt/aus_personas
uv run dbt run --profiles-dir dbt/aus_personas --project-dir dbt/aus_personas
uv run dbt test --profiles-dir dbt/aus_personas --project-dir dbt/aus_personas
```

## Model Flow

```text
censusloader raw wide tables
  -> staging metadata/geography
  -> int_abs__column_dictionary
  -> int_abs__sa2_observations
  -> dim_sa2
  -> fct_census_observation
```

The mart exposes decoded, long-form census observations and preserves source
lineage back to `physical_table` and `raw_column`.
