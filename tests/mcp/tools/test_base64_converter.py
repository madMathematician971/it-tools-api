"""
Tests for the Base64 converter MCP tool using pytest.
"""

import pytest

from mcp_server.tools.base64_converter import base64_decode_string, base64_encode_string


@pytest.mark.parametrize(
    "original",
    [
        "Hello, world!",
        "The quick brown fox jumps over the lazy dog.",
        "12345",
        "",  # Empty string
        "   leading and trailing spaces   ",
        "Special characters: !@#$%^&*()_+=-`~[]\\{}|;':\",./<>?",  # Escaped quote
        "Unicode: € © 你好",  # Euro, Copyright, Ni Hao
    ],
)
def test_encode_decode_roundtrip(original: str):
    """Test encoding and then decoding various strings maintains the original value."""
    # Encode
    encode_result = base64_encode_string(input_string=original)
    assert encode_result["error"] is None, f"Encoding failed for: {original}"
    encoded_string = encode_result["result_string"]
    assert isinstance(encoded_string, str)

    # Decode
    decode_result = base64_decode_string(input_string=encoded_string)
    assert decode_result["error"] is None, f"Decoding failed for encoded: {encoded_string}"
    assert decode_result["result_string"] == original, "Decoded string does not match original"


@pytest.mark.parametrize(
    "encoded, expected_decoded",
    [
        ("SGVsbG8sIHdvcmxkIQ==", "Hello, world!"),
        (
            "VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIHRoZSBsYXp5IGRvZy4=",
            "The quick brown fox jumps over the lazy dog.",
        ),
        ("MTIzNDU=", "12345"),
        ("", ""),  # Empty string
        ("VW5pY29kZTog4oKsIMKpIOS9oOWlvQ==", "Unicode: € © 你好"),  # Correct pair
    ],
)
def test_decode_known_values(encoded: str, expected_decoded: str):
    """Test decoding specific known Base64 strings."""
    result = base64_decode_string(input_string=encoded)
    assert result["error"] is None
    assert result["result_string"] == expected_decoded


@pytest.mark.parametrize(
    "original, expected_encoded",
    [
        ("Hello, world!", "SGVsbG8sIHdvcmxkIQ=="),
        ("Man", "TWFu"),
        ("Ma", "TWE="),
        ("M", "TQ=="),
        ("Unicode: € © 你好", "VW5pY29kZTog4oKsIMKpIOS9oOWlvQ=="),  # Correct pair
    ],
)
def test_encode_known_values(original: str, expected_encoded: str):
    """Test encoding specific strings to known Base64 values."""
    result = base64_encode_string(input_string=original)
    assert result["error"] is None
    assert result["result_string"] == expected_encoded


@pytest.mark.parametrize(
    "invalid_str",
    [
        "Invalid char!",
        "NotBase64",
        "SGVsbG8%",
        # "SGVsbG8sIHdvcmxkIQ",  # Removed: Valid because padding is added automatically
        "SGVsbG8sIHdvcmxkIQ=A",  # Incorrect padding character
        "====",  # Invalid padding placement
        "SGVsbG8g=a",  # Invalid character after padding
    ],
)
def test_decode_invalid_base64(invalid_str: str):
    """Test decoding invalid Base64 strings results in an error."""
    result = base64_decode_string(input_string=invalid_str)
    assert result["error"] is not None, f"Decoding should fail for: {invalid_str}"
    assert result["result_string"] == ""
    assert "Invalid Base64" in result["error"]


@pytest.mark.parametrize(
    "encoded_without_padding, expected_decoded",
    [
        ("TQ", "M"),  # M -> TQ==
        ("TWE", "Ma"),  # Ma -> TWE=
        ("SGVsbG8sIHdvcmxkIQ", "Hello, world!"),  # Hello, world! -> SGVsbG8sIHdvcmxkIQ==
    ],
)
def test_decode_padding_handled(encoded_without_padding: str, expected_decoded: str):
    """Test that the decode function handles missing padding correctly."""
    # The function should add necessary padding automatically
    result = base64_decode_string(input_string=encoded_without_padding)
    assert result["error"] is None, f"Decoding unexpectedly failed for '{encoded_without_padding}'"
    assert result["result_string"] == expected_decoded
