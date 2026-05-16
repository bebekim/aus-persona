# Spec 02: First PGM Feature Marts

> Status: downstream / not the next implementation target.
>
> This spec predates the semantic-layer split. Do not implement the full mart
> list until `Specs/02-census-semantic-topic-layer.md` exists in code and the
> first SA2 semantic topics have been inspected. The first rewritten tranche
> should be smaller and should promote only proven semantic topics.

## Goal

Build the first sampler-facing dbt marts on top of
`fct_census_observation`.

The current Census ingestion layer answers:

```text
For this SA2, this ABS table, and this decoded column, what count did ABS give?
```

The PGM sampler needs a narrower contract:

```text
For this SA2 and feature axis, what distribution should I sample from?
```

This spec defines the first set of feature marts that bridge those two layers.

## Context

Completed upstream models:

```text
dim_sa2
fct_census_observation
```

Important source semantics:

- `count` is nullable because some ABS profile cells are blank or not
  applicable.
- Nullable counts must not be silently converted to zero in the generic fact
  layer.
- Feature marts may exclude, coalesce, or impute null counts only when the rule
  is explicit in that mart.
- Totals are useful for validation but should usually be excluded from sampling
  categories.

## Non-Goals

- Do not build the synthetic person sampler in this spec.
- Do not generate persona prose.
- Do not use the Working Population Profile as a substitute for usual-residence
  resident population unless the feature explicitly says so.
- Do not correct counts for overcount or undercount.
- Do not invent psychographic segments yet.

## Required Feature Marts

Create models under:

```text
dbt/aus_personas/models/marts/pgm/
```

Minimum marts:

```text
mart_pgm__sa2_age_sex
mart_pgm__sa2_registered_marital_status
mart_pgm__sa2_indigenous_status
mart_pgm__sa2_country_of_birth
mart_pgm__sa2_language_home
mart_pgm__sa2_school_completion
mart_pgm__sa2_personal_income
mart_pgm__sa2_household_relationship
mart_pgm__sa2_dwelling_structure
mart_pgm__sa2_tenure_landlord
mart_pgm__sa2_labour_force_status
mart_pgm__sa2_qualification_level
mart_pgm__sa2_field_of_study
mart_pgm__sa2_occupation
```

Each mart should expose one distribution family, not a generic catch-all table.

## Standard Mart Shape

Every feature mart should use this common shape unless the source table demands
otherwise:

```text
census_year
geography_level
sa2_code
sa2_name
state_name
feature_name
feature_value
sex
age_band
count
source_physical_table
source_raw_column
source_label
is_total
```

Feature-specific marts may add extra columns, for example:

```text
income_band
occupation
qualification_level
field_of_study
language_home
country_of_birth
```

but the generic `feature_name` and `feature_value` columns must remain present
so Python sampler code can consume marts consistently.

## Source Mapping

Use `project_alias` from `fct_census_observation`:

```text
selected_person_characteristics_by_sex       -> optional validation only
age_by_sex                                   -> mart_pgm__sa2_age_sex
registered_marital_status_by_age_sex         -> mart_pgm__sa2_registered_marital_status
indigenous_status_by_age_sex                 -> mart_pgm__sa2_indigenous_status
country_of_birth_by_age_sex                  -> mart_pgm__sa2_country_of_birth
language_home_by_english_proficiency_sex     -> mart_pgm__sa2_language_home
school_completion_by_age_sex                 -> mart_pgm__sa2_school_completion
personal_income_weekly_by_age_sex            -> mart_pgm__sa2_personal_income
household_relationship_by_age_sex            -> mart_pgm__sa2_household_relationship
dwelling_structure                           -> mart_pgm__sa2_dwelling_structure
tenure_landlord_by_dwelling_structure        -> mart_pgm__sa2_tenure_landlord
labour_force_status_by_age_sex               -> mart_pgm__sa2_labour_force_status
qualification_level_by_age_sex               -> mart_pgm__sa2_qualification_level
field_of_study_by_age_sex                    -> mart_pgm__sa2_field_of_study
occupation_by_age_sex                        -> mart_pgm__sa2_occupation
```

## Null And Total Policy

Default feature mart rule:

```text
where count is not null
```

Rationale: a missing ABS cell is not a sampled zero. The sampler can only use
observed numeric mass unless a later imputation layer is explicit.

Default sampling rule:

```text
where is_total = false
```

Rationale: totals should validate distributions, not appear as categories in a
sampled person row.

If a feature needs totals for denominator checks, expose a companion validation
model or include an `is_total` row but ensure sampler-facing queries filter it
out.

## Probability Columns

For each mart, add:

```text
sa2_feature_count_total
probability_within_sa2
```

Definition:

```text
sa2_feature_count_total =
  sum(count) over (partition by sa2_code, feature_name, sex, age_band)

probability_within_sa2 =
  count / nullif(sa2_feature_count_total, 0)
```

If a feature does not include `sex` or `age_band`, partition by the axes that
actually exist for that mart.

Do not force every feature into the same partition if the ABS table does not
support it.

## First PGM Dependency Graph

The first sampler should consume these marts in this order:

```text
sa2
  -> age_sex
  -> registered_marital_status | age_band, sex, sa2
  -> school_completion | age_band, sex, sa2
  -> labour_force_status | age_band, sex, sa2
  -> occupation | age_band, sex, sa2
  -> personal_income | age_band, sex, sa2
  -> household_relationship | age_band, sex, sa2
  -> dwelling_structure | sa2
  -> tenure_landlord | sa2
  -> country_of_birth | age_band, sex, sa2
  -> language_home | sex, sa2
  -> indigenous_status | age_band, sex, sa2
```

This is a practical conditional sampler, not a full learned Bayesian network.
It should be documented as PGM-like conditional weighted sampling.

## Tests

Each feature mart must have:

- not-null tests on `sa2_code`, `feature_name`, `feature_value`, and `count`
- accepted value test for `geography_level = sa2`
- relationship test from `sa2_code` to `dim_sa2.sa2_code`
- a singular test that no sampler-facing rows have `is_total = true`
- a singular test that `probability_within_sa2` is between 0 and 1

Add at least one row-count sanity test for:

```text
mart_pgm__sa2_age_sex
mart_pgm__sa2_personal_income
mart_pgm__sa2_occupation
```

## Acceptance Criteria

- All required marts build with `uv run dbt run --select marts.pgm`.
- All PGM mart tests pass with `uv run dbt test --select marts.pgm`.
- `mart_pgm__sa2_age_sex` can produce an adult SA2 population distribution
  after filtering to age bands 18+ or compatible ABS bands.
- Null count handling is explicit in SQL and docs.
- Totals are excluded from sampler-facing rows.
- The model remains 2026-ready through existing dbt vars for year, schema, and
  geography level.

## Follow-Up

After this spec is implemented, create the Python sampler spec:

```text
Spec 03: Conditional Weighted PGM Sampler
```

That sampler should read these marts rather than raw ABS tables.

The first sampler run should use the `smallest` preset from
`aus_personas.sample_sizes`:

```text
SMALLEST_SAMPLE = 10,000
```
