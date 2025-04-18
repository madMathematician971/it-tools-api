"""MCP Tool for generating IPv6 Unique Local Addresses (ULA)."""

import logging
import secrets
from typing import Any

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def generate_ipv6_ula(
    global_id: str | None = None,
    subnet_id: str = "0001",
) -> dict[str, Any]:
    """
    Generate an IPv6 Unique Local Address (ULA) based on RFC 4193.

    Args:
        global_id: Optional 10-character hexadecimal Global ID. If None, generates randomly.
        subnet_id: 4-character hexadecimal Subnet ID (default: "0001").

    Returns:
        A dictionary containing:
            ula_address: An example IPv6 ULA address within the generated /64 prefix.
            global_id: The 10-character hex Global ID used (generated or provided).
            subnet_id: The 4-character hex Subnet ID used.
            error: Error message if generation failed.
    """
    try:
        # Validate Subnet ID format
        if not (len(subnet_id) == 4 and all(c in "0123456789abcdefABCDEF" for c in subnet_id)):
            return {"error": "Invalid Subnet ID format. Must be 4 hexadecimal characters."}
        subnet_id_hex = subnet_id.lower()

        # Validate or generate Global ID
        if global_id:
            if not (len(global_id) == 10 and all(c in "0123456789abcdefABCDEF" for c in global_id)):
                return {"error": "Invalid Global ID format. Must be 10 hexadecimal characters."}
            global_id_hex = global_id.lower()
        else:
            # Generate a random 40-bit Global ID
            global_id_int = secrets.randbits(40)
            global_id_hex = format(global_id_int, "010x")

        # Construct the example ULA address string directly
        # Format: fdXX:XXXX:XXXX:YYYY::1
        ula_address_str = f"fd{global_id_hex[:2]}:{global_id_hex[2:6]}:{global_id_hex[6:]}:{subnet_id_hex}::1"

        return {
            "ula_address": ula_address_str,
            "global_id": global_id_hex,
            "subnet_id": subnet_id_hex,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error generating IPv6 ULA: {e}", exc_info=True)
        return {"error": f"Internal server error during ULA generation: {str(e)}"}
