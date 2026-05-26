"""Data Designer config for expanding structured Australian persona seeds.

This config expects a seed dataset produced by the Census/PGM sampler. The seed
rows contain fixed demographic and geographic attributes; Data Designer only
adds natural-language persona fields.
"""

from __future__ import annotations

import os
from pathlib import Path

import data_designer.config as dd

from aus_personas.persona_fields import GENERATED_NARRATIVE_FIELDS


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_PATH = REPO_ROOT / "examples" / "seeds" / "rockbank_pgm_seed_sample.csv"


STRING_NARRATIVE_FIELDS = [
    field for field in GENERATED_NARRATIVE_FIELDS if not field.endswith("_list")
]
LIST_NARRATIVE_FIELDS = [
    field for field in GENERATED_NARRATIVE_FIELDS if field.endswith("_list")
]


PERSONA_BUNDLE_SCHEMA = {
    "type": "object",
    "properties": {
        **{field: {"type": "string"} for field in STRING_NARRATIVE_FIELDS},
        **{
            field: {
                "type": "array",
                "items": {"type": "string"},
            }
            for field in LIST_NARRATIVE_FIELDS
        },
    },
    "required": GENERATED_NARRATIVE_FIELDS,
    "additionalProperties": False,
}


SYSTEM_PROMPT = """You write grounded synthetic Australian persona records.
Respect every structured seed attribute exactly. Do not invent demographic
facts that contradict the seed. Use Australian English and local context. Do
not mention Census, source statistics, sampling, synthetic data, or this prompt.
Avoid stereotypes, slurs, deterministic claims, and named real private people.
"""


PERSONA_PROMPT = """Create concise Australian persona narrative fields from the
fixed demographic scaffold. Do not change the scaffold. Do not mention exact
Census counts. Do not claim hobbies, skills, personality, or ambitions are
Census-derived. Avoid inferring protected or sensitive attributes not present in
the scaffold.

Seed:
- profile_id: {{ profile_id }}
- SA2: {{ sa2_name }} ({{ sa2_code }})
- state: {{ state_name }}
- census_year: {{ census_year }}
- age_band: {{ age_band }}
- sex: {{ sex }}
- labour_force_status: {{ labour_force_status }}
- income_band: {{ income_band }}
- country_of_birth: {{ country_of_birth }}
- language_used_at_home: {{ language_used_at_home }}
- english_proficiency: {{ english_proficiency }}
- household_relationship: {{ household_relationship }}

Write concise but specific fields. Keep the overall persona realistic for the
seed and location. The list fields must be arrays of short strings. The output
must contain only narrative fields from the requested schema.
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
