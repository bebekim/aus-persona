# ABS Source Provenance

This project should treat ABS documentation as first-class metadata. The
`censusloader` tables provide counts, but the ABS pages below define what those
counts mean, their scope, and how they should be joined.

## Primary Sources

### Census Dictionary 2021

Source:
<https://www.abs.gov.au/census/guide-census-data/census-dictionary/2021>

Use for:

- variable definitions
- variable scope / population universe
- categories
- derivation rules
- Census form questions
- history and changes
- data-use caveats such as non-response

Design implication:

The metadata decoder should not stop at table labels. For any feature used by
the sampler, link the output variable to the relevant Census Dictionary concept
when available. For example, income, labour force status, place of usual
residence, ancestry, language used at home, and family composition each need
concept-level documentation before they become sampler features.

### 2021 Census Concepts

Source:
<https://www.abs.gov.au/tags/2021-census-concepts>

Use for:

- explanatory papers on difficult Census concepts
- known interpretation traps
- comparisons between Census and other ABS sources

Relevant concept papers listed by ABS include:

- income across administrative data, Census, and ABS surveys
- Census vs Labour Force Survey labour-force concepts
- place of work data
- family composition and grandparent families
- disability statistics
- Aboriginal and Torres Strait Islander ancestries
- ancestry data
- migrant statistics
- long-term health condition data sources
- persons temporarily absent
- place of enumeration vs place of usual residence
- non-binary sex responses
- supplementary codes in Census variables

Design implication:

These papers are the rulebook for sampler caveats. For v1, prefer conservative
resident-person sampling from General Community Profile tables. Use Place of
Enumeration and Working Population tables only with explicit semantics.

### Understanding Census Geography

Source:
<https://www.abs.gov.au/census/guide-census-data/geography>

Use for:

- choosing the right geography for a question
- ASGS hierarchy and geography semantics
- Census-night boundary caveats

Key design points:

- Census data is tied to a snapshot in time.
- ASGS defines the geographies ABS uses for released data.
- Mesh Blocks build to SA1s, then SA2s, SA3s, SA4s, State/Territories, and
  Australia.
- GCCSAs are part of the Main Structure and are built from SA4s.
- Many non-ABS structures are built from Mesh Blocks.

Design implication:

The first sampler grain remains SA2. It is the right practical balance between
locality and statistical stability. Mesh Blocks should support validation,
dwelling density, and land-use context, not full persona sampling in v1.

### ASGS Edition 3 Digital Boundary Files

Source:
<https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files>

Use for:

- authoritative boundary files
- SA2/SA3/SA4/state/GCCSA geometry
- Mesh Block geometry
- Remoteness Area geometry
- datum and spatial accuracy notes

Design notes:

- ABS provides digital boundaries in GeoPackage and ESRI Shapefile formats.
- GDA2020 and GDA94 are both available.
- GDA2020 is the newer national datum, but the current `censusloader` container
  uses `census_2021_bdys_gda94`.
- The ABS page notes that the GDA94/GDA2020 difference on the ground is about
  1.8 metres.
- Remoteness Areas are available as ASGS Edition 3 boundaries.

Design implication:

Keep the current GDA94 join because it matches the loaded database:

```text
census_2021_bdys_gda94.sa2_2021_aust_gda94
```

If importing new boundary files, record datum explicitly and do not silently mix
GDA94 and GDA2020 geometry in spatial joins.

### Census Mesh Block Counts 2021

Source:
<https://www.abs.gov.au/census/guide-census-data/mesh-block-counts/2021>

Local workbook:

```text
/Users/marcus.kim/Downloads/Mesh Block Counts, 2021.xlsx
```

Use for:

- Mesh Block usual resident population
- Mesh Block dwelling counts
- Mesh Block category / land-use context
- small-area density validation

ABS notes:

- Mesh Blocks are the smallest geography for which Census data is output.
- Most Mesh Blocks contain 30 to 60 dwellings.
- 2021 has 368,286 Mesh Blocks covering Australia without gaps or overlaps.
- The downloadable file contains total usual resident population and dwelling
  count for Mesh Blocks.

Local workbook structure:

```text
Contents
Table 1    New South Wales part 1
Table 1.1  New South Wales part 2
Table 2    Victoria part 1
Table 2.1  Victoria part 2
Table 3    Queensland part 1
Table 3.1  Queensland part 2
Table 4    South Australia
Table 5    Western Australia
Table 6    Tasmania
Table 7    Northern Territory
Table 8    Australian Capital Territory
Table 9    Other Territories / state code 9
Explanatory Notes
```

Observed data columns:

```text
MB_CODE_2021
MB_CATEGORY_NAME_2021
AREA_ALBERS_SQKM
Dwelling
Person
State
```

Example row:

```text
MB_CODE_2021: 10000010000
MB_CATEGORY_NAME_2021: Residential
AREA_ALBERS_SQKM: 0.0209
Dwelling: 44
Person: 63
State: 1
```

Design implication:

Mesh Block counts are useful for:

- validating SA2 population totals after aggregation
- deriving dwelling/person density features
- adding coarse land-use context
- checking whether a sampled SA2 is mostly residential, commercial,
  industrial, parkland, education, etc.

They should not replace SA2 profile tables for v1 personas because the workbook
does not contain the demographic cross-tabs needed for age, sex, income,
education, household, and occupation sampling.

### 2021 Census Overcount And Undercount

Source:
<https://www.abs.gov.au/statistics/people/population/2021-census-overcount-and-undercount/2021>

Use for:

- validation caveats
- uncertainty notes
- optional high-level population weighting sensitivity

Key ABS figures:

- 2021 Census net undercount: 0.7%, or 190,044 persons.
- Northern Territory net undercount: 6.0%.
- Australian Capital Territory net overcount: -0.6%.
- Males had higher net undercount than females.
- Aboriginal and Torres Strait Islander net undercount was 17.4%.
- The ABS derives net undercount using the Post Enumeration Survey.

Design implication:

Do not blindly "correct" every SA2 count with national undercount. The PES is a
coverage-quality source, not row-level truth. For v1:

- report validation against published Census counts
- note that Census counts include known coverage error
- avoid presenting synthetic row counts as true population estimates
- optionally add sensitivity weights later at state/sex/Indigenous-status level
  if a use case requires population-estimate calibration

## Source Priority

When sources appear to disagree, use this priority:

1. ABS Census Dictionary for variable meaning and scope.
2. ABS Census Concepts papers for interpretation caveats.
3. censusloader `metadata_tables` and `metadata_stats` for table/column labels.
4. ABS ASGS documentation and boundary metadata for geography semantics.
5. Mesh Block counts for small-area population/dwelling validation.
6. Overcount/undercount for coverage caveats and sensitivity analysis.

## Impact On Next Build Step

The next build step should be `sa2_feature_mart`, not the sampler.

Inputs:

```text
census_2021_data.sa2_g*
census_2021_data.metadata_tables
census_2021_data.metadata_stats
census_2021_bdys_gda94.sa2_2021_aust_gda94
optional: /Users/marcus.kim/Downloads/Mesh Block Counts, 2021.xlsx
```

Output:

```text
build/sa2_feature_mart.parquet
```

Minimum schema:

```text
sa2_code
sa2_name
state_name
source_profile
logical_table_code
logical_table_name
project_alias
physical_table
raw_column
source_label
sex
age_band
category_axis
category
count
is_total
```

The sampler should consume this feature mart, not raw `sa2_g17a.g5211` style
columns.
