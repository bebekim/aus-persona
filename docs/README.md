# Project Docs

Use this directory for repository-specific context that should improve future agent runs.

## Current Domain Docs

- [ABS Census Table Dictionary](abs-census-dictionary.md): explains the
  censusloader schemas, SA2 joins, ABS profile families, raw column decoding,
  and the first persona/PGM feature tables.
- [ABS Source Provenance](abs-source-provenance.md): records the ABS primary
  documentation, local Mesh Block workbook structure, source priority, and how
  each source constrains the feature mart and sampler.
- [Persona-Worthy SA2 Census Topics](persona-worthy-sa2-topics.md): defines
  which `sa2_g*` topics and columns should become sampler inputs, context, QA,
  or v1 exclusions for Korea-style persona rows.

Recommended sections:

- Architecture: system structure, module ownership, external services
- Testing: exact commands, required environment, slow or flaky tests
- Domain: product concepts and business rules
- Style Guide: local code conventions that are not obvious from tooling
- Common Pitfalls: mistakes agents or humans have made before

Keep durable context here instead of repeating it in every spec.
