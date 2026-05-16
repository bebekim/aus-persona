{% docs modelling_overview %}

# Aus Personas dbt Modelling Overview

Raw ABS Census tables remain source-shaped in Postgres for reproducibility.
dbt starts by declaring those sources, then builds readable layers:

1. staging models lightly standardise metadata and geography;
2. generic ABS intermediate models unpivot wide profile tables and decode columns;
3. topic-specific intermediate models make each Census table understandable;
4. marts provide core facts, QA views, and sampler-facing probability tables.

The central modelling rule is: every model must have a clear answer to
"one row represents what?"

{% enddocs %}
