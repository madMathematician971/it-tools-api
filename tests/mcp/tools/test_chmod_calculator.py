"""
Tests for the Chmod Calculator tool.
"""

import pytest

from mcp_server.tools.chmod_calculator import calculate_numeric_chmod, calculate_symbolic_chmod

# Test cases for numeric calculation: (owner_perms, group_perms, other_perms, expected_numeric)
# Perms format: (read, write, execute)
TEST_CASES_NUMERIC = [
    ((True, True, True), (True, True, True), (True, True, True), "777"),  # rwxrwxrwx
    ((True, True, False), (True, False, True), (True, False, False), "654"),  # rw-r-xr--
    ((True, False, False), (False, False, False), (False, False, False), "400"),  # r--------
    ((False, True, False), (False, True, False), (False, True, False), "222"),  # -w--w--w-
    ((False, False, True), (False, False, True), (False, False, True), "111"),  # --x--x--x
    ((False, False, False), (False, False, False), (False, False, False), "000"),  # ---------
    ((True, True, True), (False, False, False), (False, False, False), "700"),  # rwx------
]


@pytest.mark.parametrize("owner, group, others, expected", TEST_CASES_NUMERIC)
def test_calculate_numeric_chmod_success(owner, group, others, expected):
    """Test successful calculation of numeric chmod values."""
    result = calculate_numeric_chmod(
        owner_read=owner[0],
        owner_write=owner[1],
        owner_execute=owner[2],
        group_read=group[0],
        group_write=group[1],
        group_execute=group[2],
        others_read=others[0],
        others_write=others[1],
        others_execute=others[2],
    )
    assert result["error"] is None, f"Expected no error, but got: {result['error']}"
    assert result["numeric_chmod"] == expected


# Test cases for symbolic calculation: (input_numeric, expected_symbolic)
TEST_CASES_SYMBOLIC = [
    ("777", "rwxrwxrwx"),
    ("654", "rw-r-xr--"),
    ("400", "r--------"),
    ("222", "-w--w--w-"),
    ("111", "--x--x--x"),
    ("000", "---------"),
    ("700", "rwx------"),
    ("0755", "rwxr-xr-x"),  # Test with leading zero
    (" 755 ", "rwxr-xr-x"),  # Test with whitespace
    ("5", "------r-x"),  # Test single digit expansion (applies to others)
    ("0", "---------"),  # Test single digit 0 expansion
]


@pytest.mark.parametrize("numeric_input, expected_symbolic", TEST_CASES_SYMBOLIC)
def test_calculate_symbolic_chmod_success(numeric_input, expected_symbolic):
    """Test successful calculation of symbolic chmod values."""
    result = calculate_symbolic_chmod(numeric_chmod_string=numeric_input)
    assert result["error"] is None, f"Expected no error for input '{numeric_input}', but got: {result['error']}"
    assert result["symbolic_chmod"] == expected_symbolic


# Test cases for symbolic calculation errors: (input_numeric, expected_error_part)
TEST_CASES_SYMBOLIC_ERROR = [
    ("", "Numeric value must resolve to 3 digits"),  # Empty string
    ("abc", "Numeric value must resolve to 3 digits"),  # Non-numeric
    ("75", "Numeric value must resolve to 3 digits"),  # Too short
    ("7555", "Numeric value must resolve to 3 digits"),  # Too long (unless starts with 0)
    ("07555", "Numeric value must resolve to 3 digits"),  # Too long even with leading 0
    ("800", "Each digit must be between 0 and 7"),  # Invalid digit
    ("780", "Each digit must be between 0 and 7"),  # Invalid digit
    ("758", "Each digit must be between 0 and 7"),  # Invalid digit
    ("10", "Numeric value must resolve to 3 digits"),  # Invalid 2-digit number
    ("8", "Each digit must be between 0 and 7"),  # Invalid single digit > 7
]


@pytest.mark.parametrize("numeric_input, error_part", TEST_CASES_SYMBOLIC_ERROR)
def test_calculate_symbolic_chmod_error(numeric_input, error_part):
    """Test error handling for invalid numeric inputs in symbolic calculation."""
    result = calculate_symbolic_chmod(numeric_chmod_string=numeric_input)
    assert result["error"] is not None, f"Expected an error for input '{numeric_input}', but got None."
    assert result["symbolic_chmod"] == ""
    assert error_part in result["error"]
