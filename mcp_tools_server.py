"""
Model Context Protocol (MCP) server implementation for IT Tools API.
This implements an optional MCP server alongside the existing FastAPI application.
"""

# pylint: disable=unused-import
import logging
import os

# Import all modules to ensure all tools, prompts, and resources are registered
import mcp_server.prompts
import mcp_server.tools

# Import the global FastMCP instance
from mcp_server import mcp_app as it_tools_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")


if __name__ == "__main__":
    # Get the host and port from environment variables
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    # Start the MCP server using the global instance
    logger.info(f"Starting MCP server on {host}:{port}...")
    it_tools_mcp.run()
