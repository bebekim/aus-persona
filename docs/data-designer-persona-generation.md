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
examples/seeds/rockbank_seed_sample.csv
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

## Design Choice

The config currently generates one structured `persona_bundle` object rather
than thirteen separate LLM columns. That keeps one LLM call per seed row and
reduces cost. A later flattening step should expand `persona_bundle` into the
final Korea-style columns.

## Boundary

Data Designer should not sample Census fields for this project. Its built-in
person sampler is useful for generic synthetic people, but our persona rows need
to preserve ABS-grounded SA2 distributions and the PGM assumptions we document.
