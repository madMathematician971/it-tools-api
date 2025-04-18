"""Tests for the encryption processor tool using pytest."""

import pytest

from mcp_server.tools.encryption_processor import decrypt_text, encrypt_text


@pytest.fixture
def sample_data():
    return {
        "text": "This is a secret message!",
        "password": "correct-password",
        "algorithm": "aes-256-cbc",
    }


def test_encrypt_decrypt_roundtrip(sample_data):
    """Test that encrypting and then decrypting returns the original text."""
    # Encrypt
    encrypt_result = encrypt_text(**sample_data)
    assert encrypt_result.get("error") is None
    ciphertext = encrypt_result.get("ciphertext")
    assert ciphertext is not None

    # Decrypt with correct password
    decrypt_data = {
        "ciphertext": ciphertext,
        "password": sample_data["password"],
        "algorithm": sample_data["algorithm"],
    }
    decrypt_result = decrypt_text(**decrypt_data)
    assert decrypt_result.get("error") is None
    assert decrypt_result.get("plaintext") == sample_data["text"]


def test_decrypt_wrong_password(sample_data):
    """Test decryption failure with the wrong password."""
    # Encrypt
    encrypt_result = encrypt_text(**sample_data)
    assert encrypt_result.get("error") is None
    ciphertext = encrypt_result.get("ciphertext")
    assert ciphertext is not None

    # Decrypt with incorrect password
    decrypt_data = {
        "ciphertext": ciphertext,
        "password": "wrong-password",
        "algorithm": sample_data["algorithm"],
    }
    decrypt_result = decrypt_text(**decrypt_data)
    assert decrypt_result.get("error") is not None
    assert "Decryption failed" in decrypt_result.get("error")
    assert decrypt_result.get("plaintext") is None


def test_decrypt_invalid_base64():
    """Test decryption with invalid Base64 input."""
    decrypt_data = {
        "ciphertext": "this is not base64!",
        "password": "any-password",
        "algorithm": "aes-256-cbc",
    }
    decrypt_result = decrypt_text(**decrypt_data)
    assert decrypt_result.get("error") is not None
    assert "Invalid Base64 ciphertext" in decrypt_result.get("error")
    assert decrypt_result.get("plaintext") is None


def test_decrypt_ciphertext_too_short():
    """Test decryption with ciphertext shorter than salt + IV size."""
    # SALT_SIZE (16) + IV_SIZE (16) = 32. Base64 encodes 3 bytes to 4 chars.
    # Need fewer than 32 bytes -> fewer than ceil(32/3)*4 = 44 chars.
    short_b64 = "YWFhYWFhYWFhYWFhYWFhYQ=="  # 16 bytes of 'a' encoded
    decrypt_data = {
        "ciphertext": short_b64,
        "password": "any-password",
        "algorithm": "aes-256-cbc",
    }
    decrypt_result = decrypt_text(**decrypt_data)
    assert decrypt_result.get("error") is not None
    assert "Ciphertext is too short" in decrypt_result.get("error")
    assert decrypt_result.get("plaintext") is None


def test_unsupported_algorithm_encrypt(sample_data):
    """Test encryption with an unsupported algorithm."""
    encrypt_data = sample_data.copy()
    encrypt_data["algorithm"] = "des"
    encrypt_result = encrypt_text(**encrypt_data)
    assert encrypt_result.get("error") is not None
    assert "Unsupported algorithm" in encrypt_result.get("error")
    assert encrypt_result.get("ciphertext") is None


def test_unsupported_algorithm_decrypt():
    """Test decryption with an unsupported algorithm."""
    decrypt_data = {
        "ciphertext": "doesntmatter==",
        "password": "doesntmatter",
        "algorithm": "blowfish",
    }
    decrypt_result = decrypt_text(**decrypt_data)
    assert decrypt_result.get("error") is not None
    assert "Unsupported algorithm" in decrypt_result.get("error")
    assert decrypt_result.get("plaintext") is None


def test_encrypt_non_utf8_text():
    """Test encryption with text that cannot be UTF-8 encoded."""
    # Example: A lone high surrogate cannot be encoded in UTF-8
    non_utf8_text = "Hello \ud800 world"
    encrypt_data = {"text": non_utf8_text, "password": "password123", "algorithm": "aes-256-cbc"}
    encrypt_result = encrypt_text(**encrypt_data)
    assert encrypt_result.get("error") is not None
    assert "cannot be encoded to UTF-8" in encrypt_result.get("error")
    assert encrypt_result.get("ciphertext") is None
