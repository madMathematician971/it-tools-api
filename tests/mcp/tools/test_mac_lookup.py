"""Tests for the MAC Address Vendor Lookup MCP tool."""

import pytest

from mcp_server.tools.mac_lookup import lookup_mac_vendor

# --- Test Cases ---
# Format: (input_mac, expected_oui, expected_company_substring, expected_is_private, expected_error_substring)
VALID_MACS = [
    ("00:1A:C1:00:00:00", "001AC1", "3com", False, None),
    ("00-1A-C1-00-00-00", "001AC1", "3com", False, None),
    ("001ac1000000", "001AC1", "3com", False, None),
    ("001A.C100.0000", "001AC1", "3com", False, None),
    ("00:01:42:11:22:33", "000142", "cisco", False, None),
    ("000142abcdef", "000142", "cisco", False, None),
    ("00:15:17:AA:BB:CC", "001517", "intel", False, None),
    # Locally Administered Address - no vendor
    ("02:00:00:00:00:01", "020000", None, True, "Vendor not found"),
    ("0A:00:00:11:22:33", "0A0000", None, True, "Vendor not found"),
    ("0E:00:00:11:22:33", "0E0000", None, True, "Vendor not found"),
    # OUI-only input
    ("00-1A-C1", "001AC1", "3com", False, None),
    # Unknown/Unassigned OUI
    ("FF:FF:FF:00:00:00", "FFFFFF", None, True, "Vendor not found"),
]

INVALID_MACS = [
    # Too short
    ("00:1A", None, None, False, "Vendor not found"),
    ("12345", None, None, True, "Vendor not found"),
    # Invalid characters
    ("00:1A:XX:00:00:00", None, None, False, "Invalid MAC address format"),
    # Incorrect length
    ("001AC10000001", "001AC1", None, False, "Invalid MAC address format"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_mac, expected_oui, expected_company_substring, expected_is_private, expected_error_substring",
    VALID_MACS,
)
async def test_lookup_mac_vendor_valid(
    input_mac, expected_oui, expected_company_substring, expected_is_private, expected_error_substring
):
    """Test valid MAC address lookups."""
    result = await lookup_mac_vendor(mac_address=input_mac)

    assert result["oui"] == expected_oui
    assert result["is_private"] == expected_is_private

    if expected_error_substring:
        assert result["error"] is not None
        assert expected_error_substring in result["error"]
        if "Vendor not found" in result["error"]:
            assert result["company"] is None
    else:
        assert result["error"] is None
        if expected_company_substring:
            assert result["company"] is not None
            assert expected_company_substring.lower() in result["company"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_mac, expected_oui, expected_company_substring, expected_is_private, expected_error_substring",
    INVALID_MACS,
)
async def test_lookup_mac_vendor_invalid(
    input_mac, expected_oui, expected_company_substring, expected_is_private, expected_error_substring
):
    """Test invalid MAC address lookups."""
    result = await lookup_mac_vendor(mac_address=input_mac)

    assert result["error"] is not None
    assert expected_error_substring in result["error"]
    assert result["oui"] == expected_oui
    assert result["is_private"] == expected_is_private
    assert result["company"] is None
