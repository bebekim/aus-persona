# Spec 02: Census Semantic Topic Layer

## Goal

Create the modeller-facing semantic layer between raw ABS Census tables and PGM
feature marts.

The raw Census schema is a delivery format:

```text
geography level x Census profile table x coded measure columns
```

The semantic layer must expose a clearer contract:

```text
one SA2 Census topic -> one readable long semantic dataset
```

This spec exists so we do not jump directly from wide `sa2_g*` tables into PGM
marts before answering the modelling question:

```text
One row represents ___.
```

## Scope

Only `sa2_*` tables are in scope for persona generation.

Allowed source table pattern:

```text
census_2021_data.sa2_g*
census_2021_data.sa2_w*
```

Explicitly out of scope for this semantic layer:

```text
aust_*
ste_*
gccsa_*
sa1_*
sa3_*
sa4_*
lga_*
poa_*
sal_*
ucl_*
sua_*
ra_*
ced_*
sed_*
pow_*
```

Those other geography levels may be useful later for validation, rollups,
geographic QA, or public reporting, but they must not be used as the working
grain for individual persona seeds.

## Context

Completed upstream foundation:

```text
census_2021_data.*              raw ABS Census tables
census_2021_data.metadata_*     ABS metadata decoder
census_2021_bdys_gda94.*        ABS boundaries/geography
aus_personas_dbt.dim_sa2
aus_personas_dbt.fct_census_observation
```

The foundation layer currently answers:

```text
For this SA2, physical table, and raw column, what count/value exists?
```

The semantic layer should answer:

```text
For this SA2 and readable Census topic, what category count/value exists?
```

Example:

```text
raw:      census_2021_data.sa2_g06.g743
metadata: G06 = Social Marital Status by Age by Sex
semantic: sa2 + sex=Male + age_band=15-19 + social_marital_status=Married in a registered marriage
```

## Non-Goals

- Do not build the PGM sampler.
- Do not generate persona prose.
- Do not model every Census table.
- Do not ingest or model non-SA2 geography tables for persona generation.
- Do not mutate, rename, or clean raw `census_2021_data` tables.
- Do not treat `aust_*` national summary rows as persona inputs.
- Do not materialize every semantic topic as a dbt mart.
- Do not correct ABS counts for overcount or undercount.

## Design Principle

Raw tables remain untouched.

```text
census_2021_data.sa2_g06
```

continues to mean the raw ABS loader output.

The semantic layer is a decoding and modelling layer over the raw data:

```text
raw wide table
  + ABS metadata
  + semantic catalog
  -> readable long topic rows
```

The semantic layer is allowed to be query-driven. It does not need to create one
dbt model per topic unless the topic is promoted to the PGM mart layer.

## Required Artifact: Semantic Catalog

Maintain a config file:

```text
configs/abs_semantic_tables.yml
```

Each semantic table entry must define:

```text
logical_table
description
source_profile
source_geography_level
allowed_physical_tables
sections
```

Each section must define:

```text
section_name
description
raw_column_ranges
grain
measure
axes
is_sampler_candidate
total_policy
notes
```

Example:

```yaml
G06:
  description: Social Marital Status by Age by Sex
  source_geography_level: sa2
  allowed_physical_tables:
    - sa2_g06
  sections:
    social_marital_status_by_age_sex:
      raw_column_ranges:
        - G743-G862
      grain:
        - sa2
        - sex
        - age_band
        - social_marital_status
      measure: count
      axes:
        sex: parsed_from_metadata
        age_band: parsed_from_metadata
        social_marital_status: parsed_from_metadata
      is_sampler_candidate: true
      total_policy: keep_for_validation_exclude_from_sampling
```

## Required Semantic Row Contract

Every semantic long query must be able to state:

```text
One row represents one measured value for one SA2, one Census topic section,
and one combination of the section axes.
```

Minimum output columns:

```text
census_year
geography_level
sa2_code
sa2_name
state_name
logical_table
section_name
topic_name
feature_name
feature_value
count
source_physical_table
source_raw_column
source_label
is_total
is_sampler_candidate
```

Feature-specific axis columns should be included when relevant:

```text
sex
age_band
social_marital_status
income_band
ancestry
country_of_birth
language_home
education_level
occupation
labour_force_status
household_type
dwelling_type
```

