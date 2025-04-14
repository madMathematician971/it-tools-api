"""
Unit tests for the hmac_calculator tool.
"""

import hashlib
import hmac

import pytest

from mcp_server.tools.hmac_calculator import HASH_ALGOS, calculate_hmac

# --- Test Successful HMAC Calculations ---


def test_calculate_hmac_default_algorithm():
    """Test HMAC calculation with the default SHA-256 algorithm."""
    text = "Hello, world!"
    key = "secret-key"

    result = calculate_hmac(text=text, key=key)

    # Manually calculate expected HMAC with SHA-256
    text_bytes = text.encode("utf-8")
    key_bytes = key.encode("utf-8")
    expected_hmac = hmac.new(key_bytes, text_bytes, hashlib.sha256).hexdigest()

    assert result["hmac_hex"] == expected_hmac
    assert result["algorithm"] == "sha256"


@pytest.mark.parametrize("algorithm", ["md5", "sha1", "sha256", "sha512"])
def test_calculate_hmac_all_algorithms(algorithm):
    """Test HMAC calculation with all supported algorithms."""
    text = "Test message"
    key = "test-key"

    result = calculate_hmac(text=text, key=key, algorithm=algorithm)

    # Manually calculate expected HMAC
    text_bytes = text.encode("utf-8")
    key_bytes = key.encode("utf-8")
    hash_func = HASH_ALGOS[algorithm]
    expected_hmac = hmac.new(key_bytes, text_bytes, hash_func).hexdigest()

    assert result["hmac_hex"] == expected_hmac
    assert result["algorithm"] == algorithm


@pytest.mark.parametrize(
    "text, key, algorithm, expected_hmac",
    [
        # Known HMAC values
        (
            "The quick brown fox jumps over the lazy dog",
            "key",
            "sha256",
            "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8",
        ),
        ("The quick brown fox jumps over the lazy dog", "key", "md5", "80070713463e7749b90c2dc24911e275"),
        ("", "key", "sha1", "f42bb0eeb018ebbd4597ae7213711ec60760843f"),  # Empty message
    ],
)
def test_known_hmac_values(text, key, algorithm, expected_hmac):
    """Test with known HMAC values for specific inputs."""
    result = calculate_hmac(text=text, key=key, algorithm=algorithm)
    assert result["hmac_hex"] == expected_hmac


# --- Test Edge Cases ---


def test_empty_key():
    """Test HMAC calculation with an empty key."""
    text = "Some message"
    key = ""

    result = calculate_hmac(text=text, key=key)

    # Manually calculate expected HMAC with empty key
    text_bytes = text.encode("utf-8")
    key_bytes = b""  # Empty key bytes
    expected_hmac = hmac.new(key_bytes, text_bytes, hashlib.sha256).hexdigest()

    assert result["hmac_hex"] == expected_hmac


def test_unicode_input():
    """Test HMAC calculation with Unicode characters."""
    text = "你好, こんにちは, 안녕하세요"  # Hello in Chinese, Japanese, Korean
    key = "üñîçødé kêý"  # Unicode key

    result = calculate_hmac(text=text, key=key)

    # Manually calculate with proper UTF-8 encoding
    text_bytes = text.encode("utf-8")
    key_bytes = key.encode("utf-8")
    expected_hmac = hmac.new(key_bytes, text_bytes, hashlib.sha256).hexdigest()

    assert result["hmac_hex"] == expected_hmac


# --- Test Error Cases ---


def test_invalid_algorithm():
    """Test with an invalid hash algorithm."""
    with pytest.raises(ValueError) as excinfo:
        calculate_hmac(text="test", key="key", algorithm="invalid_algo")

    assert "Unsupported algorithm" in str(excinfo.value)


def test_none_text_input():
    """Test with None as text input (should raise error)."""
    with pytest.raises(ValueError) as excinfo:
        calculate_hmac(text=None, key="key")

    assert "Error calculating HMAC" in str(excinfo.value)


def test_none_key_input():
    """Test with None as key input (should raise error)."""
    with pytest.raises(ValueError) as excinfo:
        calculate_hmac(text="test", key=None)

    assert "Error calculating HMAC" in str(excinfo.value)
