"""Decode ABS censusloader metadata into human-readable persona inputs."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PROFILE_FAMILY_NAMES = {
    "G": "General Community Profile",
    "P": "Place of Enumeration Profile",
    "W": "Working Population Profile",
    "I": "Indigenous Profile",
    "T": "Time Series Profile",
}


PROJECT_ALIASES = {
    "G01": "selected_person_characteristics_by_sex",
    "G04": "age_by_sex",
    "G05": "registered_marital_status_by_age_sex",
    "G06": "social_marital_status_by_age_sex",
    "G07": "indigenous_status_by_age_sex",
    "G08": "ancestry_by_parent_birthplace",
    "G09": "country_of_birth_by_age_sex",
    "G10": "country_of_birth_by_arrival_year",
    "G13": "language_home_by_english_proficiency_sex",
    "G14": "religious_affiliation_by_sex",
    "G15": "education_attendance_by_age_sex",
    "G16": "school_completion_by_age_sex",
    "G17": "personal_income_weekly_by_age_sex",
    "G18": "core_activity_need_for_assistance_by_age_sex",
    "G19": "long_term_health_condition_type_by_age_sex",
    "G27": "household_relationship_by_age_sex",
    "G29": "family_composition",
    "G33": "household_income_weekly_by_household_composition",
    "G35": "household_composition_by_resident_count",
    "G36": "dwelling_structure",
    "G37": "tenure_landlord_by_dwelling_structure",
    "G40": "rent_weekly_by_landlord_type",
    "G43": "selected_labour_education_migration_by_sex",
    "G46": "labour_force_status_by_age_sex",
    "G49": "qualification_level_by_age_sex",
    "G50": "field_of_study_by_age_sex",
    "G54": "industry_by_age_sex",
    "G60": "occupation_by_age_sex",
    "G62": "method_of_travel_to_work_by_sex",
    "W13": "workplace_occupation_by_sex",
    "W16": "workplace_occupation_by_income_age",
}


CATEGORY_AXIS_BY_TABLE = {
    "G05": "registered_marital_status",
    "G06": "social_marital_status",
    "G07": "indigenous_status",
    "G08": "ancestry",
    "G13": "language_home",
    "G14": "religious_affiliation",
    "G16": "school_completion",
    "G17": "income_band",
    "G18": "core_activity_need_for_assistance",
    "G22": "defence_service_status",
    "G27": "household_relationship",
    "G35": "household_composition",
    "G36": "dwelling_structure",
    "G37": "tenure_landlord_type",
    "G46": "labour_force_status",
    "G49": "qualification_level",
    "G50": "field_of_study",
    "G54": "industry",
    "G60": "occupation",
    "W01": "labour_force_status",
    "W13": "occupation",
    "W16": "occupation",
}


FIRST_PASS_LOGICAL_TABLES = (
    "G01",
    "G04",
    "G05",
    "G07",
    "G08",
    "G09",
    "G13",
    "G16",
    "G17",
    "G22",
    "G27",
    "G29",
    "G35",
    "G36",
    "G37",
    "G46",
    "G49",
    "G50",
    "G54",
    "G60",
)


@dataclass(frozen=True)
class MetadataRow:
    sequential_id: str
    short_id: str
    long_id: str
    table_number: str
    profile_table: str
    column_heading_description: str
    logical_table_name: str
    population_universe: str


@dataclass(frozen=True)
class DecodedColumn:
    source_profile: str
    profile_family_name: str
    logical_table_code: str
    logical_table_name: str
    project_alias: str
    population_universe: str
    physical_table_suffix: str
    physical_table: str
    raw_column: str
    sequential_id: str
    short_id: str
    long_id: str
    source_label: str
    sex: str | None
    age_band: str | None
    category_axis: str | None
    category: str | None
    axes_json: str
    is_total: bool


def logical_table_code(table_number: str) -> str:
    return table_number[:3].upper()


def source_profile(table_number: str) -> str:
    return table_number[:1].upper()


def profile_family_name(table_number: str) -> str:
    return PROFILE_FAMILY_NAMES.get(source_profile(table_number), "Unknown")


def project_alias(table_code: str, table_name: str) -> str:
    if table_code in PROJECT_ALIASES:
        return PROJECT_ALIASES[table_code]
    return slugify(table_name)


def physical_table_name(table_number: str, geography: str = "sa2") -> str:
    return f"{geography.lower()}_{table_number.lower()}"


def raw_column_name(sequential_id: str) -> str:
    return sequential_id.lower()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", cleaned)


def parse_axes(
    logical_code: str,
    long_id: str,
    source_label: str,
) -> dict[str, str]:
    axes: dict[str, str] = {}
    if logical_code not in {"G08", "G35", "G37"}:
        sex = parse_sex(long_id, source_label)
        if sex:
            axes["sex"] = sex

    age_band = parse_age_band(long_id, source_label)
    if age_band:
        axes["age_band"] = age_band

    category = parse_primary_category(logical_code, long_id, source_label)
    axis_name = CATEGORY_AXIS_BY_TABLE.get(logical_code)
    if logical_code == "G13":
        axis_name = "language_used_at_home"
    if axis_name and category:
        axes[axis_name] = category

    if logical_code == "G13":
        english_proficiency = parse_english_proficiency(source_label, long_id)
        if english_proficiency:
            axes["english_proficiency"] = english_proficiency

    if logical_code == "G35":
        household_size = parse_household_size(source_label, long_id)
        if household_size:
            axes["household_size"] = household_size

    if logical_code == "G09":
        country = parse_country_of_birth(long_id)
        if country:
            axes["country_of_birth"] = country

    return axes


def parse_sex(long_id: str, source_label: str) -> str | None:
    upper_label = source_label.upper()
    upper_long = long_id.upper()

    if upper_label.endswith("|MALES") or upper_long.startswith("MALES_"):
        return "Male"
    if upper_label.endswith("|FEMALES") or upper_long.startswith("FEMALES_"):
        return "Female"
    if upper_label.endswith("|PERSONS") or upper_long.endswith("_PERSONS"):
        return "Persons"
    if re.search(r"(^|_)MALES($|_)", upper_long):
        return "Male"
    if re.search(r"(^|_)FEMALES($|_)", upper_long):
        return "Female"
    if re.search(r"(^|_)PERSONS($|_)", upper_long):
        return "Persons"
    return None


def parse_age_band(long_id: str, source_label: str) -> str | None:
    candidates = (long_id, source_label.replace(":", ""))
    for value in candidates:
        normal = value.replace("-", "_").replace(" ", "_")

        match = re.search(r"Age_years_(\d+)_(\d+)_years", normal, re.IGNORECASE)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        match = re.search(r"Age[_ ]?(\d+)[_ -](\d+)[_ ]years", normal, re.IGNORECASE)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        match = re.search(r"(^|_)(\d+)_(\d+)_years($|_)", normal, re.IGNORECASE)
        if match:
            return f"{match.group(2)}-{match.group(3)}"

        match = re.search(r"Age_years_(\d+)_years_and_over", normal, re.IGNORECASE)
        if match:
            return f"{match.group(1)}+"

        match = re.search(r"(^|_)(\d+)_years_and_over($|_)", normal, re.IGNORECASE)
        if match:
            return f"{match.group(2)}+"

        match = re.search(r"Age_years_(\d+)($|_)", normal, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r"(^|_)(\d+)_years($|_)", normal, re.IGNORECASE)
        if match:
            return match.group(2)

    return None


def parse_primary_category(
    logical_code: str,
    long_id: str,
    source_label: str,
) -> str | None:
    if logical_code == "G04":
        return None

    if logical_code == "G17":
        match = re.search(
            r"^(?:MALES|FEMALES|PERSONS)_(.*?)_Age_\d",
            long_id,
            re.IGNORECASE,
        )
        if match:
            return clean_category(logical_code, match.group(1).replace("_", " "))

    if logical_code == "G13":
        language = parse_g13_language(long_id)
        if language:
            return clean_category(logical_code, language)

    if logical_code == "G54":
        match = re.search(
            r"^(?:MALES|FEMALES|PERSONS)_(.*?)_Age_\d",
            long_id,
            re.IGNORECASE,
        )
        if match:
            return clean_category(logical_code, match.group(1).replace("_", " "))

    label_head = source_label.split("|", maxsplit=1)[0].strip()
    if label_head and not label_head.lower().startswith("age"):
        return clean_category(logical_code, label_head)

    tokens = long_id.split("_")
    tokens = [
        token
        for token in tokens
        if token and token.upper() not in {"MALES", "FEMALES", "PERSONS"}
    ]
    tokens = strip_age_tokens(tokens)
    if not tokens:
        return None

    return clean_category(logical_code, " ".join(tokens).replace("  ", " "))


def clean_category(logical_code: str, value: str) -> str:
    cleaned = value.strip()
    prefixes_to_strip = {
        "G13": ("Language:",),
        "G14": ("Religion:", "Religious affiliation:"),
        "G16": ("Highest year of school completed:",),
        "G17": ("Income:", "Personal income:"),
        "G08": ("Ancestry:",),
        "G36": ("Dwelling structure:",),
        "G37": ("Tenure type:", "Landlord type:"),
        "G49": ("Qualification:", "Level of education:"),
        "G50": ("Field of study:",),
        "G54": ("Industry:",),
        "G60": ("Occupation:",),
        "W13": ("Occupation:",),
        "W16": ("Occupation:",),
    }
    for prefix in prefixes_to_strip.get(logical_code, ()):
        if cleaned.lower().startswith(prefix.lower()):
            return cleaned[len(prefix) :].strip()
    return cleaned


def parse_english_proficiency(source_label: str, long_id: str) -> str | None:
    parts = [
        part.strip()
        for part in source_label.split("|")
        if part.strip() and part.strip().upper() not in {"MALES", "FEMALES", "PERSONS"}
    ]
    if len(parts) >= 2:
        value = parts[1]
        return None if value.lower() == "total" else value
    value = parse_g13_english_proficiency(long_id)
    if value is None:
        return None
    return None if value.lower() == "total" else value


G13_PROFICIENCY_PATTERNS = (
    "Speaks_English_only",
    "Uses_other_language_and_speaks_English_Very_well_or_well",
    "Uses_other_language_and_speaks_English_Not_well_or_not_at_all",
    "Uses_other_language_and_speaks_English_Total",
    "Not_stated",
    "Total",
)


def parse_g13_language(long_id: str) -> str | None:
    match = parse_g13_long_id(long_id)
    if not match:
        return None
    value = match[0].replace("_", " ")
    return None if value.lower() == "total" else value


def parse_g13_english_proficiency(long_id: str) -> str | None:
    match = parse_g13_long_id(long_id)
    if not match:
        return None
    value = clean_g13_proficiency(match[1])
    return None if value.lower() == "total" else value


def parse_g13_long_id(long_id: str) -> tuple[str, str] | None:
    pattern = "|".join(re.escape(value) for value in G13_PROFICIENCY_PATTERNS)
    match = re.match(
        rf"^(?:MALES|FEMALES|PERSONS)_(.*?)_({pattern})$",
        long_id,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1), match.group(2)


def clean_g13_proficiency(value: str) -> str:
    cleaned = value.replace("_", " ")
    cleaned = cleaned.replace("Uses other language and speaks English ", "")
    return cleaned.replace("English Very", "English: Very").replace(
        "English Not",
        "English: Not",
    )


def parse_household_size(source_label: str, long_id: str) -> str | None:
    parts = [part.strip() for part in source_label.split("|") if part.strip()]
    if len(parts) >= 2:
        value = parts[1]
        return None if value.lower() == "total" else value

    match = re.search(
        r"((?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|[0-9]+)_"
        r"persons?_usually_resident)",
        long_id,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).replace("_", " ")


def strip_age_tokens(tokens: list[str]) -> list[str]:
    stripped: list[str] = []
    skip_next = 0
    for index, token in enumerate(tokens):
        if skip_next:
            skip_next -= 1
            continue
        lower = token.lower()
        if lower in {"age", "ages"}:
            continue
        if token.isdigit() and index + 1 < len(tokens) and tokens[index + 1].isdigit():
            skip_next = (
                2
                if index + 2 < len(tokens) and tokens[index + 2].lower() == "years"
                else 1
            )
            continue
        if (
            token.isdigit()
            and index + 1 < len(tokens)
            and tokens[index + 1].lower() in {"year", "years"}
        ):
            skip_next = 1
            continue
        if lower in {"year", "years", "yr"}:
            continue
        if (
            lower == "and"
            and index + 1 < len(tokens)
            and tokens[index + 1].lower() == "over"
        ):
            skip_next = 1
            continue
        stripped.append(token)
    return stripped


def parse_country_of_birth(long_id: str) -> str | None:
    match = re.match(r"^(MALES|FEMALES|PERSONS)_(.+?)_Age_", long_id, re.IGNORECASE)
    if not match:
        return None
    value = match.group(2).replace("_", " ")
    return None if value.lower() == "total" else value


def is_total_column(
    long_id: str,
    source_label: str,
    axes: Mapping[str, str],
) -> bool:
    if any(value.lower() == "total" for value in axes.values()):
        return True
    if re.search(r"(^|_)Total($|_)", long_id, re.IGNORECASE):
        return True
    return bool(re.search(r"(^|\|)Total($|\|)", source_label, re.IGNORECASE))


def decode_metadata_row(row: MetadataRow, geography: str = "sa2") -> DecodedColumn:
    table_code = logical_table_code(row.table_number)
    axes = parse_axes(table_code, row.long_id, row.column_heading_description)
    category_axis = next(
        (axis for axis in axes if axis not in {"sex", "age_band"}),
        None,
    )
    category = axes.get(category_axis) if category_axis else None
    is_total = is_total_column(row.long_id, row.column_heading_description, axes)

    return DecodedColumn(
        source_profile=source_profile(row.table_number),
        profile_family_name=profile_family_name(row.table_number),
        logical_table_code=table_code,
        logical_table_name=row.logical_table_name,
        project_alias=project_alias(table_code, row.logical_table_name),
        population_universe=row.population_universe,
        physical_table_suffix=row.table_number.lower(),
        physical_table=physical_table_name(row.table_number, geography),
        raw_column=raw_column_name(row.sequential_id),
        sequential_id=row.sequential_id,
        short_id=row.short_id,
        long_id=row.long_id,
        source_label=row.column_heading_description,
        sex=axes.get("sex"),
        age_band=axes.get("age_band"),
        category_axis=category_axis,
        category=category,
        axes_json=json.dumps(axes, sort_keys=True),
        is_total=is_total,
    )


def dictionary_sql(logical_tables: Sequence[str] | None = None) -> str:
    where = ""
    if logical_tables:
        quoted = ", ".join(sql_quote(table.upper()) for table in logical_tables)
        where = f"where upper(left(s.table_number, 3)) in ({quoted})"

    return f"""
