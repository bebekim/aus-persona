"""Conditional weighted sampling for ABS-backed PGM seed profiles."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

Row = dict[str, Any]
AGE_SEX_PARTITION_FIELDS = ("sa2_code", "age_band", "sex")
LANGUAGE_PARTITION_FIELDS = ("sa2_code", "sex")


def generate_seed_profiles(
    *,
    age_sex_rows: Iterable[Row],
    labour_rows: Iterable[Row],
    income_rows: Iterable[Row],
    country_of_birth_rows: Iterable[Row],
    language_rows: Iterable[Row],
    household_relationship_rows: Iterable[Row],
    sample_size: int,
    rng: random.Random | None = None,
) -> list[Row]:
    """Generate fixed structured seed profiles from PGM mart rows."""
    if sample_size < 0:
        raise ValueError("sample_size must be non-negative")

    rng = rng or random.Random()
    labour_by_partition = partition_rows(labour_rows)
    income_by_partition = partition_rows(income_rows)
    country_by_partition = partition_rows(country_of_birth_rows)
    language_by_partition = partition_rows(language_rows, LANGUAGE_PARTITION_FIELDS)
    household_by_partition = partition_rows(household_relationship_rows)
    age_choices = [
        row
        for row in age_sex_rows
        if partition_key(row) in labour_by_partition
        and partition_key(row) in income_by_partition
        and partition_key(row) in country_by_partition
        and partition_key(row, LANGUAGE_PARTITION_FIELDS) in language_by_partition
        and partition_key(row) in household_by_partition
    ]

    profiles: list[Row] = []
    for index in range(1, sample_size + 1):
        age_row = weighted_choice(age_choices, rng)
        partition = partition_key(age_row)
        language_partition = partition_key(age_row, LANGUAGE_PARTITION_FIELDS)
        labour_row = weighted_choice(labour_by_partition[partition], rng)
        income_row = weighted_choice(income_by_partition[partition], rng)
        country_row = weighted_choice(country_by_partition[partition], rng)
        language_row = weighted_choice(language_by_partition[language_partition], rng)
        household_row = weighted_choice(household_by_partition[partition], rng)

        profile = {
            "profile_id": f"pgm_{index:08d}",
            "census_year": str(age_row["census_year"]),
            "sa2_code": str(age_row["sa2_code"]),
            "sa2_name": str(age_row["sa2_name"]),
            "state_name": str(age_row["state_name"]),
            "age_band": str(age_row["age_band"]),
            "sex": str(age_row["sex"]),
            "labour_force_status": str(labour_row["labour_force_status"]),
            "income_band": str(income_row["income_band"]),
            "country_of_birth": str(country_row["country_of_birth"]),
            "language_used_at_home": str(language_row["language_used_at_home"]),
            "english_proficiency": str(language_row["english_proficiency"]),
            "household_relationship": str(
                household_row["household_relationship"]
            ),
        }
        profile["pgm_trace_json"] = json.dumps(
            pgm_trace(profile), sort_keys=True, separators=(",", ":")
        )
        profile["provenance_json"] = json.dumps(
            structured_provenance(), sort_keys=True, separators=(",", ":")
        )
        profiles.append(profile)

    return profiles


def partition_rows(
    rows: Iterable[Row],
    fields: tuple[str, ...] = AGE_SEX_PARTITION_FIELDS,
) -> dict[tuple[str, ...], list[Row]]:
    partitions: dict[tuple[str, ...], list[Row]] = defaultdict(list)
    for row in rows:
        partitions[partition_key(row, fields)].append(row)
    return partitions


def partition_key(
    row: Row,
    fields: tuple[str, ...] = AGE_SEX_PARTITION_FIELDS,
) -> tuple[str, ...]:
    return tuple(str(row[field]) for field in fields)


def weighted_choice(rows: list[Row], rng: random.Random) -> Row:
    if not rows:
        raise ValueError("Cannot sample from an empty partition")

    weights = [row_weight(row) for row in rows]
    total = sum(weights)
    if total <= 0:
        raise ValueError("Cannot sample from a partition with no positive weight")

    target = Decimal(str(rng.random())) * total
    cumulative = Decimal("0")
    for row, weight in zip(rows, weights, strict=True):
        cumulative += weight
        if target <= cumulative:
            return row
    return rows[-1]


def row_weight(row: Row) -> Decimal:
    value = row.get("probability_within_partition") or row.get("count")
    return Decimal(str(value))


def pgm_trace(profile: Row) -> dict[str, dict[str, Any]]:
    return {
        "age_sex": {
            "source_mart": "mart_pgm__sa2_age_sex",
            "conditioned_on": ["sa2_code"],
            "sampled_fields": ["age_band", "sex"],
            "partition": {"sa2_code": profile["sa2_code"]},
        },
        "labour_force_status": {
            "source_mart": "mart_pgm__sa2_labour_force_status",
            "conditioned_on": ["sa2_code", "age_band", "sex"],
            "sampled_fields": ["labour_force_status"],
            "partition": {
                "sa2_code": profile["sa2_code"],
                "age_band": profile["age_band"],
                "sex": profile["sex"],
            },
        },
        "income_band": {
            "source_mart": "mart_pgm__sa2_personal_income",
            "conditioned_on": ["sa2_code", "age_band", "sex"],
            "sampled_fields": ["income_band"],
            "partition": {
                "sa2_code": profile["sa2_code"],
                "age_band": profile["age_band"],
                "sex": profile["sex"],
            },
        },
        "country_of_birth": {
            "source_mart": "mart_pgm__sa2_country_of_birth",
            "conditioned_on": ["sa2_code", "age_band", "sex"],
            "sampled_fields": ["country_of_birth"],
            "partition": {
                "sa2_code": profile["sa2_code"],
                "age_band": profile["age_band"],
                "sex": profile["sex"],
            },
        },
        "language_used_at_home": {
            "source_mart": "mart_pgm__sa2_language_home_english_proficiency",
            "conditioned_on": ["sa2_code", "sex"],
            "sampled_fields": ["language_used_at_home", "english_proficiency"],
            "partition": {
                "sa2_code": profile["sa2_code"],
                "sex": profile["sex"],
            },
        },
        "household_relationship": {
            "source_mart": "mart_pgm__sa2_household_relationship",
            "conditioned_on": ["sa2_code", "age_band", "sex"],
            "sampled_fields": ["household_relationship"],
            "partition": {
                "sa2_code": profile["sa2_code"],
                "age_band": profile["age_band"],
                "sex": profile["sex"],
            },
        },
    }


def structured_provenance() -> dict[str, str]:
    return {
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
