"""Semantic catalog for queryable ABS Census topics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SEMANTIC_CATALOG = Path("configs/abs_semantic_tables.yml")
GUARDRAIL_PURPOSES = ("sample", "condition", "validate", "generate")


@dataclass(frozen=True)
class GuardrailDecision:
    logical_table: str
    section: str
    purpose: str
    decision: str
    reason: str
    sampler_tier: str = ""
    persona_fields: tuple[str, ...] = ()
    conditioning_fields: tuple[str, ...] = ()
    promotion_status: str = ""

    def as_row(self) -> dict[str, str]:
        return {
            "logical_table": self.logical_table,
            "section": self.section,
            "purpose": self.purpose,
            "decision": self.decision,
            "reason": self.reason,
            "sampler_tier": self.sampler_tier,
            "persona_fields": ", ".join(self.persona_fields),
            "conditioning_fields": ", ".join(self.conditioning_fields),
            "promotion_status": self.promotion_status,
        }


@dataclass(frozen=True)
class SemanticSection:
    logical_table: str
    section: str
    description: str
    raw_column_ranges: tuple[str, ...]
    grain: str
    feature_name: str
    value_column: str
    is_sampler_candidate: bool
    total_policy: str
    sampler_tier: str
    guardrail: dict[str, str]
    guardrail_reason: str
    persona_fields: tuple[str, ...]
    conditioning_fields: tuple[str, ...]
    promotion_status: str

    @property
    def raw_column_predicate(self) -> str:
        predicates: list[str] = []
        for raw_range in self.raw_column_ranges:
            if raw_range == "all":
                return "true"
            start, end = parse_raw_column_range(raw_range)
            predicates.append(
                "substring(d.raw_column from 2)::integer "
                f"between {start} and {end}"
            )
        return "(" + " or ".join(predicates) + ")"


@dataclass(frozen=True)
class SemanticTable:
    logical_table: str
    name: str
    description: str
    default_physical_tables: tuple[str, ...]
    sections: dict[str, SemanticSection]

    @property
    def is_sa2_only(self) -> bool:
        return all(
            physical_table.startswith("sa2_")
            for physical_table in self.default_physical_tables
        )


@dataclass(frozen=True)
class SemanticCatalog:
    tables: dict[str, SemanticTable]

    def table(self, logical_table: str) -> SemanticTable:
        key = logical_table.upper()
        try:
            return self.tables[key]
        except KeyError as exc:
            raise ValueError(f"Unknown semantic table: {logical_table}") from exc

    def section(self, logical_table: str, section: str) -> SemanticSection:
        table = self.table(logical_table)
        try:
            return table.sections[section]
        except KeyError as exc:
            raise ValueError(
                f"Unknown semantic section for {logical_table}: {section}"
            ) from exc

    def inventory_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for table in sorted(self.tables.values(), key=lambda item: item.logical_table):
            rows.append(
                {
                    "logical_table": table.logical_table,
                    "name": table.name,
                    "description": table.description,
                    "physical_tables": ", ".join(table.default_physical_tables),
                    "section_count": str(len(table.sections)),
                    "sa2_only": str(table.is_sa2_only).lower(),
                }
            )
        return rows

    def section_rows(self, logical_table: str) -> list[dict[str, str]]:
        table = self.table(logical_table)
        return [
            {
                "logical_table": table.logical_table,
                "section": section.section,
                "description": section.description,
                "raw_column_ranges": ", ".join(section.raw_column_ranges),
                "grain": section.grain,
                "feature_name": section.feature_name,
                "value_column": section.value_column,
                "is_sampler_candidate": str(section.is_sampler_candidate).lower(),
                "total_policy": section.total_policy,
                "one_row_represents": (
                    "one measured value for one SA2, this section, and one "
                    "combination of the section axes"
                ),
            }
            for section in table.sections.values()
        ]

    def guardrail_decision(
        self,
        logical_table: str,
        section: str,
        purpose: str,
    ) -> GuardrailDecision:
        purpose_key = purpose.lower()
        if purpose_key not in GUARDRAIL_PURPOSES:
            return GuardrailDecision(
                logical_table=logical_table.upper(),
                section=section,
                purpose=purpose_key,
                decision="unknown",
                reason=f"Unknown guardrail purpose: {purpose}",
            )

        try:
            table = self.table(logical_table)
        except ValueError:
            return GuardrailDecision(
                logical_table=logical_table.upper(),
                section=section,
                purpose=purpose_key,
                decision="unknown",
                reason=f"Unknown semantic table: {logical_table}",
            )

        if not table.is_sa2_only:
            return GuardrailDecision(
                logical_table=table.logical_table,
                section=section,
                purpose=purpose_key,
                decision="deny",
                reason="Only sa2_* physical tables are allowed for persona work",
            )

        try:
            semantic_section = self.section(logical_table, section)
        except ValueError:
            return GuardrailDecision(
                logical_table=table.logical_table,
                section=section,
                purpose=purpose_key,
                decision="unknown",
                reason=f"Unknown semantic section for {table.logical_table}: {section}",
            )

        return GuardrailDecision(
            logical_table=table.logical_table,
            section=semantic_section.section,
            purpose=purpose_key,
            decision=semantic_section.guardrail.get(purpose_key, "unknown"),
            reason=semantic_section.guardrail_reason,
            sampler_tier=semantic_section.sampler_tier,
            persona_fields=semantic_section.persona_fields,
            conditioning_fields=semantic_section.conditioning_fields,
            promotion_status=semantic_section.promotion_status,
        )

    def physical_table_decision(
        self,
        physical_table: str,
        purpose: str,
    ) -> GuardrailDecision:
        normalized = physical_table.strip().lower()
        purpose_key = purpose.lower()
        if not normalized.startswith("sa2_"):
            return GuardrailDecision(
                logical_table="",
                section="",
                purpose=purpose_key,
                decision="deny",
                reason=f"Only sa2_* physical tables are allowed for persona work: {physical_table}",
            )

        for table in self.tables.values():
            if normalized in table.default_physical_tables:
                return GuardrailDecision(
                    logical_table=table.logical_table,
                    section="",
                    purpose=purpose_key,
                    decision="allow",
                    reason="Known SA2 physical table in semantic catalog",
                )

        return GuardrailDecision(
            logical_table="",
            section="",
            purpose=purpose_key,
            decision="unknown",
            reason=f"Unknown sa2_* physical table: {physical_table}",
        )

    def worthiness_rows(self, logical_table: str | None = None) -> list[dict[str, str]]:
        tables = (
            [self.table(logical_table)]
            if logical_table is not None
            else sorted(self.tables.values(), key=lambda item: item.logical_table)
        )
        rows: list[dict[str, str]] = []
        for table in tables:
            for section in table.sections.values():
                rows.append(
                    {
                        "logical_table": table.logical_table,
                        "section": section.section,
                        "sampler_tier": section.sampler_tier,
                        "sample": section.guardrail.get("sample", "unknown"),
                        "condition": section.guardrail.get("condition", "unknown"),
                        "validate": section.guardrail.get("validate", "unknown"),
                        "generate": section.guardrail.get("generate", "unknown"),
                        "persona_fields": ", ".join(section.persona_fields),
                        "conditioning_fields": ", ".join(section.conditioning_fields),
                        "promotion_status": section.promotion_status,
                    }
                )
        return rows


def load_semantic_catalog(path: Path = DEFAULT_SEMANTIC_CATALOG) -> SemanticCatalog:
    with path.open() as file:
        raw_catalog = yaml.safe_load(file)

    tables = {
        logical_table.upper(): parse_semantic_table(logical_table, table_config)
        for logical_table, table_config in raw_catalog["tables"].items()
    }
    return SemanticCatalog(tables=tables)


def parse_semantic_table(logical_table: str, raw_table: dict[str, Any]) -> SemanticTable:
    table_key = logical_table.upper()
    sections = {
        section_name: SemanticSection(
            logical_table=table_key,
            section=section_name,
            description=section_config["description"],
            raw_column_ranges=tuple(section_config["raw_column_ranges"]),
            grain=section_config["grain"],
            feature_name=section_config["feature_name"],
            value_column=section_config["value_column"],
            is_sampler_candidate=section_config.get("is_sampler_candidate", False),
            total_policy=section_config.get(
                "total_policy",
                "unspecified",
            ),
            **parse_sampler_guardrail(section_config),
        )
        for section_name, section_config in raw_table["sections"].items()
    }
    return SemanticTable(
        logical_table=table_key,
        name=raw_table["name"],
        description=raw_table["description"],
        default_physical_tables=tuple(raw_table["default_physical_tables"]),
        sections=sections,
    )


def parse_sampler_guardrail(section_config: dict[str, Any]) -> dict[str, Any]:
    sampler_config = section_config.get("sampler", {})
    is_candidate = section_config.get("is_sampler_candidate", False)
    guardrail = {
        "sample": "deny",
        "condition": "deny",
        "validate": "allow",
        "generate": "deny",
    }
    guardrail.update(sampler_config.get("guardrail", {}))
    return {
        "sampler_tier": sampler_config.get("tier", "B" if is_candidate else "C"),
        "guardrail": guardrail,
        "guardrail_reason": sampler_config.get(
            "reason",
            section_config.get("total_policy", "No sampler guardrail reason supplied"),
        ),
        "persona_fields": tuple(sampler_config.get("persona_fields", ())),
        "conditioning_fields": tuple(sampler_config.get("conditioning_fields", ())),
        "promotion_status": sampler_config.get("promotion_status", "candidate"),
    }


def parse_raw_column_range(raw_range: str) -> tuple[int, int]:
    if "-" not in raw_range:
        value = raw_column_number(raw_range)
        return value, value

    start, end = raw_range.split("-", maxsplit=1)
    return raw_column_number(start), raw_column_number(end)


def raw_column_number(raw_column: str) -> int:
    normalized = raw_column.lower()
    if not normalized.startswith("g") or not normalized[1:].isdigit():
        raise ValueError(f"Invalid raw column reference: {raw_column}")
    return int(normalized[1:])


def normalize_raw_column(raw_column: str) -> str:
    raw_column = raw_column.strip().lower()
    raw_column_number(raw_column)
    return raw_column


def validate_sa2_physical_table(physical_table: str) -> str:
    normalized = physical_table.strip().lower()
    if not normalized.startswith("sa2_"):
        raise ValueError(
            f"Only sa2_* physical tables are allowed for persona work: {physical_table}"
        )
    return normalized
