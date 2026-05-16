# Spec 03: Conditional Weighted PGM Sampler

## Goal

Generate the first structured synthetic adult Australian rows from the PGM
feature marts.

The first implementation target is deliberately small:

```text
sample_preset = smallest
sample_size = 10,000
```

The sampler must use the named presets in `aus_personas.sample_sizes`, not
hard-coded row counts.

## Sample Size Presets

```text
SMALLEST_SAMPLE = 10,000
SMALL_SAMPLE = 50,000
MEDIUM_SAMPLE = 100,000
LARGE_SAMPLE = 500,000
HUGE_SAMPLE = 1,000,000
```

Default for v0:

```text
DEFAULT_SAMPLE_PRESET = smallest
DEFAULT_SAMPLE_SIZE = SMALLEST_SAMPLE
```

## Input Contract

Read sampler-facing marts from dbt, not raw ABS tables:

```text
mart_pgm__sa2_age_sex
mart_pgm__sa2_registered_marital_status
mart_pgm__sa2_school_completion
mart_pgm__sa2_labour_force_status
mart_pgm__sa2_occupation
mart_pgm__sa2_personal_income
mart_pgm__sa2_household_relationship
mart_pgm__sa2_dwelling_structure
mart_pgm__sa2_tenure_landlord
mart_pgm__sa2_country_of_birth
mart_pgm__sa2_language_home
mart_pgm__sa2_indigenous_status
```

## Sampling Order

Use conditional weighted sampling:

```text
sa2
  -> age_band, sex
  -> registered_marital_status | sa2, age_band, sex
  -> school_completion | sa2, age_band, sex
  -> labour_force_status | sa2, age_band, sex
  -> occupation | sa2, age_band, sex
  -> personal_income | sa2, age_band, sex
  -> household_relationship | sa2, age_band, sex
  -> dwelling_structure | sa2
  -> tenure_landlord | sa2
  -> country_of_birth | sa2, age_band, sex
  -> language_home | sa2, sex
  -> indigenous_status | sa2, age_band, sex
```

## Output Contract

For the first run, write structured rows only. Do not generate persona prose.

Minimum output columns:

```text
synthetic_person_id
sa2_code
sa2_name
state_name
age_band
sex
registered_marital_status
school_completion
labour_force_status
occupation
personal_income
household_relationship
dwelling_structure
tenure_landlord
country_of_birth
language_home
indigenous_status
sample_preset
sample_size
random_seed
```

## Acceptance Criteria

- `resolve_sample_size()` returns `10,000` by default.
- The first sampler command generates exactly `10,000` rows.
- Output includes `sample_preset = smallest`.
- Output includes `sample_size = 10000`.
- The sampler uses feature-mart probabilities, not raw counts directly.
- Generated rows contain no total categories.
- Generated rows contain no null required demographic fields.
