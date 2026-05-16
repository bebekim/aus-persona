# ABS Census Table Dictionary

This project should not expose raw ABS table names such as `g01`, `g17`, or
`sa2_g60a` as product concepts. Those are loader/storage identifiers. The
human-facing layer should use ABS metadata names plus a small set of stable
project aliases.

For source authority, caveats, geography rules, and local workbook provenance,
also read [ABS Source Provenance](abs-source-provenance.md).

## Current Database State

The ABS data is available in the existing Docker container:

```text
container: censusloader-postgres
image: minus34/censusloader:latest
host port: 5433 -> container port 5432
database: postgres
schemas:
  census_2021_data
  census_2021_bdys_gda94
```

The active Docker backend is OrbStack. Docker Desktop is not needed for this
repo.

The relevant SA2 boundary table exists:

```text
census_2021_bdys_gda94.sa2_2021_aust_gda94
rows: 2,473 boundary rows
key: sa2_code_2021
useful fields:
  sa2_code_2021
  sa2_name_2021
  sa3_code_2021
  sa3_name_2021
  sa4_code_2021
  sa4_name_2021
  gccsa_code_2021
  gccsa_name_2021
  state_code_2021
  state_name_2021
  area_albers_sqkm
  geom
```

The SA2 census profile tables exist and join cleanly:

```sql
select
  s.region_id,
  b.sa2_name_2021,
  b.state_name_2021,
  s.g1,
  s.g2,
  s.g3
from census_2021_data.sa2_g01 s
join census_2021_bdys_gda94.sa2_2021_aust_gda94 b
  on b.sa2_code_2021 = s.region_id;
```

`sa2_g01`, `sa2_g04a`, and `sa2_g60a` each have 2,472 statistic rows. The
boundary table has one extra SA2 boundary row without matching census stats.

## How To Read ABS Names

An ABS physical table name has three parts:

```text
sa2_g17a
--- ----
 |    |
 |    physical profile table suffix
 geography grain
```

The geography prefix tells you the spatial level:

```text
sa2_   Statistical Area Level 2
sa3_   Statistical Area Level 3
sa4_   Statistical Area Level 4
aust_  Australia total
ste_   State/Territory
```

The profile family tells you the census profile:

```text
G  General Community Profile
P  Place of Enumeration Profile
W  Working Population Profile
I  Indigenous Profile
T  Time Series Profile
```

For resident personas, use `G` first. Use `W` to enrich work and occupation.
Use `P` only when you deliberately want place-of-enumeration rather than usual
resident population.

The suffix is often split:

```text
G17  logical ABS table: Total Personal Income by Age by Sex
G17A physical table part A
G17B physical table part B
G17C physical table part C
```

So the user-facing name should be:

```text
sa2_g17a -> SA2 / General Community / Total Personal Income by Age by Sex / part A
```

not:

```text
g17a
```

## How To Decode Columns

Every statistic table has:

```text
region_id
g1, g2, ...
w1, w2, ...
p1, p2, ...
```

`region_id` joins to the geography code. For SA2:

```text
census_2021_data.sa2_g01.region_id
  = census_2021_bdys_gda94.sa2_2021_aust_gda94.sa2_code_2021
```

The raw statistic columns are decoded by:

```text
census_2021_data.metadata_stats.sequential_id
```

Examples:

```text
raw column: g1241
metadata sequential_id: G1241
short_id: M_Afghanistan_0_4
long_id: MALES_Afghanistan_Age_0_4_years
description: Age: 0-4 years|MALES
logical table: G09 Country of Birth of Person by Age by Sex
physical table: sa2_g09a
```

```text
raw column: w1
metadata sequential_id: W1
short_id: M_15_19_EWFT
long_id: Males_15_19_years_Employed_Worked_full_time
description: Employed: Worked full-time|MALES
logical table: W01 Labour Force Status by Age by Sex
physical table: sa2_w01a
```

This means our dictionary key should be `physical_table + raw_column`, not just
`g1` or `w1`.

