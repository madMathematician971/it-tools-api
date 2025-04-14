# IT Tools API and MCP

API for various IT tools, providing both REST API (FastAPI) and Model Context Protocol (MCP) interfaces.

**Note:** This project is highly inspired by and based on the excellent [it-tools](https://github.com/CorentinTh/it-tools) project by Corentin Thomasset.

## Setup

1. Install uv: `pip install uv`
2. Create a virtual environment: `uv venv`
3. Install dependencies: `uv sync`

## Running

### FastAPI Server

Run the FastAPI server directly using `uv`:

```bash
# Run with hot-reloading for development
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run in production mode (example with 4 workers)
# uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### MCP Server

Run the MCP server script using `uv`:

```bash
# Run the MCP server
uv run mcp_tools_server.py

# Customize host and port via environment variables (example)
# export MCP_HOST=127.0.0.1
# export MCP_PORT=8001 
# uv run mcp_tools_server.py
```

## Docker Support

The project includes a multi-stage Dockerfile (`Dockerfile`) to create separate images for the FastAPI and MCP servers.

### Building Docker Images

```bash
# Build the FastAPI server image
docker build -t it-tools-api-fastapi:latest --target fastapi .

# Build the MCP server image
docker build -t it-tools-api-fastmcp:latest --target fastmcp .
```

### Running with Docker

```bash
# Run the FastAPI server container
docker run -d --name it-tools-fastapi -p 8000:8000 it-tools-api-fastapi:latest

```

### Using Docker Compose

The project includes a `docker-compose.yml` file to manage both services:

```bash
# Start both FastAPI and MCP servers in detached mode
docker-compose up -d

# Start only FastAPI server
docker-compose up -d fastapi

# Start only MCP server
docker-compose up -d fastmcp

# Stop and remove containers
docker-compose down
```

## API Documentation

- **FastAPI Docs:** Available at `/api/docs` on the running FastAPI server (e.g., `http://localhost:8000/api/docs` by default).
- **MCP Server:** Connect using an MCP client or the MCP Inspector. By default (when using `uv run` or `docker run`), it runs on port 8000. When using `docker-compose`, the MCP server runs on port 8001.

## Other Documentation

- **[MCP Server Details (MCP_README.md)](MCP_README.md):** Detailed information about the MCP server implementation, tools, resources, prompts, and integration.
- **[MCP Tool Tests (tests/mcp/tools/README.md)](tests/mcp/tools/README.md):** Information about the unit tests specifically for the MCP tools.

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.