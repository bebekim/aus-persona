# Promoted Persona Topics

These semantic topics extend the `G17` reference pattern for the static ABS
Census 2021 build.

One row in a promoted semantic long query represents one measured count for one
SA2, one semantic section, and one combination of the declared section axes.

## Sampler-Core Topics

- `G46.labour_force_status`: `sa2 x labour_force_status x age_band x sex`.
- `G09.country_of_birth`: `sa2 x country_of_birth x age_band x sex`.
- `G13.language_home_english_proficiency`:
  `sa2 x language_used_at_home x english_proficiency x sex`.
- `G08.ancestry`: `sa2 x ancestry x parent_birthplace_context`.
- `G27.household_relationship`:
  `sa2 x household_relationship x age_band x sex`.

These topics may be sampled after totals, `Persons` aggregates, and missingness
categories are excluded.

## Conditioning Context Topics

- `G37.tenure_landlord`: dwelling-grain tenure context.
- `G54.industry`: employed-person industry context.
- `G35.household_composition`: household-grain composition and resident-count
  context.
- `G22.defence_service_status`: optional Australian Defence Force service
  context.

These topics condition or validate personas. They are not direct individual
facts unless an allocation rule explicitly bridges the table grain.

## Guarded Or Deferred Topics

- `G07.indigenous_status` is decoded but guarded. It can validate or condition
  a reviewed use case, but generated narrative must not infer cultural claims
  from it by default.
- `G18` support/accessibility context is deferred until a reviewed use case
  promotes it.
- `G40` rent-band context is deferred until rented-household modelling is
  explicitly promoted.