## Canonical Dictionary View

Use this metadata view as the basis for all friendlier names:

```sql
create or replace view persona_abs_column_dictionary as
select
  lower(s.table_number) as physical_table_suffix,
  'sa2_' || lower(s.table_number) as sa2_physical_table,
  upper(left(s.table_number, 3)) as logical_table_code,
  t.table_name as logical_table_name,
  t.table_description as population_universe,
  lower(s.sequential_id) as raw_column,
  s.sequential_id,
  s.short_id,
  s.long_id,
  s.column_heading_description,
  case left(upper(s.table_number), 1)
    when 'G' then 'General Community Profile'
    when 'P' then 'Place of Enumeration Profile'
    when 'W' then 'Working Population Profile'
    when 'I' then 'Indigenous Profile'
    when 'T' then 'Time Series Profile'
    else 'Unknown'
  end as profile_family_name
from census_2021_data.metadata_stats s
left join census_2021_data.metadata_tables t
  on t.table_number = upper(left(s.table_number, 3));
```

For the product/data model, derive stable friendly names from:

```text
profile_family_name
logical_table_name
long_id
column_heading_description
```

Do not derive user-facing names from `g1`, `g1241`, or `sa2_g17a` alone.

## Profile Counts

The metadata catalogue contains:

```text
G General Community Profile: 62 logical tables
I Indigenous Profile: 21 logical tables
P Place of Enumeration Profile: 45 logical tables
T Time Series Profile: 35 logical tables
W Working Population Profile: 27 logical tables
```

The physical data schema contains 4,548 census data tables across geographies
and profiles.

## Persona-Relevant Tables

These are the sensible first-pass tables for a synthetic adult persona sampler.

### Geography

```text
SA2 geography dimension
table: census_2021_bdys_gda94.sa2_2021_aust_gda94
alias: sa2_geography
purpose: names, state, SA3, SA4, GCCSA, geometry, area
```

### Population Weighting

```text
G01 Selected Person Characteristics by Sex
alias: selected_person_characteristics_by_sex
purpose: base counts by sex and high-level demographic totals
use for: SA2 population weights, sex totals, basic QA
```

### Age And Sex

```text
G04 Age by Sex
alias: age_by_sex
purpose: age distribution by sex
use for: P(age, sex | SA2)
physical tables: sa2_g04a, sa2_g04b
```

### Marital Status

```text
G05 Registered Marital Status by Age by Sex
alias: registered_marital_status_by_age_sex
purpose: legal marital status
use for: P(registered_marital_status | age, sex, geography)
```

```text
G06 Social Marital Status by Age by Sex
alias: social_marital_status_by_age_sex
purpose: partnered/not partnered in social living arrangement
use for: P(social_marital_status | age, sex, geography)
```

For personas, prefer `G05` for legal status and optionally use `G06` to shape
household/living-partner plausibility.

### Indigenous Status

```text
G07 Indigenous Status by Age by Sex
alias: indigenous_status_by_age_sex
purpose: Indigenous status distribution by age and sex
use for: P(indigenous_status | age, sex, SA2)
```

Use carefully. This is a demographic context variable, not a licence to invent
cultural details. For richer Indigenous-specific analysis, the `I` profile
exists, but v1 should not overfit or essentialise from it.

### Ancestry, Country Of Birth, Language

```text
G08 Ancestry by Country of Birth of Parents
alias: ancestry_by_parent_birthplace
purpose: ancestry responses and parent birthplace context
use for: ancestry fields and cultural-background consistency
```

```text
G09 Country of Birth of Person by Age by Sex
alias: country_of_birth_by_age_sex
purpose: country of birth distribution by age and sex
use for: P(country_of_birth | age, sex, SA2)
physical tables: sa2_g09a through sa2_g09h
```

```text
G10 Country of Birth of Person by Year of Arrival in Australia
alias: country_of_birth_by_arrival_year
purpose: migration-era context for overseas-born personas
use for: optional arrival cohort
```

