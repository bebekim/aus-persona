import csv
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
POLITICAL_SEED_DIR = (
    REPO_ROOT / "dbt" / "aus_personas" / "seeds" / "local_political_memory"
)
SOURCES_PATH = POLITICAL_SEED_DIR / "willoughby_political_sources.csv"
CONTRACTS_PATH = POLITICAL_SEED_DIR / "willoughby_political_event_contracts.csv"
VOTE_ROWS_PATH = POLITICAL_SEED_DIR / "willoughby_2024_candidate_vote_rows.csv"
MOTION_VOTE_OUTCOMES_PATH = (
    POLITICAL_SEED_DIR / "willoughby_2025_council_motion_vote_outcomes.csv"
)
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
    assert "PortalMotionVotes" in doc
    assert "Resolution En Bloc" in doc


def test_willoughby_2024_vote_rows_sum_to_official_formal_totals() -> None:
    rows = read_csv(VOTE_ROWS_PATH)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["contest_type"], row["ward_name"])
        grouped.setdefault(key, []).append(row)

    expected_totals = {
        ("mayoral", ""): 37402,
        ("councillor", "Middle Harbour Ward"): 9181,
        ("councillor", "Naremburn Ward"): 8820,
        ("councillor", "Sailors Bay Ward"): 9437,
        ("councillor", "West Ward"): 9059,
    }

    assert set(grouped) == set(expected_totals)
    assert len(rows) == 86

    for key, total in expected_totals.items():
        contest_rows = grouped[key]
        assert {int(row["total_formal_votes"]) for row in contest_rows} == {total}
        assert sum(int(row["first_preference_votes"]) for row in contest_rows) == total


def test_willoughby_2024_vote_rows_record_elected_candidates_only() -> None:
    rows = read_csv(VOTE_ROWS_PATH)

    elected = {
        row["candidate_name"]
        for row in rows
        if row["elected_flag"] == "true" and row["ballot_line_type"] == "candidate"
    }

    assert elected == {
        "TAYLOR Tanya",
        "SAMUEL Robert",
        "ROZOS Angelo",
        "DODDS Kristina",
        "GRECO Anna",
        "ROUSSAC Georgie",
        "WRIGHT Nic",
        "MORATELLI John",
        "McCULLAGH Roy",
        "ROYDS Sarah",
        "CAMPBELL Craig",
        "CHUANG Michelle",
        "NELSON Andrew",
    }


def test_willoughby_2024_councillor_rows_preserve_atl_votes() -> None:
    rows = read_csv(VOTE_ROWS_PATH)

    councillor_rows = [row for row in rows if row["contest_type"] == "councillor"]
    atl_rows = [
        row for row in councillor_rows if row["ballot_line_type"] == "above_the_line"
    ]

    assert atl_rows
    assert all(not row["candidate_name"] for row in atl_rows)
    assert sum(int(row["first_preference_votes"]) for row in atl_rows) == 31793


def test_willoughby_2025_motion_vote_outcomes_capture_minutes_results() -> None:
    rows = read_csv(MOTION_VOTE_OUTCOMES_PATH)

    assert len(rows) == 38
    assert {row["council_slug"] for row in rows} == {"willoughby"}
    assert {row["meeting_date"] for row in rows} == {"2025-09-15"}
    assert {row["civicclerk_event_id"] for row in rows} == {"159"}
    assert {
        row["source_id"] for row in rows
    } == {"willoughby_civicclerk_motion_votes"}
    assert all(
        row["source_url"].startswith(
            "https://willoughby.civicclerk.com.au/web/Dialogs/SubDialogs/"
            "PortalMotionVotes.aspx?id="
        )
        for row in rows
    )

    result_counts: dict[str, int] = {}
    for row in rows:
        result_counts[row["vote_result"]] = result_counts.get(row["vote_result"], 0) + 1

    assert result_counts == {"Carried": 37, "Lost": 1}

    risk_policy = next(
        row for row in rows if row["agenda_object_item_id"] == "2676"
    )
    assert risk_policy["agenda_item_title"] == "5. Risk Management Policy Review"
    assert risk_policy["vote_result"] == "Carried"
    assert risk_policy["for_count"] == "12"
    assert risk_policy["against_count"] == ""

    lost_motion = next(row for row in rows if row["vote_result"] == "Lost")
    assert "Notice of Motion 40/2025" in lost_motion["agenda_item_title"]
    assert lost_motion["for_count"] == "4"
    assert lost_motion["against_count"] == "7"


def test_willoughby_2025_vote_outcomes_separate_en_bloc_from_named_votes() -> None:
    rows = read_csv(MOTION_VOTE_OUTCOMES_PATH)

    en_bloc_rows = [row for row in rows if row["action_type"] == "Resolution En Bloc"]
    named_rows = [row for row in rows if row["action_type"] != "Resolution En Bloc"]

    assert len(en_bloc_rows) == 10
    assert all(row["vote_result"] == "Carried" for row in en_bloc_rows)
    assert all(row["named_vote_available"] == "false" for row in en_bloc_rows)
    assert all(not row["for_count"] and not row["against_count"] for row in en_bloc_rows)

    assert named_rows
    assert all(row["named_vote_available"] == "true" for row in named_rows)
