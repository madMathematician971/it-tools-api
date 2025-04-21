"""Tests for the email processor tool using pytest."""

import pytest

from mcp_server.tools.email_processor import normalize_email


@pytest.mark.parametrize(
    "input_email, expected_normalized, expected_error",
    [
        # Valid emails, no normalization needed
        ("test@example.com", "test@example.com", None),
        ("TEST@EXAMPLE.COM", "test@example.com", None),  # Case normalization
        ("user.name@domain.co.uk", "user.name@domain.co.uk", None),
        ("firstname.lastname@sub.domain.com", "firstname.lastname@sub.domain.com", None),
        # Gmail/Google normalization
        ("test.email@gmail.com", "testemail@gmail.com", None),
        ("Test.Email@Gmail.com", "testemail@gmail.com", None),
        ("test+alias@gmail.com", "test@gmail.com", None),
        ("test.email+alias@gmail.com", "testemail@gmail.com", None),
        ("test.email+alias.with.dots@googlemail.com", "testemail@googlemail.com", None),
        ("test@google.com", "test@google.com", None),  # google.com treated like gmail
        # Outlook/Hotmail/Live normalization
        ("test.email@outlook.com", "test.email@outlook.com", None),  # Dots preserved
        ("test+alias@outlook.com", "test@outlook.com", None),
        ("test.email+alias@hotmail.com", "test.email@hotmail.com", None),
        ("test+other@live.com", "test@live.com", None),
        # Invalid formats
        ("plainaddress", None, "Invalid email format."),
        ("@missinglocalpart.com", None, "Invalid email format."),
        ("missingdomain@", None, "Invalid email format."),
        ("missingtld@domain.", None, "Invalid email format."),
        ("user@domain.c", None, "Invalid email format."),  # TLD too short
        ("test@domain..com", None, "Invalid email characters or structure."),  # Double dot in domain
        ("test..123@domain.com", None, "Invalid email characters or structure."),  # Double dot in local
        (".test@domain.com", None, "Invalid email characters or structure."),  # Leading dot local
        ("test.@domain.com", None, "Invalid email characters or structure."),  # Trailing dot local
        ("test@.domain.com", None, "Invalid email characters or structure."),  # Leading dot domain
        ("test@domain.com.", None, "Invalid email format."),  # Trailing dot domain
        ("test(comment)@domain.com", None, "Invalid email format."),  # Parentheses
    ],
)
def test_normalize_email(input_email, expected_normalized, expected_error):
    """Parametrized test for various email normalization scenarios."""
    result = normalize_email(input_email)

    assert result.get("original_email") == input_email
    assert result.get("normalized_email") == expected_normalized

    if expected_error:
        assert result.get("error") is not None
        assert expected_error in result.get("error")
    else:
        assert result.get("error") is None