```text
G13 Language Used at Home by Proficiency in Spoken English by Sex
alias: language_home_by_english_proficiency_sex
purpose: language at home and English proficiency
use for: language_home, English proficiency, cultural-background consistency
physical tables: sa2_g13a through sa2_g13e
```

### Religion

```text
G14 Religious Affiliation by Sex
alias: religious_affiliation_by_sex
purpose: religion distribution by sex
use for: optional context only
```

Treat religion as optional and sensitive. It should not drive deterministic
persona behaviour.

### Education

```text
G15 Type of Educational Institution Attending by Student Status by Age by Sex
alias: education_attendance_by_age_sex
purpose: current study participation
use for: student status, especially younger adults
```

```text
G16 Highest Year of School Completed by Age by Sex
alias: school_completion_by_age_sex
purpose: school attainment
use for: school-level education plausibility
```

```text
G49 Highest Non-School Qualification: Level of Education by Age by Sex
alias: qualification_level_by_age_sex
purpose: post-school qualification level
use for: P(education_level | age, sex, geography)
physical tables: sa2_g49a, sa2_g49b
```

```text
G50 Highest Non-School Qualification: Field of Study by Age by Sex
alias: field_of_study_by_age_sex
purpose: field of study for qualified persons
use for: P(field_of_study | age, sex, education_level, geography)
physical tables: sa2_g50a, sa2_g50b, sa2_g50c
```

### Income

```text
G17 Total Personal Income (Weekly) by Age by Sex
alias: personal_income_weekly_by_age_sex
purpose: personal income distribution
use for: P(income_band | age, sex, geography)
physical tables: sa2_g17a, sa2_g17b, sa2_g17c
```

```text
G33 Total Household Income (Weekly) by Household Composition
alias: household_income_weekly_by_household_composition
purpose: household-level income
use for: household context, not individual income
```

Use `G17` for persona income. Use `G33` only after household composition is
sampled.

### Disability And Health

```text
G18 Core Activity Need for Assistance by Age by Sex
alias: core_activity_need_for_assistance_by_age_sex
purpose: need for assistance
use for: optional accessibility/support context
```

```text
G19 Type of Long-Term Health Condition by Age by Sex
alias: long_term_health_condition_type_by_age_sex
purpose: long-term condition categories
use for: optional health-context simulation only
```

Health fields are sensitive. Keep them out of the first public persona text
unless there is a clearly scoped use case and safety review.

### Household And Family

```text
G27 Relationship in Household by Age by Sex
alias: household_relationship_by_age_sex
purpose: relationship role inside household
use for: P(relationship_in_household | age, sex, geography)
```

```text
G29 Family Composition
alias: family_composition
purpose: family type counts
use for: family_type and household plausibility
```

```text
G35 Household Composition by Number of Persons Usually Resident
alias: household_composition_by_resident_count
purpose: household size and composition
use for: household_type, household_size
```

### Housing

```text
G36 Dwelling Structure
alias: dwelling_structure
purpose: separate house, semi-detached, apartment, other dwelling types
use for: housing_type / dwelling_structure
```

```text
G37 Tenure and Landlord Type by Dwelling Structure
alias: tenure_landlord_by_dwelling_structure
purpose: owned, mortgage, rented, landlord type by dwelling structure
use for: tenure, renter/owner plausibility
```

```text
G40 Rent (Weekly) by Landlord Type
alias: rent_weekly_by_landlord_type
purpose: rent bands for rented dwellings
use for: renter household economics
```

### Labour Force, Industry, Occupation

```text
G43 Selected Labour Force Education and Migration Characteristics by Sex
alias: selected_labour_education_migration_by_sex
purpose: compact labour/education/migration indicators
use for: broad QA and fallback features
```

```text
G46 Labour Force Status by Age by Sex
alias: labour_force_status_by_age_sex
purpose: employed/unemployed/not-in-labour-force by age and sex
use for: P(labour_force_status | age, sex, geography)
physical tables: sa2_g46a, sa2_g46b
```

