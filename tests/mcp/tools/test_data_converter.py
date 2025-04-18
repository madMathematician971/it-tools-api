"""
Tests for the MCP data converter tool.
"""

import json

import pytest
import toml
import xmltodict
import yaml
from deepdiff import DeepDiff

# Import the tool function and Enum
from mcp_server.tools.data_converter import DataType, convert_data

# --- Test Data (Modified for TOML homogeneity and XML type parsing) ---

# Sample data structures using strings for items to ensure TOML compatibility
SAMPLE_DICT = {"name": "Test", "value": 123, "enabled": True, "items": ["1", "a", "None"]}
SAMPLE_DICT_XML_INPUT = {
    "name": "Test",
    "value": "123",
    "enabled": "true",
    "items": ["1", "a", "None"],
}  # Values parsed as strings from XML
SAMPLE_LIST = ["1", "two", '{"three": "3"}', "false"]  # Use strings for TOML compatibility

# Representations of SAMPLE_DICT
SAMPLE_JSON = json.dumps(SAMPLE_DICT, indent=2)
SAMPLE_YAML = yaml.dump(SAMPLE_DICT, allow_unicode=True, default_flow_style=False)
SAMPLE_TOML = toml.dumps(SAMPLE_DICT)  # Now homogeneous
SAMPLE_XML = xmltodict.unparse({"root": SAMPLE_DICT}, pretty=True)  # Wrap in root for XML

# Expected output strings when INPUT is XML (values become strings during parse)
EXPECTED_JSON_FROM_XML = json.dumps(SAMPLE_DICT_XML_INPUT, indent=2)
EXPECTED_YAML_FROM_XML = yaml.dump(SAMPLE_DICT_XML_INPUT, allow_unicode=True, default_flow_style=False)
EXPECTED_TOML_FROM_XML = toml.dumps(SAMPLE_DICT_XML_INPUT)

# Representations of SAMPLE_LIST
LIST_JSON = json.dumps(SAMPLE_LIST, indent=2)
LIST_YAML = yaml.dump(SAMPLE_LIST, allow_unicode=True, default_flow_style=False)
LIST_XML = xmltodict.unparse({"root": {"item": SAMPLE_LIST}}, pretty=True)  # Wrap list items

# --- Comparison Helper ---


def compare_data(str1: str, type1: DataType, str2: str, type2: DataType) -> bool:
    """Helper to compare data structures, ignoring formatting differences."""
    try:
        if type1 == DataType.xml or type2 == DataType.xml:
            # process_types=True seems unsupported by parse, remove it.
            data1 = xmltodict.parse(str1, attr_prefix="", cdata_key="text")
            data2 = xmltodict.parse(str2, attr_prefix="", cdata_key="text")
            # Use DeepDiff for structural comparison after parsing
            # Re-enable type ignoring since XML parsing results in strings
            diff = DeepDiff(data1, data2, ignore_type_in_groups=[(str, int, float, bool)])
            return not diff
        else:
            # For JSON, YAML, TOML, load and compare Python objects
            parsers = {DataType.json: json.loads, DataType.yaml: yaml.safe_load, DataType.toml: toml.loads}
            data1 = parsers[type1](str1)
            data2 = parsers[type2](str2)
            diff = DeepDiff(data1, data2, ignore_type_in_groups=[(str, int, float, bool)])
            return not diff  # No diff means they are equivalent
    except Exception as e:
        print(f"Comparison error ({type1} vs {type2}): {e}")
        return False


# --- Test Cases ---

SUCCESS_TEST_CASES = [
    # --- Dictionary Conversions ---
    # JSON -> Others
    (SAMPLE_JSON, DataType.json, DataType.yaml, SAMPLE_YAML),
    (SAMPLE_JSON, DataType.json, DataType.toml, SAMPLE_TOML),
    (SAMPLE_JSON, DataType.json, DataType.xml, SAMPLE_XML),
    # YAML -> Others
    (SAMPLE_YAML, DataType.yaml, DataType.json, SAMPLE_JSON),
    (SAMPLE_YAML, DataType.yaml, DataType.toml, SAMPLE_TOML),
    (SAMPLE_YAML, DataType.yaml, DataType.xml, SAMPLE_XML),
    # TOML -> Others
    (SAMPLE_TOML, DataType.toml, DataType.json, SAMPLE_JSON),
    (SAMPLE_TOML, DataType.toml, DataType.yaml, SAMPLE_YAML),
    (SAMPLE_TOML, DataType.toml, DataType.xml, SAMPLE_XML),
    # XML -> Others (Note: XML structure might differ slightly on round trip)
    (SAMPLE_XML, DataType.xml, DataType.json, EXPECTED_JSON_FROM_XML),
    (SAMPLE_XML, DataType.xml, DataType.yaml, EXPECTED_YAML_FROM_XML),
    (SAMPLE_XML, DataType.xml, DataType.toml, EXPECTED_TOML_FROM_XML),
    # --- List Conversions (excluding TOML output) ---
    (LIST_JSON, DataType.json, DataType.yaml, LIST_YAML),
    (LIST_JSON, DataType.json, DataType.xml, LIST_XML),
    (LIST_YAML, DataType.yaml, DataType.json, LIST_JSON),
    (LIST_YAML, DataType.yaml, DataType.xml, LIST_XML),
    (LIST_XML, DataType.xml, DataType.json, LIST_JSON),
    (LIST_XML, DataType.xml, DataType.yaml, LIST_YAML),
    # Same type conversion (should return input)
    (SAMPLE_JSON, DataType.json, DataType.json, SAMPLE_JSON),
    (SAMPLE_YAML, DataType.yaml, DataType.yaml, SAMPLE_YAML),
    (SAMPLE_TOML, DataType.toml, DataType.toml, SAMPLE_TOML),
    (SAMPLE_XML, DataType.xml, DataType.xml, SAMPLE_XML),
]