If an axis is not present in the ABS table, it must be `null` or absent by
contract. Do not invent axes to force uniformity.

## Metadata Rules

Use ABS metadata as the decoder:

```text
census_2021_data.metadata_tables
census_2021_data.metadata_stats
```

Do not infer human-readable labels from raw column names alone:

```text
g743
g110
g5211
```

are lineage identifiers, not modelling labels.

The semantic layer may parse axes from:

```text
metadata_stats.short_id
metadata_stats.long_id
metadata_stats.column_heading_description
metadata_tables.table_name
metadata_tables.table_description
```

Parsing rules must be tested for each promoted topic section.

## Initial Topic Set

The first semantic topic set is deliberately small and SA2-only.

Required first topics:

```text
sa2_g01   selected person characteristics by sex
sa2_g06   social marital status by age by sex
sa2_g08   ancestry
sa2_g09*  country of birth
sa2_g10*  language used at home / English proficiency
sa2_g17*  personal income by age by sex
```

Follow-up topics, not first tranche:

```text
education
labour force status
occupation
household relationship
dwelling structure
tenure / landlord type
field of study
qualification level
```

## G01 First Walkthrough

The first implementation walkthrough must use:

```text
census_2021_data.sa2_g01
```

It must document:

```text
What one raw row represents.
What each semantic section represents.
Which columns are totals.
Which sections are sampler candidates.
Which sections are validation-only.
How to inspect one SA2, especially Rockbank - Mount Cottrell.
```

Required Rockbank target:

```text
sa2_code = 213041359
sa2_name = Rockbank - Mount Cottrell
```

## G06 Interpretation Example

For `sa2_g06`, raw columns such as:

```text
g743
g744
g745
g746
```

must be decoded through metadata into rows equivalent to:

```text
sa2_code | sex  | age_band | social_marital_status              | count
...      | Male | 15-19    | Married in a registered marriage   | ...
...      | Male | 15-19    | Married in a de facto marriage     | ...
...      | Male | 15-19    | Not married                        | ...
...      | Male | 15-19    | Total                              | ...
```

`Total` rows are validation rows, not sampling categories.

## CLI Requirements

Expose semantic layer inspection through the `aus-personas census` CLI.

Required commands:

```text
aus-personas census tables
aus-personas census sections G01
aus-personas census columns G01
aus-personas census long G01 age_group_by_sex --sa2 213041359
```

Output formats:

```text
table
csv
jsonl
sql
```

The `sql` format is required so a modeller can copy generated SQL into a
database client and inspect it directly.

All commands must restrict semantic persona work to `sa2_*` physical tables
unless a command is explicitly marked as validation-only.

## Promotion Rule

A semantic topic may be promoted to a dbt PGM mart only when:

```text
1. Its semantic catalog entry exists.
2. Its one-row-represents contract is documented.
3. Its axes are parsed and tested.
4. Its total rows are identified.
5. Its sampler candidates are explicit.
6. A Rockbank inspection query has been run or is reproducible.
7. The downstream sampler dependency is known.
```

Otherwise it stays queryable through the semantic CLI only.

## Preflight Risks

This spec is not ready for implementation if any of these are unresolved:

```text
The source table is not SA2-level.
The raw column range is guessed without metadata confirmation.
The semantic grain cannot be stated.
Totals cannot be distinguished from categories.
The section mixes measures with incompatible grains.
The topic is validation-only but marked as sampler candidate.
The implementation requires one dbt model per raw Census table.
```

## Tests

Add tests for:

```text
semantic catalog loading
raw column range parsing
SA2-only physical table validation
required catalog fields
G01 section lookup
G06 social marital status metadata decoding
SQL generation with --sa2 filter
SQL generation excluding non-SA2 physical tables by default
```

Where possible, tests should validate generated SQL without requiring a running
Docker database.

## Acceptance Criteria

- `configs/abs_semantic_tables.yml` supports SA2-only semantic topic entries.
- Non-SA2 physical tables are excluded from persona semantic commands by
  default.
- `aus-personas census tables` or equivalent inventory command can show the
  semantic catalog.
- `aus-personas census sections G01` can show G01 sections and their grains.
- `aus-personas census long G01 <section> --sa2 213041359 --format sql`
  generates readable SQL.
- Every semantic section answers: `one row represents ___`.
- The old broad PGM mart spec is treated as downstream, not ready until this
  semantic layer exists.
