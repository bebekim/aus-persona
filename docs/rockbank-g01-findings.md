# Rockbank G01 Findings

SA2 `213041359` is `Rockbank - Mount Cottrell`, Victoria.

This note captures the first semantic inspection of `census_2021_data.sa2_g01`
for one familiar suburb-sized area. Raw Census tables remain untouched; all
rows below come from the semantic CLI and dbt metadata dictionary.

## One Row Contract

For the G01 semantic long output:

```text
one row = one measured count for one SA2, one G01 section, and one combination
of that section's axes
```

Examples:

```text
SA2 213041359 + age_group_by_sex + age_band=25-34 + sex=Male -> 2,464
SA2 213041359 + school_completion_by_sex + Year 12 + sex=Female -> 3,996
```

The `Persons` rows are aggregate validation rows. They are useful for checking
totals, but they must not be sampled as if they were a third sex category.

## Total Population

G01 reports:

| sex | count |
| --- | ---: |
| Male | 9,604 |
| Female | 7,949 |
| Persons | 17,553 |

This section is validation-only. It confirms the SA2 population base used by
other G01 counts.

## Age By Sex

The broad age groups show a young, growth-area population. The largest groups
are:

| age band | persons |
| --- | ---: |
| 25-34 | 4,639 |
| 35-44 | 3,850 |
| 5-14 | 2,421 |
| 0-4 | 1,891 |
| 45-54 | 1,471 |
| 20-24 | 1,179 |

The older population is comparatively small:

| age band | persons |
| --- | ---: |
| 55-64 | 814 |
| 65-74 | 498 |
| 75-84 | 144 |
| 85+ | 22 |

Sampler status: usable as a first age/sex distribution, but only at broad age
bands. For adult personas, G01 alone cannot cleanly separate ages 18-19 from
the `15-19` band. A narrower age table such as G04 should become the preferred
age source for the sampler.

## Indigenous Summary

G01 exposes a coarse Aboriginal and Torres Strait Islander summary by sex:

| category | male | female | persons |
| --- | ---: | ---: | ---: |
| Aboriginal | 297 | 80 | 379 |
| Torres Strait Islander | 6 | 0 | 8 |
| Both Aboriginal and Torres Strait Islander | 0 | 5 | 3 |
| Total Aboriginal and/or Torres Strait Islander | 305 | 81 | 391 |

Sampler status: potentially usable only as a coarse identity/context feature.
The total rows should be validation-only. Counts are ABS perturbed, so small
category sums may not exactly equal totals.

## Birthplace Summary

G01 has only a coarse birthplace summary:

| birthplace summary | male | female | persons |
| --- | ---: | ---: | ---: |
| Australia | 4,942 | 3,762 | 8,707 |
| Elsewhere | 4,262 | 3,817 | 8,077 |

Sampler status: validation/context only. For persona generation we need a more
detailed country-of-birth topic, likely G09.

## Language Summary

G01 has only a coarse language-at-home summary:

| language summary | male | female | persons |
| --- | ---: | ---: | ---: |
| English only | 2,796 | 2,600 | 5,396 |
| Other language | 4,460 | 4,560 | 9,016 |

Sampler status: validation/context only. For persona generation we need a more
detailed language topic, likely G13.

## School Completion

G01 gives highest year of school completed by sex:

| school completion | male | female | persons |
| --- | ---: | ---: | ---: |
| Year 12 or equivalent | 3,958 | 3,996 | 7,951 |
| Year 11 or equivalent | 338 | 316 | 660 |
| Year 10 or equivalent | 1,929 | 598 | 2,522 |
| Year 9 or equivalent | 194 | 180 | 373 |
| Year 8 or below | 150 | 167 | 316 |
| Did not go to school | 53 | 91 | 140 |

Sampler status: usable as a coarse education-attainment feature, but it is not
the same thing as highest non-school qualification. Use G49/G50 later for richer
education fields.

## Modelling Decisions

- Use G01 `age_group_by_sex` only as an early sampler source.
- Prefer G04 for sharper age/sex sampling because personas must be adult-only.
- Keep G01 totals, birthplace summary, and language summary as validation or
context, not primary sampler dimensions.
- Promote detailed country-of-birth, language, income, education, occupation,
household, and dwelling topics separately.
- Exclude `sex=Persons` and explicit total rows from sampling.

## Follow-Up

- Add G17 personal income as the next semantic topic.
- Build the first PGM input from `SA2 -> age/sex` and `SA2 + age/sex -> income`.
- Add detailed country-of-birth and language topics before generating cultural
persona fields.
