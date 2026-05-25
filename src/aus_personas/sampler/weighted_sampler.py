"""Conditional weighted sampling for ABS-backed PGM seed profiles."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

Row = dict[str, Any]


def generate_seed_profiles(
    *,
    age_sex_rows: Iterable[Row],
    labour_rows: Iterable[Row],
    income_rows: Iterable[Row],
    sample_size: int,
    rng: random.Random | None = None,
) -> list[Row]:
    """Generate fixed structured seed profiles from PGM mart rows."""
    if sample_size < 0:
        raise ValueError("sample_size must be non-negative")

    rng = rng or random.Random()
    labour_by_partition = partition_rows(labour_rows)
    income_by_partition = partition_rows(income_rows)
    age_choices = [
        row
        for row in age_sex_rows
        if partition_key(row) in labour_by_partition
        and partition_key(row) in income_by_partition
    ]

    profiles: list[Row] = []
    for index in range(1, sample_size + 1):
        age_row = weighted_choice(age_choices, rng)
        partition = partition_key(age_row)
        labour_row = weighted_choice(labour_by_partition[partition], rng)
        income_row = weighted_choice(income_by_partition[partition], rng)

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
        }
        profile["pgm_trace_json"] = json.dumps(
            pgm_trace(profile), sort_keys=True, separators=(",", ":")
        )
        profile["provenance_json"] = json.dumps(
            structured_provenance(), sort_keys=True, separators=(",", ":")
        )
        profiles.append(profile)

    return profiles


def partition_rows(rows: Iterable[Row]) -> dict[tuple[str, str, str], list[Row]]:
    partitions: dict[tuple[str, str, str], list[Row]] = defaultdict(list)
    for row in rows:
        partitions[partition_key(row)].append(row)
    return partitions


def partition_key(row: Row) -> tuple[str, str, str]:
    return (str(row["sa2_code"]), str(row["age_band"]), str(row["sex"]))


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
    }


def structured_provenance() -> dict[str, str]:
    return {
        "sa2_code": "sampled_from_abs",
        "age_band": "sampled_from_abs",
        "sex": "sampled_from_abs",
        "labour_force_status": "sampled_from_abs",
        "income_band": "sampled_from_abs",
    }
