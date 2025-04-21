"""
Unit tests for the json_diff tool.
"""

import json

import pytest

from mcp_server.tools.json_diff import json_diff

# --- Test Successful JSON Diff Cases ---


def test_json_diff_identical():
    """Test diffing two identical JSON objects."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John","age":30}'

    result = json_diff(json1=json1, json2=json2)

    # Should be no differences
    assert result["diff"] is not None
    assert result["format_used"] == "delta"
    assert result["error"] is None

    # For identical objects, the diff should be empty
    # The structure depends on the library, but it should be equivalent to an empty dict/object
    # We need to parse it since it's a JSON string
    diff_content = json.loads(result["diff"])
    assert not diff_content  # Empty dict/object evaluates to False in Python


def test_json_diff_added_field():
    """Test diffing JSON objects where a field was added."""
    json1 = '{"name":"John"}'
    json2 = '{"name":"John","age":30}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None
    assert result["format_used"] == "delta"

    # Parse the diff to check for the added field
    diff_content = json.loads(result["diff"])

    # Check for the added field in the diff
    assert "dictionary_item_added" in diff_content
    # The exact path format depends on the library, but should contain 'age'
    added_paths = diff_content["dictionary_item_added"]
    assert any("age" in path for path in added_paths)


def test_json_diff_removed_field():
    """Test diffing JSON objects where a field was removed."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John"}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # Parse the diff to check for the removed field
    diff_content = json.loads(result["diff"])

    # Check for the removed field in the diff
    assert "dictionary_item_removed" in diff_content
    # The exact path format depends on the library, but should contain 'age'
    removed_paths = diff_content["dictionary_item_removed"]
    assert any("age" in path for path in removed_paths)


def test_json_diff_changed_value():
    """Test diffing JSON objects where a value was changed."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John","age":31}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # Parse the diff to check for the changed value
    diff_content = json.loads(result["diff"])

    # Check for the changed value in the diff
    assert "values_changed" in diff_content
    # The values_changed section should show the old and new values
    assert "30" in str(diff_content["values_changed"])
    assert "31" in str(diff_content["values_changed"])


def test_json_diff_nested_changes():
    """Test diffing JSON objects with nested structure changes."""
    json1 = '{"person":{"name":"John","age":30}}'
    json2 = '{"person":{"name":"Jane","age":30}}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # Parse the diff to check for the nested change
    diff_content = json.loads(result["diff"])

    # Check for the changed name in the nested structure
    assert "values_changed" in diff_content
    # The path should include the nested structure
    assert "person" in str(diff_content["values_changed"])
    assert "John" in str(diff_content["values_changed"])
    assert "Jane" in str(diff_content["values_changed"])


def test_json_diff_array_changes():
    """Test diffing JSON objects with array changes."""
    json1 = '{"numbers":[1,2,3]}'
    json2 = '{"numbers":[1,2,4]}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # Parse the diff to check for the array change
    diff_content = json.loads(result["diff"])

    # Check for the array change in the diff
    assert "values_changed" in diff_content
    # The change should show the value transition from 3 to 4
    assert "3" in str(diff_content["values_changed"])
    assert "4" in str(diff_content["values_changed"])


def test_json_diff_ignore_order():
    """Test diffing JSON arrays with ignore_order option."""
    # These arrays have the same elements but in different order
    json1 = '{"numbers":[1,2,3]}'
    json2 = '{"numbers":[3,1,2]}'

    # With ignore_order=False (default), they should be considered different
    result_sensitive = json_diff(json1=json1, json2=json2, ignore_order=False)

    # With ignore_order=True, they should be considered the same
    result_ignored = json_diff(json1=json1, json2=json2, ignore_order=True)

    assert result_sensitive["error"] is None
    assert result_ignored["error"] is None

    # When order matters, there should be differences
    diff_sensitive = json.loads(result_sensitive["diff"])

    # When order is ignored, there should be no differences
    diff_ignored = json.loads(result_ignored["diff"])

    assert diff_sensitive  # Not empty, there are differences
    assert not diff_ignored  # Empty, no differences


def test_json_diff_simple_format():
    """Test diffing JSON objects with 'simple' output format."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John","age":31}'

    result = json_diff(json1=json1, json2=json2, output_format="simple")

    assert result["error"] is None
    assert result["format_used"] == "simple"

    # The simple format should be a string, not a JSON object
    # It shouldn't be parseable as JSON (it's a human-readable format)
    assert isinstance(result["diff"], str)
    with pytest.raises(json.JSONDecodeError):
        json.loads(result["diff"])

    # But it should contain the changed values
    assert "30" in result["diff"]
    assert "31" in result["diff"]


# --- Test Error Cases ---


def test_json_diff_invalid_first_json():
    """Test diffing with an invalid first JSON string."""
    json1 = '{"name":"John" "age":30}'  # Missing comma
    json2 = '{"name":"John","age":31}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is not None
    assert "Invalid JSON in first input" in result["error"]
    assert result["diff"] == ""


def test_json_diff_invalid_second_json():
    """Test diffing with an invalid second JSON string."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John", "age":31'  # Missing closing brace

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is not None
    assert "Invalid JSON in second input" in result["error"]
    assert result["diff"] == ""


def test_json_diff_invalid_format():
    """Test diffing with an invalid output format."""
    json1 = '{"name":"John","age":30}'
    json2 = '{"name":"John","age":31}'

    result = json_diff(json1=json1, json2=json2, output_format="invalid")

    assert result["error"] is not None
    assert "Invalid output format" in result["error"]
    assert result["diff"] == ""


# --- Test Edge Cases ---


def test_json_diff_empty_objects():
    """Test diffing empty JSON objects."""
    json1 = "{}"
    json2 = "{}"

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None
    # Empty objects should have no differences
    diff_content = json.loads(result["diff"])
    assert not diff_content  # Empty dict/object


def test_json_diff_empty_vs_populated():
    """Test diffing an empty object with a populated one."""
    json1 = "{}"
    json2 = '{"name":"John","age":30}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # All fields in json2 should be reported as added
    diff_content = json.loads(result["diff"])
    assert "dictionary_item_added" in diff_content

    # Both name and age fields should be reported as added
    added_paths = diff_content["dictionary_item_added"]
    assert any("name" in path for path in added_paths)
    assert any("age" in path for path in added_paths)


def test_json_diff_with_unicode():
    """Test diffing JSON objects with Unicode characters."""
    json1 = '{"name":"你好"}'
    json2 = '{"name":"こんにちは"}'

    result = json_diff(json1=json1, json2=json2)

    assert result["error"] is None

    # The Unicode characters should be present in the diff
    assert "你好" in result["diff"]
    assert "こんにちは" in result["diff"]
