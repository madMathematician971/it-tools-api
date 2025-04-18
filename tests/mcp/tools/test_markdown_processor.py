"""Tests for the Markdown Processor MCP tool."""

import pytest

from mcp_server.tools.markdown_processor import render_markdown

# Test Cases: (input_markdown, expected_html_substring)
VALID_MARKDOWN = [
    ("# Heading 1", "<h1>Heading 1</h1>"),
    ("**Bold Text**", "<p><strong>Bold Text</strong></p>"),
    ("*Italic Text*", "<p><em>Italic Text</em></p>"),
    ("```python\nprint('Hello')\n```", "<pre><code class=\"language-python\">print('Hello')\n</code></pre>"),
    ("| Header 1 | Header 2 |\n| -------- | -------- |\n| Cell 1   | Cell 2   |", "<table>"),  # Check for table tag
    ("This is a paragraph.\n\nWith another line.", "<p>This is a paragraph.</p>\n<p>With another line.</p>"),
    ("", ""),  # Empty string
]

INVALID_INPUTS = [
    (123, "Input must be a string."),
    (None, "Input must be a string."),
    (["list"], "Input must be a string."),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("input_markdown, expected_html_substring", VALID_MARKDOWN)
async def test_render_markdown_success(input_markdown, expected_html_substring):
    """Test successful Markdown to HTML conversion."""
    result = await render_markdown(markdown_string=input_markdown)
    assert result["error"] is None
    assert expected_html_substring in result["html_string"]


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input, expected_error", INVALID_INPUTS)
async def test_render_markdown_invalid_input(invalid_input, expected_error):
    """Test invalid input types for Markdown conversion."""
    result = await render_markdown(markdown_string=invalid_input)
    assert result["html_string"] is None
    assert result["error"] == expected_error
