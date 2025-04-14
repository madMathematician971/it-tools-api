"""
JSON formatter and minifier tool for MCP server.
"""

import json

from mcp_server import mcp_app


@mcp_app.tool()
def format_json(json_string: str, indent: int = 4, sort_keys: bool = False) -> dict:
    """
    Format JSON string with proper indentation and optional key sorting.

    Args:
        json_string: The JSON string to format
        indent: Number of spaces for indentation
        sort_keys: Whether to sort keys alphabetically

    Returns:
        A dictionary containing:
            result_string: The formatted JSON string
            error: Optional error message
    """
    try:
        # Parse the JSON string
        parsed = json.loads(json_string)

        # Format with proper indentation and sorting
        formatted = json.dumps(parsed, indent=indent, sort_keys=sort_keys, ensure_ascii=False)

        return {"result_string": formatted, "error": None}
    except json.JSONDecodeError as e:
        return {"result_string": "", "error": f"Invalid JSON input: {e}"}
    except Exception as e:
        return {"result_string": "", "error": f"Error formatting JSON: {e}"}


@mcp_app.tool()
def minify_json(json_string: str) -> dict:
    """
    Minify a JSON string (remove unnecessary whitespace).

    Args:
        json_string: The JSON string to minify

    Returns:
        A dictionary containing:
            result_string: The minified JSON string
            error: Optional error message
    """
    try:
        # Parse the JSON string
        parsed = json.loads(json_string)

        # Minify (most compact form)
        minified = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)

        return {"result_string": minified, "error": None}
    except json.JSONDecodeError as e:
        return {"result_string": "", "error": f"Invalid JSON input: {e}"}
    except Exception as e:
        return {"result_string": "", "error": f"Error minifying JSON: {e}"}
