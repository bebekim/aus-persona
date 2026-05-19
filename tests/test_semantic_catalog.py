from pathlib import Path

import pytest
import yaml

from aus_personas.census.semantic_catalog import (
    load_semantic_catalog,
    normalize_raw_column,
    parse_raw_column_range,
    validate_sa2_physical_table,
)
from aus_personas.census.semantic_queries import decode_column_sql, long_sql, profile_sql


ACTIVE_PERSONA_TABLES = {
    "G07",
    "G08",
    "G09",
    "G13",
    "G17",
    "G22",
    "G27",
    "G35",
    "G37",
    "G46",
    "G54",
}


def _physical_tables_by_logical_table(config_path: Path) -> dict[str, tuple[str, ...]]:
    raw = yaml.safe_load(config_path.read_text())
    return {
        table["logical_table"]: tuple(table["physical_tables"])
        for table in raw["profile_tables"]
    }


def test_abs_source_configs_agree_for_active_persona_topics():
    source_tables = _physical_tables_by_logical_table(Path("configs/abs_census_sources.yml"))
    dbt_sources = yaml.safe_load(
        Path("dbt/aus_personas/models/sources/abs_sources.yml").read_text()
    )
    dbt_project = yaml.safe_load(Path("dbt/aus_personas/dbt_project.yml").read_text())

    dbt_source_tables = {
        table["name"]
        for source in dbt_sources["sources"]
        if source["name"] == "abs_census"
        for table in source["tables"]
        if table["name"].startswith("sa2_g")
    }
    dbt_project_tables = set(dbt_project["vars"]["first_pass_sa2_tables"])
    active_physical_tables = {
        physical_table
        for logical_table in ACTIVE_PERSONA_TABLES
        for physical_table in source_tables[logical_table]
    }

    assert set(source_tables) >= ACTIVE_PERSONA_TABLES
    assert "G18" not in source_tables
    assert "G40" not in source_tables
    assert active_physical_tables <= dbt_source_tables
    assert active_physical_tables <= dbt_project_tables


def test_dbt_category_cleaning_handles_g17_income_prefixes():
    macro_sql = Path("dbt/aus_personas/macros/abs/parse_abs_axis_helpers.sql").read_text()
    dictionary_sql = Path(
        "dbt/aus_personas/models/intermediate/abs/int_abs__column_dictionary.sql"
    ).read_text()

    assert "G17" in macro_sql
    assert "Income:" in macro_sql
    assert "Personal income:" in macro_sql
    assert "when s.logical_table_code = 'G17'" in dictionary_sql
    assert "MALES|FEMALES|PERSONS" in dictionary_sql
    assert "_Age_'), '_', ' ')" in dictionary_sql


def test_loads_semantic_catalog():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    g01 = catalog.table("g01")
    assert g01.name == "selected_person_characteristics_by_sex"
    assert g01.default_physical_tables == ("sa2_g01",)
    assert "age_group_by_sex" in g01.sections

    g17 = catalog.table("G17")
    assert g17.default_physical_tables == ("sa2_g17a", "sa2_g17b", "sa2_g17c")
    assert g17.is_sa2_only

    for logical_table in ACTIVE_PERSONA_TABLES:
        assert catalog.table(logical_table).is_sa2_only


def test_parses_raw_column_ranges():
    assert parse_raw_column_range("g4-g36") == (4, 36)
    assert parse_raw_column_range("g17") == (17, 17)
    assert parse_raw_column_range("G743-G746") == (743, 746)


def test_rejects_invalid_raw_column_range():
    with pytest.raises(ValueError, match="Invalid raw column"):
        parse_raw_column_range("x4")


def test_normalises_raw_column():
    assert normalize_raw_column(" G743 ") == "g743"


def test_validates_sa2_physical_table():
    assert validate_sa2_physical_table("SA2_G06") == "sa2_g06"
    with pytest.raises(ValueError, match="Only sa2_"):
        validate_sa2_physical_table("aust_g06")


def test_catalog_inventory_rows():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    rows = catalog.inventory_rows()

    assert rows[0]["logical_table"] == "G01"
    assert rows[0]["sa2_only"] == "true"
    assert rows[0]["section_count"] == "10"


def test_catalog_section_rows_include_row_contract():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    rows = catalog.section_rows("G01")

    assert rows[0]["logical_table"] == "G01"
    assert "one measured value for one SA2" in rows[0]["one_row_represents"]
    assert rows[0]["is_sampler_candidate"] == "false"
    assert rows[1]["section"] == "age_group_by_sex"
    assert rows[1]["is_sampler_candidate"] == "true"
    assert "sex=Persons" in rows[1]["total_policy"]


def test_guardrail_allows_g17_personal_income_for_sampling():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    decision = catalog.guardrail_decision("G17", "personal_income", "sample")

    assert decision.decision == "allow"
    assert decision.purpose == "sample"
    assert decision.sampler_tier == "A"
    assert "income_band" in decision.persona_fields


def test_guardrail_denies_g01_birthplace_for_sampling_but_allows_validation():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    sample_decision = catalog.guardrail_decision(
        "G01",
        "birthplace_summary_by_sex",
        "sample",
    )
    validate_decision = catalog.guardrail_decision(
        "G01",
        "birthplace_summary_by_sex",
        "validate",
    )

    assert sample_decision.decision == "deny"
    assert validate_decision.decision == "allow_validate"


