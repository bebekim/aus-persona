# Persona-Worthy SA2 Census Topics

This project does not treat every `sa2_g*` column as a persona feature.
The target output is a Korea-style persona row: a structured demographic seed
expanded into narrative fields by Data Designer or another generation step.

Raw ABS tables stay untouched. This document defines which SA2 Census topics
are worth transforming into semantic long tables for sampling.

## Target Grain

One final row represents one synthetic Australian resident.

The resident is sampled from SA2-level Census distributions. The row is not a
real person and does not represent one Census response. It is a statistically
plausible persona seed, later expanded into prose.

## Output Field Groups

Structured seed fields should come from Census or controlled reference data:

- `uuid`
- `sex`
- `age`
- `marital_status`
- `education_level`
- `bachelors_field`
- `occupation`
- `labour_force_status`
- `income_band`
- `family_type`
- `housing_type`
- `ancestry`
- `country_of_birth`
- `language_used_at_home`
- `indigenous_status`
- `sa2_code`
- `sa2_name`
- `state`
- `country`

Narrative fields should be generated from the structured seed and local context:

- `professional_persona`
- `sports_persona`
- `arts_persona`
- `travel_persona`
- `culinary_persona`
- `family_persona`
- `persona`
- `cultural_background`
- `career_goals_and_ambitions`
- `skills_and_expertise`
- `skills_and_expertise_list`
- `hobbies_and_interests`
- `hobbies_and_interests_list`

ABS Census data should constrain the seed. It should not be expected to contain
ready-made hobbies, tastes, skills, or prose.

## Korea Persona Schema Mapping

The NVIDIA Nemotron Personas Korea schema is useful as an output-shape
reference, not as an Australian population base.

Map Korea-style structured columns into Australian Census-backed seed fields
before generating prose:

| Korea column | Australian persona field | ABS/Census source |
| --- | --- | --- |
| `uuid` | `uuid` | Generated identifier. |
| `sex` | `sex` | `G04` age by sex. |
| `age` | `age`, `age_band` | `G04` age by sex; exact age is sampled inside the ABS age band. |
| `marital_status` | `marital_status` | `G05` registered marital status; optionally use `G06` social marital status for partner/living arrangement context. |
| `military_status` | `defence_service_status` | `G22` Australian Defence Force service; not equivalent to Korean military-service status. |
| `family_type` | `family_type`, `household_relationship` | `G29` family composition and `G27` relationship in household; grain mismatch must be declared. |
| `housing_type` | `housing_type` | `G36` dwelling structure. |
| `education_level` | `education_level`, `school_completion` | `G16` school completion and `G49` non-school qualification level. |
| `bachelors_field` | `field_of_study` | `G50` field of study; broader than bachelor-only. |
| `occupation` | `occupation` | `G60` occupation by age and sex; condition on labour force status where possible. |
| `district` | `sa2_name` or `lga_name` | ABS geography dimension; choose the local reporting grain explicitly. |
| `province` | `state` | ABS geography dimension. |
| `country` | `country` | Constant/reference value, usually `Australia`. |

Generate Korea-style narrative columns from the fixed Australian seed instead
of reading them from ABS:

- `professional_persona`
- `sports_persona`
- `arts_persona`
- `travel_persona`
- `culinary_persona`
- `family_persona`
- `persona`
- `cultural_background`
- `skills_and_expertise`
- `skills_and_expertise_list`
- `hobbies_and_interests`
- `hobbies_and_interests_list`
- `career_goals_and_ambitions`

Useful Australian additions beyond the Korea schema:

- `sa2_code`, `sa2_name`, `state`, `lga_name`, `gccsa_name`, and remoteness or
  other geographic context when available.
- `income_band` from `G17`.
- `labour_force_status` from `G46`.
- `industry` from `G54`; this is employed-person context and should be
  conditioned by labour-force and occupation logic before it influences prose.
- `ancestry` from `G08`.
- `country_of_birth` from `G09`.
- `language_used_at_home` and `english_proficiency` from `G13`.
- `indigenous_status` from `G07`, with privacy and small-count care.
- `tenure_landlord` or owner/renter context from `G37` after
  household/dwelling context is sampled.
- Deferred `rent_band` context from `G40` only after a rented-household use case
  is explicitly promoted.
- `household_size` and composition context from `G35`.
- Deferred support/accessibility context from `G18` only for clearly scoped,
  reviewed use cases.
- `defence_service_status` from `G22`; this is Australian Defence Force
  service context, not a direct migration of Korean military status.

## Worthiness Tiers

Use these tiers before promoting any raw column into a semantic model.

| Tier | Meaning | Use |
| --- | --- | --- |
| A | Sampler core | Directly sampled into the persona seed. |
| B | Conditioning/context | Improves plausibility or conditions another sample. |
| C | Validation only | Used for totals, QA, broad sanity checks, or rollups. |
| D | Exclude for v1 | Too broad, duplicate, aggregate, sparse, or not useful for adult personas. |

