# Spec 07: ABS G-Table Coverage Promotion

Priority: high
Status: ready

## Problem

The persona pipeline has a clear target set of ABS `G*` Census topics for
Australian persona seeds, but their implementation coverage is uneven.

`G17` personal income is the best current example: it is present in source
configuration, decoded into readable axes, represented in the semantic catalog,
tested, documented, and queryable for sampler-facing work.

Most other useful topics are only partially covered. Some are loaded as dbt
sources but are missing semantic-catalog entries. Some are mentioned in docs and
provenance specs but are not wired into source configuration. Some have aliases
but do not yet decode the specific persona fields the generator needs.

Because the ABS Census dataset is mostly static between five-year Census
releases, this should not become a recurring warehouse-pipeline problem. The
right target is a reproducible one-time Census 2021 semantic build that can be
rebuilt when logic changes, when a new Census release arrives, or when a new
external enrichment source is intentionally added.

## Desired Behavior

The project should promote the remaining selected ABS `G*` tables to a
consistent, versioned coverage contract.

For each promoted table, coverage means:

- the raw `sa2_g*` physical tables are declared in dbt source configuration;
- the project source config and dbt source config agree;
- metadata headings decode into readable category axes;
- `configs/abs_semantic_tables.yml` defines the semantic topic grain,
  guardrails, sampler tier, persona fields, conditioning fields, and total
  policy;
- semantic CLI queries can inspect the topic by readable fields;
- provenance docs classify the resulting persona fields correctly;
- tests prove totals, aggregates, and unsupported categories do not silently
  become sampler values.

The target posture is:

```text
raw ABS Census 2021 tables
  -> dbt decoded foundations
  -> semantic topic catalog
  -> sampler/provenance-ready static artifacts
```

This is a compiler-style build. The compiled Census 2021 semantic dataset is the
product; Dagster/dbt selectors are development and rebuild conveniences, not a
high-frequency operational feed.

## Non-Goals

- Do not build final persona prose.
- Do not build the full conditional weighted sampler.
- Do not add non-ABS sources in this spec.
- Do not create recurring scheduled jobs for ABS Census tables.
- Do not claim sensitive or narrative fields are statistically representative.
- Do not promote every available ABS `G*` table.
- Do not rewrite raw `census_2021_data` tables.
- Do not touch unrelated local political-memory work.

## Likely Files

- `configs/abs_census_sources.yml`
- `configs/abs_semantic_tables.yml`
- `docs/persona-worthy-sa2-topics.md`
- `Specs/06-narrative-persona-field-provenance.md`
- `src/aus_personas/abs_metadata.py`
- `src/aus_personas/census/semantic_catalog.py`
- `src/aus_personas/census/semantic_queries.py`
- `dbt/aus_personas/dbt_project.yml`
- `dbt/aus_personas/models/sources/abs_sources.yml`
- `dbt/aus_personas/macros/abs/parse_abs_axis_helpers.sql`
- `dbt/aus_personas/models/intermediate/abs/int_abs__column_dictionary.sql`
- `dbt/aus_personas/models/intermediate/abs/schema.yml`
- `dbt/aus_personas/tests/assert_core_seed_observation_tables_present.sql`
- `dbt/aus_personas/tests/assert_core_seed_observation_row_counts.sql`
- `tests/test_abs_metadata.py`
- `tests/test_semantic_catalog.py`

## Current Coverage Baseline

Use this table as the starting backlog. Do not mark a row complete until it has
the full coverage contract described above.

| Table | Current status | Required promotion |
| --- | --- | --- |
| `G17` income | Best covered: source, semantic config, parser/tests, sampler-facing docs. | Treat as the reference implementation for other topics. |
| `G46` labour force | Source plus dbt category axis/docs; not yet semantic-catalog promoted like `G17`. | Add semantic catalog section and tests for `labour_force_status`. |
| `G07` Indigenous status | Source plus dbt category axis/docs/spec; needs privacy/small-count rules before persona use. | Add guarded semantic entry, provenance constraints, and deny-by-default prose-use rule. |
| `G09` country of birth | Source plus Python parser/tests/docs/spec. | Add or verify semantic catalog entry and sampler guardrails for `country_of_birth`. |
| `G13` language/proficiency | Source plus dbt axis/docs/spec; `language_used_at_home` and `english_proficiency` need cleaner split. | Decode both axes explicitly and test the split. |
| `G27` household relationship | Source plus dbt axis/docs/spec. | Add semantic catalog entry and household/person grain caveat. |
| `G37` tenure/landlord | Source plus dbt axis/docs/spec. | Add semantic catalog entry as context, not direct person fact. |
| `G54` industry | dbt source plus alias/cleaning exists, docs/spec mention it; missing from `configs/abs_census_sources.yml` and semantic catalog. | Reconcile configs, then add semantic catalog entry as conditioning context. |
| `G08` ancestry | dbt source/docs/spec mention it; category-axis decoding appears incomplete. | Add explicit ancestry axis decoding and semantic catalog entry. |
| `G22` defence service | dbt source plus alias exists, spec mentions it; no full field extraction/provenance handling. | Reconcile configs, decode `defence_service_status`, and mark as optional/context. |
| `G35` household size/composition | dbt source plus docs mention it; Spec 06 does not explicitly classify it. | Add semantic catalog entry and update provenance field map for household size/composition context. |
| `G40` rent bands | Mentioned in docs/metadata alias but not wired as dbt source/semantic topic. | Add only if needed for Tier 2 housing context; otherwise explicitly defer. |
| `G18` accessibility/support | Mentioned in docs/metadata alias but not wired as dbt source/semantic topic. | Keep deferred unless a reviewed sensitive-use case exists. |