ERROR_TEST_CASES = [
    # Invalid input formats
    ('{"invalid json', DataType.json, DataType.yaml, "Invalid JSON input"),
    ("key: value: another", DataType.yaml, DataType.json, "Invalid YAML input"),
    # Using yet another invalid TOML
    ('key = "value', DataType.toml, DataType.json, "Invalid TOML input: Unterminated string"),  # Missing closing quote
    ("<root><unclosed></root>", DataType.xml, DataType.json, "Invalid XML input: mismatched tag"),  # Unclosed tag
    # Invalid output conversions (list to TOML)
    (LIST_JSON, DataType.json, DataType.toml, "TOML output requires a dictionary structure"),
    (LIST_YAML, DataType.yaml, DataType.toml, "TOML output requires a dictionary structure"),
    # Input/Output type errors
    (SAMPLE_JSON, "invalid", DataType.json, "Invalid input or output type"),
    (SAMPLE_JSON, DataType.json, "invalid", "Invalid input or output type"),
    # Empty input
    ("", DataType.json, DataType.yaml, "Input string cannot be empty"),
    ("   \n ", DataType.yaml, DataType.json, "Input string cannot be empty"),
]


@pytest.mark.parametrize("input_string, input_type, output_type, expected_output_string", SUCCESS_TEST_CASES)
def test_convert_data_success(
    input_string: str, input_type: DataType, output_type: DataType, expected_output_string: str
):
    """Test successful data format conversions using the MCP tool."""
    input_type_val = input_type.value if isinstance(input_type, DataType) else input_type
    output_type_val = output_type.value if isinstance(output_type, DataType) else output_type

    result = convert_data(input_string=input_string, input_type=input_type_val, output_type=output_type_val)

    assert result["error"] is None, f"Conversion failed unexpectedly: {result['error']}"
    assert result["output_string"] is not None

    # Use the comparison helper to check structural equality
    assert compare_data(
        result["output_string"], output_type, expected_output_string, output_type
    ), f"Data mismatch after {input_type_val} -> {output_type_val} conversion:\nInput:\n{input_string}\nOutput:\n{result['output_string']}\nExpected:\n{expected_output_string}"


@pytest.mark.parametrize("input_string, input_type, output_type, error_substring", ERROR_TEST_CASES)
def test_convert_data_errors(input_string: str, input_type: str, output_type: str, error_substring: str):
    """Test data conversions that should result in an error."""
    input_type_val = input_type.value if isinstance(input_type, DataType) else input_type
    output_type_val = output_type.value if isinstance(output_type, DataType) else output_type

    result = convert_data(input_string=input_string, input_type=input_type_val, output_type=output_type_val)

    assert result["output_string"] is None
    assert result["error"] is not None, f"Expected an error containing '{error_substring}' but got no error."
    assert error_substring in result["error"], f"Expected error '{result['error']}' to contain '{error_substring}'"


# Specific test for JSON null -> TOML conversion
def test_convert_json_null_to_toml_output():
    """Test converting JSON null to TOML. Expects empty string based on router test."""
    # Use a dictionary that TOML won't just omit entirely
    input_string = json.dumps({"a": None, "b": "value"})
    result = convert_data(input_string=input_string, input_type=DataType.json.value, output_type=DataType.toml.value)

    assert result["error"] is None, f"Conversion failed unexpectedly: {result['error']}"
    # Check that 'a' is omitted but 'b' is present
    expected_output = 'b = "value"\n'
    assert result["output_string"] == expected_output, f"Expected TOML to omit null key, got: {result['output_string']}"
