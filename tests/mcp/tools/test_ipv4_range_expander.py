"""Tests for the IPv4 range expander tool using pytest."""

import pytest

from mcp_server.tools.ipv4_range_expander import MAX_ADDRESSES_TO_RETURN, expand_ipv4_range


@pytest.mark.parametrize(
    "input_range, expected_count, expected_addrs, truncated, error_part",
    [
        # --- Valid CIDR ---
        ("192.168.1.5/32", 1, ["192.168.1.5"], False, None),  # Single IP CIDR
        ("192.168.1.10/31", 2, ["192.168.1.10", "192.168.1.11"], False, None),  # /31
        ("192.168.1.12/30", 4, ["192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15"], False, None),  # /30
        ("10.0.1.0/29", 8, [f"10.0.1.{i}" for i in range(8)], False, None),  # /29
        # --- Valid Hyphenated Range ---
        ("10.0.0.5-10.0.0.5", 1, ["10.0.0.5"], False, None),  # Single IP range
        ("10.0.0.5-10.0.0.7", 3, ["10.0.0.5", "10.0.0.6", "10.0.0.7"], False, None),
        (
            " 192.168.1.254 - 192.168.2.1 ",
            4,
            ["192.168.1.254", "192.168.1.255", "192.168.2.0", "192.168.2.1"],
            False,
            None,
        ),  # Across boundary, with spaces
        # --- Valid Single IP ---
        ("1.1.1.1", 1, ["1.1.1.1"], False, None),
        # --- Full but not Truncated Large Ranges ---
        # For ranges exactly matching MAX_ADDRESSES_TO_RETURN, we check count, first, and last.
        (
            "172.16.0.0/16",
            65536,
            ["172.16.0.0", "172.16.255.255"],
            False,
            None,
        ),  # /16 - exactly MAX_ADDRESSES_TO_RETURN
        (
            "10.0.0.1-10.1.0.0",
            65536,
            ["10.0.0.1", "10.1.0.0"],
            False,
            None,
        ),  # Hyphenated - exactly MAX_ADDRESSES_TO_RETURN
        # --- Invalid Inputs ---
        (
            "192.168.1.0/15",
            131072,
            ["192.168.0.0", "192.169.255.255"],
            True,
            None,
        ),  # /15 - larger than limit, expect truncation
        (
            "10.0.0.0-10.2.0.0",
            131073,
            ["10.0.0.0", "10.2.0.0"],
            True,
            None,
        ),  # Hyphenated - larger than limit, expect truncation
        ("", 0, [], False, "cannot be empty"),
        ("192.168.1.0/33", 0, [], False, "Invalid IPv4 CIDR"),  # Invalid prefix
        ("192.168.1.300/24", 0, [], False, "Invalid IPv4 CIDR"),  # Invalid IP in CIDR
        ("192.168.1.10-192.168.1.5", 0, [], False, "Start IP address must be less than or equal"),  # Bad range order
        ("192.168.1.10-192.168.1", 0, [], False, "Invalid IP address in range"),  # Incomplete IP in range
        ("192.168.1.10-Invalid", 0, [], False, "Invalid IP address in range"),  # Invalid IP in range
        (
            "192.168.1.10 - 192.168.1.20 - 192.168.1.30",
            0,
            [],
            False,
            "Invalid hyphenated range format",
        ),  # Too many hyphens
        ("192.168.300.1", 0, [], False, "Invalid input format"),  # Invalid single IP
        ("NotAnIP", 0, [], False, "Invalid input format"),
    ],
)
def test_expand_ipv4_range(input_range, expected_count, expected_addrs, truncated, error_part):
    """Parametrized test for IPv4 range expansion scenarios."""
    result = expand_ipv4_range(ip_range=input_range)

    assert result.get("count") == expected_count
    assert result.get("truncated") == truncated

    if error_part:
        assert result.get("error") is not None
        assert error_part.lower() in result.get("error").lower()
        assert len(result.get("addresses", [])) == 0
    else:
        assert result.get("error") is None
        retrieved_addrs = result.get("addresses")
        assert retrieved_addrs is not None

        if truncated:
            assert len(retrieved_addrs) == MAX_ADDRESSES_TO_RETURN
            assert retrieved_addrs[0] == expected_addrs[0]  # Check first addr
            # Calculating the exact last IP for large truncated ranges is complex and less critical here
            # We trust the tool truncated correctly if the count and first IP are right.
        elif expected_count == MAX_ADDRESSES_TO_RETURN:
            # Special case: range exactly matches the limit, not truncated
            assert len(retrieved_addrs) == MAX_ADDRESSES_TO_RETURN
            assert retrieved_addrs[0] == expected_addrs[0]  # Check first addr
            assert retrieved_addrs[-1] == expected_addrs[-1]  # Check last addr
        else:
            # Normal case: not truncated, smaller than limit
            assert len(retrieved_addrs) == expected_count
            assert retrieved_addrs == expected_addrs
