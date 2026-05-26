import json
import random

from aus_personas.sampler.weighted_sampler import generate_seed_profiles


def test_generate_seed_profiles_preserves_structured_fields_and_provenance():
    profiles = generate_seed_profiles(
        age_sex_rows=[
            {
                "census_year": "2021",
                "sa2_code": "213041359",
                "sa2_name": "Rockbank - Mount Cottrell",
                "state_name": "Victoria",
                "age_band": "25-29",
                "sex": "Female",
                "count": "10",
                "probability_within_partition": "1.0",
            }
        ],
        labour_rows=[
            {
                "sa2_code": "213041359",
                "age_band": "25-29",
                "sex": "Female",
                "labour_force_status": "Employed full-time",
                "count": "7",
                "probability_within_partition": "1.0",
            }
        ],
        income_rows=[
            {
                "sa2_code": "213041359",
                "age_band": "25-29",
                "sex": "Female",
                "income_band": "1000 1249",
                "count": "5",
                "probability_within_partition": "1.0",
            }
        ],
        country_of_birth_rows=[
            {
                "sa2_code": "213041359",
                "age_band": "25-29",
                "sex": "Female",
                "country_of_birth": "Australia",
                "count": "8",
                "probability_within_partition": "1.0",
            }
        ],
        language_rows=[
            {
                "sa2_code": "213041359",
                "sex": "Female",
                "language_used_at_home": "English",
                "english_proficiency": "Speaks English only",
                "count": "9",
                "probability_within_partition": "1.0",
            }
        ],
        household_relationship_rows=[
            {
                "sa2_code": "213041359",
                "age_band": "25-29",
                "sex": "Female",
                "household_relationship": "Husband, wife or partner",
                "count": "6",
                "probability_within_partition": "1.0",
            }
        ],
        sample_size=1,
        rng=random.Random(7),
    )

    assert profiles == [
        {
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
            "pgm_trace_json": profiles[0]["pgm_trace_json"],
            "provenance_json": profiles[0]["provenance_json"],
        }
    ]

    trace = json.loads(profiles[0]["pgm_trace_json"])
    assert trace["age_sex"]["source_mart"] == "mart_pgm__sa2_age_sex"
    assert trace["labour_force_status"]["conditioned_on"] == [
        "sa2_code",
        "age_band",
        "sex",
    ]
    assert trace["income_band"]["source_mart"] == "mart_pgm__sa2_personal_income"
    assert (
        trace["country_of_birth"]["source_mart"]
        == "mart_pgm__sa2_country_of_birth"
    )
    assert trace["language_used_at_home"]["source_mart"] == (
        "mart_pgm__sa2_language_home_english_proficiency"
    )
    assert trace["language_used_at_home"]["sampled_fields"] == [
        "language_used_at_home",
        "english_proficiency",
    ]
    assert trace["household_relationship"]["source_mart"] == (
        "mart_pgm__sa2_household_relationship"
    )

    provenance = json.loads(profiles[0]["provenance_json"])
    assert provenance == {
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


def test_generate_seed_profiles_uses_conditional_labour_and_income_rows():
    profiles = generate_seed_profiles(
        age_sex_rows=[
            {
                "census_year": "2021",
                "sa2_code": "A",
                "sa2_name": "Area A",
                "state_name": "NSW",
                "age_band": "30-34",
                "sex": "Male",
                "count": "1",
                "probability_within_partition": "1.0",
            }
        ],
        labour_rows=[
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Female",
                "labour_force_status": "Wrong partition",
                "count": "100",
                "probability_within_partition": "1.0",
            },
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Male",
                "labour_force_status": "Employed part-time",
                "count": "1",
                "probability_within_partition": "1.0",
            },
        ],
        income_rows=[
            {
                "sa2_code": "A",
                "age_band": "35-39",
                "sex": "Male",
                "income_band": "Wrong partition",
                "count": "100",
                "probability_within_partition": "1.0",
            },
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Male",
                "income_band": "1500 1749",
                "count": "1",
                "probability_within_partition": "1.0",
            },
        ],
        country_of_birth_rows=[
            {
                "sa2_code": "A",
                "age_band": "35-39",
                "sex": "Male",
                "country_of_birth": "Wrong partition",
                "count": "100",
                "probability_within_partition": "1.0",
            },
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Male",
                "country_of_birth": "India",
                "count": "1",
                "probability_within_partition": "1.0",
            },
        ],
        language_rows=[
            {
                "sa2_code": "A",
                "sex": "Female",
                "language_used_at_home": "Wrong partition",
                "english_proficiency": "Wrong partition",
                "count": "100",
                "probability_within_partition": "1.0",
            },
            {
                "sa2_code": "A",
                "sex": "Male",
                "language_used_at_home": "Punjabi",
                "english_proficiency": "Very well or well",
                "count": "1",
                "probability_within_partition": "1.0",
            },
        ],
        household_relationship_rows=[
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Female",
                "household_relationship": "Wrong partition",
                "count": "100",
                "probability_within_partition": "1.0",
            },
            {
                "sa2_code": "A",
                "age_band": "30-34",
                "sex": "Male",
                "household_relationship": "Group household member",
                "count": "1",
                "probability_within_partition": "1.0",
            },
        ],
        sample_size=1,
        rng=random.Random(11),
    )

    assert profiles[0]["labour_force_status"] == "Employed part-time"
    assert profiles[0]["income_band"] == "1500 1749"
    assert profiles[0]["country_of_birth"] == "India"
    assert profiles[0]["language_used_at_home"] == "Punjabi"
    assert profiles[0]["english_proficiency"] == "Very well or well"
    assert profiles[0]["household_relationship"] == "Group household member"
