# Willoughby Hackathon Local Slice

This slice narrows the Australian persona prototype to the local council context
for a Chatswood hackathon hosted by Willoughby City Council.

## Working Scope

The persona-generation grain remains SA2. The local council scope is derived by
intersecting 2021 SA2 boundaries with the 2021 Willoughby LGA boundary.

Raw ABS tables stay untouched. The interpreted outputs live in the dbt target
schema.

## Boundary Result

`dim_willoughby_sa2_overlap` has one row per SA2 that intersects Willoughby.

| SA2 code | SA2 name | Role | % of SA2 in Willoughby | % of Willoughby from SA2 |
| --- | --- | --- | ---: | ---: |
| 121011683 | Castle Cove - Northbridge | core | 99.12 | 33.97 |
| 121011399 | Chatswood (West) - Lane Cove North | core | 70.80 | 17.48 |
| 121011684 | Chatswood - East | core | 100.00 | 15.20 |
| 121011687 | Willoughby | core | 100.00 | 13.67 |
| 121011401 | St Leonards - Naremburn | core | 93.80 | 11.55 |
| 121011682 | Artarmon | core | 100.00 | 7.40 |
| 121031408 | Lindfield - Roseville | edge | 1.38 | 0.73 |

For a quick demo, the six core SA2s are the intuitive local population frame.
For council-level estimates, the mart keeps the edge SA2 and weights all rows by
SA2 boundary overlap.

## Current Local Profile

`mart_willoughby_g01_profile` has one row per:

`Willoughby City Council x G01 topic x category x sex`

The current G01 profile covers:

- total persons by sex
- age group by sex
- birthplace summary by sex
- language summary by sex
- school completion by sex

Counts are area-weighted estimates from interpreted SA2 G01 rows, not raw ABS
delivery cells.

Selected `sex = 'Persons'` results:

| Topic | Category | Estimated count |
| --- | --- | ---: |
| total persons by sex | Total persons | 81,904 |
| age group by sex | 35-44 | 14,364 |
| age group by sex | 25-34 | 11,709 |
| age group by sex | 45-54 | 11,423 |
| birthplace summary by sex | Australia | 40,991 |
| birthplace summary by sex | Elsewhere | 38,264 |
| language summary by sex | English only | 45,458 |
| language summary by sex | Other language | 33,419 |
| school completion by sex | Year 12 or equivalent | 53,606 |

## Why This Helps Persona Generation

This gives the hackathon a small, locally meaningful frame:

1. Use the six core Willoughby SA2s as the local sampling geography.
2. Use G01 as the first descriptive layer.
3. Add adult-only and persona-critical topics next:
   - G04 age x sex
   - G08 ancestry
   - G09 country of birth
   - G13 language at home
   - G17 income
   - G46 labour force
   - G60 occupation
4. Generate structured local seed rows.
5. Expand those rows into persona prose with NVIDIA Data Designer or an
   equivalent controlled prompt pipeline.
6. Attach the source-backed
   [Willoughby political memory layer](willoughby-political-memory-layer.md) so
   policy briefs can connect synthetic persona cohorts to real election,
   meeting, notice-of-motion, and planning-determination records.

## Current Limitation

G01 is not enough for final personas. It includes children and broad summary
fields. The next sampler-ready milestone is an adult-only Willoughby feature
mart using G04 for age/sex and G17/G46/G60 for economic attributes.
