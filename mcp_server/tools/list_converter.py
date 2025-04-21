"""
List converter tool for MCP server.
"""

import logging
import re
from enum import Enum
from typing import Any

from mcp_server import mcp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListFormat(str, Enum):
    COMMA_SEPARATED = "comma"
    NEWLINE_SEPARATED = "newline"
    SPACE_SEPARATED = "space"
    SEMICOLON_SEPARATED = "semicolon"
    BULLET_ASTERISK = "bullet_asterisk"  # * item
    BULLET_HYPHEN = "bullet_hyphen"  # - item
    NUMBERED_DOT = "numbered_dot"  # 1. item
    NUMBERED_PAREN = "numbered_paren"  # 1) item


# Helper to parse input based on format
def _parse_list(text: str, input_format: ListFormat, ignore_empty: bool, trim_items: bool) -> list[str]:
    items = []
    if input_format == ListFormat.COMMA_SEPARATED:
        items = text.split(",")
    elif input_format == ListFormat.NEWLINE_SEPARATED:
        items = text.splitlines()
    elif input_format == ListFormat.SPACE_SEPARATED:
        items = text.split()
    elif input_format == ListFormat.SEMICOLON_SEPARATED:
        items = text.split(";")
    elif input_format in [
        ListFormat.BULLET_ASTERISK,
        ListFormat.BULLET_HYPHEN,
        ListFormat.NUMBERED_DOT,
        ListFormat.NUMBERED_PAREN,
    ]:
        lines = text.splitlines()
        for line in lines:
            cleaned_line = line.strip()
            if input_format == ListFormat.BULLET_ASTERISK and cleaned_line.startswith("*"):
                item_text = cleaned_line[1:]
                items.append(item_text.strip() if trim_items else item_text)
            elif input_format == ListFormat.BULLET_HYPHEN and cleaned_line.startswith("-"):
                item_text = cleaned_line[1:]
                items.append(item_text.strip() if trim_items else item_text)
            elif input_format == ListFormat.NUMBERED_DOT and re.match(r"^\d+\.\s*", cleaned_line):
                item_text = re.sub(r"^\d+\.\s*", "", cleaned_line)
                items.append(item_text.strip() if trim_items else item_text)
            elif input_format == ListFormat.NUMBERED_PAREN and re.match(r"^\d+\)\s*", cleaned_line):
                item_text = re.sub(r"^\d+\)\s*", "", cleaned_line)
                items.append(item_text.strip() if trim_items else item_text)
            elif not ignore_empty and cleaned_line:
                items.append(cleaned_line.strip() if trim_items else cleaned_line)
            # If ignore_empty is true, non-matching lines are skipped

    else:
        # Fallback or error? Defaulting to newline for unknown input format for now.
        logger.warning(f"Unknown input format '{input_format}', attempting newline split.")
        items = text.splitlines()

    if trim_items:
        items = [item.strip() for item in items]
    if ignore_empty:
        items = [item for item in items if item]

    return items


# Helper to format output based on format
def _format_list(items: list[str], output_format: ListFormat) -> str:
    if not items:
        return ""

    if output_format == ListFormat.COMMA_SEPARATED:
        return ",".join(items)
    elif output_format == ListFormat.NEWLINE_SEPARATED:
        return "\n".join(items)
    elif output_format == ListFormat.SPACE_SEPARATED:
        return " ".join(items)
    elif output_format == ListFormat.SEMICOLON_SEPARATED:
        return ";".join(items)
    elif output_format == ListFormat.BULLET_ASTERISK:
        return "\n".join([f"* {item}" for item in items])
    elif output_format == ListFormat.BULLET_HYPHEN:
        return "\n".join([f"- {item}" for item in items])
    elif output_format == ListFormat.NUMBERED_DOT:
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    elif output_format == ListFormat.NUMBERED_PAREN:
        return "\n".join([f"{i+1}) {item}" for i, item in enumerate(items)])
    else:
        logger.error(f"Unknown output format requested: {output_format}")
        raise ValueError(f"Unsupported output format: {output_format}")


@mcp_app.tool()
def convert_list(
    input_text: str, input_format: str, output_format: str, ignore_empty: bool = True, trim_items: bool = True
) -> dict[str, Any]:
    """
    Converts list items from one text format (e.g., comma-separated)
    to another (e.g., bullet points).

    Args:
        input_text: The list text to convert
        input_format: Format of the input list (comma, newline, space, semicolon, bullet_asterisk, bullet_hyphen, numbered_dot, numbered_paren)
        output_format: Desired format for the output list (comma, newline, space, semicolon, bullet_asterisk, bullet_hyphen, numbered_dot, numbered_paren)
        ignore_empty: Ignore empty lines or items during conversion
        trim_items: Trim whitespace from each list item

    Returns:
        A dictionary containing:
            result: The list converted to the desired output format
            error: Optional error message
    """
    try:
        # Validate input and output formats
        try:
            input_format_enum = ListFormat(input_format)
        except ValueError:
            valid_formats = [f.value for f in ListFormat]
            return {"result": "", "error": f"Invalid input format. Valid formats: {', '.join(valid_formats)}"}

        try:
            output_format_enum = ListFormat(output_format)
        except ValueError:
            valid_formats = [f.value for f in ListFormat]
            return {"result": "", "error": f"Invalid output format. Valid formats: {', '.join(valid_formats)}"}

        # Parse and format the list
        parsed_items = _parse_list(
            input_text,
            input_format_enum,
            ignore_empty,
            trim_items,
        )
        formatted_result = _format_list(parsed_items, output_format_enum)
        return {"result": formatted_result, "error": None}

    except ValueError as ve:
        # Re-raise ValueError for MCP framework to handle
        return {"result": "", "error": str(ve)}
    except Exception as e:
        logger.error(
            f"Error converting list from {input_format} to {output_format}: {e}",
            exc_info=True,
        )
        # Return error information
        return {"result": "", "error": f"Internal server error during list conversion: {str(e)}"}
