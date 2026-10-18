# -----------------------------------------------------------------------------
# Base Image: Lightweight Python 3.12 Debian slim
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Install required system tools (curl for healthchecks, build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv using the official Astral binary layer (fastest & most reliable)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set application working directory
WORKDIR /app

# Configure Python and uv environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

# Copy dependency lock files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-dev

# Copy application source code, config, and data directories
COPY src/ ./src
COPY config/ ./config

# Ensure persistent mount directories exist
RUN mkdir -p /app/data /app/storage/chroma /app/logs

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000
EXPOSE 8501

# Default entrypoint (FastAPI backend; overridden by docker-compose for Streamlit)
CMD ["uv", "run", "uvicorn", "--app-dir", "src", "backend.api.route:app", "--host", "0.0.0.0", "--port", "8000"]
