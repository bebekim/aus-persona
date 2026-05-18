{% docs g17_personal_income %}

# G17 Personal Weekly Income By Age And Sex

G17 is the first detailed feature table planned for the sampler path.
The intended modelling pattern is:

1. keep `sa2_g17a`, `sa2_g17b`, and `sa2_g17c` raw and wide;
2. create a long semantic income model with one row per SA2, income band, age
   band, and sex count;
3. create a PGM mart with one row per SA2, age band, sex, and income-band
   probability.

The semantic long query exposes `income_band`, `age_band`, and `sex` explicitly.
Totals, `Persons` sex aggregates, `Not stated`, and `Not applicable` values are
available for inspection but excluded from sampler eligibility.

{% enddocs %}
