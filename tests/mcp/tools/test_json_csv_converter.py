"""Tests for the JSON <=> CSV Converter MCP tools."""

import json
import logging  # Add logging
from pathlib import Path  # Add Path

import pytest
from deepdiff import DeepDiff

from mcp_server.tools.json_csv_converter import csv_to_json, json_to_csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for test data files
TEST_DATA_DIR = Path(__file__).parent / "test_data"


# Helper to read test file content
def read_test_file(filename: str) -> str:
    try:
        return (TEST_DATA_DIR / filename).read_text()
    except FileNotFoundError:
        logger.error(f"Test data file not found: {TEST_DATA_DIR / filename}")
        return ""
    except Exception as e:
        logger.error(f"Error reading test file {filename}: {e}")
        return ""


# --- Test Data for json_to_csv --- (Remove CSV specific data)
JSON_LIST = '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]'
JSON_SINGLE_OBJECT = '{"a": 1, "b": 2}'
JSON_INCONSISTENT = '[{"a": 1}, {"b": 2}]'
JSON_EMPTY_LIST = "[]"
JSON_INVALID = '{"a": 1, '  # Invalid

EXPECTED_CSV = "a,b\r\n1,2\r\n3,4\r\n"
EXPECTED_CSV_FROM_INCONSISTENT = "a,b\r\n1,\r\n,2\r\n"
EXPECTED_CSV_FROM_SINGLE = "a,b\r\n1,2\r\n"

# --- Expected JSON Outputs for csv_to_json tests ---
EXPECTED_JSON_VALID = json.dumps(
    [
        {"id": "1", "name": "Alice", "city": "New York"},
        {"id": "2", "name": "Bob", "city": "London"},
        {"id": "3", "name": "Charlie", "city": "Paris"},
    ],
    indent=2,
)
EXPECTED_JSON_WHITESPACE_TRIMMED = json.dumps(
    [
        {"id": "1", "name": "Alice", "city": "New York"},
        {"id": "2", "name": "Bob", "city": "London"},
        {"id": "3", "name": "Charlie", "city": "Paris"},
    ],
    indent=2,
)  # Expect keys and values trimmed
EXPECTED_JSON_SEMICOLON = json.dumps(
    [{"id": "1", "name": "Alice", "city": "New York"}, {"id": "2", "name": "Bob", "city": "London"}], indent=2
)
EXPECTED_JSON_EMPTY = "[]"

# Expected output for malformed cases (when not erroring)
EXPECTED_JSON_MALFORMED_ROWS = json.dumps(
    [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}, {"id": "3", "name": "Charlie"}], indent=2
)  # DictReader ignores extra data in row
EXPECTED_JSON_MALFORMED_HEADER = json.dumps([{"id": "1", 'name"invalid"': "Alice", "city": "Test"}], indent=2)
EXPECTED_JSON_WRONG_DELIMITER = json.dumps(
    [{"id,name,city": "1,Alice,New York"}, {"id,name,city": "2,Bob,London"}, {"id,name,city": "3,Charlie,Paris"}],
    indent=2,
)


# Helper to compare JSON list of dicts (Keep as is)
def compare_json_list_of_dicts(json_str1: str, json_str2: str) -> bool:
    """Compare two JSON strings representing lists of dictionaries, ignoring order and types."""
    try:
        list1 = json.loads(json_str1)
        list2 = json.loads(json_str2)
        diff = DeepDiff(
            list1,
            list2,
            ignore_order=True,
            ignore_numeric_type_changes=True,
            ignore_string_type_changes=True,
            report_repetition=True,
            verbose_level=0,
        )
        return not diff
    except Exception:
        return False


# Tests for json_to_csv


def test_json_to_csv_valid_list():
    result = json_to_csv(json_string=JSON_LIST)
    assert result["error"] is None
    assert result["result_csv"] == EXPECTED_CSV


def test_json_to_csv_single_object():
    result = json_to_csv(json_string=JSON_SINGLE_OBJECT)
    assert result["error"] is None
    assert result["result_csv"] == EXPECTED_CSV_FROM_SINGLE


def test_json_to_csv_inconsistent_keys():
    result = json_to_csv(json_string=JSON_INCONSISTENT)
    assert result["error"] is None
    assert result["result_csv"] == EXPECTED_CSV_FROM_INCONSISTENT


def test_json_to_csv_empty_list():
    result = json_to_csv(json_string=JSON_EMPTY_LIST)
    assert result["error"] == "Input JSON array cannot be empty."
    assert result["result_csv"] == ""


def test_json_to_csv_not_list_or_dict():
    result = json_to_csv(json_string='"just a string"')
    assert result["error"] == "Input JSON must be an array/list of objects or a single object."
    assert result["result_csv"] == ""


def test_json_to_csv_list_not_objects():
    result = json_to_csv(json_string="[1, 2, 3]")
    assert result["error"] == "Each item in the JSON array must be an object."
    assert result["result_csv"] == ""


def test_json_to_csv_invalid_json():
    result = json_to_csv(json_string=JSON_INVALID)
    assert result["error"] is not None
    assert "Invalid JSON input" in result["error"]
    assert result["result_csv"] == ""


def test_json_to_csv_custom_delimiter():
    result = json_to_csv(json_string=JSON_LIST, delimiter=";")
    assert result["error"] is None
    assert result["result_csv"] == "a;b\r\n1;2\r\n3;4\r\n"


# Tests for csv_to_json using files


@pytest.mark.parametrize(
    "filename, delimiter, expected_json",
    [
        ("valid.csv", ",", EXPECTED_JSON_VALID),
        ("whitespace.csv", ",", EXPECTED_JSON_WHITESPACE_TRIMMED),
        ("semicolon.csv", ";", EXPECTED_JSON_SEMICOLON),
        ("header_only.csv", ",", EXPECTED_JSON_EMPTY),
        ("empty.csv", ",", EXPECTED_JSON_EMPTY),
        ("malformed_rows.csv", ",", EXPECTED_JSON_MALFORMED_ROWS),
        ("malformed_header.csv", ",", EXPECTED_JSON_MALFORMED_HEADER),
        ("valid.csv", ";", EXPECTED_JSON_WRONG_DELIMITER),
    ],
)
def test_csv_to_json_file_processing(filename, delimiter, expected_json):
    """Test CSV to JSON conversions reading from files, accepting DictReader's default behavior."""
    csv_content = read_test_file(filename)
    assert csv_content is not None, f"Failed to read test file {filename}"
    result = csv_to_json(csv_string=csv_content, delimiter=delimiter)
    assert result["error"] is None, f"File {filename}: Expected no error, but got: {result['error']}"
    assert compare_json_list_of_dicts(
        result["result_json"], expected_json
    ), f"File {filename}: JSON output mismatch.\nExpected:\n{expected_json}\nGot:\n{result['result_json']}"
