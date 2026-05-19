# Specs

Specs are the source of truth for Night Shift work.

- [Spec 01: dbt Census Source Ingestion](01-dbt-census-source-ingestion.md)
- [Spec 02: Census Semantic Topic Layer](02-census-semantic-topic-layer.md)
- [Spec 03: Persona-Worthy SA2 Topic Selection](03-persona-worthy-sa2-topic-selection.md)
- [Spec 04: First PGM Feature Marts](02-pgm-feature-marts.md)
- [Spec 05: Conditional Weighted PGM Sampler](03-conditional-weighted-pgm-sampler.md)
- [Spec 06: Narrative Persona Field Provenance](06-narrative-persona-field-provenance.md)

`02-pgm-feature-marts.md` predates the semantic-layer split and should be
treated as downstream until Spec 02 and Spec 03 are implemented and the first
semantic topics are inspected.

- `draft-*` files are ignored.
- Any other Markdown spec is ready for agent work.
- Keep specs bounded enough for one reviewable commit.
- Prefer one to three ready specs per night.

Use the root template at `../.night-shift/templates/spec-template.md` when drafting a new spec from this repository root, or copy the structure manually if this repository is used outside the parent workspace.
