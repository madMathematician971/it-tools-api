"""
Tests for the Basic Auth Generator MCP tool.
"""

import pytest

from mcp_server.tools.basic_auth_generator import generate_basic_auth_header


@pytest.mark.parametrize(
    "username, password, expected_base64, expected_header",
    [
        ("user", "pass", "dXNlcjpwYXNz", "Basic dXNlcjpwYXNz"),
        ("Aladdin", "open sesame", "QWxhZGRpbjpvcGVuIHNlc2FtZQ==", "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
        (
            "test@example.com",
            "P@$$wOrd123!",
            "dGVzdEBleGFtcGxlLmNvbTpQQCQkd09yZDEyMyE=",
            "Basic dGVzdEBleGFtcGxlLmNvbTpQQCQkd09yZDEyMyE=",
        ),
        ("", "", "Og==", "Basic Og=="),  # Empty user and pass
        ("user", "", "dXNlcjo=", "Basic dXNlcjo="),  # Empty pass
        ("", "password", "OnBhc3N3b3Jk", "Basic OnBhc3N3b3Jk"),  # Empty user
        (
            "user:pass",
            "pass:user",
            "dXNlcjpwYXNzOnBhc3M6dXNlcg==",
            "Basic dXNlcjpwYXNzOnBhc3M6dXNlcg==",
        ),  # Colons in values
    ],
)
def test_generate_basic_auth_header_success(username, password, expected_base64, expected_header):
    """Test successful generation of basic auth headers."""
    result = generate_basic_auth_header(username=username, password=password)

    assert result["error"] is None
    assert result["username"] == username
    assert result["password"] == password
    assert result["base64"] == expected_base64
    assert result["header"] == expected_header


# Add tests for potential error scenarios if any were identified (e.g., non-string inputs)
def test_generate_basic_auth_header_errors():
    """Test error handling for non-string inputs."""
    # Although type hints should catch this, test robustness
    result_non_string_user = generate_basic_auth_header(username=123, password="pass")
    assert result_non_string_user["error"] is not None
    assert "Username and password must be strings" in result_non_string_user["error"]

    result_non_string_pass = generate_basic_auth_header(username="user", password=456)
    assert result_non_string_pass["error"] is not None
    assert "Username and password must be strings" in result_non_string_pass["error"]

    result_non_string_both = generate_basic_auth_header(username=None, password=None)
    assert result_non_string_both["error"] is not None
    assert "Username and password must be strings" in result_non_string_both["error"]
