# Spec 01: dbt Census Source Ingestion

## Goal

Set up a lightweight dbt project that ingests ABS Census tables from the
existing `censusloader-postgres` database into a documented, normalized data
model for Australian persona sampling.

This spec exists because ABS profile tables are wide (`sa2_g17a.g5211` style),
while the sampler needs explicit observations:

```text
sa2_code | G17 | age_band | sex | income_band | count
```

The implementation must be metadata-first: raw ABS storage names remain
available for lineage, but downstream models consume readable aliases and parsed
axes.

## Context

Current loaded source:

```text
Docker context: OrbStack
container: censusloader-postgres
image: minus34/censusloader:latest
database: postgres
source schemas:
  census_2021_data
  census_2021_bdys_gda94
```

Confirmed joins:

```text
census_2021_data.sa2_<profile>.region_id
  = census_2021_bdys_gda94.sa2_2021_aust_gda94.sa2_code_2021
```

Relevant docs already created:

```text
docs/abs-census-dictionary.md
docs/abs-source-provenance.md
```

Existing Python metadata decoder:

```text
src/aus_personas/abs_metadata.py
```

## KHC Reference Decision

`~/Sync/khc` is a useful reference for patterns, but it is too enterprise-heavy
to copy directly.

Do borrow:

- explicit source declarations
- source/staging/intermediate/mart layers
- metadata-driven transforms
- tests on identifiers, not-null keys, accepted values, and row-count sanity
- stable naming conventions

Do not borrow for this repo:

- Dagster orchestration
- Azure Data Factory
- Snowflake-specific macros
- 150-project domain layout
- event orchestration
- environment framework package
- enterprise deployment scaffolding

This repo needs one small dbt project, not a platform.

## `demo_dbt` Reference Decision

The lightweight dbt example at <https://github.com/mjkahan/demo_dbt> is closer
to the desired project scale than `~/Sync/khc`.

Its useful shape:

```text
analysis/
data/
macros/
models/staging/
snapshots/
tests/
dbt_project.yml
packages.yml
profiles.yml
```

Borrow:

- one dbt project at the repo level or under a simple subdirectory
- ordinary dbt folders with minimal ceremony
- checked-in example profile for local development
- staging models as the first readable layer
- tests colocated with dbt models

Adapt:

- keep our project under `dbt/aus_personas/` so Python tooling and dbt tooling
  stay separate
- use `profiles.yml.example` rather than committing active credentials
- expand beyond `models/staging/` because census normalization needs
  `staging`, `intermediate`, and `marts`

Do not borrow:

- Snowflake-specific assumptions
- demo-only starter models
- sample-data assumptions unrelated to ABS Census

## Non-Goals

- Do not build the PGM sampler in this spec.
- Do not generate synthetic personas in this spec.
- Do not ingest every ABS geography.
- Do not import 2026 Census data yet.
- Do not add Dagster/Airflow/ADF.
- Do not delete or mutate source censusloader tables.
- Do not correct counts for overcount/undercount.

## 2026 Readiness

The model must not hard-code `2021` in ways that make 2026 awkward.

Use a `census_year` variable where practical:

```yaml
vars:
  census_year: 2021
  census_data_schema: census_2021_data
  census_boundary_schema: census_2021_bdys_gda94
  geography_level: sa2
```

Object names can include `2021` where the upstream source does, but model logic
should be able to accept:

```text
census_2026_data
census_2026_bdys_<datum>
sa2_2026_aust_<datum>
```

when 2026 data arrives.

## Target Layout

Create a dbt project under:

```text
dbt/aus_personas/
```

Minimum structure:

```text
dbt/aus_personas/
  dbt_project.yml
  profiles.yml.example
  README.md
  macros/
    generate_census_observation_union.sql
    parse_abs_axis_helpers.sql
  models/
    sources/
      abs_sources.yml
    staging/
      stg_abs__metadata_tables.sql
      stg_abs__metadata_stats.sql
      stg_abs__sa2_geography.sql
      schema.yml
    intermediate/
      int_abs__column_dictionary.sql
      int_abs__sa2_observations.sql
      schema.yml
    marts/
      dim_sa2.sql
      fct_census_observation.sql
      schema.yml
```

