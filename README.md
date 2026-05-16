# aus-personas

ABS-grounded synthetic Australian persona generation tooling.

This repository is building a pipeline from 2021 ABS Census SA2 distributions
to structured persona seed rows, then to Korea-style narrative persona fields
with NVIDIA DataDesigner or a similar generation step.

Raw ABS Census tables stay untouched. dbt and Dagster create reproducible
interpreted layers in a separate target schema.

## Status

Current:

- Raw ABS Census data is expected in local Postgres from `censusloader-postgres`.
- Persona-worthy `sa2_g*` Census tables are declared as dbt sources.
- dbt materializes the shared Census foundation models:
  - `int_abs__column_dictionary`
  - `int_abs__sa2_observations`
  - `dim_sa2`
  - `fct_census_observation`
- The latest targeted dbt foundation build passed with `17,294,112` Census
  observation rows.
- Dagster can orchestrate the dbt foundation and semantic jobs.

Not complete yet:

- semantic marts for every persona seed topic;
- probabilistic sampling into one synthetic resident per output row;
- narrative expansion into final persona prose.

## Data Model

One final persona row represents one synthetic Australian resident.

It does not represent one Census row, one Census response, or one real person.
The row is sampled from SA2-level Census distributions and then expanded into
persona text.

The raw ABS delivery format is wide:

```text
geography x profile table x hundreds of coded columns
```

The working model is narrow and grain-explicit:

```text
one readable Census topic -> one queryable semantic dataset
```

Foundation grain:

- `fct_census_observation`: one row represents one `SA2 + physical Census table + raw Census column`.

Future semantic mart grains:

- `mart_sa2_age_sex_distribution`: one row represents one `SA2 + age band + sex`.
- `mart_sa2_income_by_age_sex`: one row represents one `SA2 + income band + age band + sex`.
- `mart_sa2_occupation_by_age_sex`: one row represents one `SA2 + occupation + age band + sex`.

## Core Persona Seed Topics

Stage 1 focuses only on `sa2_*` tables. Other geographies are useful later for
validation, rollups, or special views, but SA2 is the persona sampling grain.

| ABS topic | Persona use |
| --- | --- |
| `G04` | Age by sex |
| `G05` | Registered marital status |
| `G06` | Social marital status / partnered context |
| `G07` | Indigenous status, with privacy care for small counts |
| `G08` | Ancestry |
| `G09` | Country of birth |
| `G13` | Language used at home and English proficiency context |
| `G16` | Highest year of school completed |
| `G17` | Weekly personal income by age and sex |
| `G22` | Australian Defence Force service |
| `G27` | Relationship in household |
| `G29` | Family composition |
| `G35` | Household composition |
| `G36` | Dwelling structure / housing type |
| `G37` | Tenure and landlord context |
| `G46` | Labour force status |
| `G49` | Highest non-school qualification level |
| `G50` | Field of study |
| `G54` | Industry of employment |
| `G60` | Occupation |

Recommended semantic build order:

```text
SA2 -> age/sex -> labour force -> occupation -> income -> household -> housing -> education -> cultural context
```

## Local Prerequisites

- Python 3.12+
- `uv`
- Docker or OrbStack
- Existing ABS Census Postgres container:
  - container: `censusloader-postgres`
  - host port: `5433`
  - database: `postgres`
  - schemas: `census_2021_data`, `census_2021_bdys_gda94`

Install dependencies:

```sh
uv sync
```

## Database Connection

The dbt profile defaults to:

```text
AUS_PERSONAS_PGHOST=127.0.0.1
AUS_PERSONAS_PGPORT=5433
AUS_PERSONAS_PGUSER=dbt_user
AUS_PERSONAS_PGPASSWORD=dbt_password
AUS_PERSONAS_PGDATABASE=postgres
AUS_PERSONAS_DBT_SCHEMA=aus_personas_dbt
```

The Dockerized Dagster service connects back to the same local Postgres through
`host.docker.internal:5433`.

## dbt

Parse the project:

```sh
UV_CACHE_DIR="$PWD/.uv-cache" uv run dbt parse \
  --project-dir dbt/aus_personas \
  --profiles-dir dbt/aus_personas
```

Build the core Census foundation:

```sh
UV_CACHE_DIR="$PWD/.uv-cache" uv run dbt build \
  --project-dir dbt/aus_personas \
  --profiles-dir dbt/aus_personas \
  --select int_abs__column_dictionary int_abs__sa2_observations dim_sa2 fct_census_observation assert_core_seed_observation_tables_present assert_core_seed_observation_row_counts assert_no_observations_missing_dictionary
```

Run the full dbt project when the local Census database is available:

```sh
UV_CACHE_DIR="$PWD/.uv-cache" uv run dbt build \
  --project-dir dbt/aus_personas \
  --profiles-dir dbt/aus_personas
```

## Dagster

Run the local Dagster UI:

```sh
DAGSTER_HOME="$PWD/dagster_home" uv run dagster dev -w workspace.yaml
```

Run the Dockerized orchestrator:

```sh
docker compose up --build abs-persona-orchestrator
```

The current dbt jobs are configured in
`configs/orchestration/dbt_jobs.yml`.

## CLI

Inspect the semantic Census catalog:

```sh
uv run aus-personas census tables
uv run aus-personas census worthy
uv run aus-personas census sections G17
```

Inspect decoded columns and generated long SQL:

```sh
uv run aus-personas census columns G17
uv run aus-personas census long G17 personal_income --sa2 <SA2_CODE> --format sql
uv run aus-personas census decode-column sa2_g06 g743
```

## Guardrails

- Do not mutate `census_2021_data` or `census_2021_bdys_gda94`.
- Do not treat raw wide tables as the working model.
- Do not sample directly from raw coded columns.
- Every semantic mart must answer: "one row represents what?"
- Totals, aggregates, `Not stated`, `Not applicable`, and broad rollups must be
  excluded from sampling or tagged as validation/context only.
- Metadata lineage back to `physical_table` and `raw_column` must be preserved.

## Documentation

- [ABS Census table dictionary](docs/abs-census-dictionary.md)
- [ABS source provenance](docs/abs-source-provenance.md)
- [Persona-worthy SA2 topics](docs/persona-worthy-sa2-topics.md)
- [Dagster orchestration](docs/dagster-orchestration.md)
- [DataDesigner persona generation](docs/data-designer-persona-generation.md)
- [Common pitfalls](docs/common-pitfalls.md)

## Next Work

1. Build the first semantic mart: `mart_sa2_age_sex_distribution` from `G04`.
2. Add `G46`, `G60`, and `G17` semantic marts for labour force, occupation,
   and income.
3. Add sampler tests that prove rows are generated from semantic marts, not raw
   wide Census tables.
4. Generate structured seed rows.
5. Use DataDesigner to expand seed rows into final narrative persona fields.
