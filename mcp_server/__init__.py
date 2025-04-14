"""
Model Context Protocol (MCP) implementation for IT Tools API.
"""

import logging
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp")


# Server lifespan context
@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage server lifecycle for the MCP application."""
    logger.info("Starting MCP server...")

    # Initialize any resources needed at startup
    context = {"startup_time": time.time()}

    try:
        yield context
    finally:
        # Clean up any resources on shutdown
        logger.info("Shutting down MCP server...")


# Get host and port from environment
host = os.environ.get("MCP_HOST", "0.0.0.0")
port = int(os.environ.get("MCP_PORT", "8000"))

# Create global FastMCP instance with lifespan support
mcp_app = FastMCP(
    "IT Tools API", description="MCP server providing IT tools and utilities", lifespan=lifespan, host=host, port=port
)
