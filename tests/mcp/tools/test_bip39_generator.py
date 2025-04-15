"""
Tests for the BIP39 mnemonic generation tool.
"""

import pytest
from mnemonic import Mnemonic

from mcp_server.tools.bip39_generator import LANGUAGE_MAP, SUPPORTED_WORD_COUNTS, generate_bip39_mnemonic


@pytest.mark.parametrize(
    "word_count, language_code, expected_language_canonical",
    [
        (12, "en", LANGUAGE_MAP["en"]),
        (24, "en", LANGUAGE_MAP["en"]),
        (15, "es", LANGUAGE_MAP["es"]),
        (18, "jp", LANGUAGE_MAP["jp"]),
        (21, "zh_hans", LANGUAGE_MAP["zh_hans"]),
        (12, "fr", LANGUAGE_MAP["fr"]),
        (12, "invalid_lang", "english"),  # Test fallback to default language
        (12, "EN", LANGUAGE_MAP["en"]),  # Test case insensitivity
    ],
)
def test_generate_bip39_mnemonic_success(word_count: int, language_code: str, expected_language_canonical: str):
    """Test successful BIP39 mnemonic generation for various inputs."""
    result = generate_bip39_mnemonic(word_count=word_count, language=language_code)

    assert result["error"] is None, f"Expected no error, but got: {result['error']}"
    assert isinstance(result["mnemonic"], str)
    assert len(result["mnemonic"].split()) == word_count
    assert result["word_count"] == word_count
    assert result["language"] == expected_language_canonical

    try:
        mnemo = Mnemonic(expected_language_canonical)
        wordlist = mnemo.wordlist
        for word in result["mnemonic"].split():
            assert word in wordlist, f"Word '{word}' not found in '{expected_language_canonical}' wordlist."
    except Exception as e:
        pytest.fail(f"Failed to validate words against mnemonic library wordlist: {e}")


def test_generate_bip39_mnemonic_default_language():
    """Test generation using the default language (English) when none is specified."""
    word_count = 12
    result = generate_bip39_mnemonic(word_count=word_count)

    assert result["error"] is None
    assert len(result["mnemonic"].split()) == word_count
    assert result["word_count"] == word_count
    assert result["language"] == "english"


@pytest.mark.parametrize("invalid_word_count", [0, 11, 13, 25, 128])
def test_generate_bip39_mnemonic_invalid_word_count(invalid_word_count: int):
    """Test generation failure with invalid word counts."""
    result = generate_bip39_mnemonic(word_count=invalid_word_count, language="en")

    assert result["error"] is not None
    assert "Invalid word_count" in result["error"]
    assert result["mnemonic"] == ""
    assert result["word_count"] == invalid_word_count
    # Language might be the input or the canonical, check the error message for specifics
    assert str(list(SUPPORTED_WORD_COUNTS.keys())) in result["error"]
