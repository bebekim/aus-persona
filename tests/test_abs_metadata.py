import json

from aus_personas.abs_metadata import MetadataRow, decode_metadata_row, parse_axes


def test_decodes_country_of_birth_age_sex_column():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G1241",
            short_id="M_Afghanistan_0_4",
            long_id="MALES_Afghanistan_Age_0_4_years",
            table_number="G09A",
            profile_table="G09a",
            column_heading_description="Age: 0-4 years|MALES",
            logical_table_name="Country of Birth of Person by Age by Sex",
            population_universe="Persons",
        )
    )

    assert decoded.logical_table_code == "G09"
    assert decoded.project_alias == "country_of_birth_by_age_sex"
    assert decoded.physical_table == "sa2_g09a"
    assert decoded.raw_column == "g1241"
    assert decoded.sex == "Male"
    assert decoded.age_band == "0-4"
    assert decoded.category_axis == "country_of_birth"
    assert decoded.category == "Afghanistan"
    assert json.loads(decoded.axes_json) == {
        "age_band": "0-4",
        "country_of_birth": "Afghanistan",
        "sex": "Male",
    }


def test_decodes_marital_status_column():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G579",
            short_id="M_25_34_yr_Never_married",
            long_id="MALES_25_34_years_Never_married",
            table_number="G05",
            profile_table="G05",
            column_heading_description="Never married|MALES",
            logical_table_name="Registered Marital Status by Age by Sex",
            population_universe="Persons aged 15 years and over",
        )
    )

    assert decoded.project_alias == "registered_marital_status_by_age_sex"
    assert decoded.age_band == "25-34"
    assert decoded.sex == "Male"
    assert decoded.category_axis == "registered_marital_status"
    assert decoded.category == "Never married"


def test_decodes_age_by_sex_without_category():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G326",
            short_id="Age_yr_15_19_M",
            long_id="Age_years_15_19_years_Males",
            table_number="G04A",
            profile_table="G04",
            column_heading_description="Males",
            logical_table_name="Age by Sex",
            population_universe="Persons",
        )
    )

    assert decoded.project_alias == "age_by_sex"
    assert decoded.age_band == "15-19"
    assert decoded.sex == "Male"
    assert decoded.category_axis is None
    assert decoded.category is None


def test_decodes_labour_force_status_from_label():
    axes = parse_axes(
        "W01",
        "Males_15_19_years_Employed_Worked_full_time",
        "Employed: Worked full-time|MALES",
    )

    assert axes == {
        "age_band": "15-19",
        "labour_force_status": "Employed: Worked full-time",
        "sex": "Male",
    }


def test_marks_total_columns_and_keeps_age_context():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G568",
            short_id="M_15_19_yr_Tot",
            long_id="MALES_15_19_years_Total",
            table_number="G05",
            profile_table="G05",
            column_heading_description="Total|MALES",
            logical_table_name="Registered Marital Status by Age by Sex",
            population_universe="Persons aged 15 years and over",
        )
    )

    assert decoded.age_band == "15-19"
    assert decoded.category_axis == "registered_marital_status"
    assert decoded.category == "Total"
    assert decoded.is_total is True


def test_strips_redundant_occupation_prefix():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G16537",
            short_id="P65_74_Managers",
            long_id="PERSONS_65_74_years_Occupation_Managers",
            table_number="G60B",
            profile_table="G60",
            column_heading_description="Occupation: Managers|PERSONS",
            logical_table_name="Occupation by age by Sex",
            population_universe="Employed persons aged 15 years and over",
        )
    )

    assert decoded.age_band == "65-74"
    assert decoded.sex == "Persons"
    assert decoded.category_axis == "occupation"
    assert decoded.category == "Managers"
