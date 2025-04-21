"""
Basic Authentication header generator tool for MCP server.
"""

import base64
import logging
from typing import Any

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def generate_basic_auth_header(username: str, password: str) -> dict[str, Any]:
    """
    Generate a Basic Authentication HTTP header value from username and password.

    Args:
        username: The username.
        password: The password.

    Returns:
        A dictionary containing:
            username: The input username.
            password: The input password.
            base64: The Base64 encoded username:password string.
            header: The full "Basic <base64>" header value.
            error: Optional error message.
    """
    try:
        if not isinstance(username, str) or not isinstance(password, str):
            return {"error": "Username and password must be strings."}

        credentials = f"{username}:{password}"
        encoded_credentials_bytes = base64.b64encode(credentials.encode("utf-8"))
        encoded_credentials_str = encoded_credentials_bytes.decode("utf-8")
        header_value = f"Basic {encoded_credentials_str}"

        return {
            "username": username,
            "password": password,
            "base64": encoded_credentials_str,
            "header": header_value,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Error generating Basic Auth header for user '{username}': {e}", exc_info=True)
        return {"error": f"Internal error generating header: {str(e)}"}
