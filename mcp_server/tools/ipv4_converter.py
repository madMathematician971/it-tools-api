"""Tool for converting IPv4 addresses between different formats."""

import ipaddress
import logging
import re
from typing import Any, Optional

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


def _detect_and_convert_ip(ip_string: str, format_hint: Optional[str] = None) -> int:
    """Detect the format of an IP address string and convert it to a numeric value."""
    # If format hint is provided, use it
    if format_hint:
        format_hint = format_hint.lower()
        if format_hint == "dotted":
            return int(ipaddress.IPv4Address(ip_string.strip()))
        elif format_hint == "decimal":
            try:
                decimal = int(ip_string.strip())
                if decimal < 0 or decimal > 4294967295:  # 2^32 - 1
                    raise ValueError("Decimal IP must be between 0 and 4294967295")
                return decimal
            except ValueError as e:
                # Re-raise with a clearer message if needed
                raise ValueError("Invalid decimal IP format") from e
        elif format_hint == "hex":
            ip_stripped = ip_string.strip()
            hex_match = re.match(r"^0x([0-9A-Fa-f]{1,8})$", ip_stripped, re.IGNORECASE)
            if not hex_match:
                hex_match = re.match(r"^([0-9A-Fa-f]{1,8})$", ip_stripped, re.IGNORECASE)
                if not hex_match:
                    raise ValueError("Invalid hexadecimal IP format")
            return int(hex_match.group(1), 16)
        elif format_hint == "binary":
            ip_stripped = ip_string.strip()
            # Remove potential spaces often found in binary representations
            ip_stripped = ip_stripped.replace(" ", "")
            binary_match = re.match(r"^([01]{1,32})$", ip_stripped)
            if not binary_match:
                raise ValueError("Invalid binary IP format")
            # Pad to 32 bits if needed
            binary = binary_match.group(1).zfill(32)
            return int(binary, 2)
        else:
            raise ValueError(f"Unknown format hint: {format_hint}")

    # Auto-detect format
    ip_string = ip_string.strip()

    # Try dotted decimal format (e.g., 192.168.1.1)
    # Improved regex to better handle valid ranges (0-255)
    if re.match(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip_string
    ):
        try:
            # ipaddress already validates ranges
            return int(ipaddress.IPv4Address(ip_string))
        except ValueError:  # Catch specific ipaddress error
            # This might happen if regex passes but ipaddress lib finds issue (e.g., leading zeros?)
            raise ValueError("Invalid dotted decimal IP format")

    # Try hexadecimal format (e.g., 0xC0A80101)
    if re.match(r"^0x[0-9A-Fa-f]{1,8}$", ip_string, re.IGNORECASE):
        return int(ip_string[2:], 16)

    # Try plain hexadecimal format (without 0x prefix, must contain A-F)
    # Ensure it's not mistaken for decimal if it contains A-F
    if re.match(r"^[0-9A-Fa-f]{1,8}$", ip_string, re.IGNORECASE) and any(c in "ABCDEFabcdef" for c in ip_string):
        return int(ip_string, 16)

    # Try binary format (e.g., 1100...)
    # Allow spaces in binary input for readability
    binary_cleaned = ip_string.replace(" ", "")
    if re.match(r"^[01]+$", binary_cleaned):
        if len(binary_cleaned) > 32:
            raise ValueError("Binary IP must be at most 32 bits")
        # Pad shorter binary strings
        binary_padded = binary_cleaned.zfill(32)
        return int(binary_padded, 2)

    # Try decimal format LAST (e.g., 3232235777)
    if re.match(r"^\d+$", ip_string):
        try:
            decimal = int(ip_string)
            if decimal < 0 or decimal > 4294967295:  # 2^32 - 1
                raise ValueError("Decimal IP must be between 0 and 4294967295")
            return decimal
        except ValueError as e:
            # If int() fails for a huge number it raises ValueError, catch it
            raise ValueError("Invalid or out-of-range decimal IP format") from e

    raise ValueError("Could not determine IP address format")


@mcp_app.tool()
def convert_ipv4(ip_address: str, format_hint: Optional[str] = None) -> dict[str, Any]:
    """
    Convert an IPv4 address between dotted decimal, decimal, hexadecimal, and binary formats.

    Args:
        ip_address: The IP address string in dotted, decimal, hex, or binary format.
        format_hint: Optional hint ('dotted', 'decimal', 'hex', 'binary') to specify input format.

    Returns:
        A dictionary containing:
            original: The original input string.
            dotted_decimal: IP in dotted decimal format (e.g., "192.168.1.1").
            decimal: IP as an integer (e.g., 3232235777).
            hexadecimal: IP in hexadecimal format (e.g., "0xC0A80101").
            binary: IP in 32-bit binary format.
            error: An error message if conversion failed.
    """
    original_input = ip_address  # Store original before stripping
    ip_address_stripped = ip_address.strip()

    if not ip_address_stripped:
        return {
            "original": original_input,
            "dotted_decimal": None,
            "decimal": None,
            "hexadecimal": None,
            "binary": None,
            "error": "IP address cannot be empty",
        }

    try:
        numeric_value = _detect_and_convert_ip(ip_address_stripped, format_hint)

        # Create output in all formats
        dotted_decimal = str(ipaddress.IPv4Address(numeric_value))
        decimal_val = int(numeric_value)
        hexadecimal = "0x" + format(decimal_val, "08X")
        # Binary representation (32 bits with leading zeros)
        binary = format(decimal_val, "032b")

        return {
            "original": original_input,
            "dotted_decimal": dotted_decimal,
            "decimal": decimal_val,
            "hexadecimal": hexadecimal,
            "binary": binary,
            "error": None,
        }

    except ValueError as ve:
        logger.info(f"Invalid IP address '{original_input}': {ve}")
        return {
            "original": original_input,
            "dotted_decimal": None,
            "decimal": None,
            "hexadecimal": None,
            "binary": None,
            "error": f"Invalid IP address format: {str(ve)}",
        }
    except Exception as e:
        logger.error(f"Error converting IPv4 '{original_input}': {e}", exc_info=True)
        return {
            "original": original_input,
            "dotted_decimal": None,
            "decimal": None,
            "hexadecimal": None,
            "binary": None,
            "error": f"An unexpected error occurred: {str(e)}",
        }
