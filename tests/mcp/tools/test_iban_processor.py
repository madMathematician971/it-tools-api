"""Tests for the IBAN processor tool using pytest."""

import pytest

from mcp_server.tools.iban_processor import validate_iban


@pytest.mark.parametrize(
    "input_iban, is_valid, expected_format, country, check_digits, bban_contains, error_contains",
    [
        # Valid IBANs
        ("DE89 3704 0044 0532 0130 00", True, "DE89 3704 0044 0532 0130 00", "DE", "89", "370400440532013000", None),
        ("GB29 NWBK 6016 1331 9268 19", True, "GB29 NWBK 6016 1331 9268 19", "GB", "29", "NWBK60161331926819", None),
        (
            "FR14 2004 1010 0505 0001 3M02 606",
            True,
            "FR14 2004 1010 0505 0001 3M02 606",
            "FR",
            "14",
            "20041010050500013M02606",
            None,
        ),
        (
            "nl91abna0417164300",
            True,
            "NL91 ABNA 0417 1643 00",
            "NL",
            "91",
            "ABNA0417164300",
            None,
        ),  # No spaces, lowercase
        # Invalid IBANs
        ("DE89 3704 0044 0532 0130 01", False, None, None, None, None, "checksum digits"),
        ("DE89 3704 0044 0532 0130", False, None, None, None, None, "length"),
        ("XX89 3704 0044 0532 0130 00", False, None, None, None, None, "Unknown country-code"),
        ("GB29 NWBK 6016 1331 9268 1X", False, None, None, None, None, "BBAN"),
        ("NOTANIBAN", False, None, None, None, None, "Invalid characters"),
        ("", False, None, None, None, None, "Invalid characters"),
    ],
)
def test_validate_iban(
    input_iban,
    is_valid,
    expected_format,
    country,
    check_digits,
    bban_contains,
    error_contains,
):
    """Parametrized test for IBAN validation scenarios."""
    result = validate_iban(iban_string=input_iban)

    assert result.get("is_valid") == is_valid

    if is_valid:
        assert result.get("iban_string_formatted") == expected_format
        assert result.get("country_code") == country
        assert result.get("check_digits") == check_digits
        assert result.get("bban") == bban_contains
        assert result.get("error") is None
    else:
        assert result.get("iban_string_formatted") is None
        assert result.get("country_code") is None
        assert result.get("check_digits") is None
        assert result.get("bban") is None
        assert result.get("error") is not None
        assert error_contains.lower() in result.get("error").lower()