If dbt package dependencies are needed, add `packages.yml`, but keep dependency
count minimal.

## Source Layer

Declare these sources in `models/sources/abs_sources.yml`.

### `abs_census`

Schema variable:

```text
{{ var('census_data_schema', 'census_2021_data') }}
```

Required source tables:

```text
metadata_tables
metadata_stats
sa2_g01
sa2_g04a
sa2_g04b
sa2_g05
sa2_g07
sa2_g09a
sa2_g09b
sa2_g09c
sa2_g09d
sa2_g09e
sa2_g09f
sa2_g09g
sa2_g09h
sa2_g13a
sa2_g13b
sa2_g13c
sa2_g13d
sa2_g13e
sa2_g16a
sa2_g16b
sa2_g17a
sa2_g17b
sa2_g17c
sa2_g27a
sa2_g27b
sa2_g29
sa2_g36
sa2_g37
sa2_g46a
sa2_g46b
sa2_g49a
sa2_g49b
sa2_g50a
sa2_g50b
sa2_g50c
sa2_g60a
sa2_g60b
```

This is the first persona feature set. Add more tables only in later specs.

### `abs_boundaries`

Schema variable:

```text
{{ var('census_boundary_schema', 'census_2021_bdys_gda94') }}
```

Required source table:

```text
sa2_2021_aust_gda94
```

## Data Model

### `stg_abs__metadata_tables`

Grain:

```text
one row per ABS logical table, e.g. G17
```

Columns:

```text
logical_table_code
logical_table_name
population_universe
source_table_number
```

Rules:

- trim whitespace
- preserve original ABS text
- infer `source_profile` from first character of `logical_table_code`
- infer `profile_family_name`

### `stg_abs__metadata_stats`

Grain:

```text
one row per ABS statistic column, e.g. G5211
```

Columns:

```text
sequential_id
raw_column
short_id
long_id
physical_table_suffix
logical_table_code
source_profile
source_label
```

Rules:

- `raw_column = lower(sequential_id)`
- `physical_table_suffix = lower(table_number)`
- `logical_table_code = upper(left(table_number, 3))`
- keep both `table_number` and `profile_table` for lineage because split tables
  may use both differently

### `stg_abs__sa2_geography`

Grain:

```text
one row per SA2 boundary
```

Columns:

```text
sa2_code
sa2_name
sa3_code
sa3_name
sa4_code
sa4_name
gccsa_code
gccsa_name
state_code
state_name
country_code
country_name
area_albers_sqkm
```

Geometry can be excluded from the first dbt model unless the adapter handles it
cleanly. Keep spatial analysis for a later spec.

### `int_abs__column_dictionary`

Grain:

```text
one row per source statistic column
```

Columns:

```text
source_profile
profile_family_name
logical_table_code
logical_table_name
project_alias
population_universe
physical_table_suffix
physical_table
raw_column
sequential_id
short_id
long_id
source_label
sex
age_band
category_axis
category
axes_json
is_total
```

Rules:

- Match the behavior of `src/aus_personas/abs_metadata.py` as closely as
  practical in SQL.
- It is acceptable for v0.1 to implement only the first-pass parsed axes:
  `sex`, `age_band`, `category_axis`, `category`, `is_total`.
- If SQL parsing becomes ugly, implement this model from a seed/export generated
  by the Python decoder and document that choice. Prefer dbt SQL if reasonable.

### `int_abs__sa2_observations`

Grain:

```text
one row per SA2, physical table, raw statistic column
```

Columns:

```text
sa2_code
physical_table
raw_column
count
```

Rules:

- Unpivot the selected wide `sa2_*` profile tables.
- Use a macro to generate the `union all` blocks from a table list, rather than
  hand-writing thousands of column references.
