# Changelog

Repository changes worth human review should be summarized here.

## Unreleased

- Night Shift workflow scaffolding added.
- Added Willoughby City Council local dbt marts for SA2 boundary overlap and
  interpreted G01 profile estimates.
- Added a fail-closed semantic catalog guardrail for persona-worthy SA2 Census
  sections, including `aus-personas census worthy` inspection output.
- Added all core persona seed `sa2_g*` Census topics to the dbt first-pass
  observation pipeline with coverage tests for table presence and row counts.
- Added G17 personal-income semantic long-query support with explicit
  `income_band` output and sampler exclusions for totals and missingness rows.
- Promoted the remaining ABS persona G-table coverage contract for labour
  force, ancestry, country of birth, language/proficiency, household,
  tenure, industry, defence-service, and guarded Indigenous-status context.
- Defined the promotion gate from semantic Census topic to materialized PGM mart,
  including non-promotion criteria and required mart tests.
- Added a smaller first-tranche PGM mart spec scoped to age/sex, personal
  income, and labour-force status.
- Implemented first sampler-facing PGM marts for SA2 age/sex and personal
  income with probability, eligibility, lineage, and Rockbank smoke tests.
