# Benedict - Local Voice Dictation
# Production Dockerfile for Cloud Run
#
# NOTE: This deploys the Streamlit web UI only.
# Voice dictation (main.py) requires local hardware and cannot run in Cloud Run.
# Ollama must be accessible via OLLAMA_BASE_URL environment variable.

FROM python:3.11-slim

# Prevent Python from writing bytecode and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Streamlit configuration for Cloud Run
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    # Default application settings
    SESSIONS_DIR=/app/sessions

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

WORKDIR /app

# Install system dependencies
# - gcc/python3-dev: Required for some Python packages
# - curl: Health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .

# Install dependencies with production optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Create sessions directory with proper permissions
RUN mkdir -p /app/sessions && \
    chown -R appuser:appgroup /app/sessions

# Switch to non-root user
USER appuser

# Expose Cloud Run port
EXPOSE 8080

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run Streamlit app on Cloud Run port
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