## Promotion Tiers

### Tier 1: Sampler-Core Promotion

Promote these first because they directly support a statistically defensible
structured persona seed:

```text
G46 labour_force_status
G27 household_relationship
G09 country_of_birth
G13 language_used_at_home / english_proficiency
G08 ancestry
```

`G17` is already the reference pattern.

### Tier 2: Conditioning Context Promotion

Promote these after Tier 1 because they improve plausibility but have grain or
interpretation caveats:

```text
G37 tenure_landlord
G54 industry
G35 household_size / household composition
G22 defence_service_status
```

These fields may condition prose or validate seed consistency, but they must not
be treated as direct individual facts when the ABS table grain is household,
dwelling, family, or employed-person specific.

### Tier 3: Sensitive Or Optional Promotion

Handle these only behind explicit use-case gates:

```text
G07 indigenous_status
G18 accessibility/support context
G40 rent bands
```

`G07` may be semantically decoded, but persona generation must not create
unreviewed cultural claims from it. `G18` should remain deferred until the
project has a concrete accessibility/support use case. `G40` is useful for
housing economics but must be tied to rented-household context rather than every
person row.

## Required Implementation Plan

### Task 1: Reconcile Source Configuration

Files:

- Modify `configs/abs_census_sources.yml`
- Modify `dbt/aus_personas/models/sources/abs_sources.yml`
- Modify `dbt/aus_personas/dbt_project.yml`
- Modify `tests/test_semantic_catalog.py` or add a focused config test

Steps:

- [ ] Add missing chosen source tables to `configs/abs_census_sources.yml`.
- [ ] Ensure `dbt/aus_personas/models/sources/abs_sources.yml` matches the same
      chosen physical tables.
- [ ] Ensure `dbt_project.yml` `first_pass_sa2_tables` matches the same chosen
      physical tables.
- [ ] Keep `G18` and `G40` out of the active source set unless this spec is
      explicitly amended to promote them.
- [ ] Add a test that fails if project source config and dbt source config drift
      for active persona `G*` topics.

Expected active set after this task:

```text
G07, G08, G09, G13, G17, G22, G27, G35, G37, G46, G54
```

`G18` and `G40` should be documented as deferred unless promoted by a separate
use-case decision.

### Task 2: Complete Metadata Axis Decoding

Files:

- Modify `src/aus_personas/abs_metadata.py`
- Modify `dbt/aus_personas/macros/abs/parse_abs_axis_helpers.sql`
- Modify `dbt/aus_personas/models/intermediate/abs/int_abs__column_dictionary.sql`
- Modify `tests/test_abs_metadata.py`

Steps:

- [ ] Add explicit persona category axes for `G08`, `G13`, `G22`, `G35`, and
      `G54` where missing or incomplete.
- [ ] Ensure `G13` separates `language_used_at_home` from
      `english_proficiency`.
- [ ] Ensure `G35` exposes household composition and resident-count context
      without pretending it is person-level.
- [ ] Ensure `G22` maps to `defence_service_status`, not Korean-style
      `military_status`.
- [ ] Add parser tests for each newly decoded axis using representative
      metadata rows.

### Task 3: Promote Semantic Catalog Entries

Files:

- Modify `configs/abs_semantic_tables.yml`
- Modify `tests/test_semantic_catalog.py`

Steps:

- [ ] Add semantic catalog sections for Tier 1 tables.
- [ ] Add semantic catalog sections for Tier 2 tables after Tier 1 tests pass.
- [ ] For every section, specify grain, value alias, sampler tier, guardrails,
      persona fields, conditioning fields, promotion status, and total policy.
- [ ] Set household/dwelling/employed-person topics to `allow_context` or
      `allow_validate` where direct person sampling is not defensible.
- [ ] Add tests that each target table has a guardrail decision for `sample`,
      `condition`, `validate`, and `generate`.

Minimum guardrail expectations:

