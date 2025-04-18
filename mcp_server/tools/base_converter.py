"""
Base converter tool for MCP server.
"""

import string

from mcp_server import mcp_app


def int_to_base(n: int, base: int) -> str:
    """Convert an integer to a string representation in the specified base."""
    if n == 0:
        return "0"
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36")

    digits = string.digits + string.ascii_lowercase
    result = ""
    is_negative = n < 0
    n = abs(n)

    while n > 0:
        result = digits[n % base] + result
        n //= base

    return ("-" if is_negative else "") + result


@mcp_app.tool()
def base_convert(number_string: str, input_base: int, output_base: int) -> dict:
    """
    Convert a number between different numerical bases (2-36).

    Args:
        number_string: The number to convert (as a string)
        input_base: The base of the input number (2-36)
        output_base: The target base for conversion (2-36)

    Returns:
        A dictionary containing:
            result_string: The converted number as a string
            input_number_string: The original input number string
            input_base: The base of the input number
            output_base: The target base for conversion
    """
    # Validate base ranges
    if not 2 <= input_base <= 36:
        raise ValueError(f"Input base must be between 2 and 36, got {input_base}")
    if not 2 <= output_base <= 36:
        raise ValueError(f"Output base must be between 2 and 36, got {output_base}")

    # Convert input string in input_base to integer (base 10)
    try:
        input_number_int = int(number_string, input_base)
    except ValueError:
        raise ValueError(f"Invalid digits for base {input_base} in number: {number_string}")

    # Convert integer (base 10) to output_base string
    result_str = int_to_base(input_number_int, output_base)

    # Return structured result
    return {
        "result_string": result_str,
        "input_number_string": number_string,
        "input_base": input_base,
        "output_base": output_base,
    }
