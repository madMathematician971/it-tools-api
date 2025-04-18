"""Tests for the Lorem Ipsum Generator MCP tool."""

import pytest

from mcp_server.tools.lorem_generator import generate_lorem

# --- Test Success Cases ---


@pytest.mark.parametrize("lorem_type", ["words", "sentences", "paragraphs"])
@pytest.mark.parametrize("count", [1, 5, 10])
def test_generate_lorem_success(lorem_type, count):
    """Test successful generation for different types and counts."""
    result = generate_lorem(lorem_type=lorem_type, count=count)

    assert result["error"] is None
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0

    # Basic structural checks based on type
    text = result["text"]
    if lorem_type == "words":
        assert len(text.split()) == count
        assert "\n\n" not in text
    elif lorem_type == "sentences":
        # Check structure: non-empty, no paragraph breaks
        # Heuristics based on punctuation are unreliable with lorem-text
        assert "\n\n" not in text
        # Maybe check length is plausible for multiple sentences?
        if count > 1:
            assert len(text) > 20  # Arbitrary length check for multiple sentences
    elif lorem_type == "paragraphs":
        if count == 1:
            assert "\n\n" not in text  # Single paragraph
        else:
            assert text.count("\n\n") == count - 1


def test_generate_lorem_default_count():
    """Test generation with default count (1)."""
    result_word = generate_lorem(lorem_type="words")
    assert result_word["error"] is None
    assert len(result_word["text"].split()) == 1

    result_sent = generate_lorem(lorem_type="sentences")
    assert result_sent["error"] is None
    assert isinstance(result_sent["text"], str)
    assert len(result_sent["text"]) > 5  # Check it's not empty
    assert "\n\n" not in result_sent["text"]

    result_para = generate_lorem(lorem_type="paragraphs")
    assert result_para["error"] is None
    assert isinstance(result_para["text"], str)
    assert "\n\n" not in result_para["text"]


# --- Test Failure Cases ---


def test_generate_lorem_invalid_type():
    """Test error handling for invalid lorem_type."""
    result = generate_lorem(lorem_type="invalid", count=1)
    assert result["error"] is not None
    assert "Invalid lorem_type" in result["error"]
    assert result["text"] == ""


@pytest.mark.parametrize("invalid_count", [0, -1, 1.5, "abc"])
def test_generate_lorem_invalid_count(invalid_count):
    """Test error handling for invalid count values."""
    result = generate_lorem(lorem_type="words", count=invalid_count)
    assert result["error"] is not None
    assert "Count must be a positive integer" in result["error"]
    assert result["text"] == ""
