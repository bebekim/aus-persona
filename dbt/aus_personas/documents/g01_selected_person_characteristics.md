{% docs g01_selected_person_characteristics %}

# G01 Selected Person Characteristics By Sex

`sa2_g01` is a wide ABS summary table. One raw row represents one SA2, and
each `g*` column is a count cell for a selected person characteristic.

The `int_g01__column_profile` model profiles each raw column across all SA2s.
The semantic long models split G01 into readable sections such as total
persons by sex, age group by sex, birthplace summary, language summary, and
school completion.

G01 is primarily a summary and QA source. More detailed tables should be used
for sampler features when available.

{% enddocs %}
