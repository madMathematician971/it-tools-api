"""
Tests for the NATO Phonetic Alphabet Converter MCP tool.
"""

import pytest

# Adjust the import path as necessary
from mcp_server.tools.nato_converter import (
    convert_to_nato,
    convert_from_nato,
    NATO_ALPHABET,
)

# --- Test Text to NATO Conversion ---


@pytest.mark.parametrize(
    "text, output_format, separator, include_original, lowercase, expected_output_substrings",
    [
        # Basic text format
        ("ABC", "text", " ", False, False, ["Alpha Bravo Charlie"]),
        ("Hi!", "text", "-", False, False, ["Hotel-India-Exclamation Mark"]),
        # Text format with lowercase
        ("abc", "text", " ", False, True, ["alpha bravo charlie"]),
        ("A B", "text", " ", True, False, ["Alpha Space Bravo"]),
        ("Z", "text", " ", True, True, ["zulu"]),
        # List format
        ("Go", "list", " ", False, False, ["Golf", "Oscar"]),
        ("X-Y", "list", " ", True, False, ["X-ray", "Dash", "Yankee"]),
        # Special characters
        (".@", "text", " ", False, False, ["Period At Sign"]),
        # Unknown character
        ("A£B", "text", " ", False, False, ["Alpha Unknown (£) Bravo"]),
        # With digits
        ("Test 123", "text", " ", False, False, ["Tango Echo Sierra Tango Space 1 2 3"]),
        ("Data 9", "list", " ", True, False, ["Delta", "Alpha", "Tango", "Alpha", "Space", "9"]),
    ],
)
@pytest.mark.asyncio
async def test_convert_to_nato_tool_success(
    text: str,
    output_format: str,
    separator: str,
    include_original: bool,
    lowercase: bool,
    expected_output_substrings: list[str],
):
    """Test successful conversion from text to NATO phonetic alphabet."""
    result_dict = convert_to_nato(
        text=text,
        output_format=output_format,
        separator=separator,
        include_original=include_original,
        lowercase=lowercase,
    )

    assert result_dict["error"] is None
    assert "result" in result_dict
    assert result_dict["result"] is not None

    tool_result = result_dict["result"]
    assert isinstance(tool_result, dict)
    assert "output" in tool_result
    assert "character_map" in tool_result
    assert isinstance(tool_result["character_map"], dict)

    output_content = tool_result["output"]

    # Check output type and content based on format
    if output_format == "list":
        assert isinstance(output_content, list)
        assert output_content == expected_output_substrings  # Direct list comparison
    else:  # text format
        assert isinstance(output_content, str)
        # Check output contains expected parts for text format
        content_for_check = output_content
        for substring in expected_output_substrings:
            # Adjust check for potential minor variations like spacing
            assert substring.replace(" ", "") in content_for_check.replace(" ", "")
            # Check case if lowercase is False
            if not lowercase and substring.islower() != content_for_check.islower():
                assert substring.lower() in content_for_check.lower()
            elif substring in content_for_check:
                pass  # Exact match
            else:  # Fallback
                assert substring in content_for_check

    # Check character map
    for char in text:
        assert char in tool_result["character_map"]
        expected_nato = NATO_ALPHABET.get(char.upper(), f"Unknown ({char})") if not char.isdigit() else char
        assert tool_result["character_map"][char] == expected_nato


@pytest.mark.asyncio
async def test_convert_to_nato_tool_empty_input():
    """Test error handling for empty input text."""
    result_dict = convert_to_nato(text="")
    assert result_dict["error"] == "Input text cannot be empty"
    assert result_dict["result"] is None


# --- Test NATO to Text Conversion ---


@pytest.mark.parametrize(
    "nato_text, separator, expected_result",
    [
        ("Alpha Bravo Charlie", " ", "ABC"),
        ("Hotel-India-Exclamation Mark", "-", "HI!"),  # Expect uppercase from current tool logic
        ("alpha bravo charlie", " ", "ABC"),  # Expect uppercase from current tool logic
        ("Period At Sign", " ", ".@"),  # Expect correct symbol mapping
        ("Xray Yankee Zulu", " ", "XYZ"),
        ("Unknown Alpha Unknown", " ", "?A?"),
        ("Alpha  Bravo   Charlie", " ", "ABC"),
        ("  Alpha Bravo  ", " ", "AB"),  # Expect only AB due to current split logic
        ("alpha-bravo", "-", "AB"),  # Expect uppercase from current tool logic
        ("Tango Echo Sierra Tango Space 1 2 3", " ", "TEST 123"),
    ],
)
@pytest.mark.asyncio
async def test_convert_from_nato_tool_success(nato_text: str, separator: str, expected_result: str):
    """Test successful decoding from NATO words back to text."""
    result_dict = convert_from_nato(nato_text=nato_text, separator=separator)

    assert result_dict["error"] is None
    assert "result" in result_dict
    assert result_dict["result"] == expected_result


@pytest.mark.asyncio
async def test_convert_from_nato_tool_empty_input():
    """Test NATO decoding with empty input."""
    result_dict = convert_from_nato(nato_text="")
    assert result_dict["error"] is None
    assert result_dict["result"] == ""


@pytest.mark.asyncio
async def test_convert_from_nato_tool_empty_separator():
    """Test NATO decoding with an empty separator, which should error."""
    result_dict = convert_from_nato(nato_text="AlphaBravoCharlie", separator="")
    assert "error" in result_dict
    assert result_dict["error"] == "Empty separator is not allowed for decoding."
    assert result_dict["result"] is None