def test_guardrail_fails_closed_for_unknown_and_non_sa2_tables():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    non_sa2 = catalog.physical_table_decision("aust_g17", "sample")
    unknown = catalog.physical_table_decision("sa2_g99", "sample")

    assert non_sa2.decision == "deny"
    assert "Only sa2_*" in non_sa2.reason
    assert unknown.decision == "unknown"


def test_guardrail_denies_aggregate_totals_for_sampling():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    decision = catalog.guardrail_decision("G01", "total_persons_by_sex", "sample")

    assert decision.decision == "deny"
    assert "aggregate" in decision.reason


def test_legacy_sampler_candidate_flag_does_not_auto_allow_sampling():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    decision = catalog.guardrail_decision("G01", "indigenous_summary_by_sex", "sample")

    assert decision.decision == "deny"


def test_worthiness_rows_expose_purpose_decisions():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    rows = catalog.worthiness_rows("G17")

    assert rows == [
        {
            "logical_table": "G17",
            "section": "personal_income",
            "sampler_tier": "A",
            "sample": "allow",
            "condition": "allow",
            "validate": "allow",
            "generate": "deny",
            "persona_fields": "income_band",
            "conditioning_fields": "sa2_code, age_band, sex",
            "promotion_status": "candidate",
        }
    ]


@pytest.mark.parametrize(
    ("logical_table", "section", "expected"),
    [
        ("G46", "labour_force_status", ("allow", "allow", "allow", "deny")),
        ("G09", "country_of_birth", ("allow", "allow", "allow", "deny")),
        ("G13", "language_home_english_proficiency", ("allow", "allow", "allow", "deny")),
        ("G08", "ancestry", ("allow", "allow", "allow", "deny")),
        ("G27", "household_relationship", ("allow", "allow", "allow", "deny")),
        ("G37", "tenure_landlord", ("deny", "allow_context", "allow_validate", "deny")),
        ("G54", "industry", ("deny", "allow_context", "allow_validate", "deny")),
        ("G35", "household_composition", ("deny", "allow_context", "allow_validate", "deny")),
        ("G22", "defence_service_status", ("deny", "allow_context", "allow_validate", "deny")),
        ("G07", "indigenous_status", ("deny", "allow_context", "allow_validate", "deny")),
    ],
)
def test_target_g_table_guardrails(logical_table, section, expected):
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))

    decisions = tuple(
        catalog.guardrail_decision(logical_table, section, purpose).decision
        for purpose in ("sample", "condition", "validate", "generate")
    )

    assert decisions == expected


def test_builds_profile_sql_for_catalog_table():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))
    sql = profile_sql(catalog.table("G01"))

    assert "int_abs__sa2_observations" in sql
    assert "'sa2_g01'" in sql
    assert "percentile_cont" in sql


def test_builds_long_sql_for_catalog_section():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))
    table = catalog.table("G01")
    section = catalog.section("G01", "age_group_by_sex")

    sql = long_sql(table, section, sa2_code="213041359", limit=10)

    assert "'age_group_by_sex' as semantic_section" in sql
    assert "between 4 and 36" in sql
    assert "o.sa2_code = '213041359'" in sql
    assert "is_sampling_eligible" in sql
    assert "coalesce(d.sex, '') <> 'Persons'" in sql
    assert "limit 10" in sql


def test_builds_g17_long_sql_with_income_axes_and_sampling_exclusions():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))
    table = catalog.table("G17")
    section = catalog.section("G17", "personal_income")

    sql = long_sql(table, section, sa2_code="213041359", limit=10)

    assert "'personal_income' as semantic_section" in sql
    assert "'sa2_g17a'" in sql
    assert "'sa2_g17b'" in sql
    assert "'sa2_g17c'" in sql
    assert "d.category as income_band" in sql
    assert "d.age_band" in sql
    assert "d.sex" in sql
    assert "coalesce(d.sex, '') <> 'Persons'" in sql
    assert "coalesce(d.category, '') not in ('Not stated', 'Not applicable')" in sql


def test_builds_g13_long_sql_with_language_and_english_proficiency_axes():
    catalog = load_semantic_catalog(Path("configs/abs_semantic_tables.yml"))
    table = catalog.table("G13")
    section = catalog.section("G13", "language_home_english_proficiency")

    sql = long_sql(table, section, sa2_code="213041359", limit=10)

    assert "'language_home_english_proficiency' as semantic_section" in sql
    assert "d.category as language_used_at_home" in sql
    assert "d.axes_json::jsonb ->> 'english_proficiency' as english_proficiency" in sql
    assert "o.count is not null" in sql
    assert (
        "coalesce(d.axes_json::jsonb ->> 'english_proficiency', '') "
        "not in ('Not stated', 'Not applicable')"
    ) in sql


def test_builds_decode_column_sql_for_sa2_column():
    physical_table = validate_sa2_physical_table("sa2_g06")
    raw_column = normalize_raw_column("G743")

    sql = decode_column_sql(physical_table, raw_column)

    assert "int_abs__column_dictionary" in sql
    assert "d.physical_table = 'sa2_g06'" in sql
    assert "lower(d.raw_column) = 'g743'" in sql
    assert "column_heading_description" in sql
