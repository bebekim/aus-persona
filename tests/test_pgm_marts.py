from pathlib import Path

import yaml


DBT_ROOT = Path("dbt/aus_personas")
PGM_MODEL_DIR = DBT_ROOT / "models/marts/pgm"


def test_first_pgm_mart_files_are_declared():
    required_models = {
        "mart_pgm__sa2_age_sex",
        "mart_pgm__sa2_labour_force_status",
        "mart_pgm__sa2_personal_income",
    }

    for model_name in required_models:
        assert (PGM_MODEL_DIR / f"{model_name}.sql").exists()

    schema = yaml.safe_load((PGM_MODEL_DIR / "schema.yml").read_text())
    declared_models = {model["name"] for model in schema["models"]}

    assert required_models <= declared_models
