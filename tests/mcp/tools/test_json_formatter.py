"""
Unit tests for the json_formatter tools.
"""

import json

from mcp_server.tools.json_formatter import format_json, minify_json

# --- Test JSON Formatting Successful Cases ---


def test_format_json_simple():
    """Test formatting a simple JSON object."""
    json_string = '{"name":"John","age":30}'
    result = format_json(json_string=json_string)

    # Parse the result and original to compare
    parsed_result = json.loads(result["result_string"])
    parsed_original = json.loads(json_string)

    # Verify the content is the same
    assert parsed_result == parsed_original
    # Verify formatting was applied (newlines and spaces)
    assert "\n" in result["result_string"]
    assert result["error"] is None


def test_format_json_with_indent():
    """Test formatting JSON with custom indentation."""
    json_string = '{"name":"John","age":30}'

    # Test with different indent values
    result2 = format_json(json_string=json_string, indent=2)
    result8 = format_json(json_string=json_string, indent=8)

    # Count spaces in the indented output
    # The second line should start with indent spaces
    second_line_spaces_count2 = len(result2["result_string"].split("\n")[1]) - len(
        result2["result_string"].split("\n")[1].lstrip()
    )
    second_line_spaces_count8 = len(result8["result_string"].split("\n")[1]) - len(
        result8["result_string"].split("\n")[1].lstrip()
    )

    assert second_line_spaces_count2 == 2
    assert second_line_spaces_count8 == 8


def test_format_json_with_sort_keys():
    """Test formatting JSON with sorted keys."""
    # Create a JSON string with keys in non-alphabetical order
    json_string = '{"c": 3, "a": 1, "b": 2}'

    # Format with sorted keys
    result = format_json(json_string=json_string, sort_keys=True)

    # The keys should be ordered alphabetically in the output
    lines = result["result_string"].split("\n")
    # First line is {, last line is }, content is in between
    content_lines = lines[1:-1]

    # Extract keys from the content lines
    keys = [line.strip().split(":")[0].strip('"') for line in content_lines]
    assert keys == ["a", "b", "c"]  # Keys should be alphabetically sorted


def test_format_json_nested():
    """Test formatting a complex nested JSON object."""
    json_string = '{"person":{"name":"John","age":30,"address":{"street":"123 Main St","city":"New York"}}}'
    result = format_json(json_string=json_string)

    # Verify content preservation
    parsed_result = json.loads(result["result_string"])
    parsed_original = json.loads(json_string)
    assert parsed_result == parsed_original

    # Verify structure (should have multiple indentation levels)
    lines = result["result_string"].split("\n")
    assert len(lines) > 5  # Should have multiple lines

    # Different lines should have different indentation levels
    indentation_levels = set(len(line) - len(line.lstrip()) for line in lines if line.strip())
    assert len(indentation_levels) > 1  # Should have more than one indentation level


# --- Test JSON Minification Successful Cases ---


def test_minify_json_simple():
    """Test minifying a simple JSON object."""
    # Create a formatted JSON string
    formatted_json = """
    {
        "name": "John",
        "age": 30
    }
    """

    result = minify_json(json_string=formatted_json)

    # Verify content preservation
    assert json.loads(result["result_string"]) == json.loads(formatted_json)

    # Verify minification (no newlines or extra spaces)
    assert "\n" not in result["result_string"]
    assert "\t" not in result["result_string"]
    assert " " not in result["result_string"]
    assert result["error"] is None


def test_minify_json_complex():
    """Test minifying a complex nested JSON object."""
    # Create a formatted complex JSON string
    formatted_json = """
    {
        "person": {
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "New York"
            }
        }
    }
    """

    result = minify_json(json_string=formatted_json)

    # Verify content preservation
    assert json.loads(result["result_string"]) == json.loads(formatted_json)

    # Verify minification
    assert "\n" not in result["result_string"]
    assert "\t" not in result["result_string"]
    result_tmp_spaces = result["result_string"].replace("123 Main St", "address").replace("New York", "NY")
    assert " " not in result_tmp_spaces
    assert result["error"] is None


# --- Test Error Cases ---


def test_format_json_invalid_json():
    """Test formatting an invalid JSON string."""
    invalid_json = '{"name":"John", "age":30'  # Missing closing brace

    result = format_json(json_string=invalid_json)

    assert result["result_string"] == ""
    assert result["error"] is not None
    assert "Invalid JSON input" in result["error"]


def test_minify_json_invalid_json():
    """Test minifying an invalid JSON string."""
    invalid_json = '{"name":"John" "age":30}'  # Missing comma

    result = minify_json(json_string=invalid_json)

    assert result["result_string"] == ""
    assert result["error"] is not None
    assert "Invalid JSON input" in result["error"]


# --- Test Edge Cases ---


def test_format_json_empty_object():
    """Test formatting an empty JSON object."""
    json_string = "{}"

    result = format_json(json_string=json_string)

    assert result["result_string"] == "{}"  # Empty object formatted as {}
    assert result["error"] is None


def test_format_json_empty_array():
    """Test formatting an empty JSON array."""
    json_string = "[]"

    result = format_json(json_string=json_string)

    assert result["result_string"] == "[]"  # Empty array formatted as []
    assert result["error"] is None


def test_format_json_with_unicode():
    """Test formatting JSON with Unicode characters."""
    json_string = '{"name":"你好"}'

    result = format_json(json_string=json_string)

    # Verify content preservation with Unicode
    assert json.loads(result["result_string"]) == {"name": "你好"}
    assert result["error"] is None


def test_minify_json_already_minified():
    """Test minifying an already minified JSON string."""
    json_string = '{"name":"John","age":30}'

    result = minify_json(json_string=json_string)

    # Result should be the same as input (already minified)
    assert result["result_string"] == json_string
    assert result["error"] is None
