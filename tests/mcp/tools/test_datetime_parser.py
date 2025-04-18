"""
Tests for the MCP datetime parser tool.
"""

from datetime import datetime, timezone
from typing import Any

import pytest

from mcp_server.tools.datetime_parser import parse_datetime

# --- Test Data ---
NOW_DT_UTC = datetime.now(timezone.utc)
NOW_TS_S = NOW_DT_UTC.timestamp()
NOW_TS_MS = NOW_TS_S * 1000.0
NOW_ISO = NOW_DT_UTC.isoformat(timespec="microseconds").replace("+00:00", "Z")
NOW_RFC2822 = NOW_DT_UTC.strftime("%a, %d %b %Y %H:%M:%S GMT")
NOW_HUMAN = NOW_DT_UTC.strftime("%A, %B %d, %Y at %I:%M:%S %p") + " UTC"

# Test cases: (input_value, input_format, output_format, expected_result_partial, expected_parsed_iso_partial)
# Using partial checks because exact timestamp/string might vary slightly
SUCCESS_CASES: list[tuple[str | int | float, str, str, Any, str]] = [
    # Unix Seconds Input
    (NOW_TS_S, "unix_s", "unix_ms", NOW_TS_MS, NOW_ISO[:19]),  # Check timestamp ms, iso sec
    (NOW_TS_S, "unix_s", "iso8601", NOW_ISO, NOW_ISO[:19]),  # Check iso, iso sec
    (NOW_TS_S, "unix_s", "rfc2822", NOW_RFC2822[:-4], NOW_ISO[:19]),  # Check rfc prefix, iso sec
    (NOW_TS_S, "unix_s", "human_readable", "at", NOW_ISO[:19]),  # Check contains "at", iso sec
    (NOW_TS_S, "unix_s", "custom:%Y-%m-%d", NOW_ISO[:10], NOW_ISO[:19]),  # Check YMD, iso sec
    # Unix Milliseconds Input
    (NOW_TS_MS, "unix_ms", "unix_s", NOW_TS_S, NOW_ISO[:19]),
    (NOW_TS_MS, "unix_ms", "iso8601", NOW_ISO, NOW_ISO[:19]),
    # ISO8601 Input
    (NOW_ISO, "iso8601", "unix_s", NOW_TS_S, NOW_ISO[:19]),
    (NOW_ISO, "iso8601", "unix_ms", NOW_TS_MS, NOW_ISO[:19]),
    (
        "2023-10-26T12:00:00Z",
        "iso8601",
        "human_readable",
        "Thursday, October 26, 2023 at 12:00:00 PM UTC",
        "2023-10-26T12:00:00.000000Z",
    ),
    (
        "2024-01-01",
        "iso8601",
        "rfc2822",
        "Mon, 01 Jan 2024 00:00:00 GMT",
        "2024-01-01T00:00:00.000000Z",
    ),  # Date only, assume UTC
    # Auto Input - Number (Seconds)
    (NOW_TS_S, "auto", "iso8601", NOW_ISO, NOW_ISO[:19]),
    # Auto Input - Number (Milliseconds)
    (NOW_TS_MS, "auto", "unix_s", NOW_TS_S, NOW_ISO[:19]),
    # Auto Input - String (ISO)
    (NOW_ISO, "auto", "unix_ms", NOW_TS_MS, NOW_ISO[:19]),
    # Auto Input - String (Other Parsable Format)
    (
        "Oct 26 2023 2:30pm",
        "auto",
        "iso8601",
        "2023-10-26T14:30:00",
        "2023-10-26T14:30:00.000000Z",
    ),  # Assume UTC if not specified
    ("2023/12/25 08:00:00 -0500", "auto", "unix_s", 1703509200.0, "2023-12-25T13:00:00.000000Z"),
]

ERROR_CASES: list[tuple[str | int | float, str, str, str]] = [
    # Invalid Input Type for Format
    ("not a number", "unix_s", "iso8601", "unix_s input must be a number"),
    ("not a number", "unix_ms", "iso8601", "unix_ms input must be a number"),
    (12345, "iso8601", "unix_s", "iso8601 input must be a string"),
    # Invalid Input Value for Format
    ("invalid date string", "iso8601", "unix_s", "Invalid input or format: invalid literal"),
    ("invalid date string", "auto", "unix_s", "Could not automatically parse string input"),
    # Unsupported Formats
    (NOW_TS_S, "invalid_format", "iso8601", "Unsupported input_format"),
    (NOW_TS_S, "unix_s", "invalid_format", "Unsupported output_format"),
    # Invalid Custom Format
    (NOW_TS_S, "unix_s", "custom:", "Custom format pattern cannot be empty"),
    # Auto format with invalid type
    (None, "auto", "iso8601", "'auto' format requires string or numeric input"),
]


# Helper for fuzzy timestamp comparison
def approx_equal(a: int | float, b: int | float, tolerance: float = 1.0) -> bool:
    # Increase tolerance slightly for all timestamp comparisons
    return abs(float(a) - float(b)) < tolerance + 0.1


@pytest.mark.parametrize(
    "input_value, input_format, output_format, expected_result_partial, expected_parsed_iso_partial", SUCCESS_CASES
)
def test_parse_datetime_success(
    input_value: str | int | float,
    input_format: str,
    output_format: str,
    expected_result_partial: Any,
    expected_parsed_iso_partial: str,
):
    """Test successful datetime conversions."""
    result = parse_datetime(input_value=input_value, input_format=input_format, output_format=output_format)

    assert result["error"] is None, f"Expected no error, but got: {result['error']}"
    assert result["result"] is not None
    assert result["parsed_utc_iso"] is not None

    # Check parsed ISO partially
    assert expected_parsed_iso_partial in result["parsed_utc_iso"]

    # Check result based on type
    if isinstance(expected_result_partial, (int, float)):
        assert isinstance(result["result"], (int, float))
        tolerance = 10.0 if "unix_ms" in [input_format, output_format] else 1.0  # Wider tolerance for ms
        assert approx_equal(
            result["result"], expected_result_partial, tolerance=tolerance
        ), f"Timestamp mismatch: got {result['result']}, expected approx {expected_result_partial}"
    elif isinstance(expected_result_partial, str):
        assert isinstance(result["result"], str)
        assert (
            expected_result_partial in result["result"]
        ), f"String mismatch: expected partial '{expected_result_partial}' not in '{result['result']}'"


@pytest.mark.parametrize("input_value, input_format, output_format, error_substring", ERROR_CASES)
def test_parse_datetime_errors(
    input_value: str | int | float,
    input_format: str,
    output_format: str,
    error_substring: str,
):
    """Test datetime conversions that should result in an error."""
    result = parse_datetime(input_value=input_value, input_format=input_format, output_format=output_format)

    assert result["result"] is None
    assert result["parsed_utc_iso"] is None
    assert result["error"] is not None, f"Expected an error containing '{error_substring}' but got no error."
    assert error_substring in result["error"], f"Expected error '{result['error']}' to contain '{error_substring}'"
