# IT Tools API

API for various IT tools, providing both REST API (FastAPI) and Model Context Protocol (MCP) interfaces.

## Setup

1. Install uv: `pip install uv`
2. Create a virtual environment: `uv venv`
3. Install dependencies: `uv sync`

## Running

### FastAPI Server

```bash
# Run directly with uvicorn
uv run uvicorn main:app --reload

# Or use the start script
./start.sh --type=fastapi
```

### MCP Server

```bash
# Run directly with Python
uv run python mcp_server.py

# Or use the start script
./start.sh --type=mcp
```

## Docker Support

The project includes multi-stage Docker builds to create separate images for FastAPI and MCP servers.

### Building and Running with Docker

```bash
# Build and run FastAPI server with Docker
./start.sh --type=fastapi --docker

# Build and run MCP server with Docker
./start.sh --type=mcp --docker
```

### Using Docker Compose

The project includes a docker-compose.yml file to run both servers simultaneously:

```bash
# Start both FastAPI and MCP servers
docker-compose up -d

# Start only FastAPI server
docker-compose up fastapi -d

# Start only MCP server
docker-compose up fastmcp -d
```

## API Documentation

- FastAPI documentation: http://localhost:8000/api/docs
- MCP server runs on http://localhost:8001 (when using docker-compose)

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.