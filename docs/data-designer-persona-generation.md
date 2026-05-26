# Data Designer Persona Generation

Data Designer is the prose-generation stage, not the Census sampler.

The pipeline stays split:

```text
ABS Census wide tables
  -> dbt + semantic Census queries
  -> PGM/conditional sampler
  -> structured seed rows
  -> Data Designer persona text expansion
  -> flattened Korea-style dataset
```

The structured seed row owns demographic truth. Data Designer receives fixed
fields including:

- `age_band`
- `sex`
- `labour_force_status`
- `income_band`
- `country_of_birth`
- `language_used_at_home`
- `english_proficiency`
- `household_relationship`

Data Designer generates natural-language fields such as:

- `professional_persona`
- `sports_persona`
- `arts_persona`
- `travel_persona`
- `culinary_persona`
- `family_persona`
- `persona`
- `cultural_background`
- `skills_and_expertise`
- `hobbies_and_interests`
- `career_goals_and_ambitions`

## Config

The first config is:

```text
configs/data_designer/persona_text_config.py
```

It reads seed rows from:

```text
examples/seeds/rockbank_pgm_seed_sample.csv
```

Override the seed file:

```sh
AUS_PERSONAS_SEED_PATH=artifacts/seeds/rockbank_10000.csv \
UV_CACHE_DIR=.uv-cache \
uv run data-designer preview configs/data_designer/persona_text_config.py -n 5
```

Override the model alias:

```sh
AUS_PERSONAS_TEXT_MODEL_ALIAS=nvidia-text \
UV_CACHE_DIR=.uv-cache \
uv run data-designer preview configs/data_designer/persona_text_config.py -n 5
```

Create a full artifact:

```sh
AUS_PERSONAS_SEED_PATH=artifacts/seeds/rockbank_10000.csv \
UV_CACHE_DIR=.uv-cache \
uv run data-designer create configs/data_designer/persona_text_config.py \
  --num-records 10000 \
  --dataset-name rockbank_personas \
  --artifact-path artifacts/data_designer
```

## Bridge Contract

The config consumes PGM structured seed rows directly. The fixed input columns
are:

- `profile_id`
- `census_year`
- `sa2_code`
- `sa2_name`
- `state_name`
- `age_band`
- `sex`
- `labour_force_status`
- `income_band`
- `country_of_birth`
- `language_used_at_home`
- `english_proficiency`
- `household_relationship`
- `pgm_trace_json`
- `provenance_json`

Data Designer generates one structured `persona_bundle` object instead of
separate LLM columns. That keeps one LLM call per seed row and reduces cost.
The bundle contains only generated narrative fields:

- `professional_persona`
- `family_persona`
- `skills_and_expertise`
- `skills_and_expertise_list`
- `hobbies_and_interests`
- `hobbies_and_interests_list`
- `career_goals_and_ambitions`
- `persona`

Use `aus_personas.sampler.validation.build_final_persona_row(seed_row,
generated_row)` to flatten a Data Designer row into the final export shape.
The helper copies all structured PGM fields from the seed row, expands
`persona_bundle`, preserves `pgm_trace_json` and `provenance_json`, and appends
`validation_status` plus `validation_errors_json`.

The machine-readable final-field provenance contract lives in:

```text
src/aus_personas/persona_fields.py
```

Narrative fields are marked `generated_constrained`; they are not
`sampled_from_abs`.

## Validators

Post-generation validators fail the row when generated text:

- mentions an age outside `age_band`;
- describes current work when `labour_force_status` is not employed;
- exposes the exact `income_band` as prose;
- claims ABS or Census provenance for generated narrative fields;
- describes an Australia-born seed as a recent migrant;
- contradicts English-at-home seed context;
- contradicts lone-person household context;
- leaves generated narrative fields empty;
- attempts to change fixed structured fields.

## Boundary

Data Designer should not sample Census fields for this project. Its built-in
person sampler is useful for generic synthetic people, but our persona rows need
to preserve ABS-grounded SA2 distributions and the PGM assumptions we document.
