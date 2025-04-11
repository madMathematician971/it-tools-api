import ipaddress
import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from models.ipv4_converter_models import IPv4Input, IPv4Output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipv4-converter", tags=["IPv4 Address Converter"])


@router.post("/", response_model=IPv4Output)
async def convert_ipv4(input_data: IPv4Input):
    """Convert IPv4 addresses between different formats (dotted decimal, decimal, hexadecimal, binary)."""
    ip_address = ""  # Initialize for error handling case
    try:
        ip_address = input_data.ip_address.strip()
        if not ip_address:
            # Return 200 OK with error message for consistency
            return IPv4Output(
                original=ip_address,
                dotted_decimal="",
                decimal=0,
                hexadecimal="",
                binary="",
                error="IP address cannot be empty",
            )

        # Try to determine format and convert to numeric value
        numeric_value = detect_and_convert_ip(ip_address, input_data.format)

        # Create output in all formats
        dotted_decimal = str(ipaddress.IPv4Address(numeric_value))
        decimal = int(numeric_value)
        hexadecimal = "0x" + format(decimal, "08X")

        # Binary representation (32 bits with leading zeros)
        binary = format(decimal, "032b")

        return IPv4Output(
            original=ip_address, dotted_decimal=dotted_decimal, decimal=decimal, hexadecimal=hexadecimal, binary=binary
        )

    except ValueError as ve:
        logger.warning(f"Invalid IP address format: {ve}")
        return IPv4Output(
            original=ip_address,
            dotted_decimal="",
            decimal=0,
            hexadecimal="",
            binary="",
            error=f"Invalid IP address format: {str(ve)}",
        )
    except Exception as e:
        logger.error(f"Error converting IPv4 address: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert IPv4 address: {str(e)}"
        )


def detect_and_convert_ip(ip_string: str, format_hint: Optional[str] = None) -> int:
    """Detect the format of an IP address string and convert it to a numeric value."""
    # If format hint is provided, use it
    if format_hint:
        if format_hint == "dotted":
            return int(ipaddress.IPv4Address(ip_string))
        elif format_hint == "decimal":
            try:
                decimal = int(ip_string.strip())
                if decimal < 0 or decimal > 4294967295:  # 2^32 - 1
                    raise ValueError("Decimal IP must be between 0 and 4294967295")
                return decimal
            except ValueError:
                raise ValueError("Invalid decimal IP format")
        elif format_hint == "hex":
            hex_match = re.match(r"^0x([0-9A-Fa-f]{1,8})$", ip_string.strip())
            if not hex_match:
                hex_match = re.match(r"^([0-9A-Fa-f]{1,8})$", ip_string.strip())
                if not hex_match:
                    raise ValueError("Invalid hexadecimal IP format")
                return int(hex_match.group(1), 16)
            return int(hex_match.group(1), 16)
        elif format_hint == "binary":
            binary_match = re.match(r"^([01]{1,32})$", ip_string.strip())
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
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip_string):
        try:
            return int(ipaddress.IPv4Address(ip_string))
        except ValueError:  # Catch specific ipaddress error
            raise ValueError("Invalid dotted decimal IP format")

    # Try hexadecimal format (e.g., 0xC0A80101)
    if re.match(r"^0x[0-9A-Fa-f]{1,8}$", ip_string):
        return int(ip_string[2:], 16)

    # Try plain hexadecimal format (without 0x prefix, must contain A-F)
    if re.match(r"^[0-9A-Fa-f]{1,8}$", ip_string) and any(c in "ABCDEFabcdef" for c in ip_string):
        return int(ip_string, 16)

    # Try binary format FIRST (e.g., 1100...)
    if re.match(r"^[01]+$", ip_string):
        if len(ip_string) > 32:
            raise ValueError("Binary IP must be at most 32 bits")
        # Pad shorter binary strings
        binary_padded = ip_string.zfill(32)
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
