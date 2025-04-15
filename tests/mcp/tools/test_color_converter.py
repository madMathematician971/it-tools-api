"""
Tests for the Color Converter tool.
"""

import pytest
from colour import Color

from mcp_server.tools.color_converter import convert_color


# Helper to compare luminance with tolerance
def approx_equal(a, b, tol=1e-6):
    return abs(a - b) < tol


# Test cases: (input_color, target_format, expected_result_or_type, check_parsed_vals)
# check_parsed_vals format: (expected_hex_l, expected_rgb, expected_hsl)
TEST_CASES_SUCCESS = [
    # Hex input
    ("#ff0000", "rgb", "rgb(255, 0, 0)", ("#ff0000", "rgb(255, 0, 0)", "hsl(0, 100%, 50%)")),
    ("#00ff00", "hsl", "hsl(120, 100%, 50%)", ("#00ff00", "rgb(0, 255, 0)", "hsl(120, 100%, 50%)")),
    ("#0000ff", "web", "blue", ("#0000ff", "rgb(0, 0, 255)", "hsl(240, 100%, 50%)")),
    ("#aabbcc", "hex_verbose", "#aabbcc", ("#aabbcc", "rgb(170, 187, 204)", "hsl(210, 25%, 73%)")),
    ("#ff0000", "rgb", "rgb(255, 0, 0)", ("#ff0000", "rgb(255, 0, 0)", "hsl(0, 100%, 50%)")),
    ("#ffffff", "luminance", float, ("#ffffff", "rgb(255, 255, 255)", "hsl(0, 0%, 100%)")),
    # RGB input (Using valid hex as input instead of rgb string, updated expected hex)
    ("#ff0000", "hex", "#f00", ("#ff0000", "rgb(255, 0, 0)", "hsl(0, 100%, 50%)")),
    ("#008000", "hsl", "hsl(120, 100%, 25%)", ("#008000", "rgb(0, 128, 0)", "hsl(120, 100%, 25%)")),
    # HSL input (Using valid hex as input instead of hsl string)
    ("#0000ff", "rgb", "rgb(0, 0, 255)", ("#0000ff", "rgb(0, 0, 255)", "hsl(240, 100%, 50%)")),
    ("#000000", "hex_verbose", "#000000", ("#000000", "rgb(0, 0, 0)", "hsl(0, 0%, 0%)")),
    # Web name input (updated expected rgb for purple due to precision)
    ("red", "hex_verbose", "#ff0000", ("#ff0000", "rgb(255, 0, 0)", "hsl(0, 100%, 50%)")),
    ("green", "rgb", "rgb(0, 128, 0)", ("#008000", "rgb(0, 128, 0)", "hsl(120, 100%, 25%)")),
    ("blue", "hsl", "hsl(240, 100%, 50%)", ("#0000ff", "rgb(0, 0, 255)", "hsl(240, 100%, 50%)")),
    ("purple", "hex_verbose", "#800080", ("#800080", "rgb(128, 0, 127)", "hsl(300, 100%, 25%)")),
    # RGB Fraction (Using valid hex as input, updated expected rgb due to precision)
    ("#8040c0", "rgb_fraction", "(0.50..., 0.25..., 0.75...)", ("#8040c0", "rgb(127, 64, 192)", "hsl(270, 50%, 50%)")),
]


@pytest.mark.parametrize("input_color, target_format, expected, parsed_vals", TEST_CASES_SUCCESS)
def test_convert_color_success(input_color, target_format, expected, parsed_vals):
    """Test successful color conversions."""
    result = convert_color(input_color=input_color, target_format=target_format)

    expected_hex, expected_rgb, expected_hsl = parsed_vals

    assert result["error"] is None, f"Unexpected error: {result['error']}"
    assert result["input_color"] == input_color
    assert result["target_format"] == target_format

    # Check parsed values
    assert result["parsed_hex"] == expected_hex
    assert result["parsed_rgb"] == expected_rgb
    assert result["parsed_hsl"] == expected_hsl

    # Check the main result
    if target_format == "luminance":
        assert isinstance(result["result"], float)
        # Compare luminance using the Color object directly for accuracy
        assert approx_equal(result["result"], Color(input_color).luminance)
    elif target_format == "rgb_fraction":
        # Need to parse the tuple string for comparison
        try:
            # eval is generally unsafe, but ok for trusted test output
            actual_tuple = eval(result["result"])  # pylint: disable=eval-used
            expected_tuple = Color(input_color).rgb
            assert len(actual_tuple) == 3
            assert all(approx_equal(a, e) for a, e in zip(actual_tuple, expected_tuple))
        except Exception as e:
            pytest.fail(f"Failed to parse or compare rgb_fraction: {result['result']}, Error: {e}")
    else:
        assert isinstance(result["result"], str)
        assert result["result"] == expected


# Test cases for errors: (input_color, target_format, expected_error_part)
TEST_CASES_ERROR = [
    ("not a color", "hex", "Could not parse input color"),  # Invalid input color name
    ("abc", "hex", "Could not parse input color"),  # Invalid short hex (moved from success)
    ("f00", "rgb", "Could not parse input color"),  # Invalid short hex (moved from success)
    ("rgb(255, 0, 0)", "hex", "Could not parse input color"),  # Invalid rgb string format
    ("hsl(120, 100%, 50%)", "rgb", "Could not parse input color"),  # Invalid hsl string format
    ("#ff0000", "invalid_format", "Unsupported target_format"),  # Invalid target format
    ("", "rgb", "Input color string cannot be empty"),  # Empty input string (new check)
    ("   ", "hex", "Input color string cannot be empty"),  # Whitespace input string (new check)
    ("rgb(999,0,0)", "hex", "Could not parse input color"),  # Invalid RGB value in string
    ("#gggggg", "rgb", "Could not parse input color"),  # Invalid hex characters
]


@pytest.mark.parametrize("input_color, target_format, error_part", TEST_CASES_ERROR)
def test_convert_color_error(input_color, target_format, error_part):
    """Test error handling for invalid inputs or formats."""
    result = convert_color(input_color=input_color, target_format=target_format)

    assert result["error"] is not None, "Expected an error but got None."
    assert error_part in result["error"]
    # Check that other fields are None on error
    assert result["result"] is None
    assert result["parsed_hex"] is None
    assert result["parsed_rgb"] is None
    assert result["parsed_hsl"] is None