| Topic | sample | condition | validate | generate |
| --- | --- | --- | --- | --- |
| `G46` | allow | allow | allow | deny |
| `G09` | allow | allow | allow | deny |
| `G13` | allow | allow | allow | deny |
| `G08` | allow | allow | allow | deny |
| `G27` | allow | allow | allow | deny |
| `G37` | deny or allow_context | allow_context | allow_validate | deny |
| `G54` | deny or allow_context | allow_context | allow_validate | deny |
| `G35` | deny or allow_context | allow_context | allow_validate | deny |
| `G22` | deny or allow_context | allow_context | allow_validate | deny |
| `G07` | deny by default until privacy gate is implemented | allow_context only with reviewed use case | allow_validate | deny |

### Task 4: Update Provenance And Persona Docs

Files:

- Modify `Specs/06-narrative-persona-field-provenance.md`
- Modify `docs/persona-worthy-sa2-topics.md`
- Modify or create topic-specific docs under `dbt/aus_personas/documents/`

Steps:

- [ ] Add `household_size` and household composition context explicitly to the
      Spec 06 field provenance map.
- [ ] Mark `G18` and `G40` as deferred unless this spec promotes them.
- [ ] State that `G22` is an Australian defence-service context, not a direct
      migration of Korea `military_status`.
- [ ] State that `G54` is an employed-person industry context and must be
      conditioned by labour-force/occupation logic.
- [ ] Add docs for each promoted semantic topic that describe the row grain and
      one-row-represents contract.

### Task 5: Build And Verify Static Census 2021 Artifacts

Files:

- Modify dbt schema tests as needed.
- Modify `CHANGELOG.md`.

Steps:

- [ ] Run dbt parse.
- [ ] Build the shared decoded Census foundations.
- [ ] Build promoted semantic topics.
- [ ] Run source-row reconciliation tests.
- [ ] Run Python parser/catalog tests.
- [ ] Update `CHANGELOG.md` because the sampler-facing Census feature surface
      changes.

Recommended commands:

```sh
UV_CACHE_DIR=.uv-cache uv run dbt parse --project-dir dbt/aus_personas --profiles-dir dbt/aus_personas
UV_CACHE_DIR=.uv-cache uv run dbt build --project-dir dbt/aus_personas --profiles-dir dbt/aus_personas --select int_abs__column_dictionary int_abs__sa2_observations dim_sa2 fct_census_observation
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_abs_metadata.py tests/test_semantic_catalog.py -q
UV_CACHE_DIR=.uv-cache uv run ruff check src tests
```

If full dbt builds are slow, run one promoted table at a time and record the
selector coverage in the final implementation notes.

## Edge Cases

- `Persons` aggregate rows must not be sampled when sex-specific rows exist.
- Explicit totals must remain validation-only.
- `Not stated`, `Not applicable`, and low-information `Other` categories must
  not become preferred persona values.
- Household, family, dwelling, and rent tables are not automatically
  person-level.
- Industry applies to employed-person contexts and must not describe children,
  retired people, or people not in the labour force.
- Defence-service status is not equivalent to Korean military-service status.
- Indigenous status and accessibility/support fields require stricter use-case,
  privacy, and small-count treatment before narrative prose mentions them.
- Sparse SA2 categories may need fallback rules, but fallback must be explicit
  and visible in provenance or sampler diagnostics.

## Test Expectations

- Add tests proving source config and dbt source config agree for active persona
  topics.
- Add parser tests for newly decoded axes.
- Add semantic catalog tests for every promoted table and purpose.
- Add tests proving `G18` and `G40` remain deferred if they are not actively
  promoted.
- Run targeted dbt builds for the decoded foundation and promoted semantic
  topics.
- Run Python tests and ruff checks over changed code.

## Acceptance Criteria

- [ ] `G46`, `G09`, `G13`, `G08`, and `G27` have semantic-catalog coverage
      comparable to `G17`.
- [ ] `G37`, `G54`, `G35`, and `G22` are either promoted as conditioning context
      or explicitly deferred with rationale.
- [ ] `G07` has a guarded semantic/provenance policy and does not feed narrative
      cultural claims by default.
- [ ] `G18` and `G40` are either explicitly promoted by use case or clearly
      documented as deferred.
- [ ] Project source config, dbt source declarations, and dbt project source
      vars agree for active promoted tables.
- [ ] Every promoted table has tests for parser/category decoding and semantic
      guardrail decisions.
- [ ] Documentation states the static Census 2021 build posture: one-time
      reproducible build, rerun only for logic/source/release changes.
- [ ] Relevant dbt and Python checks pass or have documented unrelated blockers.
- [ ] `CHANGELOG.md` is updated for the changed Census feature surface.

## Known Risks

- Treating household or dwelling tables as direct person-level facts will break
  statistical integrity.
- Sensitive fields can make generated personas sound more certain or intrusive
  than the source supports.
- Promoting too many topics at once can hide parser mistakes. Use `G17` as the
  reference pattern and promote in small batches.
- Source configuration drift is already visible between project config, dbt
  project vars, and dbt source declarations. Add tests before broad promotion.
- ABS perturbation and sparse categories mean exact reconciliation may require
  tolerance-aware checks rather than naive equality at every aggregation level.
