import csv
import importlib.util
import json
from pathlib import Path

from aus_personas.persona_fields import (
    FIELD_PROVENANCE,
    FINAL_PERSONA_FIELDS,
    GENERATED_NARRATIVE_FIELDS,
    PROVENANCE_GENERATED_CONSTRAINED,
    PROVENANCE_SAMPLED_FROM_ABS,
)
from aus_personas.sampler.validation import build_final_persona_row


REPO_ROOT = Path(__file__).resolve().parents[1]


def seed_row() -> dict[str, str]:
    provenance = {
        "sa2_code": "sampled_from_abs",
        "age_band": "sampled_from_abs",
        "sex": "sampled_from_abs",
        "labour_force_status": "sampled_from_abs",
        "income_band": "sampled_from_abs",
        "country_of_birth": "sampled_from_abs",
        "language_used_at_home": "sampled_from_abs",
        "english_proficiency": "sampled_from_abs",
        "household_relationship": "sampled_from_abs",
    }
    return {
        "profile_id": "pgm_00000001",
        "census_year": "2021",
        "sa2_code": "213041359",
        "sa2_name": "Rockbank - Mount Cottrell",
        "state_name": "Victoria",
        "age_band": "25-29",
        "sex": "Female",
        "labour_force_status": "Employed full-time",
        "income_band": "1000 1249",
        "country_of_birth": "Australia",
        "language_used_at_home": "English",
        "english_proficiency": "Speaks English only",
        "household_relationship": "Husband, wife or partner",
        "pgm_trace_json": json.dumps({"age_sex": {"source_mart": "mart"}}),
        "provenance_json": json.dumps(provenance),
    }


def persona_bundle() -> dict[str, object]:
    return {
        "professional_persona": "Works full-time in a practical operations role.",
        "family_persona": "Lives with a partner and keeps close local ties.",
        "skills_and_expertise": "Planning, communication, and steady delivery.",
        "skills_and_expertise_list": ["Planning", "Communication"],
        "hobbies_and_interests": "Enjoys local cafes and community sport.",
        "hobbies_and_interests_list": ["Cafes", "Community sport"],
        "career_goals_and_ambitions": "Wants stable progression in her field.",
        "persona": "A grounded Rockbank resident with a busy working week.",
    }


def error_codes(row: dict[str, object]) -> set[str]:
    return {error["code"] for error in json.loads(str(row["validation_errors_json"]))}


def test_field_provenance_contract_classifies_every_final_output_column():
    assert set(FINAL_PERSONA_FIELDS) == set(FIELD_PROVENANCE)

    for field in GENERATED_NARRATIVE_FIELDS:
        assert FIELD_PROVENANCE[field].provenance == PROVENANCE_GENERATED_CONSTRAINED

    sampled_fields = [
        field
        for field, metadata in FIELD_PROVENANCE.items()
        if metadata.provenance == PROVENANCE_SAMPLED_FROM_ABS
    ]
    assert "professional_persona" not in sampled_fields
    assert "hobbies_and_interests" not in sampled_fields

    for field, metadata in FIELD_PROVENANCE.items():
        assert metadata.provenance
        assert metadata.source


def test_data_designer_config_consumes_pgm_seed_rows_without_structured_outputs():
    spec = importlib.util.spec_from_file_location(
        "persona_text_config",
        REPO_ROOT / "configs" / "data_designer" / "persona_text_config.py",
    )
    assert spec
    assert spec.loader
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)

    assert config.DEFAULT_SEED_PATH.name == "rockbank_pgm_seed_sample.csv"
    assert "{{ profile_id }}" in config.PERSONA_PROMPT
    assert "{{ age_band }}" in config.PERSONA_PROMPT
    assert "{{ language_used_at_home }}" in config.PERSONA_PROMPT
    assert "{{ uuid }}" not in config.PERSONA_PROMPT
    assert "{{ occupation }}" not in config.PERSONA_PROMPT
    assert "Do not change the scaffold" in config.PERSONA_PROMPT

    output_fields = set(config.PERSONA_BUNDLE_SCHEMA["properties"])
    assert output_fields == set(GENERATED_NARRATIVE_FIELDS)
    assert "age_band" not in output_fields
    assert "income_band" not in output_fields

    with config.DEFAULT_SEED_PATH.open(newline="") as handle:
        first_row = next(csv.DictReader(handle))
    for field in (
        "profile_id",
        "age_band",
        "income_band",
        "pgm_trace_json",
        "provenance_json",
    ):
        assert first_row[field]


def test_build_final_persona_row_preserves_seed_fields_and_validates_success():
    row = build_final_persona_row(seed_row(), {"persona_bundle": persona_bundle()})

    assert list(row) == FINAL_PERSONA_FIELDS
    assert row["profile_id"] == "pgm_00000001"
    assert row["age_band"] == "25-29"
    assert row["pgm_trace_json"] == seed_row()["pgm_trace_json"]
    assert row["provenance_json"] == seed_row()["provenance_json"]
    assert row["professional_persona"] == persona_bundle()["professional_persona"]
    assert row["validation_status"] == "passed"
    assert json.loads(str(row["validation_errors_json"])) == []


def test_build_final_persona_row_flags_generation_contract_violations():
    generated = persona_bundle()
    generated.update(
        {
            "professional_persona": (
                "At 42 years old she works full-time in a role backed by ABS "
                "Census hobby data and earns 1000 1249 per week."
            ),
            "family_persona": "She recently migrated to Australia and lives with children.",
            "persona": "She speaks Punjabi at home while settling into Rockbank.",
            "hobbies_and_interests_list": [],
        }
    )
    seed = seed_row()
    seed["labour_force_status"] = "Not in the labour force"
    seed["household_relationship"] = "Lone person"
    seed["language_used_at_home"] = "English"

    row = build_final_persona_row(
        seed,
        {
            "persona_bundle": generated,
            "age_band": "40-44",
        },
    )

    assert row["validation_status"] == "failed"
    assert {
        "age_band_contradiction",
        "labour_force_contradiction",
        "income_band_exposed",
        "provenance_leakage",
        "country_of_birth_contradiction",
        "language_home_contradiction",
        "household_relationship_contradiction",
        "missing_generated_field",
        "structured_field_changed",
    } <= error_codes(row)
