"""Tests for the Meta Tag Generator MCP tool."""

from typing import Any

import pytest

from mcp_server.tools.meta_tag_generator import generate_meta_tags_tool

# --- Test Data ---

# Basic input data
basic_data = {
    "title": "Test Title",
    "description": "Test Description",
}

# Full input data
full_data = {
    "title": "Full Test Title <Tag>",
    "description": "A more & detailed test description.",
    "keywords": "test, meta, tags",
    "author": "Test Author",
    "language": "en-GB",
    "robots": "noindex, nofollow",
    "viewport": "width=device-width, initial-scale=0.8",
    "og_type": "article",
    "og_url": "https://example.com/article",
    "og_image": "https://example.com/image.jpg",
    "twitter_card": "summary_large_image",
    "twitter_site": "@example",
}

escaping_data = {"title": "Title with <script>", "description": "Desc & stuff"}


# --- Test Cases ---


@pytest.mark.parametrize(
    "input_payload_dict, expected_html_substrings",
    [
        # Basic test
        (
            basic_data,
            [
                "<title>Test Title</title>",
                '<meta name="description" content="Test Description" />',
                '<meta name="robots" content="index, follow" />',
                '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
                '<meta property="og:title" content="Test Title" />',
                '<meta property="og:description" content="Test Description" />',
                '<meta property="og:type" content="website" />',
                '<meta property="twitter:title" content="Test Title" />',
                '<meta property="twitter:description" content="Test Description" />',
                '<meta property="twitter:card" content="summary" />',
            ],
        ),
        # Full test
        (
            full_data,
            [
                "<title>Full Test Title &lt;Tag&gt;</title>",
                '<meta name="description" content="A more &amp; detailed test description." />',
                '<meta name="keywords" content="test, meta, tags" />',
                '<meta name="author" content="Test Author" />',
                '<meta name="language" content="en-GB" />',
                '<meta name="robots" content="noindex, nofollow" />',
                '<meta name="viewport" content="width=device-width, initial-scale=0.8" />',
                '<meta property="og:title" content="Full Test Title &lt;Tag&gt;" />',
                '<meta property="og:description" content="A more &amp; detailed test description." />',
                '<meta property="og:type" content="article" />',
                '<meta property="og:url" content="https://example.com/article" />',
                '<meta property="og:image" content="https://example.com/image.jpg" />',
                '<meta property="twitter:title" content="Full Test Title &lt;Tag&gt;" />',
                '<meta property="twitter:description" content="A more &amp; detailed test description." />',
                '<meta property="twitter:card" content="summary_large_image" />',
                '<meta property="twitter:site" content="@example" />',
            ],
        ),
        # Escaping test
        (
            escaping_data,
            [
                "<title>Title with &lt;script&gt;</title>",
                '<meta name="description" content="Desc &amp; stuff" />',
                '<meta property="og:title" content="Title with &lt;script&gt;" />',
                '<meta property="og:description" content="Desc &amp; stuff" />',
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_generate_meta_tags_tool_success(input_payload_dict: dict[str, Any], expected_html_substrings: list[str]):
    """Test successful generation of meta tags with various inputs."""
    result_dict = generate_meta_tags_tool(**input_payload_dict)

    assert result_dict["error"] is None

    result = result_dict["result"]
    assert isinstance(result, dict)
    assert "html" in result
    assert "tags" in result
    assert isinstance(result["html"], str)
    assert isinstance(result["tags"], dict)

    output_html = result["html"]
    output_tags = result["tags"]

    # Check that essential tags from input are present in the tags dict
    expected_full_input = {**input_payload_dict}  # Make a copy
    # Fill in defaults for comparison if not provided in basic_data/escaping_data
    if "keywords" not in expected_full_input:
        expected_full_input["keywords"] = ""
    if "author" not in expected_full_input:
        expected_full_input["author"] = ""
    if "language" not in expected_full_input:
        expected_full_input["language"] = "en"
    if "robots" not in expected_full_input:
        expected_full_input["robots"] = "index, follow"
    if "viewport" not in expected_full_input:
        expected_full_input["viewport"] = "width=device-width, initial-scale=1.0"
    if "og_type" not in expected_full_input:
        expected_full_input["og_type"] = "website"
    if "og_url" not in expected_full_input:
        expected_full_input["og_url"] = ""
    if "og_image" not in expected_full_input:
        expected_full_input["og_image"] = ""
    if "twitter_card" not in expected_full_input:
        expected_full_input["twitter_card"] = "summary"
    if "twitter_site" not in expected_full_input:
        expected_full_input["twitter_site"] = ""

    # Compare generated tags dictionary with expected values
    assert output_tags["title"] == expected_full_input["title"]
    assert output_tags["description"] == expected_full_input["description"]
    if expected_full_input["keywords"]:
        assert output_tags["keywords"] == expected_full_input["keywords"]
    else:
        assert "keywords" not in output_tags
    if expected_full_input["author"]:
        assert output_tags["author"] == expected_full_input["author"]
    else:
        assert "author" not in output_tags
    assert output_tags["language"] == expected_full_input["language"]
    assert output_tags["robots"] == expected_full_input["robots"]
    assert output_tags["viewport"] == expected_full_input["viewport"]
    assert output_tags["og:title"] == expected_full_input["title"]
    assert output_tags["og:description"] == expected_full_input["description"]
    assert output_tags["og:type"] == expected_full_input["og_type"]
    if expected_full_input["og_url"]:
        assert output_tags["og:url"] == expected_full_input["og_url"]
    else:
        assert "og:url" not in output_tags
    if expected_full_input["og_image"]:
        assert output_tags["og:image"] == expected_full_input["og_image"]
    else:
        assert "og:image" not in output_tags
    assert output_tags["twitter:title"] == expected_full_input["title"]
    assert output_tags["twitter:description"] == expected_full_input["description"]
    assert output_tags["twitter:card"] == expected_full_input["twitter_card"]
    if expected_full_input["twitter_site"]:
        assert output_tags["twitter:site"] == expected_full_input["twitter_site"]
    else:
        assert "twitter:site" not in output_tags

    # Check for presence and escaping of substrings in the generated HTML
    for substring in expected_html_substrings:
        assert substring in output_html


# Test with missing required fields (should raise TypeError on direct call)
@pytest.mark.asyncio
async def test_generate_meta_tags_tool_missing_required():
    """Test calling the tool directly with missing required fields."""
    # Direct python call without required args will raise TypeError.
    with pytest.raises(TypeError):
        generate_meta_tags_tool()  # Missing title and description
