"""
Unit tests for the base_converter tool.
"""

import pytest

from mcp_server.tools.base_converter import base_convert

# --- Test Base Conversion Successful Cases ---


@pytest.mark.parametrize(
    "number_string, input_base, output_base, expected_result",
    [
        ("10", 10, 2, "1010"),  # Decimal to Binary
        ("1010", 2, 10, "10"),  # Binary to Decimal
        ("FF", 16, 10, "255"),  # Hex to Decimal
        ("255", 10, 16, "ff"),  # Decimal to Hex (lowercase output)
        ("777", 8, 10, "511"),  # Octal to Decimal
        ("511", 10, 8, "777"),  # Decimal to Octal
        ("10", 10, 36, "a"),  # Decimal to Base 36
        ("a", 36, 10, "10"),  # Base 36 to Decimal
        ("z", 36, 10, "35"),  # Base 36 (max digit) to Decimal
        ("35", 10, 36, "z"),  # Decimal to Base 36 (max digit)
        ("1A", 16, 2, "11010"),  # Hex to Binary
        ("11010", 2, 16, "1a"),  # Binary to Hex
        ("0", 10, 16, "0"),  # Zero conversion
        ("-10", 10, 2, "-1010"),  # Negative Decimal to Binary
        ("-1010", 2, 10, "-10"),  # Negative Binary to Decimal
        ("-FF", 16, 10, "-255"),  # Negative Hex to Decimal
        ("-255", 10, 16, "-ff"),  # Negative Decimal to Hex
    ],
)
def test_base_convert_success(number_string, input_base, output_base, expected_result):
    """Test successful base conversions."""
    result = base_convert(number_string=number_string, input_base=input_base, output_base=output_base)

    assert result["result_string"] == expected_result
    assert result["input_number_string"] == number_string
    assert result["input_base"] == input_base
    assert result["output_base"] == output_base


# --- Test Base Conversion Error Cases ---


def test_invalid_input_base():
    """Test with invalid input base (too small)."""
    with pytest.raises(ValueError) as excinfo:
        base_convert(number_string="10", input_base=1, output_base=10)
    assert "Input base must be between 2 and 36" in str(excinfo.value)


def test_invalid_output_base():
    """Test with invalid output base (too large)."""
    with pytest.raises(ValueError) as excinfo:
        base_convert(number_string="10", input_base=10, output_base=37)
    assert "Output base must be between 2 and 36" in str(excinfo.value)


@pytest.mark.parametrize(
    "number_string, input_base, output_base, expected_error",
    [
        ("12", 2, 10, "Invalid digits for base 2 in number: 12"),  # Invalid digit for base 2
        ("G", 16, 10, "Invalid digits for base 16 in number: G"),  # Invalid hex digit
        ("", 10, 16, "Invalid digits for base 10 in number: "),  # Empty string
        ("AF.B", 16, 10, "Invalid digits for base 16 in number: AF.B"),  # Non-integer input
    ],
)
def test_invalid_number_strings(number_string, input_base, output_base, expected_error):
    """Test with invalid number strings for the given base."""
    with pytest.raises(ValueError) as excinfo:
        base_convert(number_string=number_string, input_base=input_base, output_base=output_base)
    assert expected_error in str(excinfo.value)


# --- Test Edge Cases ---


def test_int_to_base_zero():
    """Test converting zero to different bases."""
    result = base_convert(number_string="0", input_base=10, output_base=16)
    assert result["result_string"] == "0"


def test_max_digit_value():
    """Test using maximum digit value for base 36 (z = 35)."""
    result = base_convert(number_string="z", input_base=36, output_base=10)
    assert result["result_string"] == "35"


def test_case_insensitivity():
    """Test case insensitivity for input number_string."""
    # Lowercase hex
    lower_result = base_convert(number_string="ff", input_base=16, output_base=10)
    # Uppercase hex
    upper_result = base_convert(number_string="FF", input_base=16, output_base=10)
    # Should produce same result
    assert lower_result["result_string"] == upper_result["result_string"] == "255"
