"""
Chmod permission calculator tools for MCP server.
"""

import logging

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def calculate_numeric_chmod(
    owner_read: bool,
    owner_write: bool,
    owner_execute: bool,
    group_read: bool,
    group_write: bool,
    group_execute: bool,
    others_read: bool,
    others_write: bool,
    others_execute: bool,
) -> dict:
    """
    Calculate the numeric (octal) chmod value from symbolic permissions.

    Args:
        owner_read: Owner read permission.
        owner_write: Owner write permission.
        owner_execute: Owner execute permission.
        group_read: Group read permission.
        group_write: Group write permission.
        group_execute: Group execute permission.
        others_read: Others read permission.
        others_write: Others write permission.
        others_execute: Others execute permission.

    Returns:
        A dictionary containing:
            numeric_chmod: The calculated 3-digit octal string (e.g., "755").
            error: An error message string if calculation failed, otherwise None.
    """
    try:
        owner_val = (4 if owner_read else 0) | (2 if owner_write else 0) | (1 if owner_execute else 0)
        group_val = (4 if group_read else 0) | (2 if group_write else 0) | (1 if group_execute else 0)
        others_val = (4 if others_read else 0) | (2 if others_write else 0) | (1 if others_execute else 0)

        numeric_str = f"{owner_val}{group_val}{others_val}"
        logger.info(f"Calculated numeric chmod: {numeric_str}")
        return {"numeric_chmod": numeric_str, "error": None}
    except Exception as e:
        error_msg = f"An unexpected error occurred during numeric chmod calculation: {e}"
        logger.error(error_msg, exc_info=True)
        return {"numeric_chmod": "", "error": error_msg}


@mcp_app.tool()
def calculate_symbolic_chmod(numeric_chmod_string: str) -> dict:
    """
    Convert a numeric chmod value (e.g., 755, "755", "0755") to symbolic representation.

    Args:
        numeric_chmod_string: The numeric chmod value as a string (1, 3 or 4 digits).

    Returns:
        A dictionary containing:
            symbolic_chmod: The calculated symbolic string (e.g., "rwxr-xr-x").
            error: An error message string if conversion failed, otherwise None.
    """
    try:
        numeric_str = numeric_chmod_string.strip()

        # Handle optional leading 0 for 4-digit input
        if len(numeric_str) == 4 and numeric_str.startswith("0"):
            numeric_str = numeric_str[1:]

        # Handle single digit 0-7 as applying to 'others'
        if len(numeric_str) == 1 and numeric_str.isdigit():
            single_digit = int(numeric_str)
            if 0 <= single_digit <= 7:
                digits = [0, 0, single_digit]
            else:
                # If single digit is invalid (e.g., 8), it will fail the next check
                pass  # Let the main validation catch digits > 7
        elif not numeric_str.isdigit() or len(numeric_str) != 3:
            raise ValueError("Numeric value must resolve to 3 digits (e.g., 755 or 0755).")
        else:
            # Regular 3-digit case
            digits = [int(d) for d in numeric_str]

        # Validate digits after determining them
        if "digits" not in locals() or not all(0 <= d <= 7 for d in digits):
            raise ValueError("Each digit must be between 0 and 7.")

        def get_symbol(val):
            r = "r" if (val & 4) else "-"
            w = "w" if (val & 2) else "-"
            x = "x" if (val & 1) else "-"
            return f"{r}{w}{x}"

        symbolic_str = f"{get_symbol(digits[0])}{get_symbol(digits[1])}{get_symbol(digits[2])}"
        logger.info(f"Calculated symbolic chmod for {numeric_chmod_string}: {symbolic_str}")
        return {"symbolic_chmod": symbolic_str, "error": None}

    except ValueError as e:
        error_msg = f"Invalid numeric input: {e}"
        logger.warning(error_msg)
        return {"symbolic_chmod": "", "error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred during symbolic chmod calculation: {e}"
        logger.error(error_msg, exc_info=True)
        return {"symbolic_chmod": "", "error": error_msg}
