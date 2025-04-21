"""
Base64 encoding/decoding tool for MCP server.
"""

import base64
import logging

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def base64_encode_string(input_string: str) -> dict:
    """
    Encode a string to Base64.

    Args:
        input_string: The string to encode.

    Returns:
        A dictionary containing:
            result_string: The Base64 encoded string.
            error: Optional error message.
    """
    try:
        input_bytes = input_string.encode("utf-8")
        encoded_bytes = base64.b64encode(input_bytes)
        return {"result_string": encoded_bytes.decode("utf-8"), "error": None}
    except Exception as e:
        logger.error(f"Error encoding Base64: {e}", exc_info=True)
        return {"result_string": "", "error": f"Error encoding Base64: {e}"}


@mcp_app.tool()
def base64_decode_string(input_string: str) -> dict:
    """
    Decode a Base64 string.

    Args:
        input_string: The Base64 string to decode.

    Returns:
        A dictionary containing:
            result_string: The decoded string.
            error: Optional error message.
    """
    try:
        input_bytes = input_string.encode("utf-8")
        # Add padding if necessary
        missing_padding = len(input_bytes) % 4
        if missing_padding:
            input_bytes += b"=" * (4 - missing_padding)
        decoded_bytes = base64.b64decode(input_bytes, validate=True)
        return {"result_string": decoded_bytes.decode("utf-8"), "error": None}
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.warning(f"Error decoding Base64: {e}")
        return {"result_string": "", "error": "Invalid Base64 input string."}
    except Exception as e:
        logger.error(f"Error decoding Base64: {e}", exc_info=True)
        return {"result_string": "", "error": f"Error decoding Base64: {e}"}
