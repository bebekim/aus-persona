# Spec 03: Persona-Worthy SA2 Topic Selection

Priority: high
Status: ready

## Problem

The raw Census schema contains many `sa2_g*` tables and thousands of coded
columns. Most columns are illegible without ABS metadata, and not every decoded
column deserves to become a persona feature.

The project goal is not to mirror the whole Census profile. The goal is to
produce Korea-style synthetic persona rows:

```text
one row = one synthetic Australian resident
```

That resident needs a coherent structured seed:

```text
SA2 + age + sex + household + housing + education + labour + occupation + income + cultural context
```

The current risk is modelling drift:

- treating every `sa2_g*` column as equally useful;
- joining too many wide Census topics too early;
- promoting totals and aggregate columns into sampler inputs;
- generating prose before the structured seed is defensible;
- skipping the modeller comfort layer: one topic, one readable long table.

## Desired Behavior

Before a Census topic can feed the sampler, it must pass a worthiness gate.

The gate classifies each selected SA2 topic and section into one of four roles:

| Tier | Meaning | Use |
| --- | --- | --- |
| A | Sampler core | Directly sampled into the persona seed. |
| B | Conditioning/context | Conditions another sample or improves plausibility. |
| C | Validation only | Used for totals, QA, rollups, or sanity checks. |
| D | Exclude for v1 | Not useful, duplicate, aggregate, too sparse, or not adult-persona relevant. |

The gate must be persisted in configuration, not left as conversation memory.

The first persisted source of truth is:

```text
docs/persona-worthy-sa2-topics.md
configs/abs_semantic_tables.yml
```

The later implementation should make the same classification queryable through
the CLI.

Example CLI shape:

```text
aus-personas census worthy --stage 1
aus-personas census worthy G17
aus-personas census long G17 personal_income --sa2 121011684
```

## Guardrail Contract

Treat Census topic selection like an allowlist, not a free-form prompt.

A downstream model, CLI command, sampler, or generation step may request a
Census topic, but the request is not trusted by default. The request must be
resolved through the semantic catalog before any raw table is queried or any
sampler field is produced.

Guardrail decision values:

```text
allow           topic/section may be used for the requested purpose
allow_context   topic/section may be used only as conditioning or prompt context
allow_validate  topic/section may be used only for QA, totals, or reconciliation
deny            topic/section must not be used for the requested purpose
unknown         topic/section is not catalogued and must fail closed
```

The guardrail must answer three questions:

```text
Can this topic be used?
Can this section be used?
Can it be used for this purpose: sample, condition, validate, or generate?
```

Fail closed. If the topic, section, tier, purpose, or grain is missing, the
answer is `deny` or `unknown`, not a best-effort query.

## Allow / Disallow Rules

Allowed for `sample`:

- Tier A sections with `promotion_status` at least `semantic_ready` for semantic
  inspection, and at least `mart_ready` for sampler use.
- Category cells that belong to the declared grain.
- Adult-compatible categories when the requested output is adult personas.
- Detailed topics preferred over summaries, such as `G09` over G01 birthplace
  summary.

Allowed for `condition`:

- Tier A or B sections.
- Household and dwelling topics where the grain mismatch is explicitly declared.
- Industry as context for occupation/professional persona, even when occupation
  remains the sampled work field.

Allowed for `validate`:

- Tier A, B, or C sections.
- Total columns.
- `Persons` sex aggregates.
- Coarse summaries used only to check detailed-topic rollups.

Allowed for `generate`:

- Structured seed fields that already passed `sample` or `condition`.
- Local context derived from allowed semantic topics.
- Narrative expansion fields after the seed is fixed.

Disallowed for `sample`:

- Any topic outside the stage-1 allowlist unless a new spec updates the
  inventory.
- Any non-SA2 raw geography table.
- Any raw wide column not decoded through ABS metadata.
- Explicit totals.
- `Persons` sex aggregates when sex-specific rows exist.
- `Not stated` and `Not applicable`.
- `Other` as a preferred final value unless no better category exists and the
  fallback is documented.
- Broad rollups when a detailed table exists.
- Child-only age categories for adult-persona generation.
- Household or dwelling distributions treated as if they were person-level facts
  without an allocation rule.

Disallowed for `generate`:

- Inventing structured demographics that the sampler did not choose.
- Overriding sampled age, sex, occupation, income, household, education, or
  cultural fields because a prose prompt asks for it.
