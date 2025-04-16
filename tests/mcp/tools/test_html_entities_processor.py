"""Tests for the HTML entities processor tool using pytest."""

import pytest

from mcp_server.tools.html_entities_processor import decode_html_entities, encode_html_entities


@pytest.mark.parametrize(
    "input_text, expected_encoded",
    [
        ("Hello, world!", "Hello, world!"),  # No special chars
        ("<script>alert('XSS');</script>", "&lt;script&gt;alert(&#x27;XSS&#x27;);&lt;/script&gt;"),
        (""""Quotes" & ampersands'""", "&quot;Quotes&quot; &amp; ampersands&#x27;"),
        ("", ""),  # Empty string
        ("Price: > $10", "Price: &gt; $10"),
    ],
)
def test_encode_html_entities(input_text, expected_encoded):
    """Test HTML entity encoding."""
    result = encode_html_entities(text=input_text)
    assert result.get("error") is None
    assert result.get("result") == expected_encoded


@pytest.mark.parametrize(
    "input_encoded, expected_decoded",
    [
        ("Hello, world!", "Hello, world!"),  # No entities
        ("&lt;script&gt;alert(&#x27;XSS&#x27;);&lt;/script&gt;", "<script>alert('XSS');</script>"),
        ("&quot;Quotes&quot; &amp; ampersands&#x27;", '"Quotes" & ampersands\''),
        ("", ""),  # Empty string
        ("Price: &gt; $10", "Price: > $10"),
        ("&lt;&gt;&amp;&quot;&#x27;", "<>&\"'"),  # All escaped chars
        ("Text with &unknown; entity", "Text with &unknown; entity"),  # Unknown entities are preserved
        ("Partially encoded &amp; text", "Partially encoded & text"),
    ],
)
def test_decode_html_entities(input_encoded, expected_decoded):
    """Test HTML entity decoding."""
    result = decode_html_entities(text=input_encoded)
    assert result.get("error") is None
    assert result.get("result") == expected_decoded


def test_encode_decode_roundtrip():
    """Test encoding then decoding returns the original string."""
    # Correctly escape quotes within the string
    original_text = '<tag attribute="value">Content & more content</tag>\'"'
    encode_result = encode_html_entities(original_text)
    assert encode_result.get("error") is None
    encoded = encode_result.get("result")
    assert encoded is not None

    decode_result = decode_html_entities(encoded)
    assert decode_result.get("error") is None
    decoded = decode_result.get("result")

    assert decoded == original_text
