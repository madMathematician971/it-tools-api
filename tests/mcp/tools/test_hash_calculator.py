"""
Unit tests for the hash_calculator tool.
"""

import hashlib

import pytest

from mcp_server.tools.hash_calculator import calculate_hash

# --- Test Successful Hash Calculations ---


def test_calculate_hash_text():
    """Test hash calculation with a simple text string."""
    text = "Hello, world!"
    result = calculate_hash(text=text)

    # Manually calculate expected hashes
    text_bytes = text.encode("utf-8")
    expected_md5 = hashlib.md5(text_bytes).hexdigest()
    expected_sha1 = hashlib.sha1(text_bytes).hexdigest()
    expected_sha256 = hashlib.sha256(text_bytes).hexdigest()
    expected_sha512 = hashlib.sha512(text_bytes).hexdigest()

    # Verify all hashes match
    assert result["md5"] == expected_md5
    assert result["sha1"] == expected_sha1
    assert result["sha256"] == expected_sha256
    assert result["sha512"] == expected_sha512


def test_calculate_hash_empty_string():
    """Test hash calculation with an empty string."""
    text = ""
    result = calculate_hash(text=text)

    # Manually calculate expected hashes for empty string
    text_bytes = text.encode("utf-8")
    expected_md5 = hashlib.md5(text_bytes).hexdigest()
    expected_sha1 = hashlib.sha1(text_bytes).hexdigest()
    expected_sha256 = hashlib.sha256(text_bytes).hexdigest()
    expected_sha512 = hashlib.sha512(text_bytes).hexdigest()

    # Verify all hashes match
    assert result["md5"] == expected_md5
    assert result["sha1"] == expected_sha1
    assert result["sha256"] == expected_sha256
    assert result["sha512"] == expected_sha512

    # Empty string has known hash values
    assert result["md5"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert result["sha1"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


@pytest.mark.parametrize(
    "text, expected_md5, expected_sha1",
    [
        ("Hello, world!", "6cd3556deb0da54bca060b4c39479839", "943a702d06f34599aee1f8da8ef9f7296031d699"),
        (
            "The quick brown fox jumps over the lazy dog",
            "9e107d9d372bb6826bd81d3542a419d6",
            "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12",
        ),
    ],
)
def test_known_hash_values(text, expected_md5, expected_sha1):
    """Test with known hash values for specific inputs."""
    result = calculate_hash(text=text)

    assert result["md5"] == expected_md5
    assert result["sha1"] == expected_sha1


def test_unicode_string_hash():
    """Test with a Thai Unicode string."""
    text = "ทดสอบภาษาไทย"  # Test with Thai characters
    result = calculate_hash(text=text)

    # Calculate the expected values correctly
    text_bytes = text.encode("utf-8")
    expected_md5 = hashlib.md5(text_bytes).hexdigest()
    expected_sha1 = hashlib.sha1(text_bytes).hexdigest()

    assert result["md5"] == expected_md5
    assert result["sha1"] == expected_sha1


# --- Test Edge Cases ---


def test_hash_with_special_characters():
    """Test hash calculation with special characters."""
    text = "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
    result = calculate_hash(text=text)

    # Just verify we get hash values of expected length
    assert len(result["md5"]) == 32  # MD5 is 128 bits = 32 hex chars
    assert len(result["sha1"]) == 40  # SHA1 is 160 bits = 40 hex chars
    assert len(result["sha256"]) == 64  # SHA256 is 256 bits = 64 hex chars
    assert len(result["sha512"]) == 128  # SHA512 is 512 bits = 128 hex chars


def test_hash_with_unicode():
    """Test hash calculation with Unicode characters."""
    text = "你好, こんにちは, 안녕하세요"  # Hello in Chinese, Japanese, Korean
    result = calculate_hash(text=text)

    # Verify encoding works correctly by manual calculation
    text_bytes = text.encode("utf-8")
    expected_md5 = hashlib.md5(text_bytes).hexdigest()

    assert result["md5"] == expected_md5


# --- Test Error Cases ---


def test_non_string_input():
    """Test with non-string input (should convert to string)."""
    # The tool should handle this by raising a specific error
    with pytest.raises(ValueError) as excinfo:
        calculate_hash(text=None)

    assert "Error calculating hashes" in str(excinfo.value)
