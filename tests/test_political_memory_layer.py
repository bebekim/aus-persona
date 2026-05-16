import csv
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
POLITICAL_SEED_DIR = (
    REPO_ROOT / "dbt" / "aus_personas" / "seeds" / "local_political_memory"
)
SOURCES_PATH = POLITICAL_SEED_DIR / "willoughby_political_sources.csv"
CONTRACTS_PATH = POLITICAL_SEED_DIR / "willoughby_political_event_contracts.csv"
DOC_PATH = REPO_ROOT / "docs" / "willoughby-political-memory-layer.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_willoughby_political_source_registry_covers_required_families() -> None:
    rows = read_csv(SOURCES_PATH)

    source_ids = [row["source_id"] for row in rows]
    assert len(source_ids) == len(set(source_ids))
    assert {row["council_slug"] for row in rows} == {"willoughby"}
    assert {
        "election_results",
        "meeting_votes",
        "notices_of_motion",
        "planning_determinations",
    }.issubset({row["source_family"] for row in rows})

    for row in rows:
        parsed = urlparse(row["primary_url"])
        assert parsed.scheme == "https", row["source_id"]
        assert parsed.netloc, row["source_id"]
        assert row["authority"], row["source_id"]
        assert row["grain"], row["source_id"]


def test_willoughby_political_event_contracts_are_cohort_safe() -> None:
    rows = read_csv(CONTRACTS_PATH)

    contract_ids = [row["contract_id"] for row in rows]
    assert len(contract_ids) == len(set(contract_ids))
    assert {row["council_slug"] for row in rows} == {"willoughby"}
    assert {
        "election_contest",
        "election_candidate_result",
        "council_meeting_item",
        "councillor_vote",
        "notice_of_motion",
        "planning_determination",
        "policy_issue_annotation",
    }.issubset(set(contract_ids))

    for row in rows:
        assert "|" in row["natural_key"], row["contract_id"]
        assert "|" in row["required_fields"], row["contract_id"]
        assert row["persona_policy_use"], row["contract_id"]

    candidate_result = next(
        row for row in rows if row["contract_id"] == "election_candidate_result"
    )
    assert "without claiming synthetic residents voted" in (
        candidate_result["persona_policy_use"]
    )


def test_political_memory_docs_capture_election_cycle_and_guardrails() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")

    for expected in ["2004", "2008", "2012", "2017", "2021", "2024"]:
        assert expected in doc

    assert "postponed" in doc
    assert "must never be described as real voters" in doc
    assert "Treat missing named votes as unknown" in doc