- Treating free-text prompt instructions as permission to bypass catalog rules.

Example decisions:

| Request | Decision | Reason |
| --- | --- | --- |
| sample `G17.personal_income` for `income_band` | `allow` after mart promotion | Tier A, direct seed field. |
| sample G01 birthplace summary for `country_of_birth` | `deny` | Use detailed `G09`; G01 summary is validation/context only. |
| validate G01 birthplace summary against G09 rollup | `allow_validate` | Coarse summary can support QA. |
| sample `Persons` total from `G04` | `deny` | Aggregate across sex. |
| condition prose with `G54.industry` | `allow_context` | Industry improves professional plausibility. |
| query `aust_g17` for individual sampling | `deny` | Non-SA2 geography. |
| use uncatalogued `sa2_g99` | `unknown` | Fail closed until catalogued. |

## Persona Seed Contract

The sampler-facing structured seed should target these fields first:

```text
uuid
sa2_code
sa2_name
state
country
age
age_band
sex
marital_status
family_type
household_relationship
housing_type
tenure_landlord
education_level
field_of_study
labour_force_status
occupation
industry
income_band
ancestry
country_of_birth
language_used_at_home
english_proficiency
indigenous_status
```

These fields are not expected to come directly from Census:

```text
professional_persona
sports_persona
arts_persona
travel_persona
culinary_persona
family_persona
persona
cultural_background
skills_and_expertise
skills_and_expertise_list
hobbies_and_interests
hobbies_and_interests_list
career_goals_and_ambitions
```

Those are generated after sampling, using the structured seed plus local context.
Census constrains the demographic skeleton; Data Designer or another generator
expands the prose.

## Stage-1 Topic Inventory

The following stage-1 topics are confirmed by `census_2021_data.metadata_tables`
and are the only initial `sa2_g*` topics in scope.

| Topic | Metadata title | Persona mapping | Tier |
| --- | --- | --- | --- |
| `G01` | Selected Person Characteristics by Sex | Mixed first-pass summary. Use only specific sections; most totals/coarse summaries are QA. | A/C |
| `G04` | Age by Sex | `age_band`, `sex`; adult base population. | A |
| `G05` | Registered Marital Status by Age by Sex | `marital_status`. | A |
| `G06` | Social Marital Status by Age by Sex | Partnering context for household/family plausibility. | B |
| `G07` | Indigenous Status by Age by Sex | `indigenous_status`, subject to small-count policy. | A/B |
| `G08` | Ancestry by Country of Birth of Parents | `ancestry`, cultural context. | A |
| `G09` | Country of Birth of Person by Age by Sex | `country_of_birth`; replaces G01 coarse birthplace summary. | A |
| `G13` | Language Used at Home by Proficiency in Spoken English by Sex | `language_used_at_home`, `english_proficiency`. | A/B |
| `G16` | Highest Year of School Completed by Age by Sex | School completion baseline. | A |
| `G17` | Total Personal Income (Weekly) by Age by Sex | `income_band`, conditioned by age and sex. | A |
| `G27` | Relationship in Household by Age by Sex | `household_relationship`, family role. | A |
| `G29` | Family Composition | `family_type` context; family-level distribution. | B |
| `G35` | Household Composition by Number of Persons Usually Resident | Household size/composition context. | B |
| `G36` | Dwelling Structure | `housing_type`. | A |
| `G37` | Tenure and Landlord Type by Dwelling Structure | Tenure/housing context. | B |
| `G46` | Labour Force Status by Age by Sex | `labour_force_status`. | A |
| `G49` | Highest Non-School Qualification: Level of Education by Age by Sex | Qualification level. | A |
| `G50` | Highest Non-School Qualification: Field of Study by Age by Sex | `field_of_study`. | A |
| `G54` | Industry of Employment by Age by Sex | `industry`; conditions occupation/professional persona. | B |
| `G60` | Occupation by age by Sex | `occupation`; primary work identity feature. | A |

## Column-Worthiness Rules

Inside a worthy topic, not all columns are sampler columns.

Sampler candidates must:

- have a readable category label from ABS metadata;
- belong to the semantic section's declared grain;
- represent a count for a real category, not a total;
- be compatible with adult-persona sampling;
- map to one seed field or one conditioning field.

Columns must be validation-only or excluded when they are:

