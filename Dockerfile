# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy the dependency file
COPY pyproject.toml .

# Install production dependencies system-wide
# --system installs to the global python environment
# --no-dev avoids installing development dependencies
RUN uv sync --system --no-dev

# Copy the application code
COPY main.py .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn via uv run
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 