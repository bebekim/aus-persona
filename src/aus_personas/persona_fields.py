"""Persona field provenance contract for final generated rows."""

from __future__ import annotations

from dataclasses import dataclass


PROVENANCE_GENERATED_IDENTIFIER = "generated_identifier"
PROVENANCE_SAMPLED_FROM_ABS = "sampled_from_abs"
PROVENANCE_GENERATED_CONSTRAINED = "generated_constrained"


@dataclass(frozen=True)
class FieldProvenance:
    provenance: str
    source: str


PGM_STRUCTURED_SEED_FIELDS = [
    "profile_id",
    "census_year",
    "sa2_code",
    "sa2_name",
    "state_name",
    "age_band",
    "sex",
    "labour_force_status",
    "income_band",
    "country_of_birth",
    "language_used_at_home",
    "english_proficiency",
    "household_relationship",
]

GENERATED_NARRATIVE_FIELDS = [
    "professional_persona",
    "family_persona",
    "skills_and_expertise",
    "skills_and_expertise_list",
    "hobbies_and_interests",
    "hobbies_and_interests_list",
    "career_goals_and_ambitions",
    "persona",
]

PGM_TRACE_FIELDS = [
    "pgm_trace_json",
    "provenance_json",
]

VALIDATION_FIELDS = [
    "validation_status",
    "validation_errors_json",
]

FINAL_PERSONA_FIELDS = [
    *PGM_STRUCTURED_SEED_FIELDS,
    *GENERATED_NARRATIVE_FIELDS,
    *PGM_TRACE_FIELDS,
    *VALIDATION_FIELDS,
]

FIELD_PROVENANCE = {
    "profile_id": FieldProvenance(
        PROVENANCE_GENERATED_IDENTIFIER,
        "PGM sampler profile identifier",
    ),
    "census_year": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "ABS Census release year",
    ),
    "sa2_code": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "ABS SA2 geography selection",
    ),
    "sa2_name": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "ABS SA2 geography dimension",
    ),
    "state_name": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "ABS SA2 geography dimension",
    ),
    "age_band": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_age_sex",
    ),
    "sex": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_age_sex",
    ),
    "labour_force_status": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_labour_force_status",
    ),
    "income_band": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_personal_income",
    ),
    "country_of_birth": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_country_of_birth",
    ),
    "language_used_at_home": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_language_home_english_proficiency",
    ),
    "english_proficiency": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_language_home_english_proficiency",
    ),
    "household_relationship": FieldProvenance(
        PROVENANCE_SAMPLED_FROM_ABS,
        "mart_pgm__sa2_household_relationship",
    ),
    "professional_persona": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "family_persona": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "skills_and_expertise": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "skills_and_expertise_list": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "hobbies_and_interests": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "hobbies_and_interests_list": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "career_goals_and_ambitions": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "persona": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Data Designer narrative expansion constrained by PGM seed fields",
    ),
    "pgm_trace_json": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "PGM sampler trace metadata",
    ),
    "provenance_json": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "PGM sampler structured-field provenance metadata",
    ),
    "validation_status": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Rule-based post-generation validator output",
    ),
    "validation_errors_json": FieldProvenance(
        PROVENANCE_GENERATED_CONSTRAINED,
        "Rule-based post-generation validator output",
    ),
}
