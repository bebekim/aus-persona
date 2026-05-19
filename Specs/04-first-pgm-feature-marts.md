# Spec 04: First PGM Feature Marts

## Goal

Build the first sampler-facing dbt marts from proven ABS Census semantic topics.

The first tranche is deliberately small:

```text
mart_pgm__sa2_age_sex
mart_pgm__sa2_personal_income
mart_pgm__sa2_labour_force_status
```

These marts give the first practical conditional chain:

```text
SA2
  -> age_band, sex
  -> labour_force_status | SA2, age_band, sex
  -> income_band | SA2, age_band, sex
```

This is a conditional weighted sampler input, not a learned Bayesian network.

## Context

The semantic layer now separates source availability from sampler readiness.
`Specs/02-pgm-feature-marts.md` defines the promotion gate; this spec applies it
to the first implementation tranche.

Relevant upstream contracts:

- `dim_sa2` provides SA2 geography.
- `fct_census_observation` provides long-form ABS observations.
- `configs/abs_semantic_tables.yml` defines semantic topic guardrails.
- `int_abs__column_dictionary` exposes decoded axes and sampler eligibility.
- `G01.age_group_by_sex` is usable as the provisional age/sex base.
- `G17.personal_income` is the reference detailed sampler topic.
- `G46.labour_force_status` is the only approved adjacent first-tranche topic.

## Non-Goals

- Do not build the Python sampler.
- Do not generate narrative personas.
- Do not materialize the older broad mart backlog in this tranche.
- Do not sample guarded/context-only topics such as Indigenous status, defence
  service status, tenure/landlord, household composition, ancestry, or industry.
- Do not introduce external enrichment or model-generated values.
- Do not solve cross-topic consistency beyond the explicit conditional chain
  above.

## Mart Directory

Create marts under:

```text
dbt/aus_personas/models/marts/pgm/
```

Add a `schema.yml` in that directory with model descriptions, column tests, and
singular test references.

## Mart Contracts

Every first-tranche mart must expose:

```text
census_year
geography_level
sa2_code
sa2_name
state_name
feature_name
feature_value
age_band
sex
count
denominator_count
probability_within_partition
source_logical_table
source_physical_table
source_raw_column
source_label
is_total
is_sampler_eligible
```

Feature-specific aliases must also be present:

```text
mart_pgm__sa2_age_sex.age_band
mart_pgm__sa2_age_sex.sex
mart_pgm__sa2_personal_income.income_band
mart_pgm__sa2_labour_force_status.labour_force_status
```

All sampler-facing rows must satisfy:

```sql
count is not null
and is_total = false
and is_sampler_eligible = true
and geography_level = 'sa2'
```

Do not coerce null ABS cells to zero. Missing ABS cells are not sampled mass.

## Mart Grain

`mart_pgm__sa2_age_sex`:

```text
one row per census_year, SA2, age_band, sex
```

Use the currently implemented `G01.age_group_by_sex` semantic output as the
provisional base. Keep the mart replaceable by a later G04 age-by-sex mart.

`mart_pgm__sa2_personal_income`:

```text
one row per census_year, SA2, age_band, sex, income_band
```

Use `G17.personal_income`. Partition probabilities by:

```text
census_year, sa2_code, age_band, sex
```

`mart_pgm__sa2_labour_force_status`:

```text
one row per census_year, SA2, age_band, sex, labour_force_status
```

Use `G46.labour_force_status`. Partition probabilities by:

```text
census_year, sa2_code, age_band, sex
```

## Probability Policy

For each mart:

```sql
denominator_count =
  sum(count) over (partition by the mart denominator axes)

probability_within_partition =
  count / nullif(denominator_count, 0)
```

Rows with zero denominator must not be sampler-facing. If they are retained for
QA, they must be excluded by `is_sampler_eligible = false`.

Probability sums should be approximately 1.0 for every populated denominator
partition. Use a tolerance to avoid decimal noise.

## Exclusions

Exclude from this tranche:

```text
G07 Indigenous status
G08 ancestry
G09 country of birth
G13 language/proficiency
G22 defence service status
G27 household relationship
G35 household composition
G37 tenure/landlord
G54 industry
G18 accessibility/support
G40 rent bands
```

These topics remain semantic CLI/query coverage or follow-up mart candidates.
The older broad mart list in `Specs/02-pgm-feature-marts.md` is a follow-up
backlog, not current scope.

## Required Tests

Generic tests:

- `not_null` on `census_year`, `geography_level`, `sa2_code`, `feature_name`,
  `feature_value`, `count`, `denominator_count`, and
  `probability_within_partition`.
- accepted value test for `geography_level = sa2`.
- relationship test from `sa2_code` to `dim_sa2.sa2_code`.
- unique grain test for each mart.

Singular tests:

- no sampler-facing rows have `is_total = true`.
- no sampler-facing rows have `is_sampler_eligible = false`.
- no sampler-facing rows have null counts.
- no sampler-facing rows have null or zero denominators.
- probability is between 0 and 1.
- probabilities sum to approximately 1 per denominator partition.
- source lineage columns are populated.

Smoke tests:

- Rockbank SA2 `213041359` returns rows from all three marts.
- `mart_pgm__sa2_personal_income` contains at least one non-total income band for
  Rockbank adult-compatible age/sex partitions.
- `mart_pgm__sa2_labour_force_status` contains at least one employed or
  unemployed category for Rockbank adult-compatible age/sex partitions.

## Runnable Acceptance Criteria

Implementation is complete only when these commands pass:

```sh
UV_CACHE_DIR=.uv-cache uv run dbt parse \
  --project-dir dbt/aus_personas \
  --profiles-dir dbt/aus_personas

UV_CACHE_DIR=.uv-cache uv run dbt build \
  --project-dir dbt/aus_personas \
  --profiles-dir dbt/aus_personas \
  --select mart_pgm__sa2_age_sex mart_pgm__sa2_personal_income mart_pgm__sa2_labour_force_status

UV_CACHE_DIR=.uv-cache uv run pytest -q
```

The final implementation report must include:

- row counts for all three marts;
- probability-sum check evidence;
- the Rockbank smoke-test output;
- any known age-band limitation caused by using G01 before G04.

## Follow-Up Backlog

After this tranche is working, promote additional topics one at a time through
the gate in `Specs/02-pgm-feature-marts.md`.

Likely next candidates:

```text
G09 country_of_birth
G13 language_used_at_home / english_proficiency
G27 household_relationship
```

Guarded or context-only topics need a reviewed use case before sampler-facing
mart work starts.
