"""
Tests for the Case Converter tool.
"""

import pytest

from mcp_server.tools.case_converter import SUPPORTED_CASES, convert_case

# Test cases: (input_string, target_case, expected_output)
TEST_CASES_SUCCESS = [
    # Basic conversions
    ("hello world", "camel", "helloWorld"),
    ("hello world", "snake", "hello_world"),
    ("hello world", "pascal", "HelloWorld"),
    ("hello world", "constant", "HELLO_WORLD"),
    ("hello world", "kebab", "hello-world"),
    ("hello world", "capital", "Hello World"),  # Note: caseconverter.titlecase
    ("hello world", "lower", "hello world"),
    ("hello world", "upper", "HELLO WORLD"),
    # Mixed input case
    ("Hello World 123", "snake", "hello_world_123"),
    ("someHTTPRequest", "kebab", "some-httprequest"),
    ("userID", "pascal", "UserID"),
    ("user_id", "camel", "userId"),  # Snake to Camel
    # Strings with numbers and symbols
    ("version 1.2.3", "constant", "VERSION_123"),
    ("data-value", "pascal", "DataValue"),
    # Edge cases
    ("", "camel", ""),  # Empty string
    ("single", "snake", "single"),  # Single word
    ("UPPERCASE", "lower", "uppercase"),
    ("lowercase", "upper", "LOWERCASE"),
    ("alreadyCamel", "camel", "alreadyCamel"),
    ("already_snake", "snake", "already_snake"),
]


@pytest.mark.parametrize("input_str, target, expected", TEST_CASES_SUCCESS)
def test_convert_case_success(input_str: str, target: str, expected: str):
    """Test successful case conversions for various inputs and targets."""
    result = convert_case(input_string=input_str, target_case=target)
    assert result["error"] is None, f"Expected no error for '{input_str}' -> '{target}', but got: {result['error']}"
    assert result["result"] == expected


@pytest.mark.parametrize("invalid_target_case", ["invalid", "dot", "sentence", " ", "UnknownCase"])
def test_convert_case_invalid_target(invalid_target_case: str):
    """Test conversion failure with invalid target case names."""
    input_str = "test input"
    result = convert_case(input_string=input_str, target_case=invalid_target_case)
    assert result["error"] is not None
    assert "Invalid target_case" in result["error"]
    assert result["result"] == ""
    # Check that the error message lists the supported cases
    assert str(list(SUPPORTED_CASES.keys())) in result["error"]


def test_convert_case_preserves_input_type():
    """Ensure the function expects strings and handles them appropriately."""
    # While type hints handle this, basic check
    result = convert_case(input_string="123", target_case="upper")
    assert result["error"] is None
    assert result["result"] == "123"
