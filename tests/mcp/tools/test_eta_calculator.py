"""Tests for the ETA calculator tool using pytest."""

import pytest

from mcp_server.tools.eta_calculator import calculate_eta


@pytest.mark.parametrize(
    "start_iso, duration_sec, expected_start, expected_end, expected_error",
    [
        # Basic UTC
        ("2023-10-27T10:00:00Z", 3600, "2023-10-27T10:00:00+00:00", "2023-10-27T11:00:00+00:00", None),
        # Basic Offset
        ("2023-10-27T12:00:00+02:00", 7200, "2023-10-27T12:00:00+02:00", "2023-10-27T14:00:00+02:00", None),
        # Zero duration
        ("2024-01-01T00:00:00Z", 0, "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00", None),
        # Naive datetime (should assume UTC)
        ("2023-11-15T15:30:00", 60, "2023-11-15T15:30:00+00:00", "2023-11-15T15:31:00+00:00", None),
        # Large duration
        ("2023-01-01T00:00:00Z", 86400 * 3, "2023-01-01T00:00:00+00:00", "2023-01-04T00:00:00+00:00", None),
        # Invalid ISO format
        ("27 Oct 2023 10:00", 60, None, None, "Invalid start_time_iso format"),
        # Negative duration
        ("2023-10-27T10:00:00Z", -60, None, None, "Duration must be non-negative"),
    ],
)
def test_calculate_eta(start_iso, duration_sec, expected_start, expected_end, expected_error, caplog):
    """Parametrized test for ETA calculation scenarios."""
    result = calculate_eta(start_time_iso=start_iso, duration_seconds=duration_sec)

    assert result.get("start_time") == expected_start
    assert result.get("duration_seconds") == duration_sec
    assert result.get("end_time") == expected_end

    if expected_error:
        assert result.get("error") is not None
        assert expected_error in result.get("error")
    else:
        assert result.get("error") is None

    # Check for warning log when naive datetime is provided
    if "T" in start_iso and ("Z" not in start_iso and "+" not in start_iso and "-" not in start_iso.split("T")[-1]):
        assert f"Input start_time '{start_iso}' lacks timezone info. Assuming UTC." in caplog.text
    else:
        # Ensure no warning was logged unnecessarily
        if result.get("error") is None:  # Only check logs if the call didn't fail early
            assert f"Input start_time '{start_iso}' lacks timezone info. Assuming UTC." not in caplog.text
