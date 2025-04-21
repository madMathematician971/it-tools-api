import logging
from typing import Any

import markdown

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
async def render_markdown(*, markdown_string: str) -> dict[str, Any | None]:
    """
    Convert a Markdown string to HTML using the python-markdown library.

    Args:
        markdown_string: The Markdown string to convert.

    Returns:
        A dictionary containing:
            html_string: The converted HTML string.
            error: An error message if conversion failed, otherwise None.
    """
    if not isinstance(markdown_string, str):
        return {"html_string": None, "error": "Input must be a string."}

    try:
        # Using common extensions for better compatibility
        html_content = markdown.markdown(markdown_string, extensions=["fenced_code", "tables"])
        return {"html_string": html_content, "error": None}
    except Exception as e:
        logger.exception(f"Error converting Markdown to HTML: {e}")
        return {"html_string": None, "error": f"Markdown conversion error: {e}"}
