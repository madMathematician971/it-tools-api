"""Tests for the JWT processor MCP tool."""

import pytest  # pylint: disable=unused-import
from jose.constants import ALGORITHMS

from mcp_server.tools.jwt_processor import parse_jwt

# --- Test Data ---

# Generated at jwt.io
SECRET = "your-256-bit-secret"
HEADER_HS256 = {"alg": "HS256", "typ": "JWT"}
PAYLOAD_HS256 = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
JWT_HS256_VALID = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

INVALID_JWT_STRUCTURE = "this.is.not.a.jwt"
INVALID_JWT_BASE64 = "eyJhbGciOiJI#.eyJzdWIi#.signature"
JWT_NO_ALG = "eyJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ0ZXN0In0."


# --- Test Cases ---


def test_parse_jwt_unverified_success():
    """Test successful parsing of header and payload without verification."""
    result = parse_jwt(jwt_string=JWT_HS256_VALID)
    assert result.get("error") is None
    assert result["header"] == HEADER_HS256
    assert result["payload"] == PAYLOAD_HS256
    assert "signature_verified" not in result


def test_parse_jwt_verify_hs256_success():
    """Test successful parsing and HS256 verification."""
    result = parse_jwt(
        jwt_string=JWT_HS256_VALID,
        secret_or_key=SECRET,
        # algorithms=["HS256"] # Optional, should pick up from header
    )
    assert result.get("error") is None
    assert result["header"] == HEADER_HS256
    assert result["payload"] == PAYLOAD_HS256
    assert result["signature_verified"] is True


def test_parse_jwt_verify_hs256_wrong_secret():
    """Test HS256 verification failure with the wrong secret."""
    result = parse_jwt(jwt_string=JWT_HS256_VALID, secret_or_key="wrong-secret", algorithms=[ALGORITHMS.HS256])
    assert result.get("error") is not None
    assert "Signature verification failed" in result["error"]
    assert result["header"] == HEADER_HS256
    assert result["payload"] == PAYLOAD_HS256
    assert result["signature_verified"] is False


def test_parse_jwt_verify_hs256_bad_signature():
    """Test HS256 verification failure with a tampered token."""
    # Manually tamper with the valid token to ensure bad signature
    parts = JWT_HS256_VALID.split(".")
    bad_sig_token = f"{parts[0]}.{parts[1]}.{parts[2][:-1]}X"  # Change last char of sig

    result = parse_jwt(jwt_string=bad_sig_token, secret_or_key=SECRET, algorithms=[ALGORITHMS.HS256])
    assert result.get("error") is not None
    assert "Signature verification failed" in result["error"]
    assert result["header"] == HEADER_HS256
    assert result["payload"] == PAYLOAD_HS256
    assert result["signature_verified"] is False


def test_parse_jwt_verify_hs256_wrong_algorithm():
    """Test HS256 verification failure when specifying the wrong algorithm."""
    result = parse_jwt(jwt_string=JWT_HS256_VALID, secret_or_key=SECRET, algorithms=[ALGORITHMS.RS256])
    assert result.get("error") is not None
    assert "specified alg value is not allowed" in result["error"]
    assert result["signature_verified"] is False


def test_parse_jwt_verify_no_alg_header_no_input():
    """Test verification failure when algorithm is missing everywhere."""
    result = parse_jwt(jwt_string=JWT_NO_ALG, secret_or_key=SECRET)
    assert result.get("error") is not None
    assert "Algorithm required" in result["error"]
    assert result["signature_verified"] is False


def test_parse_jwt_invalid_structure():
    """Test parsing failure with structurally invalid JWT."""
    result = parse_jwt(jwt_string=INVALID_JWT_STRUCTURE)
    assert result.get("error") is not None
    assert "Failed to decode header" in result["error"]
    assert result.get("header") is None
    assert result.get("payload") is None


def test_parse_jwt_invalid_base64():
    """Test parsing failure with invalid Base64 encoding."""
    result = parse_jwt(jwt_string=INVALID_JWT_BASE64)
    assert result.get("error") is not None
    assert "Failed to decode header" in result["error"]
    assert result.get("header") is None
    assert result.get("payload") is None