- Exclude `region_id` from unpivoted columns.
- Preserve zero counts.
- Cast counts to integer.

### `dim_sa2`

Grain:

```text
one row per SA2 used in Census profile stats
```

Columns:

```text
sa2_code
sa2_name
sa3_code
sa3_name
sa4_code
sa4_name
gccsa_code
gccsa_name
state_code
state_name
country_name
area_albers_sqkm
```

Rules:

- Source from `stg_abs__sa2_geography`.
- Include only SA2s that have matching census observations unless explicitly
  configured otherwise.

### `fct_census_observation`

Grain:

```text
one row per decoded observation
```

Columns:

```text
census_year
geography_level
sa2_code
sa2_name
state_name
source_profile
profile_family_name
logical_table_code
logical_table_name
project_alias
population_universe
physical_table
raw_column
sequential_id
short_id
long_id
source_label
sex
age_band
category_axis
category
axes_json
is_total
count
```

Rules:

- Join `int_abs__sa2_observations` to `int_abs__column_dictionary` on:

```text
physical_table
raw_column
```

- Join to `dim_sa2` on `sa2_code`.
- No raw `g17a`/`g5211` semantics should be needed downstream.

## Tests

Add dbt tests for:

### Sources

- `metadata_tables.table_number` not null
- `metadata_stats.sequential_id` not null
- `metadata_stats.sequential_id` unique
- SA2 geography `sa2_code_2021` not null

### Staging

- `stg_abs__metadata_tables.logical_table_code` unique and not null
- `stg_abs__metadata_stats.sequential_id` unique and not null
- `stg_abs__sa2_geography.sa2_code` unique and not null

### Intermediate

- `int_abs__column_dictionary` unique on `(physical_table, raw_column)`
- no null `project_alias` for selected persona tables
- accepted values for `source_profile`: `G`, `P`, `W`, `I`, `T`
- accepted values for `sex`: `Male`, `Female`, `Persons`, null

### Mart

- `dim_sa2.sa2_code` unique and not null
- `fct_census_observation.sa2_code` not null
- `fct_census_observation.count` not null
- no observations missing dictionary metadata
- row count sanity:
  - `sa2_g01` contributes `2472 * 108` observation rows
  - `sa2_g60a` contributes `2472 * 200` observation rows

If exact row-count tests are awkward in dbt generic tests, add singular SQL
tests.

## CLI / Developer Commands

Add a short README section for local use:

```sh
docker start censusloader-postgres
cd dbt/aus_personas
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

If the local environment does not have dbt-postgres installed, document the
installation command rather than vendoring it.

## Acceptance Criteria

- `dbt/aus_personas` exists with a minimal dbt project.
- Sources are declared for the first-pass ABS profile tables.
- Models exist for:
  - `stg_abs__metadata_tables`
  - `stg_abs__metadata_stats`
  - `stg_abs__sa2_geography`
  - `int_abs__column_dictionary`
  - `int_abs__sa2_observations`
  - `dim_sa2`
  - `fct_census_observation`
- The model naming and columns match this spec unless a documented reason is
  added.
- Tests cover source keys, model keys, metadata joins, accepted values, and row
  sanity.
- The project can target the running `censusloader-postgres` Postgres database.
- 2026 Census support is represented through dbt variables and naming choices.
- Documentation states that this is a lightweight dbt project, not a KHC-style
  enterprise platform.

## Implementation Notes

The hardest part is unpivoting wide source tables. Keep it boring:

1. Use dbt source metadata or a manually curated first-pass table list.
2. Query `information_schema.columns` for each selected table.
3. Generate `union all` SQL that emits:

```text
region_id as sa2_code
'sa2_g17a' as physical_table
'g5211' as raw_column
g5211::integer as count
```

4. Join to the dictionary.

Avoid making the parser perfect in v0.1. The important success condition is a
lossless, documented, normalized observation model. Fine-grained axis parsing
can improve incrementally.
