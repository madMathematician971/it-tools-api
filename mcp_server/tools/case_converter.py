"""
Case conversion tool for MCP server using the caseconverter library.
"""

import logging

import caseconverter

from mcp_server import mcp_app

logger = logging.getLogger(__name__)

# Define supported cases and map them to corresponding functions
# Using library functions directly where possible for maintainability
SUPPORTED_CASES = {
    "camel": caseconverter.camelcase,
    "snake": caseconverter.snakecase,
    "pascal": caseconverter.pascalcase,
    "constant": caseconverter.macrocase,  # Mapped to macrocase
    "kebab": caseconverter.kebabcase,
    "capital": caseconverter.titlecase,  # Mapped to titlecase
    "lower": lambda s: s.lower(),
    "upper": lambda s: s.upper(),
}


@mcp_app.tool()
def convert_case(input_string: str, target_case: str) -> dict:
    """
    Convert an input string to a specified case format.

    Args:
        input_string: The string to convert.
        target_case: The target case format (e.g., 'camel', 'snake', 'pascal',
                     'constant', 'kebab', 'capital', 'lower', 'upper').

    Returns:
        A dictionary containing:
            result: The converted string.
            error: An error message string if conversion failed, otherwise None.
    """
    normalized_target_case = target_case.lower()

    if normalized_target_case not in SUPPORTED_CASES:
        error_msg = f"Invalid target_case: '{target_case}'. Supported cases: {list(SUPPORTED_CASES.keys())}"
        logger.warning(error_msg)
        return {"result": "", "error": error_msg}

    conversion_func = SUPPORTED_CASES.get(normalized_target_case)

    if not conversion_func:
        error_msg = f"Case conversion function for '{target_case}' not found internally, though it passed validation."
        logger.error(error_msg)  # Should not happen
        return {"result": "", "error": error_msg}

    try:
        result_string = conversion_func(input_string)
        logger.info(f"Converted string to {normalized_target_case} case.")
        return {"result": result_string, "error": None}
    except AttributeError as e:
        # This might occur if the caseconverter library version lacks an expected function
        error_msg = f"Case '{target_case}' might not be supported by the installed caseconverter library version: {e}"
        logger.error(error_msg, exc_info=True)
        return {"result": "", "error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred during case conversion: {e}"
        logger.error(error_msg, exc_info=True)
        return {"result": "", "error": error_msg}