```text
G54 Industry of Employment by Age by Sex
alias: industry_by_age_sex
purpose: industry distribution for employed persons
use for: P(industry | age, sex, geography)
```

```text
G60 Occupation by Age by Sex
alias: occupation_by_age_sex
purpose: occupation distribution for employed persons
use for: P(occupation | age, sex, geography)
physical tables: sa2_g60a, sa2_g60b
```

```text
W13 Occupation by Sex
alias: workplace_occupation_by_sex
purpose: workplace-population occupation distribution
use for: employment enrichment and validation, not resident base sampling
```

```text
W16 Occupation by Total Personal Income by Age
alias: workplace_occupation_by_income_age
purpose: occupation-income-age relationships
use for: P(income_band | occupation, age) calibration
```

For resident personas, start with `G46` and `G60`. Use `W` later to improve
occupation-income consistency for employed personas.

## Recommended Friendly Naming Convention

Use three levels of names.

### 1. Physical Source Name

Keep exact source provenance:

```text
census_2021_data.sa2_g17a.g5211
```

### 2. Stable Project Alias

Use a readable table alias:

```text
personal_income_weekly_by_age_sex
```

### 3. Feature Name

Use a sampler-facing variable/category name:

```text
income_band = "Nil income"
age_band = "25-34"
sex = "Female"
count = 123
```

The sampler should never consume `g5211` directly. It should consume normalized
records:

```text
sa2_code
feature_group
conditional_axes
category
count
source_table
source_column
source_label
```

## First PGM Feature Mart

Build the first long-form feature mart from these tables only:

```text
sa2_geography
G01 selected_person_characteristics_by_sex
G04 age_by_sex
G05 registered_marital_status_by_age_sex
G07 indigenous_status_by_age_sex
G09 country_of_birth_by_age_sex
G13 language_home_by_english_proficiency_sex
G16 school_completion_by_age_sex
G17 personal_income_weekly_by_age_sex
G27 household_relationship_by_age_sex
G29 family_composition
G36 dwelling_structure
G37 tenure_landlord_by_dwelling_structure
G46 labour_force_status_by_age_sex
G49 qualification_level_by_age_sex
G50 field_of_study_by_age_sex
G60 occupation_by_age_sex
```

This gives enough structure for:

```text
P(SA2)
P(age, sex | SA2)
P(marital_status | age, sex, SA2/state)
P(indigenous_status | age, sex, SA2)
P(country_of_birth | age, sex, SA2)
P(language_home | sex, SA2)
P(education_level | age, sex, SA2/state)
P(labour_force_status | age, sex, SA2/state)
P(occupation | age, sex, SA2/state)
P(income_band | age, sex, SA2/state)
P(dwelling_structure, tenure | SA2)
P(family_type | SA2/state)
```

## Important Caveats

ABS tables are aggregate cross-tabs. They do not contain individual rows. A
single table may give a clean joint distribution for two or three variables,
but no table gives the full joint distribution needed for complete personas.

That is why the sampler needs documented assumptions:

```text
age/sex comes from G04
marital status comes from G05 conditioned on age/sex
education comes from G16/G49 conditioned on age/sex
occupation comes from G60 conditioned on age/sex
income comes from G17 conditioned on age/sex
occupation-income interaction is approximated until W16 is integrated
```

Where exact joint distributions are missing, use conditional weighted sampling,
raking/IPF, or explicit fallback from SA2 to SA3/state/Australia.

## Next Implementation Step

Create a real dictionary table/view and a small extractor that emits normalized
long-form rows for the first PGM tables.

Target output:

```text
build/abs_dictionary.parquet
build/sa2_feature_mart.parquet
```

Minimum long-form schema:

```text
sa2_code
sa2_name
state_name
source_profile
logical_table_code
logical_table_name
physical_table
raw_column
short_id
long_id
source_label
count
```

Once this exists, the PGM sampler can use sensible concepts instead of raw ABS
storage names.