select
  s.sequential_id,
  s.short_id,
  s.long_id,
  s.table_number,
  s.profile_table,
  s.column_heading_description,
  coalesce(t.table_name, '') as logical_table_name,
  coalesce(t.table_description, '') as population_universe
from census_2021_data.metadata_stats s
left join census_2021_data.metadata_tables t
  on t.table_number = upper(left(s.table_number, 3))
{where}
order by
  upper(left(s.table_number, 3)),
  s.table_number,
  substring(s.sequential_id from 2)::int
""".strip()


def fetch_dictionary(
    *,
    logical_tables: Sequence[str] | None = None,
    geography: str = "sa2",
    container: str = "censusloader-postgres",
) -> list[DecodedColumn]:
    rows = run_psql_csv(dictionary_sql(logical_tables), container=container)
    metadata_rows = [
        MetadataRow(
            sequential_id=row["sequential_id"],
            short_id=row["short_id"],
            long_id=row["long_id"],
            table_number=row["table_number"],
            profile_table=row["profile_table"],
            column_heading_description=row["column_heading_description"],
            logical_table_name=row["logical_table_name"],
            population_universe=row["population_universe"],
        )
        for row in rows
    ]
    return [decode_metadata_row(row, geography=geography) for row in metadata_rows]


def run_psql_csv(sql: str, *, container: str) -> list[dict[str, str]]:
    copy_sql = f"copy ({sql}) to stdout with csv header"
    completed = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-c",
            copy_sql,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Failed to fetch ABS metadata with docker/psql: " + completed.stderr.strip()
        )
    return list(csv.DictReader(completed.stdout.splitlines()))


def write_decoded_columns(
    columns: Iterable[DecodedColumn],
    path: Path,
    *,
    file_format: str | None = None,
) -> None:
    rows = [asdict(column) for column in columns]
    path.parent.mkdir(parents=True, exist_ok=True)
    format_name = file_format or path.suffix.lstrip(".")

    if format_name == "csv":
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(DecodedColumn.__dataclass_fields__)
            )
            writer.writeheader()
            writer.writerows(rows)
        return

    if format_name == "jsonl":
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        return

    if format_name == "parquet":
        import pandas as pd

        pd.DataFrame(rows).to_parquet(path, index=False)
        return

    raise ValueError(f"Unsupported dictionary output format: {format_name}")


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
