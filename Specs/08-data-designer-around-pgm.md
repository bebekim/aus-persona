# Spec 08: Data Designer Around PGM

## Goal

Use NVIDIA Data Designer around the ABS-backed PGM sampler rather than as the
PGM engine.

The target pipeline is:

```text
ABS Census dbt silver layer
  -> PGM mart layer
  -> conditional weighted sampler
  -> structured seed profiles
  -> NVIDIA Data Designer
  -> narrative persona fields
  -> validation and provenance export
```

## Current Silver-Layer Readiness

The silver layer is partially ready.

Ready:

- `int_abs__sa2_observations` materializes normalized SA2 Census observations
  across configured ABS physical tables.
- `int_abs__column_dictionary` decodes raw ABS columns into logical table,
  category axis, category, age band, sex, total flag, and semantic axis JSON.
- `fct_census_observation` joins observations, decoded metadata, and SA2
  geography into a reusable long fact table.
- `configs/abs_semantic_tables.yml` records sampler guardrails for promoted
  semantic topics.
- `mart_pgm__sa2_age_sex` and `mart_pgm__sa2_personal_income` already expose
  sampler-facing probability distributions.

Not ready:

- `mart_pgm__sa2_labour_force_status` is still missing, so Tier 1 is not
  complete.
- There is no materialized sampler output table/file yet.
- There is no Data Designer seed dataset export contract.
- There is no Data Designer config that consumes PGM seed rows.
- There are no validators for narrative contradictions or provenance leakage.

Conclusion:

```text
Silver is ready enough for Step 1 implementation to continue.
Silver is not yet ready as a final Data Designer input surface.
```

## Step 1: Produce ABS-Backed Structured Seed Profiles

Build the structured demographic spine outside Data Designer.

Inputs:

```text
mart_pgm__sa2_age_sex
mart_pgm__sa2_personal_income
mart_pgm__sa2_labour_force_status
```

Required output fields:

```text
profile_id
census_year
sa2_code
sa2_name
state_name
age_band
sex
labour_force_status
income_band
pgm_trace_json
provenance_json
```

Sampling order:

```text
SA2
  -> age_band, sex
  -> labour_force_status | SA2, age_band, sex
  -> income_band | SA2, age_band, sex
```

`pgm_trace_json` must record which mart and denominator partition supplied each
draw.

`provenance_json` must label each structured field as `sampled_from_abs`.

Step 1 does not generate narrative text.

## Step 2: Feed Structured Seeds Into Data Designer

Use Data Designer as an enrichment orchestrator.

Input:

```text
structured seed profile rows from Step 1
```

Data Designer must treat these fields as fixed seed context:

```text
profile_id
sa2_name
state_name
age_band
sex
labour_force_status
income_band
```

Generated narrative fields:

```text
professional_persona
family_persona
skills_and_expertise
skills_and_expertise_list
hobbies_and_interests
hobbies_and_interests_list
career_goals_and_ambitions
persona
```

Prompt contract:

```text
Create a concise Australian persona narrative from the fixed demographic
scaffold. Do not change the scaffold. Do not mention exact Census counts. Do
not claim hobbies, skills, personality, or ambitions are Census-derived. Avoid
inferring protected or sensitive attributes not present in the scaffold.
```

Data Designer may use LLM columns for narrative fields and validator columns for
consistency checks. It must not resample or overwrite Tier 1 fields.

## Step 3: Validate, Export, And Preserve Provenance

Validation must run after Data Designer generation.

Required validators:

- Narrative does not contradict `age_band`.
- Narrative does not contradict `labour_force_status`.
- Narrative does not expose exact `income_band` as a claimed salary unless the
  downstream use case explicitly allows income-band wording.
- Narrative does not claim ABS provenance for generated hobbies, skills, or
  career goals.
- Generated fields are non-empty.
- Output preserves `profile_id`.
- Output preserves `pgm_trace_json`.
- Output preserves `provenance_json`.

Final output fields:

```text
profile_id
census_year
sa2_code
sa2_name
state_name
age_band
sex
labour_force_status
income_band
professional_persona
family_persona
skills_and_expertise
skills_and_expertise_list
hobbies_and_interests
hobbies_and_interests_list
career_goals_and_ambitions
persona
pgm_trace_json
provenance_json
validation_status
validation_errors_json
```

## Tier 1 / 2 / 3 Boundary

Tier 1 is the only part required before Data Designer integration:

```text
SA2
age_band
sex
labour_force_status
income_band
```

Tier 2 remains future structured context:

```text
country_of_birth
language_used_at_home
english_proficiency
household_relationship
```

Tier 3 is Data Designer narrative generation:

```text
personality/narrative fields
skills
hobbies
career goals
family prose
professional prose
```

Data Designer starts at Tier 3. It can see Tier 1 and Tier 2 fields as context,
but it does not own their sampling.

## Implementation Order

1. Complete `mart_pgm__sa2_labour_force_status`.
2. Build the Step 1 sampler/export that emits structured seed profiles.
3. Add a Data Designer config that consumes seed profiles and generates Tier 3
   narrative fields.
4. Add validators and provenance checks.
5. Add a small preview job using Rockbank SA2 `213041359`.

## Acceptance Criteria

- Tier 1 dbt marts build and pass probability tests.
- A structured seed export exists and contains no generated narrative fields.
- Data Designer consumes the seed export without changing Tier 1 fields.
- Generated narrative fields pass contradiction and provenance validators.
- Final output contains `pgm_trace_json` and `provenance_json`.
- Documentation states that ABS supports only the structured spine, not the
  generated narrative layer.
