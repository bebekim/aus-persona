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


def test_decodes_ancestry_column():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G984",
            short_id="Australian_Both_parents_born_Aust",
            long_id="Australian_Both_parents_born_in_Australia",
            table_number="G08",
            profile_table="G08",
            column_heading_description=(
                "Ancestry: Australian|Both parents born in Australia"
            ),
            logical_table_name="Ancestry by Country of Birth of Parents",
            population_universe="Persons",
        )
    )

    assert decoded.logical_table_code == "G08"
    assert decoded.project_alias == "ancestry_by_parent_birthplace"
    assert decoded.category_axis == "ancestry"
    assert decoded.category == "Australian"
    assert json.loads(decoded.axes_json) == {
        "ancestry": "Australian",
    }


def test_decodes_language_and_english_proficiency_axes():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G4586",
            short_id="MSEO_UOLSE_VWorW",
            long_id=(
                "MALES_Speaks_English_only_"
                "Uses_other_language_and_speaks_English_Very_well_or_well"
            ),
            table_number="G13A",
            profile_table="G13a",
            column_heading_description=(
                "Uses other language and speaks English: Very well or well|MALES"
            ),
            logical_table_name=(
                "Language Used at Home by Proficiency in Spoken English by Sex"
            ),
            population_universe="Persons",
        )
    )

    assert decoded.logical_table_code == "G13"
    assert decoded.category_axis == "language_used_at_home"
    assert decoded.category == "Speaks English only"
    assert json.loads(decoded.axes_json) == {
        "english_proficiency": "Very well or well",
        "language_used_at_home": "Speaks English only",
        "sex": "Male",
    }


def test_decodes_other_language_without_abs_prefix():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G4610",
            short_id="MOL_CL_Canton_UOLSE_VWorW",
            long_id=(
                "MALES_Uses_other_language_Chinese_languages_Cantonese_"
                "Uses_other_language_and_speaks_English_Very_well_or_well"
            ),
            table_number="G13A",
            profile_table="G13a",
            column_heading_description=(
                "Uses other language and speaks English: Very well or well|MALES"
            ),
            logical_table_name=(
                "Language Used at Home by Proficiency in Spoken English by Sex"
            ),
            population_universe="Persons",
        )
    )

    assert decoded.category_axis == "language_used_at_home"
    assert decoded.category == "Chinese languages Cantonese"
    assert json.loads(decoded.axes_json) == {
        "english_proficiency": "Very well or well",
        "language_used_at_home": "Chinese languages Cantonese",
        "sex": "Male",
    }


def test_decodes_defence_service_status_column():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G6901",
            short_id="M_25_34_Has_served",
            long_id="MALES_25_34_years_Has_served_in_the_Australian_Defence_Force",
            table_number="G22",
            profile_table="G22",
            column_heading_description=(
                "Has served in the Australian Defence Force|MALES"
            ),
            logical_table_name="Australian Defence Force Service by Age by Sex",
            population_universe="Persons aged 15 years and over",
        )
    )

    assert decoded.category_axis == "defence_service_status"
    assert decoded.category == "Has served in the Australian Defence Force"
    assert json.loads(decoded.axes_json) == {
        "age_band": "25-34",
        "defence_service_status": "Has served in the Australian Defence Force",
        "sex": "Male",
    }


def test_decodes_household_composition_and_size_axes():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G9201",
            short_id="Couple_children_4_persons",
            long_id=(
                "One_family_household_Couple_family_with_children_"
                "Four_persons_usually_resident"
            ),
            table_number="G35",
            profile_table="G35",
            column_heading_description=(
                "One family household: Couple family with children|"
                "Four persons usually resident"
            ),
            logical_table_name=(
                "Household Composition by Number of Persons Usually Resident"
            ),
            population_universe="Occupied private dwellings",
        )
    )

    assert decoded.category_axis == "household_composition"
    assert decoded.category == "One family household: Couple family with children"
    assert json.loads(decoded.axes_json) == {
        "household_composition": "One family household: Couple family with children",
        "household_size": "Four persons usually resident",
    }


def test_decodes_household_relationship_from_long_id_when_label_is_age():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G8643",
            short_id="F_Partner_registered_marriage_15_24",
            long_id="FEMALES_Partner_in_a_registered_marriage_Age_15_24_years",
            table_number="G27A",
            profile_table="G27a",
            column_heading_description="Age: 15-24 years|FEMALES",
            logical_table_name="Relationship in Household by Age by Sex",
            population_universe="Persons",
        )
    )

    assert decoded.logical_table_code == "G27"
    assert decoded.physical_table == "sa2_g27a"
    assert decoded.sex == "Female"
    assert decoded.age_band == "15-24"
    assert decoded.category_axis == "household_relationship"
    assert decoded.category == "Partner in a registered marriage"
    assert json.loads(decoded.axes_json) == {
        "age_band": "15-24",
        "household_relationship": "Partner in a registered marriage",
        "sex": "Female",
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


def test_decodes_g17_income_band_from_long_id_when_label_is_age():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G5857",
            short_id="M_Neg_Nil_income_15_19_yrs",
            long_id="MALES_Negative_Nil_income_Age_15_19_years",
            table_number="G17A",
            profile_table="G17a",
            column_heading_description="Age: 15-19 years|MALES",
            logical_table_name="Total Personal Income (Weekly) by Age by Sex",
            population_universe="Persons aged 15 years and over",
        )
    )

    assert decoded.logical_table_code == "G17"
    assert decoded.physical_table == "sa2_g17a"
    assert decoded.sex == "Male"
    assert decoded.age_band == "15-19"
    assert decoded.category_axis == "income_band"
    assert decoded.category == "Negative Nil income"


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


def test_strips_redundant_industry_prefix():
    decoded = decode_metadata_row(
        MetadataRow(
            sequential_id="G15301",
            short_id="M_25_34_Health_care",
            long_id=(
                "MALES_Health_Care_and_Social_Assistance_Age_25_34_years"
            ),
            table_number="G54A",
            profile_table="G54a",
            column_heading_description="Age: 25-34 years|MALES",
            logical_table_name="Industry of Employment by Age by Sex",
            population_universe="Employed persons aged 15 years and over",
        )
    )

    assert decoded.category_axis == "industry"
    assert decoded.category == "Health Care and Social Assistance"
