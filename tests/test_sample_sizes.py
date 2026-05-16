import pytest

from aus_personas.sample_sizes import (
    DEFAULT_SAMPLE_PRESET,
    DEFAULT_SAMPLE_SIZE,
    HUGE_SAMPLE,
    LARGE_SAMPLE,
    MEDIUM_SAMPLE,
    SAMPLE_SIZE_PRESETS,
    SMALLEST_SAMPLE,
    SMALL_SAMPLE,
    resolve_sample_size,
)


def test_declares_expected_sample_size_presets():
    assert SMALLEST_SAMPLE == 10_000
    assert SMALL_SAMPLE == 50_000
    assert MEDIUM_SAMPLE == 100_000
    assert LARGE_SAMPLE == 500_000
    assert HUGE_SAMPLE == 1_000_000
    assert SAMPLE_SIZE_PRESETS == {
        "smallest": 10_000,
        "small": 50_000,
        "medium": 100_000,
        "large": 500_000,
        "huge": 1_000_000,
    }


def test_defaults_to_smallest_sample():
    assert DEFAULT_SAMPLE_PRESET == "smallest"
    assert DEFAULT_SAMPLE_SIZE == 10_000
    assert resolve_sample_size() == 10_000


def test_resolves_sample_size_case_insensitively():
    assert resolve_sample_size("SMALLEST") == 10_000
    assert resolve_sample_size("small") == 50_000


def test_rejects_unknown_sample_preset():
    with pytest.raises(ValueError, match="Unknown sample preset"):
        resolve_sample_size("tiny")
