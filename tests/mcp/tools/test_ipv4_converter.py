"""Tests for the IPv4 converter tool using pytest."""

import pytest

from mcp_server.tools.ipv4_converter import convert_ipv4

# Define expected results for a common IP
IP_DOT = "192.168.1.1"
IP_DEC = 3232235777
IP_HEX = "0xC0A80101"
IP_BIN = "11000000101010000000000100000001"

# Expected dictionary for successful conversion of IP_DOT
EXPECTED_RESULT = {
    "dotted_decimal": IP_DOT,
    "decimal": IP_DEC,
    "hexadecimal": IP_HEX,
    "binary": IP_BIN,
    "error": None,
}


@pytest.mark.parametrize(
    "input_ip, input_format, expected_partial_result, expected_error_part",
    [
        # --- Auto-detection ---
        (IP_DOT, None, EXPECTED_RESULT, None),
        (str(IP_DEC), None, EXPECTED_RESULT, None),
        (IP_HEX, None, EXPECTED_RESULT, None),  # With 0x
        (IP_HEX[2:], None, EXPECTED_RESULT, None),  # Without 0x
        (IP_BIN, None, EXPECTED_RESULT, None),
        # Binary with spaces
        ("11000000 10101000 00000001 00000001", None, EXPECTED_RESULT, None),
        # Edge cases
        ("0.0.0.0", None, {"decimal": 0, "hexadecimal": "0x00000000"}, None),
        ("255.255.255.255", None, {"decimal": 4294967295, "hexadecimal": "0xFFFFFFFF"}, None),
        ("0", None, {"dotted_decimal": "0.0.0.0"}, None),
        ("4294967295", None, {"dotted_decimal": "255.255.255.255"}, None),
        ("0x0", None, {"dotted_decimal": "0.0.0.0"}, None),
        ("0xFFFFFFFF", None, {"dotted_decimal": "255.255.255.255"}, None),
        ("00000000000000000000000000000000", None, {"dotted_decimal": "0.0.0.0"}, None),
        ("11111111111111111111111111111111", None, {"dotted_decimal": "255.255.255.255"}, None),
        # --- Format hints ---
        (IP_DOT, "dotted", EXPECTED_RESULT, None),
        (str(IP_DEC), "decimal", EXPECTED_RESULT, None),
        (IP_HEX, "hex", EXPECTED_RESULT, None),
        (IP_BIN, "binary", EXPECTED_RESULT, None),
        # --- Invalid inputs ---
        ("", None, None, "cannot be empty"),
        (" ", None, None, "cannot be empty"),
        ("192.168.1.256", None, None, "Invalid IP address format"),
        ("192.168.1", None, None, "Invalid IP address format"),
        ("192.168.1.1.1", None, None, "Could not determine IP address format"),
        ("c0a80101", "decimal", None, "Invalid decimal IP format"),  # Hex mistaken for decimal
        ("192.168.1.1", "binary", None, "Invalid binary IP format"),
        ("11000000101010000000000100000001", "hex", None, "Invalid hexadecimal IP format"),
        ("0xGHIJKLMN", None, None, "Could not determine IP address format"),
        ("12345", "binary", None, "Invalid binary IP format"),
        ("010101010101010101010101010101010", None, None, "Binary IP must be at most 32 bits"),
        ("4294967296", None, None, "Invalid or out-of-range decimal IP format"),
        ("-1", None, None, "Could not determine IP address format"),
        ("127.0.0.1", "unknown_format", None, "Unknown format hint"),
    ],
)
def test_convert_ipv4(input_ip, input_format, expected_partial_result, expected_error_part):
    """Parametrized test for IPv4 conversion scenarios."""
    result = convert_ipv4(ip_address=input_ip, format_hint=input_format)

    assert result.get("original") == input_ip  # Check original is preserved

    if expected_error_part:
        assert result.get("error") is not None
        assert expected_error_part.lower() in result.get("error").lower()
        # Check other fields are None on error
        assert result.get("dotted_decimal") is None
        assert result.get("decimal") is None
        assert result.get("hexadecimal") is None
        assert result.get("binary") is None
    else:
        assert result.get("error") is None
        assert result.get("dotted_decimal") is not None
        assert result.get("decimal") is not None
        assert result.get("hexadecimal") is not None
        assert result.get("binary") is not None
        # Check specific expected values
        for key, value in expected_partial_result.items():
            assert result.get(key) == value
