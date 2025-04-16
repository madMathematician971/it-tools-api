"""Tool for encoding and decoding HTML entities."""

import html
import logging
from typing import Any

logger = logging.getLogger(__name__)


def encode_html_entities(text: str) -> dict[str, Any]:
    """
    Encode special characters in text into HTML entities.

    Uses html.escape() with quote=True.

    Args:
        text: The input string.

    Returns:
        A dictionary containing:
            result: The encoded string.
            error: An error message if encoding failed.
    """
    try:
        encoded_text = html.escape(text, quote=True)
        return {"result": encoded_text, "error": None}
    except Exception as e:
        logger.error(f"Error encoding HTML entities: {e}", exc_info=True)
        return {"result": None, "error": f"Internal server error during encoding: {str(e)}"}


def decode_html_entities(text: str) -> dict[str, Any]:
    """
    Decode HTML entities in text back into characters.

    Uses html.unescape().

    Args:
        text: The input string containing HTML entities.

    Returns:
        A dictionary containing:
            result: The decoded string.
            error: An error message if decoding failed.
    """
    try:
        decoded_text = html.unescape(text)
        return {"result": decoded_text, "error": None}
    except Exception as e:
        logger.error(f"Error decoding HTML entities: {e}", exc_info=True)
        return {"result": None, "error": f"Internal server error during decoding: {str(e)}"}
