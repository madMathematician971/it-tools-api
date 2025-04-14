"""
Roman numeral converter tool for MCP server.
"""

import logging
import re
from typing import Any

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Roman numeral mapping (descending order for easy conversion)
ROMAN_MAP = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

# Reverse mapping for decoding
DECIMAL_MAP = {v: k for k, v in ROMAN_MAP}


@mcp_app.tool()
def encode_to_roman(number: int) -> dict[str, Any]:
    """
    Convert an integer (1-3999) to its Roman numeral representation.

    Args:
        number: Integer to convert to Roman numerals (1-3999)

    Returns:
        A dictionary containing:
            input_value: Original input (integer)
            result: Conversion result (Roman numeral)
            error: Optional error message
    """
    try:
        # Validate input range
        if not 1 <= number <= 3999:
            return {"input_value": number, "result": "", "error": "Number must be between 1 and 3999"}

        result = ""
        num = number
        for value, numeral in ROMAN_MAP:
            while num >= value:
                result += numeral
                num -= value

        return {"input_value": number, "result": result, "error": None}

    except Exception as e:
        logger.error(f"Error encoding to Roman numeral: {e}", exc_info=True)
        return {"input_value": number, "result": "", "error": f"Failed to encode: {str(e)}"}


@mcp_app.tool()
def decode_from_roman(roman_numeral: str) -> dict[str, Any]:
    """
    Convert a Roman numeral string to its integer representation.

    Args:
        roman_numeral: Roman numeral string to convert to integer

    Returns:
        A dictionary containing:
            input_value: Original input (Roman numeral)
            result: Conversion result (integer)
            error: Optional error message
    """
    try:
        # Validate basic format (only valid characters)
        roman_numeral = roman_numeral.upper()
        if not re.match(r"^[MDCLXVI]+$", roman_numeral):
            return {
                "input_value": roman_numeral,
                "result": 0,
                "error": "Invalid characters in Roman numeral. Only M, D, C, L, X, V, I are allowed.",
            }

        result = 0
        i = 0
        while i < len(roman_numeral):
            # Check for two-character subtractive combinations (e.g., CM, IX)
            if i + 1 < len(roman_numeral) and roman_numeral[i : i + 2] in DECIMAL_MAP:
                result += DECIMAL_MAP[roman_numeral[i : i + 2]]
                i += 2
            # Otherwise, process single character
            elif roman_numeral[i] in DECIMAL_MAP:
                result += DECIMAL_MAP[roman_numeral[i]]
                i += 1
            else:
                # Should not happen given the regex check, but for safety
                return {
                    "input_value": roman_numeral,
                    "result": 0,
                    "error": f"Invalid Roman numeral symbol encountered: {roman_numeral[i]}",
                }

        # Check for validity by re-encoding. This catches non-standard forms.
        # Need to handle potential errors in re-encoding
        try:
            if 1 <= result <= 3999:  # Only re-validate if within valid range
                re_encoded = encode_to_roman(result)
                if re_encoded.get("error") or re_encoded.get("result") != roman_numeral:
                    return {
                        "input_value": roman_numeral,
                        "result": result,
                        "error": "Warning: Roman numeral is not in standard form.",
                    }
        except Exception:
            # Tolerate re-encoding check failures but log them
            logger.warning(f"Re-encoding check failed for {roman_numeral} -> {result}")

        return {"input_value": roman_numeral, "result": result, "error": None}

    except ValueError as ve:
        return {"input_value": roman_numeral, "result": 0, "error": f"Invalid Roman numeral: {str(ve)}"}
    except Exception as e:
        logger.error(f"Error decoding Roman numeral: {e}", exc_info=True)
        return {"input_value": roman_numeral, "result": 0, "error": f"Failed to decode: {str(e)}"}