- explicit table totals;
- `Persons` sex aggregates where male/female categories are present;
- broad rollups that duplicate more detailed bands;
- `Not stated`;
- `Not applicable`;
- `Other`, unless no better category exists;
- child-only categories for adult persona generation;
- categories too sparse to sample safely without a collapse rule;
- delivery-format artifacts rather than meaningful demographic states.

## Required Config Shape

Extend `configs/abs_semantic_tables.yml` topic sections with these fields as the
semantic layer matures:

```yaml
sampler:
  tier: A
  guardrail:
    sample: allow
    condition: allow
    validate: allow
    generate: deny
  persona_fields:
    - income_band
  conditioning_fields:
    - sa2_code
    - age_band
    - sex
  adult_persona_policy: include_adult_categories_only
  aggregate_policy: exclude_from_sampling_keep_for_validation
  missingness_policy: not_stated_as_missing
  sparse_category_policy: preserve_label_then_collapse_if_needed
  promotion_status: candidate
```

Promotion statuses:

```text
candidate       identified as useful, not implemented yet
semantic_ready  readable long topic exists and reconciles
mart_ready      sampler-facing mart exists and passes tests
sampler_ready   used by sampler with validation evidence
deferred        useful later, not needed for v1
excluded        intentionally out of v1
```

Guardrail rules should be machine-readable. Avoid encoding core policy only in
comments or prose.

## Required Semantic Long Contract

Every worthy topic must expose a readable long dataset before mart promotion.

Minimum columns:

```text
census_year
geography_level
sa2_code
sa2_name
state_name
logical_table
section_name
feature_name
count
source_physical_table
source_raw_column
source_label
is_total
is_sampler_candidate
sampler_tier
```

Topic-specific axis columns should be explicit where relevant:

```text
age_band
sex
marital_status
social_marital_status
household_relationship
family_type
dwelling_structure
tenure_landlord
education_level
field_of_study
labour_force_status
occupation
industry
income_band
ancestry
country_of_birth
language_used_at_home
english_proficiency
indigenous_status
```

Do not invent an axis that is not in the source topic. Missing axes should be
`null` or absent by contract.

## Implementation Order

Implement one topic at a time in this order:

1. `G04` age by sex.
2. `G46` labour force status by age and sex.
3. `G60` occupation by age and sex.
4. `G17` personal income by age and sex.
5. `G05` registered marital status.
6. `G27`, `G29`, and `G35` household/family structure.
7. `G36` and `G37` housing.
8. `G16`, `G49`, and `G50` education.
9. `G08`, `G09`, and `G13` cultural/linguistic context.
10. `G07` Indigenous status with small-count handling.

This produces a useful seed chain:

```text
SA2
  -> age/sex
  -> labour force
  -> occupation
  -> income
  -> household/family
  -> housing
  -> education
  -> cultural context
```

## Non-Goals

- Do not mutate `census_2021_data`.
- Do not rename raw ABS columns.
- Do not model non-SA2 geography as persona grain.
- Do not generate final persona prose in this spec.
- Do not build every `sa2_g*` topic.
- Do not use `aust_*`, `ste_*`, `lga_*`, `sa1_*`, or other geography tables as
  individual-persona inputs.
- Do not sample from totals or broad aggregate columns.
- Do not treat the semantic catalog as optional implementation commentary.

## Likely Files

- `docs/persona-worthy-sa2-topics.md`
- `configs/abs_semantic_tables.yml`
- `src/aus_personas/cli.py`
- `src/aus_personas/census_semantics.py`
- `dbt/aus_personas/models/intermediate/abs/`
- `dbt/aus_personas/models/marts/pgm/`
- `tests/`
- `CHANGELOG.md`

## Edge Cases

- ABS table parts: topics such as `G09`, `G13`, `G17`, `G49`, `G50`, and `G60`
  span multiple physical tables. The semantic topic must merge parts without
  losing source provenance.
- Perturbation: ABS small-cell perturbation means subtotals may not reconcile
  exactly. QA should allow documented tolerance rather than forcing exact sums.
- Adult personas: child-only rows must not feed adult persona generation.
- Sex aggregates: `Persons` rows are useful for QA but must not be sampled when
  sex-specific rows exist.
- Household topics: `G29`, `G35`, `G36`, and `G37` are household or dwelling
  distributions, not person distributions. They condition the seed but should
  not be blindly joined as if they share the same person grain.
