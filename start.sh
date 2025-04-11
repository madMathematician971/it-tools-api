#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the FastAPI application using uvicorn via uv run
echo "Starting FastAPI application with uvicorn..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 