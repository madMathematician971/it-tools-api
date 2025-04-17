"""Tests for the IPv6 ULA Generator MCP tool."""

import re

import pytest  # pylint: disable=unused-import

from mcp_server.tools.ipv6_ula_generator import generate_ipv6_ula


def test_generate_ula_with_global_id():
    """Test ULA generation with a specific Global ID."""
    global_id = "a1b2c3d4e5"
    subnet_id = "abcd"
    result = generate_ipv6_ula(global_id=global_id, subnet_id=subnet_id)
    assert result["error"] is None
    assert result["global_id"] == global_id
    assert result["subnet_id"] == subnet_id
    # Check address format: fdXX:XXXX:XXXX:YYYY::1
    assert result["ula_address"] == f"fda1:b2c3:d4e5:{subnet_id}::1"


def test_generate_ula_random_global_id():
    """Test ULA generation with a random Global ID."""
    subnet_id = "beef"
    result = generate_ipv6_ula(subnet_id=subnet_id)
    assert result["error"] is None
    assert result["subnet_id"] == subnet_id
    # Check Global ID format and length
    assert re.match(r"^[0-9a-f]{10}$", result["global_id"])
    # Check address format
    global_id = result["global_id"]
    assert result["ula_address"] == f"fd{global_id[:2]}:{global_id[2:6]}:{global_id[6:]}:{subnet_id}::1"


def test_generate_ula_default_subnet_id():
    """Test ULA generation using the default Subnet ID."""
    global_id = "abcdef0123"
    result = generate_ipv6_ula(global_id=global_id)
    assert result["error"] is None
    assert result["global_id"] == global_id
    assert result["subnet_id"] == "0001"
    assert result["ula_address"] == f"fdab:cdef:0123:0001::1"


def test_generate_ula_invalid_global_id_format():
    """Test error handling for invalid Global ID format."""
    result = generate_ipv6_ula(global_id="invalid-hex", subnet_id="0001")
    assert result["error"] is not None
    assert "Invalid Global ID format" in result["error"]


def test_generate_ula_invalid_global_id_length():
    """Test error handling for incorrect Global ID length."""
    result = generate_ipv6_ula(global_id="abc", subnet_id="0001")
    assert result["error"] is not None
    assert "Invalid Global ID format" in result["error"]
    result = generate_ipv6_ula(global_id="abcdef012345", subnet_id="0001")
    assert result["error"] is not None
    assert "Invalid Global ID format" in result["error"]


def test_generate_ula_invalid_subnet_id_format():
    """Test error handling for invalid Subnet ID format."""
    result = generate_ipv6_ula(subnet_id="wxyz")
    assert result["error"] is not None
    assert "Invalid Subnet ID format" in result["error"]


def test_generate_ula_invalid_subnet_id_length():
    """Test error handling for incorrect Subnet ID length."""
    result = generate_ipv6_ula(subnet_id="123")
    assert result["error"] is not None
    assert "Invalid Subnet ID format" in result["error"]
    result = generate_ipv6_ula(subnet_id="12345")
    assert result["error"] is not None
    assert "Invalid Subnet ID format" in result["error"]
