"""Tests for the JSON <=> CSV Converter MCP tools."""

import json

import pytest
from deepdiff import DeepDiff

from mcp_server.tools.json_csv_converter import json_to_csv

# --- Test Data for json_to_csv --- (Remove CSV specific data)
JSON_LIST = '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]'
JSON_SINGLE_OBJECT = '{"a": 1, "b": 2}'
JSON_INCONSISTENT = '[{"a": 1}, {"b": 2}]'
JSON_EMPTY_LIST = "[]"
JSON_INVALID = '{"a": 1, '  # Invalid

EXPECTED_CSV = "a,b\r\n1,2\r\n3,4\r\n"
EXPECTED_CSV_FROM_INCONSISTENT = "a,b\r\n1,\r\n,2\r\n"
EXPECTED_CSV_FROM_SINGLE = "a,b\r\n1,2\r\n"


# --- Tests for json_to_csv --- (Keep existing json_to_csv tests)


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
