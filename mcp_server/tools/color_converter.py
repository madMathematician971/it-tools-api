"""
Color conversion tool for MCP server using the colour library.
"""

import logging
from typing import Any, Optional, Union

from colour import Color

from mcp_server import mcp_app

logger = logging.getLogger(__name__)

# Supported target formats (HSV removed for now)
SUPPORTED_TARGET_FORMATS = ["hex", "hex_verbose", "rgb", "rgb_fraction", "hsl", "web", "luminance"]


@mcp_app.tool()
def convert_color(input_color: str, target_format: str) -> dict[str, Any]:
    """
    Convert a color string between different formats (hex, rgb, hsl, etc.).

    Args:
        input_color: The color string to convert (e.g., "#ff0000", "rgb(255,0,0)", "red").
                     Note: The underlying library works best with hex codes or standard web names.
        target_format: The desired output format (e.g., "hex", "rgb", "hsl", "web", "luminance").
                     Supported: {SUPPORTED_TARGET_FORMATS}

    Returns:
        A dictionary containing:
            result: The converted color value (string or float).
            input_color: The original input color string.
            target_format: The requested target format.
            parsed_hex: The color represented as a hex string (e.g., "#ff0000").
            parsed_rgb: The color represented as an rgb string (e.g., "rgb(255, 0, 0)").
            parsed_hsl: The color represented as an hsl string (e.g., "hsl(0, 100%, 50%)").
            error: An error message string if conversion failed, otherwise None.
    """
    # Initial input validation
    if not input_color or input_color.isspace():
        error_msg = "Input color string cannot be empty."
        logger.warning(error_msg)
        # Return structure consistent with other errors
        return {
            "result": None,
            "input_color": input_color,
            "target_format": target_format,
            "parsed_hex": None,
            "parsed_rgb": None,
            "parsed_hsl": None,
            "error": error_msg,
        }

    try:
        c = Color(input_color)
    except Exception as e:
        error_msg = f"Could not parse input color: '{input_color}'. Error: {e}"
        logger.warning(error_msg)
        return {
            "result": None,
            "input_color": input_color,
            "target_format": target_format,
            "parsed_hex": None,
            "parsed_rgb": None,
            "parsed_hsl": None,
            "error": error_msg,
        }

    normalized_target = target_format.lower()
    result_value: Union[str, float, None] = None  # Use Union
    error_msg: Optional[str] = None

    # Check target format validity before proceeding
    if normalized_target not in SUPPORTED_TARGET_FORMATS:
        error_msg = f"Unsupported target_format: '{target_format}'. Supported: {SUPPORTED_TARGET_FORMATS}"
        logger.warning(error_msg)
        # Return early if target format is invalid
        return {
            "result": None,
            "input_color": input_color,
            "target_format": target_format,
            "parsed_hex": None,
            "parsed_rgb": None,
            "parsed_hsl": None,  # Should not attempt parsing if target is invalid
            "error": error_msg,
        }

    try:
        # Calculate standard representations first (only if target format is valid)
        parsed_hex = c.hex_l  # Use long hex format for consistency
        r_int, g_int, b_int = [int(x * 255) for x in c.rgb]
        parsed_rgb = f"rgb({r_int}, {g_int}, {b_int})"
        h_deg_hsl, s_hsl, l_hsl = (
            round(c.hsl[0] * 360),
            round(c.hsl[1] * 100),
            round(c.hsl[2] * 100),
        )
        parsed_hsl = f"hsl({h_deg_hsl}, {s_hsl}%, {l_hsl}%)"

        # Determine the target result (removed hsv case)
        if normalized_target == "hex":
            result_value = c.hex  # Short hex
        elif normalized_target == "hex_verbose":
            result_value = c.hex_l  # Long hex
        elif normalized_target == "rgb":
            result_value = parsed_rgb  # Use the calculated integer rgb string
        elif normalized_target == "rgb_fraction":
            result_value = str(c.rgb)  # Tuple of floats as string
        elif normalized_target == "hsl":
            result_value = parsed_hsl  # Use the calculated integer hsl string
        # Removed HSV case
        # elif normalized_target == "hsv":
        #     ...
        elif normalized_target == "web":
            result_value = c.web
        elif normalized_target == "luminance":
            result_value = c.luminance
        # The else case for unsupported format is now handled earlier

    except Exception as e:
        error_msg = f"Internal error converting color '{input_color}' to '{target_format}': {e}"
        logger.error(error_msg, exc_info=True)
        # Ensure parsed values are None if conversion fails mid-way
        parsed_hex = None
        parsed_rgb = None
        parsed_hsl = None

    return {
        "result": result_value,
        "input_color": input_color,
        "target_format": target_format,
        "parsed_hex": parsed_hex,
        "parsed_rgb": parsed_rgb,
        "parsed_hsl": parsed_hsl,
        "error": error_msg,
    }