- Sparse categories: preserve original labels in semantic output, then collapse
  only in sampler-facing marts when needed.
- Cultural fields: ancestry, language, and country of birth are distinct. Do not
  collapse them into one generic `cultural_background` field before generation.

## Test Expectations

Use TDD for the guardrail and catalog work. Do not write all tests first. Use
small vertical slices:

```text
RED: one behavior test
GREEN: minimal implementation
REFACTOR: simplify while preserving the passing behavior
```

First TDD slices:

1. RED: `G17.personal_income` is allowed for `sample`.
   GREEN: catalog lookup returns `allow`.
2. RED: G01 birthplace summary is denied for `sample` but allowed for
   `validate`.
   GREEN: purpose-specific decisions are supported.
3. RED: `aust_g17` and uncatalogued `sa2_g99` fail closed.
   GREEN: non-SA2 and unknown topics return `deny` or `unknown`.
4. RED: total columns and `Persons` aggregates are denied for `sample`.
   GREEN: aggregate policy is enforced from catalog metadata.
5. RED: `G54.industry` is allowed for `condition` but not as the primary
   `occupation` sample.
   GREEN: conditioning-only topics are handled distinctly from sampled fields.

For config/catalog work:

- YAML parses successfully.
- Every stage-1 topic has a `sampler.tier` or equivalent worthiness marker.
- Every sampler candidate declares at least one persona or conditioning field.
- Excluded/validation-only sections declare why they are not sampled.
- Every section has machine-readable guardrail decisions for `sample`,
  `condition`, `validate`, and `generate`.
- Unknown topics fail closed.
- Non-SA2 geography tables fail closed for persona sampling.

For semantic long views:

- dbt model builds for the topic.
- dbt tests confirm non-null `sa2_code`, `source_raw_column`, and `count`.
- Aggregates and totals are marked `is_total = true` or excluded from sampling.
- A single-SA2 smoke query returns readable category values.
- Counts reconcile to source totals within an explicit perturbation tolerance.

For CLI work:

- `aus-personas census worthy --stage 1` lists topic, title, tier, fields, and
  promotion status.
- `aus-personas census worthy G17` explains sampled and excluded sections.
- Tests cover missing topic, unknown section, and validation-only topic handling.

Suggested commands:

```sh
uv run pytest
uv run ruff check src tests
uv run dbt --project-dir dbt/aus_personas parse
```

Topic-specific implementation should also run the relevant dbt build/test
selectors.

## Acceptance Criteria

- [ ] `configs/abs_semantic_tables.yml` records worthiness metadata for all
  stage-1 topics.
- [ ] Catalog entries expose explicit `allow`, `allow_context`,
  `allow_validate`, `deny`, or `unknown` decisions by purpose.
- [ ] Disallowed requests fail closed before querying raw wide tables.
- [ ] Non-SA2 geography tables are denied for persona sampling.
- [ ] The CLI can list stage-1 topic worthiness without querying raw wide tables
  directly.
- [ ] The CLI can explain why a topic/section is denied for a requested purpose.
- [ ] At least the next implemented topic follows the worthiness gate before mart
  promotion.
- [ ] TDD slices cover at least one allowed sample, one validation-only section,
  one context-only section, one unknown topic, and one aggregate denial.
- [ ] Totals, sex aggregates, missingness categories, and adult-persona
  exclusions are handled consistently.
- [ ] Documentation states that one final row represents one synthetic
  Australian resident.
- [ ] Tests cover catalog parsing and at least one topic-specific worthiness
  lookup.
- [ ] Relevant checks pass.
- [ ] `CHANGELOG.md` is updated when behavior changes.

## Known Risks

- Some ABS metadata labels are long and inconsistent. Parsing should use
  structured metadata patterns where possible and preserve source labels.
- Household and dwelling distributions do not share the same grain as person
  distributions. Treat them as conditioning/context unless a defensible
  person-level allocation rule exists.
- Overfitting to one SA2 can make the sampler brittle. Validate with a local SA2
  such as Chatswood/Willoughby and a contrasting regional SA2.
- G01 is tempting because it is already partly implemented, but it is too coarse
  for many final persona fields. Prefer detailed topics once available.
- Data Designer should not invent structured demographics that the sampler has
  already decided. The prose step consumes the seed; it does not repair it.