Column-level rules:

- Exclude explicit total columns from sampling.
- Exclude `Persons` sex aggregates when male/female rows are available.
- Treat `Not stated`, `Not applicable`, and `Other` as missingness or fallback,
  not as preferred persona values.
- Exclude child-only categories when producing adult personas.
- Collapse very small categories only after preserving the original semantic
  label in the catalog.
- Prefer detailed topics over coarse summaries when both exist.

## Stage-1 Table Selection

These table meanings are confirmed from `census_2021_data.metadata_tables`.

| ABS topic | Metadata title | Persona role | Tier |
| --- | --- | --- | --- |
| `G01` | Selected Person Characteristics by Sex | Useful first pass, but mixed. Use age/sex, Indigenous summary, and school completion. Use totals, broad birthplace, broad language, citizenship, Census-night location, and dwelling residence as QA/context only. | A/C |
| `G04` | Age by Sex | Primary age and sex distribution. Better adult-age base than broad G01. | A |
| `G05` | Registered Marital Status by Age by Sex | Legal marital status. Maps to `marital_status`. | A |
| `G06` | Social Marital Status by Age by Sex | Partnered/de facto context. Useful for household and family plausibility. | B |
| `G07` | Indigenous Status by Age by Sex | Maps to `indigenous_status`, with careful handling of small counts. | A/B |
| `G08` | Ancestry by Country of Birth of Parents | Maps to ancestry and cultural background constraints. | A |
| `G09` | Country of Birth of Person by Age by Sex | Maps to `country_of_birth`; preferred over G01 birthplace summary. | A |
| `G13` | Language Used at Home by Proficiency in Spoken English by Sex | Maps to `language_used_at_home` and English proficiency context. | A/B |
| `G16` | Highest Year of School Completed by Age by Sex | Maps to school completion and education baseline. | A |
| `G17` | Total Personal Income (Weekly) by Age by Sex | Maps to `income_band`, conditioned by age and sex. | A |
| `G27` | Relationship in Household by Age by Sex | Maps to family role and living arrangement. | A |
| `G29` | Family Composition | Conditions `family_type`; household-level, not person-level. | B |
| `G35` | Household Composition by Number of Persons Usually Resident | Conditions household size and family plausibility. | B |
| `G36` | Dwelling Structure | Maps to `housing_type`. | A |
| `G37` | Tenure and Landlord Type by Dwelling Structure | Housing tenure/context; useful for richer local plausibility. | B |
| `G46` | Labour Force Status by Age by Sex | Maps to `labour_force_status`; conditions occupation and income. | A |
| `G49` | Highest Non-School Qualification: Level of Education by Age by Sex | Maps to post-school qualification level. | A |
| `G50` | Highest Non-School Qualification: Field of Study by Age by Sex | Maps to `bachelors_field` or broader field of study. | A |
| `G54` | Industry of Employment by Age by Sex | Conditions occupation and professional persona. | B |
| `G60` | Occupation by age by Sex | Maps to `occupation`; one of the strongest persona fields. | A |

## Not All Columns Are Worthy

Even inside a worthy table, only category cells that match the topic grain are
sampler candidates.

For example, `G17` is worthy as a table, but the sampler should use:

- SA2
- age band
- sex
- weekly income band
- count

It should not sample from:

- table totals
- sex totals where sex-specific rows exist
- broad rollups that duplicate narrower bands
- `Not stated` as a normal income value

Likewise, `G09` is worthy for country of birth, but country detail should
replace G01's coarse `Australia` versus `Elsewhere` summary for final sampling.
The G01 summary remains useful for checking that detailed-country results roll
up approximately correctly.

## Build Order

Use this order for semantic long tables and sampler features:

1. `G04` age by sex.
2. `G46` labour force status by age and sex.
3. `G60` occupation by age and sex.
4. `G17` personal income by age and sex.
5. `G05` registered marital status.
6. `G27`, `G29`, and `G35` household and family structure.
7. `G36` and `G37` dwelling and tenure.
8. `G16`, `G49`, and `G50` education.
9. `G08`, `G09`, and `G13` ancestry, country of birth, and language.
10. `G07` Indigenous status, with stricter small-count and privacy treatment.

This order gets to usable persona seeds quickly:

`SA2 -> age/sex -> labour force -> occupation -> income -> household -> housing -> education -> cultural context`

## Stop Condition For A Topic

A topic is ready for sampler use only when:

- the raw `sa2_g*` physical tables are listed;
- metadata headings are decoded into readable category fields;
- the semantic long table has an explicit grain;
- total and aggregate columns are excluded or tagged as validation only;
- the topic can be queried for a single SA2 by readable category names;
- QA checks prove that semantic counts reconcile to source totals within known
  ABS perturbation limits.
