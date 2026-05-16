"""Named sample-size presets for synthetic persona generation."""

from __future__ import annotations

SMALLEST_SAMPLE = 10_000
SMALL_SAMPLE = 50_000
MEDIUM_SAMPLE = 100_000
LARGE_SAMPLE = 500_000
HUGE_SAMPLE = 1_000_000

DEFAULT_SAMPLE_PRESET = "smallest"
DEFAULT_SAMPLE_SIZE = SMALLEST_SAMPLE

SAMPLE_SIZE_PRESETS = {
    "smallest": SMALLEST_SAMPLE,
    "small": SMALL_SAMPLE,
    "medium": MEDIUM_SAMPLE,
    "large": LARGE_SAMPLE,
    "huge": HUGE_SAMPLE,
}


def resolve_sample_size(preset: str | None = None) -> int:
    """Return the configured sample size for a named preset."""
    preset_name = (preset or DEFAULT_SAMPLE_PRESET).strip().lower()
    try:
        return SAMPLE_SIZE_PRESETS[preset_name]
    except KeyError as exc:
        valid_presets = ", ".join(sorted(SAMPLE_SIZE_PRESETS))
        msg = f"Unknown sample preset {preset!r}. Expected one of: {valid_presets}"
        raise ValueError(msg) from exc
