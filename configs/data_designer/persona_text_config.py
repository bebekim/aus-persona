"""Data Designer config for expanding structured Australian persona seeds.

This config expects a seed dataset produced by the Census/PGM sampler. The seed
rows contain fixed demographic and geographic attributes; Data Designer only
adds natural-language persona fields.
"""

from __future__ import annotations

import os
from pathlib import Path

import data_designer.config as dd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_PATH = REPO_ROOT / "examples" / "seeds" / "rockbank_seed_sample.csv"


PERSONA_BUNDLE_SCHEMA = {
    "type": "object",
    "properties": {
        "professional_persona": {"type": "string"},
        "sports_persona": {"type": "string"},
        "arts_persona": {"type": "string"},
        "travel_persona": {"type": "string"},
        "culinary_persona": {"type": "string"},
        "family_persona": {"type": "string"},
        "persona": {"type": "string"},
        "cultural_background": {"type": "string"},
        "skills_and_expertise": {"type": "string"},
        "skills_and_expertise_list": {
            "type": "array",
            "items": {"type": "string"},
        },
        "hobbies_and_interests": {"type": "string"},
        "hobbies_and_interests_list": {
            "type": "array",
            "items": {"type": "string"},
        },
        "career_goals_and_ambitions": {"type": "string"},
    },
    "required": [
        "professional_persona",
        "sports_persona",
        "arts_persona",
        "travel_persona",
        "culinary_persona",
        "family_persona",
        "persona",
        "cultural_background",
        "skills_and_expertise",
        "skills_and_expertise_list",
        "hobbies_and_interests",
        "hobbies_and_interests_list",
        "career_goals_and_ambitions",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """You write grounded synthetic Australian persona records.
Respect every structured seed attribute exactly. Do not invent demographic
facts that contradict the seed. Use Australian English and local context. Do
not mention Census, source statistics, sampling, synthetic data, or this prompt.
Avoid stereotypes, slurs, deterministic claims, and named real private people.
"""


PERSONA_PROMPT = """Expand this fixed structured seed into Korea-style persona
text fields.

Seed:
- uuid: {{ uuid }}
- SA2: {{ sa2_name }} ({{ sa2_code }})
- state: {{ state }}
- country: {{ country }}
- age: {{ age }}
- sex: {{ sex }}
- marital_status: {{ marital_status }}
- family_type: {{ family_type }}
- housing_type: {{ housing_type }}
- education_level: {{ education_level }}
- field_of_study: {{ field_of_study }}
- labour_force_status: {{ labour_force_status }}
- occupation: {{ occupation }}
- income_band: {{ income_band }}
- language_home: {{ language_home }}
- country_of_birth: {{ country_of_birth }}
- ancestry_1: {{ ancestry_1 }}
- ancestry_2: {{ ancestry_2 }}
- indigenous_status: {{ indigenous_status }}

Write concise but specific fields. Keep the overall persona realistic for the
seed and location. The list fields must be arrays of short strings.
"""


def load_config_builder() -> dd.DataDesignerConfigBuilder:
    seed_path = Path(os.environ.get("AUS_PERSONAS_SEED_PATH", DEFAULT_SEED_PATH))
    model_alias = os.environ.get("AUS_PERSONAS_TEXT_MODEL_ALIAS", "openai-text")

    config_builder = dd.DataDesignerConfigBuilder()
    config_builder.with_seed_dataset(
        dd.LocalFileSeedSource(path=str(seed_path)),
        sampling_strategy=dd.SamplingStrategy.ORDERED,
    )
    config_builder.add_column(
        dd.LLMStructuredColumnConfig(
            name="persona_bundle",
            model_alias=model_alias,
            system_prompt=SYSTEM_PROMPT,
            prompt=PERSONA_PROMPT,
            output_format=PERSONA_BUNDLE_SCHEMA,
        )
    )
    return config_builder
