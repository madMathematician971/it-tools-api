# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Add curl for healthcheck
RUN apt-get update && apt-get install -y curl 
# Install uv
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy the dependency file
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Install production dependencies system-wide
# --no-dev avoids installing development dependencies
RUN uv sync --no-dev

# Copy the application code
COPY main.py .
COPY routers/ routers/
COPY models/ models/

# Expose the port the app runs on
EXPOSE 8000


# Setup healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Command to run the application using uvicorn via uv run
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]