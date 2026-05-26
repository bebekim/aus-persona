"""Validation helpers for synthetic-person samples."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from aus_personas.persona_fields import (
    FINAL_PERSONA_FIELDS,
    GENERATED_NARRATIVE_FIELDS,
    PGM_STRUCTURED_SEED_FIELDS,
    PGM_TRACE_FIELDS,
)


LIST_NARRATIVE_FIELDS = {
    "skills_and_expertise_list",
    "hobbies_and_interests_list",
}
STRUCTURED_FIELDS_TO_PRESERVE = [
    *PGM_STRUCTURED_SEED_FIELDS,
    *PGM_TRACE_FIELDS,
]


@dataclass(frozen=True)
class ValidationError:
    code: str
    field: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
        }


def build_final_persona_row(
    seed_row: dict[str, Any],
    generated_row: dict[str, Any],
    *,
    allow_income_band_wording: bool = False,
) -> dict[str, Any]:
    """Combine a fixed PGM seed row with Data Designer narrative output."""
    bundle = extract_persona_bundle(generated_row)
    final_row: dict[str, Any] = {}

    for field in PGM_STRUCTURED_SEED_FIELDS:
        final_row[field] = seed_row.get(field, "")

    for field in GENERATED_NARRATIVE_FIELDS:
        final_row[field] = normalise_generated_value(field, bundle.get(field, ""))

    for field in PGM_TRACE_FIELDS:
        final_row[field] = seed_row.get(field, "")

    errors = validate_final_persona_row(
        seed_row,
        generated_row,
        final_row,
        allow_income_band_wording=allow_income_band_wording,
    )
    final_row["validation_status"] = "passed" if not errors else "failed"
    final_row["validation_errors_json"] = json.dumps(
        [error.as_dict() for error in errors],
        sort_keys=True,
        separators=(",", ":"),
    )

    return {field: final_row[field] for field in FINAL_PERSONA_FIELDS}


def extract_persona_bundle(generated_row: dict[str, Any]) -> dict[str, Any]:
    bundle = generated_row.get("persona_bundle", generated_row)
    if isinstance(bundle, str):
        bundle = json.loads(bundle)
    if not isinstance(bundle, dict):
        raise TypeError("persona_bundle must be an object or JSON object string")
    return bundle


def normalise_generated_value(field: str, value: Any) -> Any:
    if field not in LIST_NARRATIVE_FIELDS:
        return "" if value is None else str(value)
    if value is None:
        return []
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value.strip() else []
        return decoded if isinstance(decoded, list) else [value]
    if isinstance(value, list):
        return value
    return [str(value)]


def validate_final_persona_row(
    seed_row: dict[str, Any],
    generated_row: dict[str, Any],
    final_row: dict[str, Any],
    *,
    allow_income_band_wording: bool = False,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    errors.extend(validate_preserved_fields(seed_row, generated_row))
    errors.extend(validate_generated_fields_present(final_row))
    narrative_text = combined_narrative_text(final_row)
    errors.extend(validate_age_band(seed_row, narrative_text))
    errors.extend(validate_labour_force(seed_row, narrative_text))
    errors.extend(
        validate_income_band(
            seed_row,
            narrative_text,
            allow_income_band_wording=allow_income_band_wording,
        )
    )
    errors.extend(validate_provenance_leakage(narrative_text))
    errors.extend(validate_country_of_birth(seed_row, narrative_text))
    errors.extend(validate_language_home(seed_row, narrative_text))
    errors.extend(validate_household_relationship(seed_row, narrative_text))
    return errors


def validate_preserved_fields(
    seed_row: dict[str, Any],
    generated_row: dict[str, Any],
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for field in STRUCTURED_FIELDS_TO_PRESERVE:
        if field not in seed_row or seed_row[field] in (None, ""):
            errors.append(
                ValidationError(
                    "missing_preserved_field",
                    field,
                    f"Seed row is missing required preserved field {field}.",
                )
            )
        if field in generated_row and str(generated_row[field]) != str(seed_row[field]):
            errors.append(
                ValidationError(
                    "structured_field_changed",
                    field,
                    f"Generated row attempted to change fixed field {field}.",
                )
            )
    return errors


def validate_generated_fields_present(
    final_row: dict[str, Any],
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for field in GENERATED_NARRATIVE_FIELDS:
        value = final_row[field]
        if isinstance(value, list):
            empty = not value or any(str(item).strip() == "" for item in value)
        else:
            empty = str(value).strip() == ""
        if empty:
            errors.append(
                ValidationError(
                    "missing_generated_field",
                    field,
                    f"Generated field {field} must be non-empty.",
                )
            )
    return errors


def validate_age_band(
    seed_row: dict[str, Any],
    narrative_text: str,
) -> list[ValidationError]:
    age_range = parse_age_band(str(seed_row.get("age_band", "")))
    if age_range is None:
        return []

    minimum, maximum = age_range
    for age in mentioned_ages(narrative_text):
        if age < minimum or (maximum is not None and age > maximum):
            return [
                ValidationError(
                    "age_band_contradiction",
                    "age_band",
                    "Generated text mentions an age outside the fixed age band.",
                )
            ]
    return []


def validate_labour_force(
    seed_row: dict[str, Any],
    narrative_text: str,
) -> list[ValidationError]:
    status = str(seed_row.get("labour_force_status", "")).lower()
    if "employed" in status and "unemployed" not in status:
        return []

    current_work_patterns = (
        r"\bworks full[- ]time\b",
        r"\bfull[- ]time job\b",
        r"\bcurrently works\b",
        r"\bemployed as\b",
        r"\bworks as\b",
    )
    if any(re.search(pattern, narrative_text) for pattern in current_work_patterns):
        return [
            ValidationError(
                "labour_force_contradiction",
                "labour_force_status",
                "Generated text describes current employment contrary to status.",
            )
        ]
    return []


def validate_income_band(
    seed_row: dict[str, Any],
    narrative_text: str,
    *,
    allow_income_band_wording: bool,
) -> list[ValidationError]:
    if allow_income_band_wording:
        return []

    income_band = str(seed_row.get("income_band", "")).strip()
    if not income_band:
        return []

    if normalise_for_matching(income_band) in normalise_for_matching(narrative_text):
        return [
            ValidationError(
                "income_band_exposed",
                "income_band",
                "Generated text exposes the exact income band as prose.",
            )
        ]
    return []


def validate_provenance_leakage(narrative_text: str) -> list[ValidationError]:
    if re.search(r"\b(abs|census)\b", narrative_text):
        return [
            ValidationError(
                "provenance_leakage",
                "provenance_json",
                "Generated text claims Census or ABS provenance for narrative fields.",
            )
        ]
    return []


def validate_country_of_birth(
    seed_row: dict[str, Any],
    narrative_text: str,
) -> list[ValidationError]:
    country = str(seed_row.get("country_of_birth", "")).lower()
    if country != "australia":
        return []

    patterns = (
        r"\brecent migrant\b",
        r"\brecently migrated to australia\b",
        r"\bnewly arrived in australia\b",
    )
    if any(re.search(pattern, narrative_text) for pattern in patterns):
        return [
            ValidationError(
                "country_of_birth_contradiction",
                "country_of_birth",
                "Generated text describes migration unsupported by country of birth.",
            )
        ]
    return []


def validate_language_home(
    seed_row: dict[str, Any],
    narrative_text: str,
) -> list[ValidationError]:
    language = str(seed_row.get("language_used_at_home", "")).lower()
    if language != "english":
        return []

    if re.search(r"\bspeaks (?!english\b)[a-z]+ at home\b", narrative_text):
        return [
            ValidationError(
                "language_home_contradiction",
                "language_used_at_home",
                "Generated text contradicts the fixed language used at home.",
            )
        ]
    return []


def validate_household_relationship(
    seed_row: dict[str, Any],
    narrative_text: str,
) -> list[ValidationError]:
    relationship = str(seed_row.get("household_relationship", "")).lower()
    if "lone person" not in relationship and "lives alone" not in relationship:
        return []

    patterns = (
        r"\blives with\b",
        r"\bwith (a )?(partner|spouse|children|kids)\b",
    )
    if any(re.search(pattern, narrative_text) for pattern in patterns):
        return [
            ValidationError(
                "household_relationship_contradiction",
                "household_relationship",
                "Generated text contradicts the fixed household relationship.",
            )
        ]
    return []


def combined_narrative_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in GENERATED_NARRATIVE_FIELDS:
        value = row[field]
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        else:
            parts.append(str(value))
    return " ".join(parts).lower()


def parse_age_band(age_band: str) -> tuple[int, int | None] | None:
    numbers = [int(value) for value in re.findall(r"\d+", age_band)]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    if len(numbers) == 1 and "over" in age_band.lower():
        return numbers[0], None
    return None


def mentioned_ages(text: str) -> list[int]:
    patterns = (
        r"\b(\d{1,3})\s*years?\s*old\b",
        r"\b(\d{1,3})\s*year[- ]old\b",
        r"\baged\s*(\d{1,3})\b",
    )
    ages: list[int] = []
    for pattern in patterns:
        ages.extend(int(value) for value in re.findall(pattern, text))
    return ages


def normalise_for_matching(value: str) -> str:
    lowered = value.lower().replace("$", " ")
    without_punctuation = re.sub(r"[,/–—-]", " ", lowered)
    return re.sub(r"\s+", " ", without_punctuation).strip()
